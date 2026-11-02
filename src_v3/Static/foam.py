# -*- coding: utf-8 -*-
"""
SceneDataset 逐帧：统计 GT newFoam 数量，并按 RealTimeWaterMinimal 同结构推理泡沫并输出预测数量。

管线：Falcor 表面剔除 → ``search`` → ``CovDecoderModel`` → ``GaussianProjector`` →
本模块内 **重写** 的泡沫采样（等价扩展 ``sample_foam_from_gt_network_output``）：
``y`` 逆映射得 ``prob`` 后，按体素均分：某体素内有 ``N`` 个高斯则每个乘 ``1/N``；若有高斯落在体素盒外则 **报错**，需扩大 ``corner_min/max``。
``sampleTimes`` 取 **本帧 GT newFoam 数量**
（0 时不采样）；``noiseThreshold`` 仍从 Falcor 读取。

可选 **指标专用** 体素网格（与采样网格独立）：``--metric_corner_min/max``、``--metric_voxel_size``。
对 GT / Pred 泡沫位置分别做 8-corner 三线性 splat，统计非零体素交集/并集及密度 MAE、平均相对误差百分比。

示例::

    python -m src_v3.Static.foam --data_path F:/DataSet/ShowData --scene Boat \\
        --model path/to.pth --corner_min -5 -5 -5 --corner_max 5 5 5 --voxel_size 0.1 \\
        --metric_corner_min -6 -6 -6 --metric_corner_max 6 6 6 --metric_voxel_size 0.2
"""

from __future__ import annotations

import argparse
import math
from dataclasses import dataclass
from typing import Any, Dict, Optional, Sequence, Tuple

import numpy as np
import torch

from src_v3.core.Searching import search
from src_v3.core.render import GaussianProjector
from src_v3.core.render.falcor_manager import (
    FalcorParticleFilterConfig,
    FalcorParticelFilterRenderer,
    FalcorRealTimeWaterConfig,
    FalcorRealTimeWaterRenderer,
)
from src_v3.data import SceneDataset
from src_v3.data.camera_from_particles import camera_from_particles
from src_v3.data.foam_density import inverse_map_gt_log_to_density
from src_v3.models import CovDecoderModel, DEFAULT_COV_DIM
from src_v3.training.config import InferConfig


def _newfoam_gt_count(sample: Optional[Dict[str, Any]]) -> int:
    if sample is None:
        return -1
    nf = sample.get("newfoam") or {}
    pos = nf.get("positions")
    if pos is None:
        return 0
    t = np.asarray(pos)
    if t.ndim != 2 or t.shape[1] < 3:
        return 0
    return int(t.shape[0])


def _gt_newfoam_xyz_np(sample: Optional[Dict[str, Any]]) -> np.ndarray:
    """GT newFoam 位置 ``[N,3]``，无则空数组。"""
    if sample is None:
        return np.zeros((0, 3), dtype=np.float64)
    nf = sample.get("newfoam") or {}
    pos = nf.get("positions")
    if pos is None:
        return np.zeros((0, 3), dtype=np.float64)
    t = np.asarray(pos, dtype=np.float64)
    if t.ndim != 2 or t.shape[1] < 3:
        return np.zeros((0, 3), dtype=np.float64)
    return np.ascontiguousarray(t[:, :3])


def _voxel_grid_shape(
    corner_min: Sequence[float],
    corner_max: Sequence[float],
    voxel_size: float,
) -> Tuple[int, int, int]:
    vs = float(voxel_size)
    if vs <= 0.0:
        raise ValueError("voxel_size must be positive")
    out: list[int] = []
    for i in range(3):
        ext = float(corner_max[i]) - float(corner_min[i])
        n = int(math.floor(ext / vs + 1e-9))
        out.append(max(1, n))
    return int(out[0]), int(out[1]), int(out[2])


def _metric_grid_points_inside(
    positions: np.ndarray,
    corner_min: Sequence[float],
    corner_max: Sequence[float],
) -> np.ndarray:
    cm = np.asarray(corner_min, dtype=np.float64).reshape(1, 3)
    cM = np.asarray(corner_max, dtype=np.float64).reshape(1, 3)
    return np.all((positions >= cm) & (positions < cM), axis=1)


