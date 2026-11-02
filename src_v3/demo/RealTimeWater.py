#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Real-time Water Demo (framework)
python -m src_v3.demo.RealTimeWater --mode scene --data_path F:\DataSet\ShowData --scene WaterFall --model "F:\DataSet\Output\split\run_0403_010634_af18a476\checkpoints\test.pth" --device cuda:0 --search_optimized --decoder_layer 256,512 --gs_num 24 --decoder_variant split --surface_neighbor_threshold 0 --width 1920 --height 1080 --factor 4.0 --foam_density_log_alpha 200 
目标：
1) 两种输入模式统一接口：
   - scene: 从 SceneDataset 读取 sample（与 infer 类似）
   - simulation: 接受 Simulation 输出的 pos/vel（TODO 占位）
2) while 循环主流程：
   searching -> culling -> model -> GS splatting
3) 当前阶段先稳定打印每帧读取到的 pos/vel 信息。
"""

from __future__ import annotations

import argparse
import csv
import gc
import json
import math
import statistics
import time
from dataclasses import dataclass, replace
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

import numpy as np
import torch
import torch.nn.functional as F

from src_v3.core.Searching import search
from src_v3.core.render import GaussianProjector
from src_v3.core.spatial_filters import gaussian_filter_image
from src_v3.data.camera_from_particles import camera_from_particles
from src_v3.data.foam_density import (
    NEWFOAM_DENSITY_CORNER_MAX,
    NEWFOAM_DENSITY_CORNER_MIN,
    pair_foam_density_mae_on_union_support,
    sample_foam_from_gt_network_output,
    sample_foam_from_gt_network_output_adjustV,
)
from src_v3.demo.sample_provider import SceneSampleProvider, build_provider
from src_v3.models import CovDecoderModel, DEFAULT_COV_DIM
from src_v3.training.config import InferConfig

# ``--timing_max_frames`` 为 0 时用 max(Falcor SaveFrames, 此下限)，避免 SaveFrames 默认 1 时非暂停一帧就退出。
_TIMING_MAX_WHEN_ZERO_MIN = 100

TEST_FOAM_CORNER_MIN = (-15.0, -15.0, -15.0)
TEST_FOAM_CORNER_MAX = (15.0, 15.0, 15.0)
TEST_FOAM_GRID_NUM = (300, 300, 300)



def _trilinear_sample_density_grid_sample(
    density: torch.Tensor,
    pos_v: torch.Tensor,
    cmin: torch.Tensor,
    cmax: torch.Tensor,
) -> torch.Tensor:
    """
    与原先手写 8 邻域等价语义：连续体素坐标 ``idx_f = (pos - cmin) / (cmax-cmin) * [nx,ny,nz]``，
    用 ``F.grid_sample(..., mode='bilinear', align_corners=False)`` 做三线性采样。

    ``density`` 为 ``[Nx, Ny, Nz]``（与 ``compute_Foam_Density`` 一致）；``pos_v`` 为 ``[M, 3]``。
    返回 ``[M]``。
    """
    nx, ny, nz = int(density.shape[0]), int(density.shape[1]), int(density.shape[2])
    scene = cmax - cmin
    g = pos_v.new_tensor([float(nx), float(ny), float(nz)])
    idx_f = (pos_v - cmin) / scene * g
    gx = 2.0 * (idx_f[:, 0] + 0.5) / float(max(nx, 1)) - 1.0
    gy = 2.0 * (idx_f[:, 1] + 0.5) / float(max(ny, 1)) - 1.0
    gz = 2.0 * (idx_f[:, 2] + 0.5) / float(max(nz, 1)) - 1.0
    grid = torch.stack((gx, gy, gz), dim=-1).view(1, 1, 1, -1, 3)
    vol = density.view(1, 1, nz, ny, nx)
    sampled = F.grid_sample(
        vol,
        grid,
        mode="bilinear",
        padding_mode="zeros",
        align_corners=False,
    )
    return sampled.reshape(-1)


def CountFoam(
    positions: torch.Tensor,
    cornerMin,
    cornerMax,
    gridNum,
) -> torch.Tensor:
    """
    统计每个体素内的泡沫点数量。

    - `positions`: `[N, 3]`
    - 返回: `[nx, ny, nz]`，每格为该体素内的点数
    - 盒外点按 `[cornerMin, cornerMax)` 半开区间忽略
    """
    pos = torch.as_tensor(positions)
    if pos.ndim != 2 or pos.shape[1] < 3 or pos.shape[0] == 0:
        if isinstance(gridNum, int):
            gx = gy = gz = int(gridNum)
        else:
            gx, gy, gz = int(gridNum[0]), int(gridNum[1]), int(gridNum[2])
        return torch.zeros((gx, gy, gz), dtype=torch.int32, device=pos.device if isinstance(pos, torch.Tensor) else None)

    pos = pos[:, :3].to(dtype=torch.float32)
    device = pos.device

    cmin = pos.new_tensor(cornerMin, dtype=torch.float32).view(1, 3)
    cmax = pos.new_tensor(cornerMax, dtype=torch.float32).view(1, 3)
    g = torch.as_tensor(gridNum, dtype=torch.int64, device=device).view(-1)
    if g.numel() == 1:
        g = g.repeat(3)
    nx, ny, nz = int(g[0].item()), int(g[1].item()), int(g[2].item())
    if nx <= 0 or ny <= 0 or nz <= 0:
        raise ValueError("gridNum must be positive")

    scene = (cmax - cmin).view(3)
    if bool(torch.any(scene <= 0).item()):
        raise ValueError("cornerMax must be larger than cornerMin")

    inside = torch.all((pos >= cmin) & (pos < cmax), dim=1)
    if not bool(inside.any().item()):
        return torch.zeros((nx, ny, nz), dtype=torch.int32, device=device)

    pos_in = pos[inside]
    scale = pos.new_tensor([float(nx), float(ny), float(nz)])
    idx_f = (pos_in - cmin) / scene * scale.view(1, 3)
    idx = torch.floor(idx_f).long()
    idx[:, 0] = idx[:, 0].clamp(0, nx - 1)
    idx[:, 1] = idx[:, 1].clamp(0, ny - 1)
    idx[:, 2] = idx[:, 2].clamp(0, nz - 1)

    lin = idx[:, 0] + nx * (idx[:, 1] + ny * idx[:, 2])
    hist = torch.zeros((nx * ny * nz,), dtype=torch.int32, device=device)
    hist.scatter_add_(0, lin, torch.ones_like(lin, dtype=torch.int32))
    return hist.view(nx, ny, nz)


def _foam_xyz_numpy(foam: Any) -> np.ndarray:
    """取泡沫输入的 xyz，兼容 torch.Tensor / numpy / 空输入。"""
    if foam is None:
        return np.zeros((0, 3), dtype=np.float32)
    if isinstance(foam, torch.Tensor):
        arr = foam.detach().float().cpu().numpy()
    else:
        arr = np.asarray(foam, dtype=np.float32)
    if arr.ndim != 2 or arr.shape[1] < 3 or arr.shape[0] == 0:
        return np.zeros((0, 3), dtype=np.float32)
    return np.ascontiguousarray(arr[:, :3], dtype=np.float32)


def _save_foam_voxel_scatter(
    density: torch.Tensor,
    out_path: Path,
    title: str,
    corner_min,
    corner_max,
    idx_range=None  # 新增参数：统一的索引范围 (min_vec, max_vec)
) -> None:
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    import numpy as np

    density_np = density.detach().cpu().numpy()
    
    # 确定裁剪范围
    if idx_range is not None:
        imin, imax = idx_range
        # 增加 1 个格子的 padding 避免贴边，并防止越界
        z0, y0, x0 = np.maximum(imin - 1, 0)
        z1, y1, x1 = np.minimum(imax + 2, density_np.shape)
    else:
        # 如果没有传，就按自身非零区域切（这种情况下两张图边界会不一致）
        nz = np.argwhere(density_np > 0)
        if len(nz) == 0: z0,y0,x0,z1,y1,x1 = 0,0,0,1,1,1
        else:
            z0, y0, x0 = nz.min(axis=0)
            z1, y1, x1 = nz.max(axis=0) + 1

    # 裁剪数据
    cropped = density_np[z0:z1, y0:y1, x0:x1]
    filled = cropped > 0

    # 风格设置：体素颜色和透明度
    fig = plt.figure(figsize=(8, 8), dpi=120)
    ax = fig.add_subplot(111, projection="3d")
    
    # 调色盘：使用带有深度的颜色映射
    norm = plt.Normalize(0, 200.0)
    colors = plt.cm.plasma(norm(cropped)) # 使用 plasma 增加对比度
    colors[..., 3] = np.clip(cropped / 100.0 + 0.3, 0.3, 0.8) # 动态透明度

    if np.any(filled):
        ax.voxels(filled, facecolors=colors, edgecolor='k', linewidth=0.05)
    else:
        ax.text(0.5, 0.5, 0.5, "Empty", transform=ax.transAxes)

    # 统一视角和比例
    ax.view_init(elev=25, azim=45)
    ax.set_box_aspect(filled.shape) # 关键：让长宽高比例符合实际物理形态
    
    # 隐藏坐标轴刻度，让画面更干净，只留标题
    ax.set_xticks([]); ax.set_yticks([]); ax.set_zticks([])
    ax.set_title(title, fontsize=12, fontweight='bold')

    # 背景设为淡灰色增加高级感（可选）
    ax.xaxis.set_pane_color((0.95, 0.95, 0.95, 1.0))
    
    fig.tight_layout()
    out_path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(out_path, bbox_inches='tight')
    plt.close(fig)

def writeVis(
    gt_foam: Any,
    pred_foam: Any,
    frame_id: Any = None,
    out_dir: Optional[Path] = None,
    corner_min=TEST_FOAM_CORNER_MIN,
    corner_max=TEST_FOAM_CORNER_MAX,
    grid_num=(100, 100, 100),
) -> None:
    out_root = Path(out_dir) if out_dir is not None else Path("output/realTime/foam_vis")
    frame_name = f"{int(frame_id):04d}" if frame_id is not None else "unknown"

    # 获取坐标
    gt_xyz = _foam_xyz_numpy(gt_foam)
    pred_xyz = _foam_xyz_numpy(pred_foam)
    
    # 计算体素密度
    gt_density = CountFoam(torch.from_numpy(gt_xyz), corner_min, corner_max, grid_num)
    pred_density = CountFoam(torch.from_numpy(pred_xyz), corner_min, corner_max, grid_num)

    # --- 关键步骤：计算统一的边界 ---
    # 找到所有非零格子的索引
    nz_gt = torch.nonzero(gt_density > 0)
    nz_pred = torch.nonzero(pred_density > 0)
    
    # 合并索引以寻找全局最大/最小
    all_nz = torch.cat([nz_gt, nz_pred], dim=0)
    
    if all_nz.shape[0] > 0:
        # 获取体素索引的统一边界 (min_idx, max_idx)
        idx_min = all_nz.min(dim=0).values.numpy()
        idx_max = all_nz.max(dim=0).values.numpy()
    else:
        # 如果全是空的，回退到默认
        idx_min, idx_max = np.array([0,0,0]), np.array(grid_num)

    # 将这个统一的“索引范围”传给绘图函数
    common_idx_range = (idx_min, idx_max)

    # 绘图调用
    _save_foam_voxel_scatter(
        gt_density,
        out_root / f"frame_{frame_name}_gt_foam_voxels.png",
        f"GT Foam - {frame_name}",
        corner_min, corner_max,
        idx_range=common_idx_range  # 传入统一边界
    )
    _save_foam_voxel_scatter(
        pred_density, 
        out_root / f"frame_{frame_name}_pred_foam_voxels.png",
        f"Pred Foam - {frame_name}",
        corner_min, corner_max,
        idx_range=common_idx_range  # 传入统一边界
    )

def computeExpectCount(sample,pos,total_num):
    sample = torch.as_tensor(sample, dtype=torch.float32)
    pos = torch.as_tensor(pos, dtype=torch.float32)
    total_num = int(total_num)

    g = torch.as_tensor(TEST_FOAM_GRID_NUM, dtype=torch.int64, device=pos.device).view(-1)
    if g.numel() == 1:
        g = g.repeat(3)
    nx, ny, nz = int(g[0].item()), int(g[1].item()), int(g[2].item())

    if sample.ndim != 1:
        sample = sample.reshape(-1)
    if pos.ndim != 2 or pos.shape[1] < 3 or pos.shape[0] == 0 or sample.numel() == 0:
        return torch.zeros((nx, ny, nz), dtype=torch.int32, device=pos.device)

    pos = pos[:, :3]
    if sample.numel() != pos.shape[0]:
        raise ValueError("sample and pos must have the same length")

    sample_sum = float(sample.sum().item())
    if sample_sum <= 0.0:
        return torch.zeros((nx, ny, nz), dtype=torch.int32, device=pos.device)
    sample = sample / sample_sum

    cmin = pos.new_tensor(TEST_FOAM_CORNER_MIN, dtype=torch.float32).view(1, 3)
    cmax = pos.new_tensor(TEST_FOAM_CORNER_MAX, dtype=torch.float32).view(1, 3)
    scene = (cmax - cmin).view(3)

    inside = torch.all((pos >= cmin) & (pos < cmax), dim=1)
    if not bool(inside.any().item()):
        return torch.zeros((nx, ny, nz), dtype=torch.int32, device=pos.device)

    pos_in = pos[inside]
    sample_in = sample[inside]
    sample_in_sum = float(sample_in.sum().item())
    if sample_in_sum <= 0.0:
        return torch.zeros((nx, ny, nz), dtype=torch.int32, device=pos.device)
    sample_in = sample_in / sample_in_sum

    scale = pos.new_tensor([float(nx), float(ny), float(nz)])
    idx_f = (pos_in - cmin) / scene * scale.view(1, 3)
    idx = torch.floor(idx_f).long()
    idx[:, 0] = idx[:, 0].clamp(0, nx - 1)
    idx[:, 1] = idx[:, 1].clamp(0, ny - 1)
    idx[:, 2] = idx[:, 2].clamp(0, nz - 1)

    lin = idx[:, 0] + nx * (idx[:, 1] + ny * idx[:, 2])
    voxel_prob = torch.zeros((nx * ny * nz,), dtype=torch.float32, device=pos.device)
    voxel_prob.scatter_add_(0, lin, sample_in)

    voxel_expect = torch.floor(voxel_prob * float(total_num)).to(torch.int32)
    return voxel_expect.view(nx, ny, nz)


def computeFoamError(prob,pos,gt_foam_xyz):
    from src_v3.data.foam_density import compute_Foam_Density,inverse_map_gt_log_to_density
    if gt_foam_xyz is None or int(gt_foam_xyz.shape[0]) == 0:
        return None
    density = compute_Foam_Density(gt_foam_xyz.cpu(),0.0,TEST_FOAM_CORNER_MIN,TEST_FOAM_CORNER_MAX,TEST_FOAM_GRID_NUM,1.0,100.0,apply_gt_log_map=False)
    density = density.to(device=pos.device, dtype=torch.float32)

    cmin = torch.tensor(TEST_FOAM_CORNER_MIN, device=pos.device)
    cmax = torch.tensor(TEST_FOAM_CORNER_MAX, device=pos.device)

    densityGT = _trilinear_sample_density_grid_sample(density, pos, cmin, cmax)
    prob = inverse_map_gt_log_to_density(prob,200)
    prob = torch.nan_to_num(prob.reshape(-1).float(), nan=0.0, posinf=0.0, neginf=0.0).clamp_min(0.0)
    densityGT = torch.nan_to_num(densityGT.reshape(-1).float(), nan=0.0, posinf=0.0, neginf=0.0).clamp_min(0.0)

    n_pre = int((prob > 0).sum().item())
    n_gt = int((densityGT > 0).sum().item())
    sample_n = min(int(gt_foam_xyz.shape[0]), n_pre, n_gt)
    if sample_n <= 0:
        print("[computeFoamError] skip: no positive weights to sample")
        return None

    idx_pre = torch.multinomial(prob, sample_n, replacement=False)
    idx_gt = torch.multinomial(densityGT, sample_n, replacement=False)

    mask = densityGT > 0.0

    f_pre = pos[idx_pre]
    f_gt = pos[idx_gt]

    if mask != None:
        mae = torch.abs(densityGT[mask] - prob[mask]).mean()

        sample_gt = densityGT[mask]
        sample_pre = prob[mask]

        gt_Expect = computeExpectCount(sample_gt,pos[mask],gt_foam_xyz.shape[0])
        pre_Expect = computeExpectCount(sample_pre,pos[mask],gt_foam_xyz.shape[0])

        localmask = gt_Expect > 0.0

        print(gt_Expect[localmask])
        print(pre_Expect[localmask])


        if bool(localmask.any().item()):
            gt_expect_f = gt_Expect[localmask].to(dtype=torch.float32)
            pre_expect_f = pre_Expect[localmask].to(dtype=torch.float32)
            errorCount = torch.abs(gt_expect_f - pre_expect_f).mean()
            # 先算逐体素相对误差，再按该体素数量占总数比例放缩（占比越大权重越高）
            rel_per_voxel = torch.abs(gt_expect_f - pre_expect_f) / gt_expect_f.clamp_min(1e-6) * 100.0
            rel_per_voxel = torch.clamp(rel_per_voxel, 0.0, 100.0)
            total_gt = max(int(gt_foam_xyz.shape[0]), 1)
            scale = torch.min(gt_expect_f,pre_expect_f)/ float(total_gt)
            errorRel = (rel_per_voxel * scale).sum()
        else:
            errorCount = torch.tensor(float("nan"), device=gt_Expect.device)
            errorRel = torch.tensor(float("nan"), device=gt_Expect.device)

        print(f"[computeFoamError] errorCount={errorCount:.6f}, errorRel={errorRel:.6f}")

    else:
        mae = None
        errorCount = None
        errorRel = None
    
    Density_pre = CountFoam(f_pre,TEST_FOAM_CORNER_MIN,TEST_FOAM_CORNER_MAX,TEST_FOAM_GRID_NUM)
    Density_gt = CountFoam(f_gt,TEST_FOAM_CORNER_MIN,TEST_FOAM_CORNER_MAX,TEST_FOAM_GRID_NUM)

    Density_pre_f = Density_pre.to(dtype=torch.float32)
    Density_gt_f = Density_gt.to(dtype=torch.float32)
    both_nonzero = (Density_pre_f > 0) & (Density_gt_f > 0)
    both_count = int(both_nonzero.sum().item())
    if both_count <= 0:
        print("[computeFoamError] both_nonzero_voxels=0 error_pct=nan")
        return {
            "Density_mae":mae,
            "CountError":errorCount,
            "CountErrorRel":errorRel,
            "both_nonzero_voxels": 0,
            "mean_error_pct_both_nonzero": float("nan"),
        }
    

    pred_vals = Density_pre_f[both_nonzero]
    gt_vals = Density_gt_f[both_nonzero]
    error_pct = torch.abs(pred_vals - gt_vals) / gt_vals.clamp_min(1e-6) * 100.0
    error_pct = torch.clamp(error_pct, 0.0, 100.0)
    mean_error_pct = float(error_pct.mean().item())
    print(
        f"[computeFoamError] both_nonzero_voxels={both_count} "
        f"mean_error_pct_both_nonzero={mean_error_pct:.6f}"
    )

    return {
        "Density_mae":mae,
        "CountError":errorCount,
        "CountErrorRel":errorRel,
        "both_nonzero_voxels": both_count,
        "mean_error_pct_both_nonzero": mean_error_pct,
    }


def _to_plain_number(v: Any):
    """将 tensor/标量统一转为 Python float（NaN/Inf 保留），无法转换时返回原值。"""
    if isinstance(v, torch.Tensor):
        if v.numel() == 0:
            return float("nan")
        return float(v.detach().float().mean().item())
    if isinstance(v, (np.floating, float, int)):
        return float(v)
    return v



def _effective_timing_max_frames(cfg: DemoConfig, runner: RealTimeWaterRunner) -> int:
    raw = int(getattr(cfg, "timing_max_frames", 0) or 0)
    sf = max(1, int(runner.falcorRender.getSaveFrames()))
    sfs = max(0, int(runner.falcorRender.getSaveFrameStart()))
    if raw > 0:
        return max(1, raw)
    return max(1, sfs + sf, _TIMING_MAX_WHEN_ZERO_MIN)


def sample_gt_foam_positions_xyz(sample: Dict[str, Any], device: torch.device) -> Optional[torch.Tensor]:
    """数据集 GT 泡沫位置 xyz，取自 ``sample['foam']['positions']`` 前三维；无则 None。"""
    foam = sample.get("foam")
    if not foam:
        return None
    pos = foam.get("positions")
    if pos is None:
        return None
    t = torch.as_tensor(pos, dtype=torch.float32)
    if t.ndim != 2 or t.shape[1] < 3:
        return None
    if t.shape[0] == 0:
        return None
    return t[:, :3].to(device=device, dtype=torch.float32, non_blocking=True)


def sample_gt_newfoam_positions_np(sample: Dict[str, Any]) -> np.ndarray:
    """GT 新生泡沫 xyz，来自 ``sample['newfoam']['positions']`` 前三维；无则空数组。"""
    nf = sample.get("newfoam") or {}
    pos = nf.get("positions")
    if pos is None:
        return np.zeros((0, 3), dtype=np.float32)
    t = np.asarray(pos, dtype=np.float32)
    if t.ndim != 2 or t.shape[1] < 3:
        return np.zeros((0, 3), dtype=np.float32)
    return np.ascontiguousarray(t[:, :3])


def sample_gt_newfoam_positions_xyz(sample: Dict[str, Any], device: torch.device) -> Optional[torch.Tensor]:
    """数据集 GT 新生泡沫位置 xyz，取自 ``sample['newfoam']['positions']`` 前三维；无则 None。"""
    nf = sample.get("newfoam") or {}
    pos = nf.get("positions")
    if pos is None:
        return None
    t = torch.as_tensor(pos, dtype=torch.float32)
    if t.ndim != 2 or t.shape[1] < 3:
        return None
    if t.shape[0] == 0:
        return None
    return t[:, :3].to(device=device, dtype=torch.float32, non_blocking=True)


def _sample_fluid_particle_count(sample: Dict[str, Any]) -> int:
    """流体粒子数，与 ``sample['num_particles']`` / ``positions`` 行数一致。"""
    n = sample.get("num_particles")
    if n is not None:
        return int(n)
    pos = sample.get("positions")
    if pos is None:
        return 0
    if hasattr(pos, "shape") and len(pos.shape) >= 1:
        return int(pos.shape[0])
    return 0


def sample_has_gt_newfoam(sample: Dict[str, Any]) -> bool:
    """本帧是否至少有一个 GT newFoam 点（会话 MAE 平均与 foam CSV 仅统计此类帧）。"""
    nf = sample.get("newfoam") or {}
    pos = nf.get("positions")
    if pos is None:
        return False
    t = np.asarray(pos)
    if t.ndim != 2 or t.shape[1] < 3:
        return False
    return int(t.shape[0]) > 0


@dataclass
class DemoConfig:
    mode: str = "scene"  # "scene" | "simulation"
    data_path: str = ""
    scene: str = ""
    model: Optional[str] = None
    device: str = "cuda:0"
    width: int = 256
    height: int = 256
    loop: bool = True
    pause: bool = False
    save_dir: str = "output/realTime"

    # searching
    search_factor: float = 8
    search_workers: int = -1
    search_timing: bool = True
    search_optimized: bool = True
    search_cov_method: int = 0
    search_exclude_self: bool = False
    search_splash_threshold: int = 2
    surface_neighbor_threshold: int = 32
    surface_flatness_threshold: float = 0.45
    surface_splash_neighbor: int = 6

    # net
    net_gs_num: int = 36
    net_decoder_variant: str = "split"
    net_decoder_layers: str = "256,512,512"

    # simulation placeholder
    sim_radius: float = 0.01
    preload_scene: bool = True
    # scene 模式：是否只加载「particle+mesh 同时存在」的帧（默认 False，否则 mesh 不全时只剩极少帧）
    require_mesh: bool = False

    # 与训练 GT 一致：foam 网络输出为 y（log 映射空间），采样前做逆映射
    foam_density_log_alpha: float = 1.0
    foam_density_log_d_max: float = 1.0
    # _sample_new_foam：True=用 projector 剔除后的 *_culled；False=用网络全量 gs_pos/gs_vel/foam_prob
    foam_loss_use_culled_gaussians: bool = True
    # Timing 模式：与 dataset newFoamDensity 一致，默认每轴 100（见 foam_density.NEWFOAM_DENSITY_GRID_NUM）
    foam_metric_grid: int = 100
    # Timing 模式：汇总 JSON 路径（空则默认 output_dir/RealTimeWater_timing_summary.json）
    timing_summary_path: str = ""
    # Timing 模式：非暂停统计帧数上限（0 表示 max(Falcor SaveFrames, 全局下限)，见 _effective_timing_max_frames）
    timing_max_frames: int = 0
    # Timing 模式：compare_renderers free 写出的 chosen JSON（v1）；与 --timing 同时指定时按条目测时并写同一套 summary
    timing_chosen_log: str = ""


class RealTimeWaterRunner:
    def __init__(self, cfg: DemoConfig):
        self.cfg = cfg
        self.device = self._resolve_device(cfg.device)
        self.infer_cfg = self._build_infer_cfg(cfg)
        self.model = CovDecoderModel(self.infer_cfg.to_net_config(), cov_dim=DEFAULT_COV_DIM).to(self.device)
        self.model.eval()
        self.projector = GaussianProjector(
            width=self.infer_cfg.width,
            height=self.infer_cfg.height,
            device=self.device,
            hit_threshold=0.5,
        )
        from src_v3.core.render.falcor_manager import (
            FalcorRealTimeWaterConfig,
            FalcorRealTimeWaterRenderer,
            FalcorParticleFilterConfig,
            FalcorParticelFilterRenderer,
            FalcorBaseLineConfig,
            BaseLineRenderer,
        )

        renderConfig = FalcorRealTimeWaterConfig(
            width=cfg.width,
            height=cfg.height,
            data_path=cfg.data_path,
            scene=cfg.scene,
        )
        self.falcorRender = FalcorRealTimeWaterRenderer(renderConfig)

        filterConfig = FalcorParticleFilterConfig()
        self.falcorPartilceFilter = FalcorParticelFilterRenderer(filterConfig)

        baseLineConfig= FalcorBaseLineConfig(width=cfg.width,height=cfg.height,create_window=True)
        self.baseLineRenderer = BaseLineRenderer(baseLineConfig)

        if cfg.model:
            self._load_checkpoint(cfg.model)

    @staticmethod
    def _resolve_device(device: str) -> torch.device:
        d = (device or "cpu").strip().lower()
        if d.startswith("cuda") and not torch.cuda.is_available():
            print("[RealTimeWater] CUDA 不可用，自动回退 CPU")
            return torch.device("cpu")
        return torch.device(device)

    @staticmethod
    def _build_infer_cfg(cfg: DemoConfig) -> InferConfig:
        return InferConfig(
            output_dir="OutputRealtime",
            device=cfg.device,
            search_factor=cfg.search_factor,
            search_workers=cfg.search_workers,
            search_timing=cfg.search_timing,
            search_optimized=cfg.search_optimized,
            search_cov_method=cfg.search_cov_method,
            search_exclude_self=cfg.search_exclude_self,
            search_splash_threshold=cfg.search_splash_threshold,
            net_gs_num=cfg.net_gs_num,
            net_decoder_variant=cfg.net_decoder_variant,
            net_decoder_layers=[int(x) for x in cfg.net_decoder_layers.split(",") if x.strip()],
            width=cfg.width,
            height=cfg.height,
            surface_neighbor_threshold=cfg.surface_neighbor_threshold,
            surface_flatness_threshold=cfg.surface_flatness_threshold,
            surface_splash_neighbor=cfg.surface_splash_neighbor,
            foam_density_log_alpha=cfg.foam_density_log_alpha,
            foam_density_log_d_max=cfg.foam_density_log_d_max,
            foam_loss_use_culled_gaussians=cfg.foam_loss_use_culled_gaussians,
        )

    def _load_checkpoint(self, ckpt_path: str) -> None:
        ckpt = torch.load(ckpt_path, map_location=self.device)
        state = ckpt.get("model_state_dict", ckpt)
        self.model.load_state_dict(state, strict=True)
        self.model.eval()
        print(f"[RealTimeWater] loaded checkpoint: {ckpt_path}")

    def _sync_if_needed(self) -> None:
        if self.device.type == "cuda":
            torch.cuda.synchronize(self.device)

    def cleanup_cuda_memory(self) -> None:
        """每帧结束后显式回收 Python 引用并清理 CUDA 缓存。"""
        if self.device.type != "cuda":
            return
        self._sync_if_needed()
        gc.collect()
        torch.cuda.empty_cache()
        # 回收 IPC 共享缓存，进一步降低长期运行时显存占用波动
        torch.cuda.ipc_collect()

    def save_result(self, frame_id: int, render_result: Optional[torch.Tensor]) -> None:
        if render_result is None:
            print(f"[RealTimeWater] skip save frame {frame_id}: render_result is None")
            return
        out_dir = Path(self.cfg.save_dir).expanduser().resolve()
        out_dir.mkdir(parents=True, exist_ok=True)
        out_path = out_dir / f"frame_{int(frame_id):04d}.exr"
        try:
            import pyexr
        except ImportError:
            print("[RealTimeWater] pyexr 未安装，无法保存 EXR。请安装: pip install pyexr")
            return
        img = render_result.detach().float().cpu().numpy()
        pyexr.write(str(out_path), img)
        print(f"[RealTimeWater] saved result: {out_path}")

    def _sample_new_foam(
        self,
        gs_pos: torch.Tensor,
        gs_vel: torch.Tensor,
        foam_gt_y: Optional[torch.Tensor],
        factor = 1.0,
        sampleTimes: int = 2000,
        noiseThreshold: float = 0.002,
    ) -> torch.Tensor:
        """
        将网络 foam 输出视为 GT 监督空间 y（与 ``map_foam_density_to_gt_log`` 一致），
        经 :func:`~src_v3.data.foam_density.inverse_map_gt_log_to_density` 得到密度尺度 d，
        再 ``p = (d / d_ref).clamp(0,1)`` 做 Bernoulli；命中行返回 ``[pos | vel]``，shape ``[M, 6]``。
        Falcor 仅需要 xyz：调用方对 ``newFoam[:, :3]`` 切片。
        """
        cfg = self.infer_cfg
        return sample_foam_from_gt_network_output(
            gs_pos,
            gs_vel,
            foam_gt_y,
            alpha=float(getattr(cfg, "foam_density_log_alpha", 1.0)),
            d_max_reference=float(getattr(cfg, "foam_density_log_d_max", 1.0)),
            factor=float(factor),
            noiseThreshold=noiseThreshold,
            sampleTimes=sampleTimes,
        )

    def prepare_sample(self, sample: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        if sample is None:
            return None
        pos = sample.get("positions")
        vel = sample.get("vel")
        if pos is None:
            return None
        if not isinstance(pos, torch.Tensor):
            pos = torch.as_tensor(pos, dtype=torch.float32)
        if vel is not None and not isinstance(vel, torch.Tensor):
            vel = torch.as_tensor(vel, dtype=torch.float32)
        # 统一数据流：读取到后立刻放到 runner device（通常是 GPU）
        pos = pos.to(self.device, dtype=torch.float32, non_blocking=True)
        if vel is not None:
            vel = vel.to(self.device, dtype=torch.float32, non_blocking=True)
        sample["positions"] = pos
        sample["vel"] = vel
        sample["num_particles"] = int(sample.get("num_particles", pos.shape[0]))
        sample["radius"] = float(sample.get("radius", self.cfg.sim_radius))
        if sample.get("camera") is None:
            sample["camera"] = camera_from_particles(pos)
        return sample

    def _prepare_inputs(
        self,
        sample: Dict[str, Any],
        *,
        assume_prepared: bool,
    ) -> Optional[Dict[str, Any]]:
        if not assume_prepared:
            sample = self.prepare_sample(sample)
        if sample is None:
            return None
        n = int(sample["num_particles"])
        if n <= 0:
            return None
        return sample

    def cullSurfaceParticles(self,pos:torch.Tensor,radius:float) -> torch.Tensor:
        """
        Cull Surface Particles By Falcor
        """

        self.falcorPartilceFilter.setCamera(self.falcorRender.get_FalcorCamInstance())

        _ = self.falcorPartilceFilter.filterParticle(pos,radius)


        return _,self.falcorPartilceFilter.getDownSampleX()

    def _run_search_cull_model_splat(self, sample: Dict[str, Any],falcorCamera:Dict[str, Any]) -> Optional[Dict[str, torch.Tensor]]:
        cfg = self.infer_cfg
        pos = sample["positions"]
        vel = sample.get("vel")
        n = int(sample["num_particles"])
        particle_radius = float(sample["radius"])
        radius = cfg.search_factor * particle_radius
        minRadius = particle_radius*2

        """
        Cull By Flaocr
        """
        surfaceIndex,downSampleX = self.cullSurfaceParticles(pos,particle_radius)
        if surfaceIndex.shape[0] == 0:
            surfaceIndex = torch.tensor([0],dtype=torch.uint32,device=self.device)
        
        surfaceIndex = surfaceIndex.long()
        pos = pos[surfaceIndex]
        vel = vel[surfaceIndex]

        #To Do: DonwSample then Use Bigger Radius

        src, dst, cov_pos, cov_vel, center_delta = search(
            pos,
            radius*downSampleX,
            vel=vel,
            minRadius=minRadius*downSampleX,
            pos_scale=radius*downSampleX,
            exclude_self=cfg.search_exclude_self,
            splash_threshold=cfg.search_splash_threshold,
            workers=cfg.search_workers,
            timing=cfg.search_timing,
            use_optimized=cfg.search_optimized,
            cov_method=cfg.search_cov_method,
        )

        cov_pos_t = cov_pos.to(device=self.device, dtype=torch.float32)
        cov_vel_t = cov_vel.to(device=self.device, dtype=torch.float32)
        center_delta_t = center_delta.to(device=self.device, dtype=torch.float32)
        pos_t = pos.to(device=self.device, dtype=torch.float32)


        with torch.no_grad():
            gs_pos, gs_scale, gs_rotation, target_n, foam_prob, foam_prob_raw = self.model(
                cov_pos_t,
                cov_vel_t,
                center_delta_t,
                pos_t,
                radius=float(particle_radius*downSampleX),
                kernel_size=float(cfg.search_factor),
            )
            gs_num = int(cfg.net_gs_num)
            gs_anchor_pos = pos_t.unsqueeze(1).repeat(1, gs_num, 1).reshape(-1, 3)
            if vel is not None:
                vel_t = vel.to(device=self.device, dtype=torch.float32)
                gs_vel = vel_t.unsqueeze(1).repeat(1, gs_num, 1).reshape(-1, 3)
            else:
                gs_vel = torch.zeros_like(gs_pos, device=self.device)

        torch.cuda.synchronize()
        camera = falcorCamera
        normal, depth, hit, vel_img, foam_prob_culled, gs_pos_culled, foam_prob_raw_culled, gs_vel_culled, gs_anchor_pos_culled = (
            self.projector.project(
                camera,
                gs_pos,
                gs_scale,
                gs_rotation,
                target_n,
                None,
                foam_prob,
                gs_vel,
                foam_prob_raw,
                gs_anchor_pos,
            )
        )
        torch.cuda.synchronize()
        foamDensity = self.falcorRender.getFoamDensity()
        #获取采样的次数 和 噪声阈值
        sampleTimes,noiseThreshold = self.falcorRender.getSampleTimesAndNoiseThreshold()
        if getattr(self.cfg, "foam_loss_use_culled_gaussians", True):
            _fp, _fv, _fprob = gs_pos_culled, gs_vel_culled, foam_prob_culled
            _fanchor = gs_anchor_pos_culled
        else:
            _fp, _fv, _fprob = gs_pos, gs_vel, foam_prob
            _fanchor = gs_anchor_pos
        new_foam = self._sample_new_foam(_fp, _fv, _fprob, foamDensity, sampleTimes, noiseThreshold)

        return {
            "normal": normal,
            "depth": depth,
            "hit": hit,
            "vel": vel_img,
            "foam_prob_culled": foam_prob_culled,
            "foam_prob_raw": foam_prob_raw_culled,
            "gs_pos_culled": gs_pos_culled,
            "newFoam": new_foam,
        }
    

    def BaseLineOutput(self,sample:Dict[str,Any],falcorCamera:Dict[str,Any]) -> Optional[Dict[str,torch.Tensor]]:

        self.baseLineRenderer.setCamera(self.falcorRender.get_FalcorCamInstance())
        pos = sample["positions"]
        radius = sample["radius"]
        samplePath = sample.get("gt_mesh_path")
        normalDepth = self.baseLineRenderer.renderNormalDepth(pos,radius,samplePath)

        hit = torch.all(normalDepth!=0,dim=-1)

        #与 ``GaussianProjector`` 在 N=0 时一致：culled 泡沫概率为 [0,1]，避免 1D 空张量维数不对
        _z1 = torch.zeros((0, 1), device=self.device, dtype=torch.float32)
        _z3 = torch.zeros((0, 3), device=self.device, dtype=torch.float32)
        _z6 = torch.zeros((0, 6), device=self.device, dtype=torch.float32)
        return {
            "normal": normalDepth[:, :, :3],
            "depth": normalDepth[:, :, 3:4],
            "hit": hit,
            "vel": torch.zeros(
                (normalDepth.shape[0], normalDepth.shape[1], 3),
                device=self.device,
                dtype=torch.float32,
            ),
            "foam_prob_culled": _z1,
            "foam_prob_raw": _z1,
            "gs_pos_culled": _z3,
            "newFoam": _z6,
        }

    def process_frame_realtime(
        self,
        sample: Dict[str, Any],
        refresh: bool,
        *,
        assume_prepared: bool = False,
    ) -> Optional[Dict[str, torch.Tensor]]:
        sample = self._prepare_inputs(sample, assume_prepared=assume_prepared)
        if sample is None:
            return None
        
        falcorCamera = self.falcorRender.get_camera()

        normalSelected = self.falcorRender.getNormalSelected()
        
        torch.cuda.synchronize()
        if normalSelected == 0:
            outputs = self._run_search_cull_model_splat(sample, falcorCamera)
        else:
            outputs = self.BaseLineOutput(sample,falcorCamera)
        torch.cuda.synchronize()

        if outputs is None:
            return None
        gt_new = sample_gt_newfoam_positions_np(sample)

        pos = sample["positions"]
        radius = sample["radius"]

        frame_id = sample.get("meta_frame_id", -1)
        self.falcorRender.setFrameId(frame_id)

        waterND = torch.cat((outputs["normal"], outputs["depth"]), dim=-1)
        #Gaussian Filter On waterNormal
        kernelSize = self.falcorRender.getGaussianFilterKernelSize()
        sigma = self.falcorRender.getGaussianFilterSigma()
        filter_iterations = self.falcorRender.getGaussianFilterIterations()
        if kernelSize > 1:
            waterND = gaussian_filter_image(
                waterND,
                kernel_size=kernelSize,
                sigma=sigma,
                spatial_layout="hwc",
                exclude_zero=True,
                iterations=3,
            )
        surfaceVelDepth = torch.cat((outputs["vel"], outputs["depth"]), dim=-1)
        newFoam = outputs["newFoam"]
        gt_foam_xyz = sample_gt_foam_positions_xyz(sample, self.device)
        """
        Run Falcor Render
        """

        if self.falcorRender.UseGTNewFoam():
            size = gt_new.shape[0]
            
            if size == 0:
                newFoam = torch.zeros((0, newFoam.shape[1]), dtype=newFoam.dtype, device=newFoam.device)
            else:

                temp = torch.zeros((size, newFoam.shape[1]), dtype=newFoam.dtype, device=newFoam.device)

                gt_tensor = torch.from_numpy(gt_new).to(dtype=newFoam.dtype, device=newFoam.device)
                temp[:, :3] = gt_tensor
                newFoam = temp

        
        render_result = self.falcorRender.render_real_time_water(
            pos,
            radius,
            waterND,
            surfaceVelDepth,
            newFoam,
            refresh,
            gt_foam_positions=gt_foam_xyz,
            gtNewFoamNum=int(gt_new.shape[0]),
        )
        outputs["meta_next_is_loop"] = bool(sample.get("meta_next_is_loop", False))
        outputs["meta_is_last_frame_in_scene"] = bool(sample.get("meta_is_last_frame_in_scene", False))
        outputs["meta_provider_idx"] = int(sample.get("meta_provider_idx", -1))
        outputs["meta_total_frames"] = int(sample.get("meta_total_frames", -1))
        if self.falcorRender.getSaveResult() or self.falcorRender.getSaveCur():
            outputs["render_result"] = render_result
        outputs["timing_info"] = None
        return outputs

    def process_frame_timing(
        self,
        sample: Dict[str, Any],
        refresh: bool,
        *,
        assume_prepared: bool = False,
    ) -> Optional[Dict[str, torch.Tensor]]:
        self._sync_if_needed()
        t_total0 = time.perf_counter()

        self._sync_if_needed()
        t_prepare0 = time.perf_counter()
        sample = self._prepare_inputs(sample, assume_prepared=assume_prepared)
        self._sync_if_needed()
        t_prepare1 = time.perf_counter()
        if sample is None:
            return None

        cfg = self.infer_cfg
        pos = sample["positions"]
        vel = sample.get("vel")
        n = int(sample["num_particles"])
        particle_radius = float(sample["radius"])
        radius = cfg.search_factor * particle_radius
        minRadius = particle_radius*2
        gt_foam_xyz = sample_gt_foam_positions_xyz(sample, self.device)

        self._sync_if_needed()
        t_cull0 = time.perf_counter()
        # 与 realtime 分支保持一致：先用 Falcor 过滤表面粒子，再做 search
        surfaceIndex,downSampleX = self.cullSurfaceParticles(pos, particle_radius)
        surface_num = int(surfaceIndex.shape[0])
        if surfaceIndex.shape[0] == 0:
            surfaceIndex = torch.tensor([0], dtype=torch.uint32, device=self.device)
        surfaceIndex = surfaceIndex.long()
        pos = pos[surfaceIndex]
        vel = vel[surfaceIndex]
        self._sync_if_needed()
        t_cull1 = time.perf_counter()

        self._sync_if_needed()
        t_search0 = time.perf_counter()
        src, dst, cov_pos, cov_vel, center_delta = search(
            pos,
            radius*downSampleX,
            vel=vel,
            minRadius=minRadius*downSampleX,
            pos_scale=radius*downSampleX,
            exclude_self=cfg.search_exclude_self,
            splash_threshold=cfg.search_splash_threshold,
            workers=cfg.search_workers,
            timing=cfg.search_timing,
            use_optimized=cfg.search_optimized,
            cov_method=cfg.search_cov_method,
        )
        self._sync_if_needed()
        t_search1 = time.perf_counter()

        cov_pos_t = cov_pos.to(device=self.device, dtype=torch.float32)
        cov_vel_t = cov_vel.to(device=self.device, dtype=torch.float32)
        center_delta_t = center_delta.to(device=self.device, dtype=torch.float32)
        pos_t = pos.to(device=self.device, dtype=torch.float32)

        self._sync_if_needed()
        t_model0 = time.perf_counter()
        with torch.no_grad():
            gs_pos, gs_scale, gs_rotation, target_n, foam_prob, foam_prob_raw = self.model(
                cov_pos_t,
                cov_vel_t,
                center_delta_t,
                pos_t,
                radius=float(particle_radius*downSampleX),
                kernel_size=float(cfg.search_factor),
            )
            if vel is not None:
                vel_t = vel.to(device=self.device, dtype=torch.float32)
                gs_num = int(cfg.net_gs_num)
                gs_anchor_pos = pos_t.unsqueeze(1).repeat(1, gs_num, 1).reshape(-1, 3)
                gs_vel = vel_t.unsqueeze(1).repeat(1, gs_num, 1).reshape(-1, 3)
            else:
                gs_vel = torch.zeros_like(gs_pos, device=self.device)
        self._sync_if_needed()
        t_model1 = time.perf_counter()

        camera = self.falcorRender.get_camera()
        self._sync_if_needed()
        t_splat0 = time.perf_counter()
        normal, depth, hit, vel_img, foam_prob_culled, gs_pos_culled, foam_prob_raw_culled, gs_vel_culled,gs_anchor_pos_culled = (
            self.projector.project(
                camera,
                gs_pos,
                gs_scale,
                gs_rotation,
                target_n,
                None,
                foam_prob,
                gs_vel,
                foam_prob_raw,
                gs_anchor_pos,
            )
        )
        self._sync_if_needed()
        t_splat1 = time.perf_counter()

        sampleTimes,noiseThreshold = self.falcorRender.getSampleTimesAndNoiseThreshold()
        # 与 _run_search_cull_model_splat（非 timing）一致：Falcor 泡沫密度作为采样 factor
        foamDensity = self.falcorRender.getFoamDensity()
        if getattr(self.cfg, "foam_loss_use_culled_gaussians", True):
            _fp, _fv, _fprob = gs_pos_culled, gs_vel_culled, foam_prob_culled
            _fanchor = gs_anchor_pos_culled
        else:
            _fp, _fv, _fprob = gs_pos, gs_vel, foam_prob
            _fanchor = gs_anchor_pos
        new_foam = self._sample_new_foam(_fp, _fv, _fprob, foamDensity, sampleTimes, noiseThreshold)
        outputs = {
            "normal": normal,
            "depth": depth,
            "hit": hit,
            "vel": vel_img,
            "foam_prob_culled": foam_prob_culled,
            "foam_prob_raw": foam_prob_raw_culled,
            "gs_pos_culled": gs_pos_culled,
            "newFoam": new_foam,
        }

        gt_newfoam_xyz = sample_gt_newfoam_positions_xyz(sample, self.device)
        #Compute FoamError
        if gt_newfoam_xyz is not None:
            #print(gt_newfoam_xyz.shape)
            # 与训练一致：GT 采样位置使用每个高斯对应的父流体粒子锚点
            test = computeFoamError(_fprob, _fanchor, gt_newfoam_xyz)
            writeVis(
                gt_newfoam_xyz,
                new_foam,
                frame_id=sample.get("meta_frame_id", -1),
                out_dir=Path(self.cfg.save_dir).expanduser().resolve() / "foam_vis",
                grid_num=(int(self.cfg.foam_metric_grid),) * 3,
            )
        else:
            test = None

        

        # 采样 newFoam vs GT newFoam：与 dataset ``newFoamDensity`` 相同方案（固定 [-5,5]^3、compute_Foam_Density）
        pred_nf_np = (
            new_foam[:, :3].detach().float().cpu().numpy()
            if int(new_foam.shape[0]) > 0
            else np.zeros((0, 3), dtype=np.float32)
        )
        gt_nf_np = sample_gt_newfoam_positions_np(sample)
        _nf = sample.get("newfoam") or {}
        _r_foam = float(_nf.get("radius", sample["radius"]))
        foam_density_mae, foam_density_union_voxels = pair_foam_density_mae_on_union_support(
            pred_nf_np,
            gt_nf_np,
            _r_foam,
            gridNum=int(self.cfg.foam_metric_grid),
            Densityfactor=1.0,
            log_map_alpha=float(self.infer_cfg.foam_density_log_alpha),
            log_map_d_max=float(self.infer_cfg.foam_density_log_d_max),
        )

        # 与 realtime 路径保持一致：加入 Falcor 实时渲染
        pos = sample["positions"]
        radius = sample["radius"]
        waterND = torch.cat((outputs["normal"], outputs["depth"]), dim=-1)
        surfaceVelDepth = torch.cat((outputs["vel"], outputs["depth"]), dim=-1)
        newFoam = outputs["newFoam"]
        gt_foam_xyz = sample_gt_foam_positions_xyz(sample, self.device)

        self._sync_if_needed()
        t_falcor0 = time.perf_counter()
        render_result = self.falcorRender.render_real_time_water(
            pos,
            radius,
            waterND,
            surfaceVelDepth,
            newFoam,
            refresh,
            gt_foam_positions=gt_foam_xyz,
            gtNewFoamNum=int(gt_nf_np.shape[0]),
        )
        self._sync_if_needed()
        t_falcor1 = time.perf_counter()

        t_total1 = time.perf_counter()
        prepare_ms = (t_prepare1 - t_prepare0) * 1000.0
        search_ms = (t_search1 - t_search0) * 1000.0
        cull_ms = (t_cull1 - t_cull0) * 1000.0
        model_ms = (t_model1 - t_model0) * 1000.0
        splat_ms = (t_splat1 - t_splat0) * 1000.0
        core_ms = search_ms + cull_ms + model_ms + splat_ms
        falcor_ms = (t_falcor1 - t_falcor0) * 1000.0
        total_ms = (t_total1 - t_total0) * 1000.0
        _foam_pred_n = int(pred_nf_np.shape[0])
        _foam_gt_n = int(gt_nf_np.shape[0])
        timing_info = {
            "prepare_ms": prepare_ms,
            "search_ms": search_ms,
            "cull_ms": cull_ms,
            "model_ms": model_ms,
            "splat_ms": splat_ms,
            "core_ms": core_ms,
            "falcor_ms": falcor_ms,
            "total_ms": total_ms,
            "foam_density_mae": foam_density_mae,
            "foam_density_union_voxels": float(foam_density_union_voxels),
            "foam_pred_num": _foam_pred_n,
            "foam_gt_num": _foam_gt_n,
            "foam_metric_grid": int(self.cfg.foam_metric_grid),
            "surface_num": int(surface_num),
        }
        if isinstance(test, dict):
            timing_info["foam_error_density_mae"] = _to_plain_number(test.get("Density_mae"))
            timing_info["foam_error_count"] = _to_plain_number(test.get("CountError"))
            timing_info["foam_error_rel"] = _to_plain_number(test.get("CountErrorRel"))
        _mae_s = f"{foam_density_mae:.6f}" if foam_density_mae == foam_density_mae else "nan"
        """
        print(
            f"[RealTimeWaterTiming] prepare={prepare_ms:.2f} ms, "
            f"search={search_ms:.2f} ms, "
            f"cull={cull_ms:.2f} ms, "
            f"model={model_ms:.2f} ms, "
            f"splat={splat_ms:.2f} ms, "
            f"falcor={falcor_ms:.2f} ms, "
            f"total={total_ms:.2f} ms | "
            f"surface_num={surface_num} | "
            f"foam_density_mae={_mae_s} (union_voxels={foam_density_union_voxels})"
        )
        print(
            f"[RealTimeWaterFoamMetric] "
            f"pred_newfoam={_foam_pred_n} gt_newfoam={_foam_gt_n} "
            f"foam_density_mae={_mae_s} union_voxels={foam_density_union_voxels} "
            f"grid={int(self.cfg.foam_metric_grid)}^3 "
            f"box_min={tuple(float(x) for x in NEWFOAM_DENSITY_CORNER_MIN)} "
            f"box_max={tuple(float(x) for x in NEWFOAM_DENSITY_CORNER_MAX)} "
            f"(same as dataset newFoamDensity) "
            f"foam_radius={_r_foam:.6g}"
        )
        """
        outputs["meta_next_is_loop"] = bool(sample.get("meta_next_is_loop", False))
        outputs["meta_is_last_frame_in_scene"] = bool(sample.get("meta_is_last_frame_in_scene", False))
        outputs["meta_provider_idx"] = int(sample.get("meta_provider_idx", -1))
        outputs["meta_total_frames"] = int(sample.get("meta_total_frames", -1))
        if self.falcorRender.getSaveResult():
            outputs["render_result"] = render_result
        outputs["timing_info"] = timing_info
        return outputs


def parse_args() -> DemoConfig:
    p = argparse.ArgumentParser("Real-time water demo framework")
    p.add_argument("--mode", type=str, default="scene", choices=["scene", "simulation"])
    p.add_argument("--data_path", type=str, default="")
    p.add_argument("--scene", type=str, default="")
    p.add_argument("--model", type=str, default=None)
    p.add_argument("--device", type=str, default="cuda:0")
    p.add_argument("--width", type=int, default=1920)
    p.add_argument("--height", type=int, default=1080)
    p.add_argument("--no_loop", action="store_true")
    p.add_argument(
        "--pause",
        action="store_true",
        help="暂停帧推进：运行时复用当前帧，不加载下一帧",
    )
    p.add_argument(
        "--output_dir",
        type=str,
        default="",
        help="SaveResult 输出目录（默认: <data_path>/<scene>/OurResult）",
    )

    p.add_argument("--factor", type=float, default=4.0)
    p.add_argument("--workers", type=int, default=-1)
    p.add_argument("--timing", action="store_true")
    p.add_argument("--search_optimized", action="store_true")
    p.add_argument("--cov_method", type=int, default=0)
    p.add_argument("--search_exclude_self", type=int, default=1, choices=(0, 1))
    p.add_argument("--search_splash_threshold", type=int, default=2)
    p.add_argument("--surface_neighbor_threshold", type=int, default=32)
    p.add_argument(
        "--surface_flatness_threshold",
        type=float,
        default=0.45,
        help="表面检测：位置协方差 λ_min/λ_max 小于该值视为几何表面（与 v2 surface_threshold）",
    )
    p.add_argument(
        "--surface_splash_neighbor",
        type=int,
        default=6,
        help="邻居数严格小于该值视为飞溅（始终作为表面）；独立于 search_splash_threshold",
    )

    p.add_argument("--gs_num", type=int, default=36)
    p.add_argument("--decoder_variant", type=str, default="split", choices=["split", "direct"])
    p.add_argument("--decoder_layers", type=str, default="256,512,512")
    p.add_argument("--sim_radius", type=float, default=0.01)
    p.add_argument("--no_preload_scene", action="store_true", help="scene 模式关闭启动预加载（默认预加载以降低 fetch 延迟）")
    p.add_argument(
        "--require_mesh",
        action="store_true",
        help="scene 模式只保留同时存在 particle 与 mesh 的帧（与训练 --require_mesh 一致；默认关闭以加载全部粒子帧）",
    )
    p.add_argument(
        "--foam_density_log_alpha",
        type=float,
        default=1.0,
        help="与训练 GT 一致的 foam log 映射 α（逆映射采样用）",
    )
    p.add_argument(
        "--foam_density_log_d_max",
        type=float,
        default=1.0,
        help="与训练 GT 一致的 d_ref（逆映射与 p=d/d_ref 用）",
    )
    p.add_argument(
        "--foam_loss_unculled",
        action="store_true",
        help="_sample_new_foam 使用 scale 剔除前的 gs_pos/gs_vel/foam_prob；默认与训练一致用 *_culled",
    )
    p.add_argument(
        "--foam_metric_grid",
        type=int,
        default=100,
        help="Timing 模式：newFoam 密度 MAE 的每轴体素数（默认与 dataset newFoamDensity 的 100³ 一致）",
    )
    p.add_argument(
        "--timing_summary",
        type=str,
        default="",
        help="Timing 模式：汇总指标写入的 JSON 路径（默认 output_dir/RealTimeWater_timing_summary.json）",
    )
    p.add_argument(
        "--timing_max_frames",
        type=int,
        default=0,
        help="Timing 模式：非暂停时累积多少帧后退出并写 summary；0 表示 max(Falcor SaveFrames,100)，"
        "避免 SaveFrames=1 时一帧即退出；需少帧请显式设如 1。"
        "与 --timing_chosen_log 联用时表示「最多处理日志中前 N 条」成功测时条目（0=全部）。",
    )
    p.add_argument(
        "--timing_chosen_log",
        type=str,
        default="",
        help="Timing 模式：compare_renderers free 记录的 JSON（version 1，含 scene/data_path/width/height/entries）。"
        "指定后与 --timing 联用：按 dataset_idx+camera 逐条测时并写 summary（须与 CLI 的 data_path/width/height/--scene 一致；"
        "将自动启用 --require_mesh 以与记录索引一致）。",
    )
    a = p.parse_args()
    default_output_dir = str(Path(a.data_path) / a.scene / "OurResult") if a.data_path and a.scene else "output/realTime"
    output_dir = a.output_dir if str(a.output_dir).strip() else default_output_dir
    return DemoConfig(
        mode=a.mode,
        data_path=a.data_path,
        scene=a.scene,
        model=a.model,
        device=a.device,
        width=a.width,
        height=a.height,
        loop=not a.no_loop,
        pause=bool(a.pause),
        save_dir=output_dir,
        search_factor=a.factor,
        search_workers=a.workers,
        search_timing=a.timing,
        search_optimized=a.search_optimized,
        search_cov_method=a.cov_method,
        search_exclude_self=bool(a.search_exclude_self),
        search_splash_threshold=a.search_splash_threshold,
        surface_neighbor_threshold=a.surface_neighbor_threshold,
        surface_flatness_threshold=a.surface_flatness_threshold,
        surface_splash_neighbor=a.surface_splash_neighbor,
        net_gs_num=a.gs_num,
        net_decoder_variant=a.decoder_variant,
        net_decoder_layers=a.decoder_layers,
        sim_radius=a.sim_radius,
        preload_scene=not a.no_preload_scene,
        require_mesh=bool(a.require_mesh),
        foam_density_log_alpha=a.foam_density_log_alpha,
        foam_density_log_d_max=a.foam_density_log_d_max,
        foam_loss_use_culled_gaussians=not bool(getattr(a, "foam_loss_unculled", False)),
        foam_metric_grid=int(a.foam_metric_grid),
        timing_summary_path=str(getattr(a, "timing_summary", "") or ""),
        timing_max_frames=int(getattr(a, "timing_max_frames", 0) or 0),
        timing_chosen_log=str(getattr(a, "timing_chosen_log", "") or ""),
    )


def _timing_summary_json_path(cfg: DemoConfig) -> Path:
    raw = (getattr(cfg, "timing_summary_path", None) or "").strip()
    if raw:
        return Path(raw).expanduser().resolve()
    return Path(cfg.save_dir).expanduser().resolve() / "RealTimeWater_timing_summary.json"


def _copy_timing_cam_dict(cam: Dict[str, Any]) -> Dict[str, Any]:
    return {
        "origin": [float(x) for x in cam["origin"]],
        "target": [float(x) for x in cam["target"]],
        "up": [float(x) for x in cam["up"]],
        "fov": float(cam["fov"]),
    }


def _load_timing_chosen_doc(cfg: DemoConfig, log_path: Path) -> Dict[str, Any]:
    if not log_path.is_file():
        raise SystemExit(f"[RealTimeWater] timing_chosen_log 文件不存在: {log_path}")
    doc = json.loads(log_path.read_text(encoding="utf-8"))
    if not isinstance(doc, dict) or int(doc.get("version", -1)) != 1:
        raise SystemExit(f"[RealTimeWater] timing_chosen_log 须为 JSON version 1: {log_path}")
    file_scene = str(doc.get("scene", "") or "")
    file_data = str(doc.get("data_path", "") or "")
    fw, fh = int(doc.get("width", 0)), int(doc.get("height", 0))
    entries = doc.get("entries")
    if not file_scene or not isinstance(entries, list) or not entries:
        raise SystemExit(f"[RealTimeWater] timing_chosen_log 缺少 scene 或非空 entries: {log_path}")
    if cfg.scene and cfg.scene != file_scene:
        raise SystemExit(
            f"[RealTimeWater] timing_chosen_log 中 scene={file_scene!r} 与 --scene {cfg.scene!r} 不一致"
        )
    if str(Path(cfg.data_path).resolve()) != str(Path(file_data).resolve()):
        raise SystemExit(
            f"[RealTimeWater] --data_path 与 timing_chosen_log 不一致：当前 {cfg.data_path!r}，记录 {file_data!r}"
        )
    if int(cfg.width) != fw or int(cfg.height) != fh:
        raise SystemExit(
            f"[RealTimeWater] --width/--height 须与 timing_chosen_log 一致（{fw}x{fh}），当前 {cfg.width}x{cfg.height}"
        )
    return doc


def _write_timing_summary_config(
    path: Path,
    cfg: DemoConfig,
    *,
    cull_ms: List[float],
    search_ms: List[float],
    model_ms: List[float],
    splat_ms: List[float],
    foam_mae_vals: List[float],
    foam_error_density_mae_vals: List[float],
    timing_effective_cap: int,
    max_fluid_particles: int = 0,
    max_fluid_particles_meta_frame_id: Any = None,
    max_fluid_particles_loop_frame_idx: Optional[int] = None,
    max_surface_num: int = 0,
    max_surface_num_meta_frame_id: Any = None,
    max_surface_num_loop_frame_idx: Optional[int] = None,
    timing_session_kind: str = "sequential",
    timing_chosen_log_path: Optional[str] = None,
    chosen_n_entries_file: Optional[int] = None,
    chosen_n_skip: Optional[int] = None,
    timing_frames_effective_cap_override: Optional[int] = None,
) -> None:
    def _mean(xs: List[float]) -> Optional[float]:
        if not xs:
            return None
        return float(statistics.mean(xs))

    n = len(cull_ms)
    out: Dict[str, Any] = {
        "version": 1,
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "description": "RealTimeWater Timing：各阶段耗时为「非暂停」帧上 process_frame_timing 内毫秒值的平均；泡沫 MAE 为有限值帧上的平均；fluid_particles_max / surface_num_max 为同会话非暂停统计帧上的最大值（surface_num 为 Falcor 表面剔除返回索引数，空则为 0）。",
        "mode": cfg.mode,
        "scene": cfg.scene,
        "data_path": cfg.data_path,
        "output_dir": str(Path(cfg.save_dir).expanduser().resolve()),
        "summary_frame_count": n,
        "timing_ms": {
            "culling_mean": _mean(cull_ms),
            "domain_search_mean": _mean(search_ms),
            "network_inference_mean": _mean(model_ms),
            "splatting_mean": _mean(splat_ms),
        },
        "foam_density_mae_mean": _mean(foam_mae_vals),
        "foam_density_mae_valid_frame_count": len(foam_mae_vals),
        "foam_density_mae_note": "mean over non-pause frames that have GT newFoam (>=1 point); finite MAE only",
        "foam_error_density_mae_mean": _mean(foam_error_density_mae_vals),
        "foam_error_density_mae_valid_frame_count": len(foam_error_density_mae_vals),
        "foam_error_density_mae_note": "mean over non-pause frames with finite computeFoamError()['Density_mae']",
        "timing_max_frames_config": int(getattr(cfg, "timing_max_frames", 0) or 0),
        "timing_frames_effective_cap": int(
            timing_effective_cap
            if timing_frames_effective_cap_override is None
            else timing_frames_effective_cap_override
        ),
        "timing_frames_completed": n,
        "timing_session_kind": timing_session_kind,
        "fluid_particles_max_over_timing_session": int(max_fluid_particles),
        "fluid_particles_max_at_meta_frame_id": max_fluid_particles_meta_frame_id,
        "fluid_particles_max_at_loop_frame_idx": max_fluid_particles_loop_frame_idx,
        "surface_num_max_over_timing_session": int(max_surface_num),
        "surface_num_max_at_meta_frame_id": max_surface_num_meta_frame_id,
        "surface_num_max_at_loop_frame_idx": max_surface_num_loop_frame_idx,
        "units": {
            "timing": "milliseconds",
            "foam_density_mae": "dimensionless (|d_pred-d_gt| on union support voxels)",
            "foam_error_density_mae": "dimensionless (computeFoamError()['Density_mae'])",
            "fluid_particles_max": "count",
            "surface_num_max": "count (Falcor surface cull index count before empty fallback)",
        },
    }
    if timing_chosen_log_path:
        out["timing_chosen_log"] = timing_chosen_log_path
    if chosen_n_entries_file is not None:
        out["chosen_n_entries_file"] = int(chosen_n_entries_file)
    if chosen_n_skip is not None:
        out["chosen_n_skip"] = int(chosen_n_skip)
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(out, f, indent=2, ensure_ascii=False)
        f.write("\n")


def run_loop_timing(cfg: DemoConfig, provider, runner: RealTimeWaterRunner) -> None:
    refresh = False
    frame_count = 0
    saved_count = 0
    paused_sample: Optional[Dict[str, Any]] = None
    last_saved_frame: int = -1
    foam_mae_vals: List[float] = []
    foam_error_density_mae_vals: List[float] = []
    cull_ms_list: List[float] = []
    search_ms_list: List[float] = []
    model_ms_list: List[float] = []
    splat_ms_list: List[float] = []
    max_fluid_particles = 0
    max_fluid_particles_meta_frame_id: Any = None
    max_fluid_particles_loop_frame_idx: Optional[int] = None
    max_surface_num = 0
    max_surface_num_meta_frame_id: Any = None
    max_surface_num_loop_frame_idx: Optional[int] = None
    foam_csv_path = Path(cfg.save_dir).expanduser().resolve() / "foam_density_metrics.csv"
    foam_csv_path.parent.mkdir(parents=True, exist_ok=True)
    timing_summary_path = _timing_summary_json_path(cfg)
    max_timing_frames = _effective_timing_max_frames(cfg, runner)
    timing_runs = 0
    prev_save_result_enabled = bool(runner.falcorRender.getSaveResult())
    force_loop_boundary = False
    while True:
        cfg.pause = runner.falcorRender.getPause()
        save_result_enabled = bool(runner.falcorRender.getSaveResult())
        if save_result_enabled and not prev_save_result_enabled:
            # 保存开关刚开启：从第一帧重新加载并重置保存计数
            if hasattr(provider, "reset"):
                provider.reset()
            paused_sample = None
            frame_count = 0
            saved_count = 0
            last_saved_frame = -1
            max_fluid_particles = 0
            max_fluid_particles_meta_frame_id = None
            max_fluid_particles_loop_frame_idx = None
            max_surface_num = 0
            max_surface_num_meta_frame_id = None
            max_surface_num_loop_frame_idx = None
            refresh = True
            force_loop_boundary = True
            print("[RealTimeWater] SaveResult enabled: reset provider to first frame.")
        prev_save_result_enabled = save_result_enabled
        save_frame_start = max(0, int(runner.falcorRender.getSaveFrameStart()))
        t_loop0 = time.perf_counter()
        if runner.device.type == "cuda":
            torch.cuda.synchronize(runner.device)

        t_fetch0 = time.perf_counter()
        if (not save_result_enabled) and cfg.pause and paused_sample is not None:
            sample = paused_sample
        else:
            sample = provider.next_sample()
            if sample is not None:
                paused_sample = sample
        t_fetch1 = time.perf_counter()
        if sample is None:
            continue
        if force_loop_boundary:
            # SaveResult 触发重载首帧，语义上视为“上一循环结束”
            sample["meta_next_is_loop"] = True
            sample["meta_is_last_frame_in_scene"] = True
            refresh = True
            force_loop_boundary = False

        t_prepare_outer0 = time.perf_counter()
        sample = runner.prepare_sample(sample)
        t_prepare_outer1 = time.perf_counter()
        if sample is None:
            continue
        pos = sample.get("positions")
        vel = sample.get("vel")
        frame_id = sample.get("meta_frame_id", frame_count)
        scene_name = sample.get("meta_scene", cfg.scene if cfg.scene else cfg.mode)

        if isinstance(pos, torch.Tensor):
            pos_shape = tuple(pos.shape)
            pos_dev = str(pos.device)
        else:
            pos_shape = None
            pos_dev = type(pos).__name__
        if isinstance(vel, torch.Tensor):
            vel_shape = tuple(vel.shape)
            vel_dev = str(vel.device)
        else:
            vel_shape = None
            vel_dev = type(vel).__name__

        print(
            f"[RealTimeWater][frame={frame_count}] scene={scene_name} frame_id={frame_id} "
            f"pos={pos_shape}@{pos_dev} vel={vel_shape}@{vel_dev} "
            f"next_loop={sample.get('meta_next_is_loop', False)} pause={cfg.pause}"
        )

        outputs = runner.process_frame_timing(sample, refresh=refresh, assume_prepared=True)

        if not isinstance(outputs, dict):
            continue

        ti = outputs.get("timing_info")
        if not isinstance(ti, dict):
            continue

        # 暂停时不累积 timing_runs / 各阶段耗时 / foam CSV（与 frame_count 一致）
        if not cfg.pause:
            timing_runs += 1
            cull_ms_list.append(float(ti.get("cull_ms", 0.0)))
            search_ms_list.append(float(ti.get("search_ms", 0.0)))
            model_ms_list.append(float(ti.get("model_ms", 0.0)))
            splat_ms_list.append(float(ti.get("splat_ms", 0.0)))
            _fn = _sample_fluid_particle_count(sample)
            if _fn > max_fluid_particles:
                max_fluid_particles = _fn
                max_fluid_particles_meta_frame_id = sample.get("meta_frame_id")
                max_fluid_particles_loop_frame_idx = int(frame_count)
            _sn = int(ti.get("surface_num", 0) or 0)
            if _sn > max_surface_num:
                max_surface_num = _sn
                max_surface_num_meta_frame_id = sample.get("meta_frame_id")
                max_surface_num_loop_frame_idx = int(frame_count)
            if "foam_density_mae" in ti and sample_has_gt_newfoam(sample):
                mae_v = ti.get("foam_density_mae")
                if isinstance(mae_v, float) and mae_v == mae_v:
                    foam_mae_vals.append(mae_v)
                try:
                    _need_header = not foam_csv_path.exists() or foam_csv_path.stat().st_size == 0
                    with open(foam_csv_path, "a", newline="", encoding="utf-8") as fp:
                        w = csv.writer(fp)
                        if _need_header:
                            w.writerow(
                                [
                                    "frame_idx",
                                    "meta_frame_id",
                                    "scene",
                                    "foam_pred_num",
                                    "foam_gt_num",
                                    "foam_density_mae",
                                    "foam_error_count",
                                    "foam_error_rel",
                                    "foam_density_union_voxels",
                                    "foam_metric_grid",
                                ]
                            )
                        w.writerow(
                            [
                                frame_count,
                                sample.get("meta_frame_id", frame_count),
                                sample.get("meta_scene", cfg.scene if cfg.scene else cfg.mode),
                                ti.get("foam_pred_num", ""),
                                ti.get("foam_gt_num", ""),
                                ti.get("foam_density_mae", ""),
                                ti.get("foam_error_count", ""),
                                ti.get("foam_error_rel", ""),
                                ti.get("foam_density_union_voxels", ""),
                                ti.get("foam_metric_grid", ""),
                            ]
                        )
                except OSError as e:
                    print(f"[RealTimeWaterFoamMetric] 写入 CSV 失败: {e}")
            foam_error_density_mae_v = ti.get("foam_error_density_mae")
            if isinstance(foam_error_density_mae_v, (int, float)) and math.isfinite(float(foam_error_density_mae_v)):
                foam_error_density_mae_vals.append(float(foam_error_density_mae_v))

        if runner.device.type == "cuda":
            torch.cuda.synchronize(runner.device)
        t_loop1 = time.perf_counter()
        loop_ms = (t_loop1 - t_loop0) * 1000.0
        fps = 1000.0 / max(loop_ms, 1e-6)

        # 与 process_frame 内部模块时间进行对比（模块和在日志中可见）
        module_total_ms = None
        module_gap_ms = None
        if isinstance(outputs, dict):
            ti = outputs.get("timing_info")
            if isinstance(ti, dict):
                module_total_ms = float(ti.get("total_ms", 0.0))
                module_gap_ms = loop_ms - module_total_ms
                fetch_ms = (t_fetch1 - t_fetch0) * 1000.0
                prepare_outer_ms = (t_prepare_outer1 - t_prepare_outer0) * 1000.0
        print(
            f"[RealTimeWaterLoop] frame={frame_count} loop={loop_ms:.2f} ms, fps={fps:.2f}, "
            f"next_loop={sample.get('meta_next_is_loop', False)}, pause={cfg.pause}"
        )
        if module_total_ms is not None and module_gap_ms is not None:
            print(
                f"[RealTimeWaterCompare] modules_total={module_total_ms:.2f} ms, "
                f"loop={loop_ms:.2f} ms, gap={module_gap_ms:.2f} ms"
            )
            print(
                f"[RealTimeWaterOverhead] fetch={fetch_ms:.2f} ms, "
                f"prepare_outer={prepare_outer_ms:.2f} ms"
            )

        if (not cfg.pause) and sample.get('meta_next_is_loop', False):
            refresh = True
        else:
            refresh = False

        if save_result_enabled and frame_count >= save_frame_start and frame_count != last_saved_frame:
            render_result = outputs.get("render_result") if isinstance(outputs, dict) else None
            runner.save_result(frame_count, render_result)
            if isinstance(outputs, dict):
                outputs.pop("render_result", None)
            last_saved_frame = frame_count
            saved_count += 1

        # 每帧结束后显式清理一次显存缓存（与 run_loop_realtime 一致：默认关闭）
        # runner.cleanup_cuda_memory()

        save_target_frames = int(runner.falcorRender.getSaveFrames())

        if save_result_enabled and saved_count >= save_target_frames:
            print(
                f"[RealTimeWater] save_result: wrote {saved_count} frame(s), disabling save mode."
            )
            runner.falcorRender.setSaveResult(False)
            saved_count = 0
            last_saved_frame = -1

        if timing_runs >= max_timing_frames:
            print(
                f"[RealTimeWater] Timing: reached max frames {max_timing_frames} "
                f"(timing_runs={timing_runs}), write summary and exit. "
                f"Use --timing_max_frames N (0=max(SaveFrames,{_TIMING_MAX_WHEN_ZERO_MIN})) to change."
            )
            break

        if not cfg.pause:
            frame_count += 1
        
        # Timing 模式只由 timing_runs 与上面 break 结束；不复用 realtime 的 no_loop/frame_count 提前退出，
        # 否则 SaveFrames=1 且 --no_loop 时会在未跑满统计帧数前直接退出。

    try:
        _write_timing_summary_config(
            timing_summary_path,
            cfg,
            cull_ms=cull_ms_list,
            search_ms=search_ms_list,
            model_ms=model_ms_list,
            splat_ms=splat_ms_list,
            foam_mae_vals=foam_mae_vals,
            foam_error_density_mae_vals=foam_error_density_mae_vals,
            timing_effective_cap=max_timing_frames,
            max_fluid_particles=max_fluid_particles,
            max_fluid_particles_meta_frame_id=max_fluid_particles_meta_frame_id,
            max_fluid_particles_loop_frame_idx=max_fluid_particles_loop_frame_idx,
            max_surface_num=max_surface_num,
            max_surface_num_meta_frame_id=max_surface_num_meta_frame_id,
            max_surface_num_loop_frame_idx=max_surface_num_loop_frame_idx,
        )
    except OSError as e:
        print(f"[RealTimeWaterTiming] 写入 timing summary JSON 失败: {e}")

    _cm = statistics.mean(cull_ms_list) if cull_ms_list else float("nan")
    _sm = statistics.mean(search_ms_list) if search_ms_list else float("nan")
    _mm = statistics.mean(model_ms_list) if model_ms_list else float("nan")
    _spm = statistics.mean(splat_ms_list) if splat_ms_list else float("nan")
    _fm = statistics.mean(foam_mae_vals) if foam_mae_vals else float("nan")
    _fem = statistics.mean(foam_error_density_mae_vals) if foam_error_density_mae_vals else float("nan")
    print(
        f"[RealTimeWaterTimingSummary] culling_ms_mean={_cm:.4f} domain_search_ms_mean={_sm:.4f} "
        f"network_ms_mean={_mm:.4f} splat_ms_mean={_spm:.4f} "
        f"foam_density_mae_mean={_fm:.6f} foam_error_density_mae_mean={_fem:.6f} "
        f"frames={len(cull_ms_list)} "
        f"fluid_particles_max={max_fluid_particles} "
        f"(at meta_frame_id={max_fluid_particles_meta_frame_id!s} loop_idx={max_fluid_particles_loop_frame_idx}) "
        f"surface_num_max={max_surface_num} "
        f"(at meta_frame_id={max_surface_num_meta_frame_id!s} loop_idx={max_surface_num_loop_frame_idx}) "
        f"json={timing_summary_path}"
    )

    if foam_mae_vals:
        _mean = statistics.mean(foam_mae_vals)
        print(
            f"[RealTimeWaterFoamMetric] session_mean_foam_density_mae={_mean:.6f} "
            f"(n_valid_frames={len(foam_mae_vals)}, csv={foam_csv_path})"
        )
    else:
        print(
            f"[RealTimeWaterFoamMetric] session_mean_foam_density_mae=nan (no valid "
            f"finite MAE rows; csv may still exist at {foam_csv_path})"
        )
    if foam_error_density_mae_vals:
        print(
            f"[RealTimeWaterFoamMetric] session_mean_foam_error_density_mae="
            f"{statistics.mean(foam_error_density_mae_vals):.6f} "
            f"(n_valid_frames={len(foam_error_density_mae_vals)})"
        )
    else:
        print("[RealTimeWaterFoamMetric] session_mean_foam_error_density_mae=nan")


def run_loop_timing_chosen(
    cfg: DemoConfig,
    provider: SceneSampleProvider,
    runner: RealTimeWaterRunner,
    log_path: Path,
) -> None:
    """按 compare_renderers free 写出的 chosen JSON逐条测时，汇总与 run_loop_timing 相同。"""
    doc = _load_timing_chosen_doc(cfg, log_path)
    entries = doc.get("entries")
    assert isinstance(entries, list)
    file_scene = str(doc.get("scene", "") or "")
    n_ds = len(provider.dataset)
    timing_summary_path = _timing_summary_json_path(cfg)
    foam_csv_path = Path(cfg.save_dir).expanduser().resolve() / "foam_density_metrics.csv"
    foam_csv_path.parent.mkdir(parents=True, exist_ok=True)

    foam_mae_vals: List[float] = []
    foam_error_density_mae_vals: List[float] = []
    cull_ms_list: List[float] = []
    search_ms_list: List[float] = []
    model_ms_list: List[float] = []
    splat_ms_list: List[float] = []
    max_fluid_particles = 0
    max_fluid_particles_meta_frame_id: Any = None
    max_fluid_particles_loop_frame_idx: Optional[int] = None
    max_surface_num = 0
    max_surface_num_meta_frame_id: Any = None
    max_surface_num_loop_frame_idx: Optional[int] = None
    n_skip = 0
    timing_runs = 0
    user_cap = int(getattr(cfg, "timing_max_frames", 0) or 0)
    summary_effective_cap = user_cap if user_cap > 0 else len(entries)
    prev_idx: Optional[int] = None

    print(
        f"[RealTimeWater] Timing chosen: scene={file_scene} entries_in_file={len(entries)} "
        f"dataset_len={n_ds} log={log_path}"
    )

    for ei, ent in enumerate(entries):
        if user_cap > 0 and timing_runs >= user_cap:
            break
        if not isinstance(ent, dict):
            n_skip += 1
            continue
        idx = int(ent.get("dataset_idx", -1))
        cam_raw = ent.get("camera")
        if idx < 0 or idx >= n_ds or not isinstance(cam_raw, dict):
            n_skip += 1
            continue
        sample = provider.dataset[idx]
        if sample is None or not sample.get("gt_mesh_path"):
            n_skip += 1
            continue
        exp_mid = ent.get("meta_frame_id")
        act_mid = sample.get("meta_frame_id")
        if exp_mid is not None and act_mid != exp_mid:
            print(
                f"  [Warn] timing_chosen[{ei}] meta_frame_id 记录={exp_mid!s} 数据集={act_mid!s}（仍按 dataset_idx）"
            )
        try:
            cam = _copy_timing_cam_dict(cam_raw)
        except (KeyError, TypeError, ValueError):
            n_skip += 1
            continue

        sample = dict(sample)
        sample["meta_total_frames"] = int(n_ds)
        sample["meta_provider_idx"] = int(idx)
        is_last = bool(idx == n_ds - 1)
        sample["meta_is_last_frame_in_scene"] = is_last
        sample["meta_next_is_loop"] = is_last

        t_loop0 = time.perf_counter()
        if runner.device.type == "cuda":
            torch.cuda.synchronize(runner.device)
        t_fetch0 = time.perf_counter()
        t_fetch1 = time.perf_counter()
        t_prepare_outer0 = time.perf_counter()
        sample = runner.prepare_sample(sample)
        t_prepare_outer1 = time.perf_counter()
        if sample is None:
            n_skip += 1
            continue
        sample["camera"] = cam
        runner.falcorRender.set_camera_from_dict(cam)
        refresh = prev_idx is None or idx != prev_idx
        prev_idx = idx

        frame_id = sample.get("meta_frame_id", ei)
        pos = sample.get("positions")
        vel = sample.get("vel")
        if isinstance(pos, torch.Tensor):
            pos_shape = tuple(pos.shape)
            pos_dev = str(pos.device)
        else:
            pos_shape = None
            pos_dev = type(pos).__name__
        if isinstance(vel, torch.Tensor):
            vel_shape = tuple(vel.shape)
            vel_dev = str(vel.device)
        else:
            vel_shape = None
            vel_dev = type(vel).__name__
        print(
            f"[RealTimeWater][chosen ei={ei}] scene={file_scene} dataset_idx={idx} frame_id={frame_id} "
            f"pos={pos_shape}@{pos_dev} vel={vel_shape}@{vel_dev} refresh={refresh}"
        )

        outputs = runner.process_frame_timing(sample, refresh=refresh, assume_prepared=True)
        if not isinstance(outputs, dict):
            n_skip += 1
            continue
        ti = outputs.get("timing_info")
        if not isinstance(ti, dict):
            n_skip += 1
            continue

        timing_runs += 1
        cull_ms_list.append(float(ti.get("cull_ms", 0.0)))
        search_ms_list.append(float(ti.get("search_ms", 0.0)))
        model_ms_list.append(float(ti.get("model_ms", 0.0)))
        splat_ms_list.append(float(ti.get("splat_ms", 0.0)))
        _fn = _sample_fluid_particle_count(sample)
        if _fn > max_fluid_particles:
            max_fluid_particles = _fn
            max_fluid_particles_meta_frame_id = sample.get("meta_frame_id")
            max_fluid_particles_loop_frame_idx = int(ei)
        _sn = int(ti.get("surface_num", 0) or 0)
        if _sn > max_surface_num:
            max_surface_num = _sn
            max_surface_num_meta_frame_id = sample.get("meta_frame_id")
            max_surface_num_loop_frame_idx = int(ei)
        if "foam_density_mae" in ti and sample_has_gt_newfoam(sample):
            mae_v = ti.get("foam_density_mae")
            if isinstance(mae_v, float) and mae_v == mae_v:
                foam_mae_vals.append(mae_v)
            try:
                _need_header = not foam_csv_path.exists() or foam_csv_path.stat().st_size == 0
                with open(foam_csv_path, "a", newline="", encoding="utf-8") as fp:
                    w = csv.writer(fp)
                    if _need_header:
                        w.writerow(
                            [
                                "frame_idx",
                                "meta_frame_id",
                                "scene",
                                "foam_pred_num",
                                "foam_gt_num",
                                "foam_density_mae",
                                "foam_error_count",
                                "foam_error_rel",
                                "foam_density_union_voxels",
                                "foam_metric_grid",
                            ]
                        )
                    w.writerow(
                        [
                            ei,
                            sample.get("meta_frame_id", ei),
                            sample.get("meta_scene", file_scene),
                            ti.get("foam_pred_num", ""),
                            ti.get("foam_gt_num", ""),
                            ti.get("foam_density_mae", ""),
                            ti.get("foam_error_count", ""),
                            ti.get("foam_error_rel", ""),
                            ti.get("foam_density_union_voxels", ""),
                            ti.get("foam_metric_grid", ""),
                        ]
                    )
            except OSError as e:
                print(f"[RealTimeWaterFoamMetric] 写入 CSV 失败: {e}")
        foam_error_density_mae_v = ti.get("foam_error_density_mae")
        if isinstance(foam_error_density_mae_v, (int, float)) and math.isfinite(float(foam_error_density_mae_v)):
            foam_error_density_mae_vals.append(float(foam_error_density_mae_v))

        if runner.device.type == "cuda":
            torch.cuda.synchronize(runner.device)
        t_loop1 = time.perf_counter()
        loop_ms = (t_loop1 - t_loop0) * 1000.0
        module_total_ms = float(ti.get("total_ms", 0.0))
        module_gap_ms = loop_ms - module_total_ms
        fetch_ms = (t_fetch1 - t_fetch0) * 1000.0
        prepare_outer_ms = (t_prepare_outer1 - t_prepare_outer0) * 1000.0
        print(
            f"[RealTimeWaterLoop] chosen ei={ei} loop={loop_ms:.2f} ms, fps={1000.0 / max(loop_ms, 1e-6):.2f}"
        )
        print(
            f"[RealTimeWaterCompare] modules_total={module_total_ms:.2f} ms, "
            f"loop={loop_ms:.2f} ms, gap={module_gap_ms:.2f} ms"
        )
        print(
            f"[RealTimeWaterOverhead] fetch={fetch_ms:.2f} ms, "
            f"prepare_outer={prepare_outer_ms:.2f} ms"
        )

    try:
        _write_timing_summary_config(
            timing_summary_path,
            cfg,
            cull_ms=cull_ms_list,
            search_ms=search_ms_list,
            model_ms=model_ms_list,
            splat_ms=splat_ms_list,
            foam_mae_vals=foam_mae_vals,
            foam_error_density_mae_vals=foam_error_density_mae_vals,
            timing_effective_cap=summary_effective_cap,
            max_fluid_particles=max_fluid_particles,
            max_fluid_particles_meta_frame_id=max_fluid_particles_meta_frame_id,
            max_fluid_particles_loop_frame_idx=max_fluid_particles_loop_frame_idx,
            max_surface_num=max_surface_num,
            max_surface_num_meta_frame_id=max_surface_num_meta_frame_id,
            max_surface_num_loop_frame_idx=max_surface_num_loop_frame_idx,
            timing_session_kind="chosen_log",
            timing_chosen_log_path=str(log_path),
            chosen_n_entries_file=len(entries),
            chosen_n_skip=n_skip,
        )
    except OSError as e:
        print(f"[RealTimeWaterTiming] 写入 timing summary JSON 失败: {e}")

    _cm = statistics.mean(cull_ms_list) if cull_ms_list else float("nan")
    _sm = statistics.mean(search_ms_list) if search_ms_list else float("nan")
    _mm = statistics.mean(model_ms_list) if model_ms_list else float("nan")
    _spm = statistics.mean(splat_ms_list) if splat_ms_list else float("nan")
    _fm = statistics.mean(foam_mae_vals) if foam_mae_vals else float("nan")
    _fem = statistics.mean(foam_error_density_mae_vals) if foam_error_density_mae_vals else float("nan")
    print(
        f"[RealTimeWaterTimingSummary] (chosen) culling_ms_mean={_cm:.4f} domain_search_ms_mean={_sm:.4f} "
        f"network_ms_mean={_mm:.4f} splat_ms_mean={_spm:.4f} "
        f"foam_density_mae_mean={_fm:.6f} foam_error_density_mae_mean={_fem:.6f} "
        f"frames={len(cull_ms_list)} n_skip={n_skip} "
        f"fluid_particles_max={max_fluid_particles} "
        f"surface_num_max={max_surface_num} "
        f"json={timing_summary_path}"
    )
    if foam_mae_vals:
        print(
            f"[RealTimeWaterFoamMetric] session_mean_foam_density_mae={statistics.mean(foam_mae_vals):.6f} "
            f"(n_valid_frames={len(foam_mae_vals)}, csv={foam_csv_path})"
        )
    else:
        print(
            f"[RealTimeWaterFoamMetric] session_mean_foam_density_mae=nan (csv={foam_csv_path})"
        )
    if foam_error_density_mae_vals:
        print(
            f"[RealTimeWaterFoamMetric] session_mean_foam_error_density_mae="
            f"{statistics.mean(foam_error_density_mae_vals):.6f} "
            f"(n_valid_frames={len(foam_error_density_mae_vals)})"
        )
    else:
        print("[RealTimeWaterFoamMetric] session_mean_foam_error_density_mae=nan")


def run_loop_realtime(cfg: DemoConfig, provider, runner: RealTimeWaterRunner) -> None:
    frame_count = 0
    saved_count = 0
    refresh = False
    paused_sample: Optional[Dict[str, Any]] = None
    last_saved_frame: int = -1
    prev_save_result_enabled = bool(runner.falcorRender.getSaveResult())
    force_loop_boundary = False
    while True:
        cfg.pause = runner.falcorRender.getPause()
        save_result_enabled = bool(runner.falcorRender.getSaveResult())

        #print(f"[RealTimeWater] save_result_enabled: {save_result_enabled}")
        if save_result_enabled and not prev_save_result_enabled:# and runner.falcorRender.getNeedRefresh():
            if hasattr(provider, "reset"):
                provider.reset()
            paused_sample = None
            frame_count = 0
            saved_count = 0
            last_saved_frame = -1
            refresh = True
            force_loop_boundary = True
            print("[RealTimeWater] SaveResult enabled: reset provider to first frame.")
        prev_save_result_enabled = save_result_enabled
        save_frame_start = max(0, int(runner.falcorRender.getSaveFrameStart()))
        t_loop0 = time.perf_counter()
        if runner.device.type == "cuda":
            torch.cuda.synchronize(runner.device)

        if (not save_result_enabled) and cfg.pause and paused_sample is not None:
            sample = paused_sample
        else:
            sample = provider.next_sample()
            if sample is not None:
                paused_sample = sample
        if sample is None:
            continue
        if force_loop_boundary:
            sample["meta_next_is_loop"] = True
            sample["meta_is_last_frame_in_scene"] = True
            refresh = True
            force_loop_boundary = False

        sample = runner.prepare_sample(sample)
        if sample is None:
            continue

       #print("[WaterRealTime]Frames:{}",sample.get("meta_frame_id", frame_count))
        outputs = runner.process_frame_realtime(sample, assume_prepared=True, refresh=refresh)

        if runner.device.type == "cuda":
            torch.cuda.synchronize(runner.device)
        t_loop1 = time.perf_counter()
        loop_ms = (t_loop1 - t_loop0) * 1000.0
        fps = 1000.0 / max(loop_ms, 1e-6)
        print(f"fps={fps:.2f}, next_loop={sample.get('meta_next_is_loop', False)}, pause={cfg.pause}")


        if (not cfg.pause) and sample.get('meta_next_is_loop', False):
            refresh = True
        else:
            refresh = False
        

        if runner.falcorRender.getSaveCur():
            frameC = sample.get("meta_frame_id", frame_count)
            render_result = outputs.get("render_result") if isinstance(outputs, dict) else None
            runner.save_result(frameC, render_result)
            runner.falcorRender.savedCur()
        

        #print(f"frame_count={frame_count}, save_frame_start={save_frame_start}, last_saved_frame={last_saved_frame} save_result_enabled={save_result_enabled}")
        if save_result_enabled and frame_count >= save_frame_start and frame_count != last_saved_frame:
            render_result = outputs.get("render_result") if isinstance(outputs, dict) else None
            runner.save_result(frame_count, render_result)
            if isinstance(outputs, dict):
                outputs.pop("render_result", None)
            last_saved_frame = frame_count
            saved_count += 1

        # 每帧结束后显式清理一次显存缓存
        #runner.cleanup_cuda_memory()

        save_target_frames = int(runner.falcorRender.getSaveFrames())
        if save_result_enabled and saved_count >= save_target_frames:
            print(
                f"[RealTimeWater] save_result: wrote {saved_count} frame(s), disabling save mode."
            )
            runner.falcorRender.setSaveResult(False)
            saved_count = 0
            last_saved_frame = -1

        if(not cfg.pause):
            frame_count += 1
        else:
            frame_count = sample.get("meta_frame_id", frame_count)

        if not save_result_enabled:
            loop_target_frames = int(runner.falcorRender.getSaveFrames())
            if not cfg.loop and frame_count >= loop_target_frames:
                break
            if cfg.loop and frame_count >= loop_target_frames:
                frame_count = 0
        


def main() -> None:
    cfg = parse_args()
    chosen_raw = (getattr(cfg, "timing_chosen_log", "") or "").strip()
    timing_chosen_path: Optional[Path] = None
    timing_chosen_doc: Optional[Dict[str, Any]] = None
    if chosen_raw:
        if not cfg.search_timing:
            raise SystemExit("[RealTimeWater] --timing_chosen_log 须与 --timing 联用")
        if cfg.mode != "scene":
            raise SystemExit("[RealTimeWater] --timing_chosen_log 仅支持 --mode scene")
        timing_chosen_path = Path(chosen_raw).expanduser().resolve()
        if not timing_chosen_path.is_file():
            raise SystemExit(f"[RealTimeWater] timing_chosen_log 不存在: {timing_chosen_path}")
        timing_chosen_doc = json.loads(timing_chosen_path.read_text(encoding="utf-8"))
        sc = str(timing_chosen_doc.get("scene", "") or "")
        if not (cfg.scene or "").strip():
            if not sc:
                raise SystemExit("[RealTimeWater] timing_chosen_log 缺少 scene 且未指定 --scene")
            cfg = replace(cfg, scene=sc)
        cfg = replace(cfg, require_mesh=True)

    provider = build_provider(
        cfg.mode,
        cfg.data_path,
        cfg.scene,
        cfg.sim_radius,
        preload_scene=cfg.preload_scene,
        require_mesh=cfg.require_mesh,
        ensure_newfoam_density=False,
    )
    runner = RealTimeWaterRunner(cfg)
    timing = bool(runner.infer_cfg.search_timing)
    print(f"[RealTimeWater] start mode={cfg.mode}, device={runner.device}")
    if runner.falcorRender.getSaveResult():
        save_target_frames = int(runner.falcorRender.getSaveFrames())
        save_frame_start = max(0, int(runner.falcorRender.getSaveFrameStart()))
        print(
            f"[RealTimeWater] SaveResult enabled by Falcor, output_dir={Path(cfg.save_dir).expanduser().resolve()}, "
            f"start saving from frame>={save_frame_start}, will disable save after writing {save_target_frames} frame(s)"
        )
    else:
        print("[RealTimeWater] SaveResult disabled by Falcor")

    if timing:
        _foam_csv = Path(cfg.save_dir).expanduser().resolve() / "foam_density_metrics.csv"
        _timing_json = _timing_summary_json_path(cfg)
        print(f"[RealTimeWater] Timing mode: per-frame foam_density metrics -> {_foam_csv}")
        print(f"[RealTimeWater] Timing mode: session summary JSON -> {_timing_json}")
        if timing_chosen_path is not None:
            assert timing_chosen_doc is not None
            n_ent = len(timing_chosen_doc.get("entries") or [])
            cap_cfg = int(getattr(cfg, "timing_max_frames", 0) or 0)
            cap_msg = (
                f"前 {cap_cfg} 条成功测时条目"
                if cap_cfg > 0
                else f"全部 {n_ent} 条日志条目（--timing_max_frames 0）"
            )
            print(
                f"[RealTimeWater] Timing chosen_log: {timing_chosen_path} "
                f"entries={n_ent}；将处理 {cap_msg}（与 compare_renderers 记录索引一致，已 require_mesh）"
            )
            if not isinstance(provider, SceneSampleProvider):
                raise SystemExit("[RealTimeWater] timing_chosen_log 需要 scene 模式的 SceneSampleProvider")
            run_loop_timing_chosen(cfg, provider, runner, timing_chosen_path)
        else:
            _cap = _effective_timing_max_frames(cfg, runner)
            print(
                f"[RealTimeWater] Timing mode: will exit after {_cap} non-pause frame(s) "
                f"(--timing_max_frames N; N=0 → max(SaveFrames,{_TIMING_MAX_WHEN_ZERO_MIN}))"
            )
            run_loop_timing(cfg, provider, runner)
    else:
        run_loop_realtime(cfg, provider, runner)


if __name__ == "__main__":
    main()