def splat_foam_trilinear_8_corners(
    positions: np.ndarray,
    corner_min: Sequence[float],
    corner_max: Sequence[float],
    voxel_size: float,
) -> np.ndarray:
    """
    每个泡沫点对所在体素格的 **8 个角点** 做三线性 splat（权重和为 1），
    返回角点格 ``C``，shape ``(nx+1, ny+1, nz+1)``。
    有点落在盒外则 ``RuntimeError``，提示扩大 **指标** 体素范围。
    """
    pos = np.asarray(positions, dtype=np.float64)
    if pos.size == 0:
        nx, ny, nz = _voxel_grid_shape(corner_min, corner_max, voxel_size)
        return np.zeros((nx + 1, ny + 1, nz + 1), dtype=np.float64)
    if pos.ndim != 2 or pos.shape[1] < 3:
        nx, ny, nz = _voxel_grid_shape(corner_min, corner_max, voxel_size)
        return np.zeros((nx + 1, ny + 1, nz + 1), dtype=np.float64)
    pos = pos[:, :3]
    inside = _metric_grid_points_inside(pos, corner_min, corner_max)
    n_out = int(np.sum(~inside))
    if n_out > 0:
        raise RuntimeError(
            f"指标体素网格内有 {n_out}/{pos.shape[0]} 个泡沫点落在盒外（须 corner_min <= xyz < corner_max）。"
            f"请扩大 --metric_corner_min / --metric_corner_max；"
            f"当前 metric_box={tuple(corner_min)!r}..{tuple(corner_max)!r}, voxel_size={voxel_size!r}。"
        )
    nx, ny, nz = _voxel_grid_shape(corner_min, corner_max, voxel_size)
    vs = float(voxel_size)
    cm = np.asarray(corner_min, dtype=np.float64).reshape(1, 3)
    C = np.zeros((nx + 1, ny + 1, nz + 1), dtype=np.float64)
    u = (pos - cm) / vs
    ix = np.floor(u[:, 0]).astype(np.int64)
    iy = np.floor(u[:, 1]).astype(np.int64)
    iz = np.floor(u[:, 2]).astype(np.int64)
    fx = u[:, 0] - ix
    fy = u[:, 1] - iy
    fz = u[:, 2] - iz
    for a in (0, 1):
        for b in (0, 1):
            for c in (0, 1):
                wx = np.where(a, fx, 1.0 - fx)
                wy = np.where(b, fy, 1.0 - fy)
                wz = np.where(c, fz, 1.0 - fz)
                w = wx * wy * wz
                ci = ix + a
                cj = iy + b
                ck = iz + c
                np.add.at(C, (ci, cj, ck), w)
    return C


def corner_grid_to_cell_sum8(C: np.ndarray) -> np.ndarray:
    """角点格上每个 **体素** 的 8 个角点值之和，shape ``(nx, ny, nz)``。"""
    return (
        C[0:-1, 0:-1, 0:-1]
        + C[1:, 0:-1, 0:-1]
        + C[0:-1, 1:, 0:-1]
        + C[1:, 1:, 0:-1]
        + C[0:-1, 0:-1, 1:]
        + C[1:, 0:-1, 1:]
        + C[0:-1, 1:, 1:]
        + C[1:, 1:, 1:]
    )


@dataclass
class FoamMetricVoxelResult:
    """单帧：8-corner splat 体素格上的 GT/Pred 对比指标。"""

    n_cells_gt: int
    n_cells_pred: int
    n_cells_inter: int
    n_cells_union: int
    mae_density_on_union: float
    mean_rel_err_pct_on_union: float


def compute_foam_metric_voxel_overlap(
    gt_xyz: np.ndarray,
    pred_xyz: np.ndarray,
    *,
    metric_corner_min: Sequence[float],
    metric_corner_max: Sequence[float],
    metric_voxel_size: float,
    density_eps: float = 1e-9,
) -> FoamMetricVoxelResult:
    """
    在 **独立** 指标体素网格上，对 GT / Pred 泡沫点分别做 8-corner splat，
    用体素格 8 角点密度和作为体素值，再算非零交集 / 并集及密度误差。

    - ``mae_density_on_union``：在并集体素上 ``mean(|g - p|)``。
    - ``mean_rel_err_pct_on_union``：并集上 ``mean(|g-p| / max(g,p,eps) * 100)``。
    """
    Cg = splat_foam_trilinear_8_corners(gt_xyz, metric_corner_min, metric_corner_max, metric_voxel_size)
    Cp = splat_foam_trilinear_8_corners(pred_xyz, metric_corner_min, metric_corner_max, metric_voxel_size)
    g = corner_grid_to_cell_sum8(Cg)
    p = corner_grid_to_cell_sum8(Cp)
    mask_g = g > density_eps
    mask_p = p > density_eps
    n_gt = int(mask_g.sum())
    n_pred = int(mask_p.sum())
    inter = mask_g & mask_p
    uni = mask_g | mask_p
    n_inter = int(inter.sum())
    n_union = int(uni.sum())
    if n_union == 0:
        return FoamMetricVoxelResult(
            n_cells_gt=n_gt,
            n_cells_pred=n_pred,
            n_cells_inter=n_inter,
            n_cells_union=n_union,
            mae_density_on_union=float("nan"),
            mean_rel_err_pct_on_union=float("nan"),
        )
    diff = np.abs(g - p)
    denom = np.maximum(np.maximum(g, p), density_eps)
    mae = float(diff[uni].mean())
    pct = float((diff[uni] / denom[uni] * 100.0).mean())
    return FoamMetricVoxelResult(
        n_cells_gt=n_gt,
        n_cells_pred=n_pred,
        n_cells_inter=n_inter,
        n_cells_union=n_union,
        mae_density_on_union=mae,
        mean_rel_err_pct_on_union=pct,
    )


def _gaussian_voxel_inv_count_scale(
    gs_pos: torch.Tensor,
    corner_min: Sequence[float],
    corner_max: Sequence[float],
    voxel_size: float,
) -> torch.Tensor:
    """
    体素内 ``N`` 个高斯均分权重：每个高斯的系数为 ``1/N``。

    若有任一高斯中心落在 ``[corner_min, corner_max)`` **外**，抛出 ``RuntimeError``，
    提示扩大体素网格范围（与命令行 ``--corner_min`` / ``--corner_max`` 一致）。
    """
    pos_flat = gs_pos.reshape(-1, 3).float()
    n = int(pos_flat.shape[0])
    if n == 0:
        return pos_flat.new_zeros((0,))
    nx, ny, nz = _voxel_grid_shape(corner_min, corner_max, voxel_size)
    vs = float(voxel_size)
    cm = pos_flat.new_tensor(corner_min, dtype=torch.float32).view(1, 3)
    cM = pos_flat.new_tensor(corner_max, dtype=torch.float32).view(1, 3)
    inside = torch.all((pos_flat >= cm) & (pos_flat < cM), dim=1)
    n_out = int((~inside).sum().item())
    if n_out > 0:
        cmin_t = tuple(float(corner_min[i]) for i in range(3))
        cmax_t = tuple(float(corner_max[i]) for i in range(3))
        raise RuntimeError(
            f"泡沫采样体素盒内有 {n_out}/{n} 个高斯落在盒外（须满足 corner_min <= xyz < corner_max）。"
            f"请扩大体素网格范围，例如调整 --corner_min {cmin_t!r} / --corner_max {cmax_t!r} "
            f"或增大包围盒；voxel_size={voxel_size!r}。"
        )
    ix = torch.floor((pos_flat[:, 0] - cm[0, 0]) / vs).long()
    iy = torch.floor((pos_flat[:, 1] - cm[0, 1]) / vs).long()
    iz = torch.floor((pos_flat[:, 2] - cm[0, 2]) / vs).long()
    ix = ix.clamp(0, nx - 1)
    iy = iy.clamp(0, ny - 1)
    iz = iz.clamp(0, nz - 1)
    lin = ix + nx * (iy + ny * iz)
    hist = pos_flat.new_zeros((nx * ny * nz,), dtype=torch.float32)
    hist.scatter_add_(0, lin, torch.ones_like(lin, dtype=torch.float32))
    n_in_cell = hist[lin]
    inv_n = 1.0 / torch.clamp(n_in_cell, min=1.0)
    return inv_n


def _sample_foam_from_network_output_voxel_scaled(
    gs_pos: torch.Tensor,
    gs_vel: torch.Tensor,
    foam_gt_y: Optional[torch.Tensor],
    *,
    alpha: float,
    d_max_reference: float,
    voxel_corner_min: Sequence[float],
    voxel_corner_max: Sequence[float],
    voxel_size: float,
    sample_times_gt_newfoam: int,
    noise_threshold: float,
    replacement: bool = False,
    factor_when_zero_gt: float = 1.0,
) -> torch.Tensor:
    """
    ``sample_foam_from_gt_network_output`` 的 foam.py 内联变体：
    映射得到 ``prob`` 后乘以 ``1/N``（``N`` = 该高斯所在体素内高斯数）；``sample_times_gt_newfoam`` 为 **GT newFoam 数量**
    （无泡沫时传 ``-1`` 表示不采样）。若传入 ``0`` 则与库一致，使用 ``round(sum(p)*2143*factor_when_zero_gt)``。
    """
    if foam_gt_y is None:
        return gs_pos.new_zeros((0, 6))
    y = foam_gt_y.reshape(-1).float().clamp(0.0, 1.0)
    pos_flat = gs_pos.reshape(-1, 3)
    vel_flat = gs_vel.reshape(-1, 3)
    if y.numel() != pos_flat.shape[0] or vel_flat.shape[0] != pos_flat.shape[0]:
        return gs_pos.new_zeros((0, 6))
    d_ref = float(d_max_reference)
    d = inverse_map_gt_log_to_density(y, float(alpha), d_max_reference=d_ref)
    if d_ref > 1e-20:
        prob = (d / d_ref).clamp(0.0, 1.0)
    else:
        prob = torch.zeros_like(d)
    prob_scale = _gaussian_voxel_inv_count_scale(gs_pos, voxel_corner_min, voxel_corner_max, voxel_size)
    if prob_scale.numel() != prob.numel():
        return gs_pos.new_zeros((0, 6))
    prob = prob * prob_scale

    prob = torch.clamp(prob, min=0.0)
    prob = torch.where(prob < float(noise_threshold), torch.zeros_like(prob), prob)

    st = int(sample_times_gt_newfoam)
    if st == -1:
        return gs_pos.new_zeros((0, 6))
    if st > 0:
        k = st
    else:
        k = int(round(float(prob.sum().item()) * 2143.0 * float(factor_when_zero_gt)))

    n_nonempty = int((prob > 0).sum().item())
    if n_nonempty == 0 or k <= 0:
        return gs_pos.new_zeros((0, 6))

    if replacement:
        k = max(0, k)
    else:
        k = max(0, min(k, n_nonempty))
    if k == 0:
        return gs_pos.new_zeros((0, 6))

    idx = torch.multinomial(prob, k, replacement=bool(replacement))
    return torch.cat([pos_flat[idx], vel_flat[idx]], dim=-1)


def prepare_sample(sample: Optional[Dict[str, Any]], device: torch.device) -> Optional[Dict[str, Any]]:
    """与 compare_foam / RealTimeWater 一致：pos/vel/radius/camera 放到 device。"""
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
    pos = pos.to(device, dtype=torch.float32, non_blocking=True)
    if vel is not None:
        vel = vel.to(device, dtype=torch.float32, non_blocking=True)
    else:
        vel = torch.zeros_like(pos)
    sample["positions"] = pos
    sample["vel"] = vel
    sample["num_particles"] = int(sample.get("num_particles", pos.shape[0]))
    _r = sample.get("radius")
    sample["radius"] = float(0.01 if _r is None else _r)
    if sample.get("camera") is None:
        sample["camera"] = camera_from_particles(pos)
    return sample


@dataclass
class FoamSceneConfig:
    data_path: str
    scene: str
    model_path: str
    device: str = "cuda:0"
    width: int = 1080
    height: int = 1080
    create_window: bool = False
    require_mesh: bool = False
    max_frames: int = 0
    # Minimal 对齐默认
    search_factor: float = 4.0
    search_workers: int = -1
    search_timing: bool = False
    search_optimized: bool = True
    search_cov_method: int = 0
    search_exclude_self: bool = False
    search_splash_threshold: int = 2
    surface_neighbor_threshold: int = 32
    surface_flatness_threshold: float = 0.45
    surface_splash_neighbor: int = 6
    net_gs_num: int = 24
    net_decoder_variant: str = "direct"
    net_decoder_layers: Tuple[int, ...] = (256, 512)
    foam_density_log_alpha: float = 200.0
    foam_density_log_d_max: float = 1.0
    foam_loss_use_culled_gaussians: bool = True
    projector_hit_threshold: float = 0.5
    # 泡沫采样体素盒（prob 按体素内 1/N 均分）
    voxel_corner_min: Tuple[float, float, float] = (-5.0, -5.0, -5.0)
    voxel_corner_max: Tuple[float, float, float] = (5.0, 5.0, 5.0)
    voxel_size: float = 0.1


class FoamSceneRunner:
    """
    RealTimeWaterMinimal 式推理（Falcor 剔除 + 网络 + 投影）；泡沫采样对 ``prob`` 乘体素内 ``1/N``，
    ``sampleTimes`` 为 GT newFoam 数量，``noiseThreshold`` 来自 Falcor。
    """

    def __init__(self, cfg: FoamSceneConfig):
        self.cfg = cfg
        d = (cfg.device or "cpu").strip().lower()
        if d.startswith("cuda") and not torch.cuda.is_available():
            self.device = torch.device("cpu")
        else:
            self.device = torch.device(cfg.device)
        self.infer_cfg = InferConfig(
            output_dir="OutputFoamScene",
            device=str(self.device),
            search_factor=cfg.search_factor,
            search_workers=cfg.search_workers,
            search_timing=cfg.search_timing,
            search_optimized=cfg.search_optimized,
            search_cov_method=cfg.search_cov_method,
            search_exclude_self=cfg.search_exclude_self,
            search_splash_threshold=cfg.search_splash_threshold,
            net_gs_num=cfg.net_gs_num,
            net_decoder_variant=cfg.net_decoder_variant,
            net_decoder_layers=list(cfg.net_decoder_layers),
            width=cfg.width,
            height=cfg.height,
            surface_neighbor_threshold=cfg.surface_neighbor_threshold,
            surface_flatness_threshold=cfg.surface_flatness_threshold,
            surface_splash_neighbor=cfg.surface_splash_neighbor,
            foam_density_log_alpha=cfg.foam_density_log_alpha,
            foam_density_log_d_max=cfg.foam_density_log_d_max,
            foam_loss_use_culled_gaussians=cfg.foam_loss_use_culled_gaussians,
        )
        self.model = CovDecoderModel(self.infer_cfg.to_net_config(), cov_dim=DEFAULT_COV_DIM).to(self.device)
        self.model.eval()
        self.projector = GaussianProjector(
            width=self.infer_cfg.width,
            height=self.infer_cfg.height,
            device=self.device,
            hit_threshold=float(cfg.projector_hit_threshold),
        )
        self.falcor_render = FalcorRealTimeWaterRenderer(
            FalcorRealTimeWaterConfig(
                width=cfg.width,
                height=cfg.height,
                create_window=cfg.create_window,
                data_path=cfg.data_path,
                scene=cfg.scene,
            )
        )
        self.particle_filter = FalcorParticelFilterRenderer(FalcorParticleFilterConfig())
        ckpt = torch.load(cfg.model_path, map_location=self.device)
        state = ckpt.get("model_state_dict", ckpt)
        self.model.load_state_dict(state, strict=True)
        self.model.eval()

    def _cull_surface(self, pos: torch.Tensor, particle_radius: float):
        self.particle_filter.setCamera(self.falcor_render.get_FalcorCamInstance())
        surface_index = self.particle_filter.filterParticle(pos, particle_radius)
        return surface_index, self.particle_filter.getDownSampleX()

    def infer_pred_newfoam(self, sample: Dict[str, Any]) -> torch.Tensor:
        """返回 ``newFoam``，shape ``[M, 6]``（pos+vel）。"""
        cfg = self.infer_cfg
        pos = sample["positions"]
        vel = sample.get("vel")
        particle_radius = float(sample["radius"])
        radius = float(cfg.search_factor) * particle_radius
        min_radius = particle_radius * 2.0

        if cfg.search_optimized:
            pos = pos.to(self.device)
            if vel is not None:
                vel = vel.to(self.device)

        falcor_camera = self.falcor_render.get_camera()

        surface_index, down_sample_x = self._cull_surface(pos, particle_radius)
        if surface_index.shape[0] == 0:
            surface_index = torch.tensor([0], dtype=torch.uint32, device=self.device)
        surface_index = surface_index.long()
        pos = pos[surface_index]
        if vel is not None:
            vel = vel[surface_index]
        else:
            vel = torch.zeros_like(pos)

        _src, _dst, cov_pos, cov_vel, center_delta = search(
            pos,
            radius * down_sample_x,
            vel=vel,
            minRadius=min_radius * down_sample_x,
            pos_scale=radius * down_sample_x,
            exclude_self=cfg.search_exclude_self,
            splash_threshold=cfg.search_splash_threshold,
            workers=cfg.search_workers,
            timing=cfg.search_timing,
            use_optimized=cfg.search_optimized,
            cov_method=cfg.search_cov_method,
        )

        center_delta_t = (
            center_delta.to(device=self.device, dtype=torch.float32)
            if center_delta is not None
            else torch.zeros((cov_pos.shape[0], 3), dtype=torch.float32, device=self.device)
        )
        cov_pos_t = cov_pos.to(device=self.device, dtype=torch.float32)
        cov_vel_t = cov_vel.to(device=self.device, dtype=torch.float32)
        pos_t = pos.to(device=self.device, dtype=torch.float32)

        with torch.no_grad():
            gs_pos, gs_scale, gs_rotation, target_n, foam_prob, foam_prob_raw = self.model(
                cov_pos_t,
                cov_vel_t,
                center_delta_t,
                pos_t,
                radius=float(particle_radius * down_sample_x),
                kernel_size=float(cfg.search_factor),
            )
            vel_t = vel.to(device=self.device, dtype=torch.float32)
            gs_num = int(cfg.net_gs_num)
            gs_vel = vel_t.unsqueeze(1).repeat(1, gs_num, 1).reshape(-1, 3)

        _normal, _depth, _hit, _vel_img, foam_prob_culled, gs_pos_culled, _foam_prob_raw_culled, gs_vel_culled = (
            self.projector.project(
                falcor_camera,
                gs_pos,
                gs_scale,
                gs_rotation,
                target_n,
                None,
                foam_prob,
                gs_vel,
                foam_prob_raw,
            )
        )

        _, noise_threshold = self.falcor_render.getSampleTimesAndNoiseThreshold()
        gt_n = _newfoam_gt_count(sample)
        sample_times_gt = -1 if gt_n <= 0 else int(gt_n)

        if getattr(self.infer_cfg, "foam_loss_use_culled_gaussians", True):
            fp, fv, fprob = gs_pos_culled, gs_vel_culled, foam_prob_culled
        else:
            fp, fv, fprob = gs_pos, gs_vel, foam_prob

        scfg = self.cfg
        return _sample_foam_from_network_output_voxel_scaled(
            fp,
            fv,
            fprob,
            alpha=float(self.infer_cfg.foam_density_log_alpha),
            d_max_reference=float(self.infer_cfg.foam_density_log_d_max),
            voxel_corner_min=scfg.voxel_corner_min,
            voxel_corner_max=scfg.voxel_corner_max,
            voxel_size=float(scfg.voxel_size),
            sample_times_gt_newfoam=sample_times_gt,
            noise_threshold=float(noise_threshold),
            replacement=False,
            factor_when_zero_gt=1.0,
        )


def main() -> None:
    p = argparse.ArgumentParser(description="SceneDataset：GT newFoam 数量 + Minimal 式推理泡沫数量")
    p.add_argument("--data_path", type=str, required=True)
    p.add_argument("--scene", type=str, required=True)
    p.add_argument("--model", type=str, required=True, help="checkpoint 路径（结构需与 net 参数一致）")
    p.add_argument("--device", type=str, default="cuda:0")
    p.add_argument("--max_frames", type=int, default=0, help="0 表示全部帧")
    p.add_argument("--require_mesh", action="store_true")
    p.add_argument("--create_window", action="store_true", help="Falcor 是否创建窗口（默认关，适合批处理）")
    p.add_argument("--width", type=int, default=1080)
    p.add_argument("--height", type=int, default=1080)
    p.add_argument("--search_factor", type=float, default=4.0)
    p.add_argument("--net_gs_num", type=int, default=24)
    p.add_argument("--decoder_variant", type=str, default="direct")
    p.add_argument("--decoder_layers", type=str, default="256,512", help="逗号分隔，如 256,512")
    p.add_argument("--foam_log_alpha", type=float, default=200.0)
    p.add_argument("--foam_log_d_max", type=float, default=1.0)
    p.add_argument("--search_optimized", action="store_true", default=True)
    p.add_argument("--no_search_optimized", action="store_false", dest="search_optimized")
    p.add_argument("--search_exclude_self", action="store_true", default=False)
    p.add_argument("--projector_hit_threshold", type=float, default=0.5)
    p.add_argument("--corner_min", nargs=3, type=float, required=True, metavar=("X", "Y", "Z"))
    p.add_argument("--corner_max", nargs=3, type=float, required=True, metavar=("X", "Y", "Z"))
    p.add_argument("--voxel_size", type=float, required=True, help="体素边长（世界单位）")
    p.add_argument(
        "--metric_corner_min",
        nargs=3,
        type=float,
        default=None,
        metavar=("X", "Y", "Z"),
        help="指标用体素盒 min（与采样网格独立）；须与 metric_corner_max、metric_voxel_size 同时给出",
    )
    p.add_argument("--metric_corner_max", nargs=3, type=float, default=None, metavar=("X", "Y", "Z"))
    p.add_argument("--metric_voxel_size", type=float, default=None, help="指标用体素边长")
    args = p.parse_args()

    _m_tri = (
        args.metric_corner_min is not None,
        args.metric_corner_max is not None,
        args.metric_voxel_size is not None,
    )
    if any(_m_tri) and not all(_m_tri):
        raise SystemExit("指标网格须同时提供 --metric_corner_min、--metric_corner_max、--metric_voxel_size")
    metric_enabled = all(_m_tri)

    layers = tuple(int(x.strip()) for x in args.decoder_layers.split(",") if x.strip())
    if not layers:
        layers = (256, 512)

    cfg = FoamSceneConfig(
        data_path=args.data_path,
        scene=args.scene,
        model_path=args.model,
        device=args.device,
        width=int(args.width),
        height=int(args.height),
        create_window=bool(args.create_window),
        require_mesh=bool(args.require_mesh),
        max_frames=int(args.max_frames),
        search_factor=float(args.search_factor),
        net_gs_num=int(args.net_gs_num),
        net_decoder_variant=str(args.decoder_variant),
        net_decoder_layers=layers,
        foam_density_log_alpha=float(args.foam_log_alpha),
        foam_density_log_d_max=float(args.foam_log_d_max),
        search_optimized=bool(args.search_optimized),
        search_exclude_self=bool(args.search_exclude_self),
        projector_hit_threshold=float(args.projector_hit_threshold),
        voxel_corner_min=tuple(float(x) for x in args.corner_min),
        voxel_corner_max=tuple(float(x) for x in args.corner_max),
        voxel_size=float(args.voxel_size),
    )

    ds = SceneDataset(cfg.data_path, cfg.scene, require_mesh=cfg.require_mesh)
    n = len(ds)
    limit = n if cfg.max_frames <= 0 else min(n, cfg.max_frames)

    runner = FoamSceneRunner(cfg)

    metric_mins = tuple(float(x) for x in args.metric_corner_min) if metric_enabled else None
    metric_maxs = tuple(float(x) for x in args.metric_corner_max) if metric_enabled else None
    metric_vs = float(args.metric_voxel_size) if metric_enabled else None

    print(
        f"scene={ds.scene_name} frames_total={n} frames_used={limit} "
        f"voxel_box={cfg.voxel_corner_min}..{cfg.voxel_corner_max} vs={cfg.voxel_size} "
        f"(splat: GT-count sampleTimes + per-voxel prob /N)"
    )
    if metric_enabled:
        print(
            f"foam_voxel_metrics_enabled: metric_box={metric_mins}..{metric_maxs} metric_vs={metric_vs} "
            f"(8-corner splat, independent grid)"
        )
    print("frame_idx\tmeta_frame_id\tgt_newfoam\tpred_newfoam")
    metric_rows: list[FoamMetricVoxelResult] = []
    for i in range(limit):
        raw = ds[i]
        if raw is None:
            print(f"{i}\t-1\t-1\t-1")
            continue
        meta = int(raw.get("meta_frame_id", -1))
        gt_n = _newfoam_gt_count(raw)
        sample = prepare_sample(dict(raw), runner.device)
        if sample is None or int(sample.get("num_particles", 0)) <= 0:
            print(f"{i}\t{meta}\t{gt_n}\t0")
            continue
        runner.falcor_render.setFrameId(meta)
        try:
            pred = runner.infer_pred_newfoam(sample)
            pred_n = int(pred.shape[0])
        except Exception as e:
            print(f"{i}\t{meta}\t{gt_n}\t-1\terror={e!r}")
            continue
        print(f"{i}\t{meta}\t{gt_n}\t{pred_n}")
        if metric_enabled:
            try:
                gt_xyz = _gt_newfoam_xyz_np(raw)
                pred_xyz = pred[:, :3].detach().cpu().numpy().astype(np.float64)
                m = compute_foam_metric_voxel_overlap(
                    gt_xyz,
                    pred_xyz,
                    metric_corner_min=metric_mins,  # type: ignore[arg-type]
                    metric_corner_max=metric_maxs,  # type: ignore[arg-type]
                    metric_voxel_size=metric_vs,  # type: ignore[arg-type]
                )
                metric_rows.append(m)
                cnt_diff = abs(m.n_cells_gt - m.n_cells_pred)
                print(
                    f"  [metric] n_gt_cells={m.n_cells_gt} n_pred_cells={m.n_cells_pred} "
                    f"n_inter={m.n_cells_inter} n_union={m.n_cells_union} "
                    f"|n_gt-n_pred|={cnt_diff} "
                    f"mae_union={m.mae_density_on_union:.6g} mean_rel_pct={m.mean_rel_err_pct_on_union:.6g}"
                )
            except Exception as me:
                print(f"  [metric] error: {me!r}")

    if metric_enabled and metric_rows:
        k = len(metric_rows)
        mean_inter = sum(r.n_cells_inter for r in metric_rows) / k
        mean_union = sum(r.n_cells_union for r in metric_rows) / k
        mean_ngt = sum(r.n_cells_gt for r in metric_rows) / k
        mean_npred = sum(r.n_cells_pred for r in metric_rows) / k
        mean_cnt_diff = sum(abs(r.n_cells_gt - r.n_cells_pred) for r in metric_rows) / k
        mae_vals = [r.mae_density_on_union for r in metric_rows if math.isfinite(r.mae_density_on_union)]
        pct_vals = [r.mean_rel_err_pct_on_union for r in metric_rows if math.isfinite(r.mean_rel_err_pct_on_union)]
        mean_mae = sum(mae_vals) / len(mae_vals) if mae_vals else float("nan")
        mean_pct = sum(pct_vals) / len(pct_vals) if pct_vals else float("nan")
        print("")
        print("### foam_voxel_metrics_summary (8-corner splat on metric grid)")
        print(f"  frames_in_summary={k}")
        print(f"  mean_n_cells_gt={mean_ngt:.6g}  mean_n_cells_pred={mean_npred:.6g}")
        print(f"  mean_n_cells_intersection={mean_inter:.6g}  mean_n_cells_union={mean_union:.6g}")
        print(f"  mean_abs_diff_nonzero_cell_counts(|gt-pred|)={mean_cnt_diff:.6g}")
        print(f"  mean_mae_density_on_union={mean_mae:.6g}  mean_mean_rel_err_pct_on_union={mean_pct:.6g}")


if __name__ == "__main__":
    main()
