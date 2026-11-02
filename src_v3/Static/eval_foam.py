#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
`RealTimeWater.py` 非 timing 模式的简化副本。

目标:
1. 保留核心推理/渲染链路:
   provider -> prepare_sample -> cull -> search -> model -> projector -> Falcor
2. 省略 `pause`、`SaveResult` 状态切换、复杂循环重置等控制逻辑。
3. 同时提供泡沫体素评估工具，便于静态对比 GT / Pred newFoam。

示例:

    python -m src_v3.Static.eval_foam --data_path F:/DataSet/ShowData --scene Boat \
        --model Output/latest.pth --width 1920 --height 1080 --max_frames 10
"""

from __future__ import annotations

import argparse
import math
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, Mapping, Optional, Sequence

import numpy as np
import torch


FOAM_COUNT_TO_DENSITY: float = 2143.0


def _as_numpy_xyz(positions: Any) -> np.ndarray:
    """将输入统一成连续的 `float64 [N,3]` numpy 数组。"""
    if positions is None:
        return np.zeros((0, 3), dtype=np.float64)
    if isinstance(positions, torch.Tensor):
        arr = positions.detach().cpu().numpy()
    else:
        arr = np.asarray(positions)
    if arr.size == 0:
        return np.zeros((0, 3), dtype=np.float64)
    arr = np.asarray(arr, dtype=np.float64)
    if arr.ndim != 2 or arr.shape[1] < 3:
        return np.zeros((0, 3), dtype=np.float64)
    return np.ascontiguousarray(arr[:, :3])


def _voxel_grid_shape(
    corner_min: Sequence[float],
    corner_max: Sequence[float],
    voxel_size: float,
) -> tuple[int, int, int]:
    vs = float(voxel_size)
    if vs <= 0.0:
        raise ValueError("voxel_size must be positive")
    out: list[int] = []
    for i in range(3):
        extent = float(corner_max[i]) - float(corner_min[i])
        if extent <= 0.0:
            raise ValueError("corner_max must be larger than corner_min")
        n = int(math.floor(extent / vs + 1e-9))
        out.append(max(1, n))
    return int(out[0]), int(out[1]), int(out[2])


def _splat_foam_trilinear_8_corners(
    positions: Any,
    corner_min: Sequence[float],
    corner_max: Sequence[float],
    voxel_size: float,
) -> np.ndarray:
    """
    对泡沫点做 8-corner 三线性 splat，返回角点网格 `(nx+1, ny+1, nz+1)`。

    盒外点直接忽略，便于做离线统计。
    """
    pos = _as_numpy_xyz(positions)
    nx, ny, nz = _voxel_grid_shape(corner_min, corner_max, voxel_size)
    C = np.zeros((nx + 1, ny + 1, nz + 1), dtype=np.float64)
    if pos.shape[0] == 0:
        return C

    cm = np.asarray(corner_min, dtype=np.float64).reshape(1, 3)
    cM = np.asarray(corner_max, dtype=np.float64).reshape(1, 3)
    inside = np.all((pos >= cm) & (pos < cM), axis=1)
    pos = pos[inside]
    if pos.shape[0] == 0:
        return C

    vs = float(voxel_size)
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
                wx = fx if a else (1.0 - fx)
                wy = fy if b else (1.0 - fy)
                wz = fz if c else (1.0 - fz)
                w = wx * wy * wz
                np.add.at(C, (ix + a, iy + b, iz + c), w)
    return C


def _corner_grid_to_cell_sum8(corner_grid: np.ndarray) -> np.ndarray:
    """将角点网格汇总成体素网格 `(nx, ny, nz)`。"""
    return (
        corner_grid[0:-1, 0:-1, 0:-1]
        + corner_grid[1:, 0:-1, 0:-1]
        + corner_grid[0:-1, 1:, 0:-1]
        + corner_grid[1:, 1:, 0:-1]
        + corner_grid[0:-1, 0:-1, 1:]
        + corner_grid[1:, 0:-1, 1:]
        + corner_grid[0:-1, 1:, 1:]
        + corner_grid[1:, 1:, 1:]
    )


def ComputeFoamDensitySplat8(
    positions: Any,
    corner_min: Sequence[float],
    corner_max: Sequence[float],
    voxel_size: float,
) -> torch.Tensor:
    """
    计算泡沫计数体素场。

    返回值是 `torch.float64 [nx, ny, nz]`，语义是三线性 splat 后的体素 count volume。
    """
    corner_grid = _splat_foam_trilinear_8_corners(positions, corner_min, corner_max, voxel_size)
    return torch.from_numpy(_corner_grid_to_cell_sum8(corner_grid))


@dataclass
class FoamVoxelEvalMetrics:
    count_mae_union: float
    count_pct_union: float
    count_mae_both: float
    count_pct_both: float
    density_mae_union: float
    density_mae_both: float
    integral_projection_pct: Dict[str, float]

    def scalar_row_finite(self) -> bool:
        values = (
            self.count_mae_union,
            self.count_pct_union,
            self.count_mae_both,
            self.count_pct_both,
            self.density_mae_union,
            self.density_mae_both,
        )
        return all(math.isfinite(float(v)) for v in values)

    def integral_all_finite(self) -> bool:
        if not isinstance(self.integral_projection_pct, Mapping):
            return False
        return all(math.isfinite(float(v)) for v in self.integral_projection_pct.values())


class FoamVoxelEvaluator:
    """用统一体素盒评估 GT / Pred 泡沫点集。"""

    def __init__(
        self,
        gt_positions: Any,
        pred_positions: Any,
        *,
        corner_min: Sequence[float],
        corner_max: Sequence[float],
        voxel_size: float,
        count_to_density: float = FOAM_COUNT_TO_DENSITY,
        eps: float = 1e-12,
    ) -> None:
        self.corner_min = tuple(float(x) for x in corner_min)
        self.corner_max = tuple(float(x) for x in corner_max)
        self.voxel_size = float(voxel_size)
        self.count_to_density = float(count_to_density)
        self.eps = float(eps)

        self.gt_positions = _as_numpy_xyz(gt_positions)
        self.pred_positions = _as_numpy_xyz(pred_positions)
        self.count_volume_gt = ComputeFoamDensitySplat8(
            self.gt_positions,
            self.corner_min,
            self.corner_max,
            self.voxel_size,
        ).to(torch.float64)
        self.count_volume_pred = ComputeFoamDensitySplat8(
            self.pred_positions,
            self.corner_min,
            self.corner_max,
            self.voxel_size,
        ).to(torch.float64)

    def _masked_mae(self, gt: torch.Tensor, pred: torch.Tensor, mask: torch.Tensor) -> float:
        if int(mask.sum().item()) <= 0:
            return float("nan")
        return float(torch.mean(torch.abs(gt[mask] - pred[mask])).item())

    def _masked_pct(self, gt: torch.Tensor, pred: torch.Tensor, mask: torch.Tensor) -> float:
        if int(mask.sum().item()) <= 0:
            return float("nan")
        gt_sel = gt[mask]
        pred_sel = pred[mask]
        gt_sum = float(gt_sel.sum().item())
        pred_sum = float(pred_sel.sum().item())
        if gt_sum <= self.eps or pred_sum <= self.eps:
            return float("nan")
        return float(torch.abs(gt_sel - pred_sel).sum().item() / max(gt_sum, self.eps) * 100.0)

    def _projection_pct(self, gt: torch.Tensor, pred: torch.Tensor) -> float:
        gt_sum = float(gt.sum().item())
        pred_sum = float(pred.sum().item())
        if gt_sum <= self.eps or pred_sum <= self.eps:
            return float("nan")
        return float(torch.abs(gt - pred).sum().item() / max(gt_sum, self.eps) * 100.0)

    def compute_metrics(self) -> FoamVoxelEvalMetrics:
        gt_count = self.count_volume_gt
        pred_count = self.count_volume_pred
        union = (gt_count > self.eps) | (pred_count > self.eps)
        both = (gt_count > self.eps) & (pred_count > self.eps)

        gt_density = gt_count / self.count_to_density
        pred_density = pred_count / self.count_to_density

        metrics = FoamVoxelEvalMetrics(
            count_mae_union=self._masked_mae(gt_count, pred_count, union),
            count_pct_union=self._masked_pct(gt_count, pred_count, union),
            count_mae_both=self._masked_mae(gt_count, pred_count, both),
            count_pct_both=self._masked_pct(gt_count, pred_count, both),
            density_mae_union=self._masked_mae(gt_density, pred_density, union),
            density_mae_both=self._masked_mae(gt_density, pred_density, both),
            integral_projection_pct={
                "sum_z_xy": self._projection_pct(gt_density.sum(dim=2), pred_density.sum(dim=2)),
                "sum_y_xz": self._projection_pct(gt_density.sum(dim=1), pred_density.sum(dim=1)),
                "sum_x_yz": self._projection_pct(gt_density.sum(dim=0), pred_density.sum(dim=0)),
            },
        )
        return metrics


def sample_gt_foam_positions_xyz(sample: Dict[str, Any], device: torch.device) -> Optional[torch.Tensor]:
    """GT 泡沫位置 xyz，取自 `sample["foam"]["positions"]`。"""
    foam = sample.get("foam")
    if not foam:
        return None
    pos = foam.get("positions")
    if pos is None:
        return None
    t = torch.as_tensor(pos, dtype=torch.float32)
    if t.ndim != 2 or t.shape[1] < 3 or t.shape[0] <= 0:
        return None
    return t[:, :3].to(device=device, dtype=torch.float32, non_blocking=True)


def sample_gt_newfoam_positions_np(sample: Dict[str, Any]) -> np.ndarray:
    """GT 新生泡沫 xyz，取自 `sample["newfoam"]["positions"]`。"""
    nf = sample.get("newfoam") or {}
    pos = nf.get("positions")
    if pos is None:
        return np.zeros((0, 3), dtype=np.float32)
    arr = np.asarray(pos, dtype=np.float32)
    if arr.ndim != 2 or arr.shape[1] < 3:
        return np.zeros((0, 3), dtype=np.float32)
    return np.ascontiguousarray(arr[:, :3])


@dataclass
class EvalFoamConfig:
    mode: str = "scene"
    data_path: str = ""
    scene: str = ""
    model: Optional[str] = None
    device: str = "cuda:0"
    width: int = 1920
    height: int = 1080
    save_dir: str = "output/eval_foam"
    max_frames: int = 0
    create_window: bool = True
    preload_scene: bool = True
    require_mesh: bool = False
    save_exr: bool = False

    search_factor: float = 4.0
    search_workers: int = -1
    search_timing: bool = False
    search_optimized: bool = True
    search_cov_method: int = 0
    search_exclude_self: bool = True
    search_splash_threshold: int = 2
    surface_neighbor_threshold: int = 0
    surface_flatness_threshold: float = 0.45
    surface_splash_neighbor: int = 6

    net_gs_num: int = 24
    net_decoder_variant: str = "split"
    net_decoder_layers: str = "256,512"

    sim_radius: float = 0.01
    foam_density_log_alpha: float = 200.0
    foam_density_log_d_max: float = 1.0
    foam_loss_use_culled_gaussians: bool = True

    eval_voxel: bool = False
    voxel_corner_min: tuple[float, float, float] = (-5.0, -5.0, -5.0)
    voxel_corner_max: tuple[float, float, float] = (5.0, 5.0, 5.0)
    voxel_size: float = 0.1


class EvalFoamRunner:
    """`RealTimeWater` 非 timing 路径的精简 Runner。"""

    def __init__(self, cfg: EvalFoamConfig):
        from src_v3.core.render import GaussianProjector
        from src_v3.core.render.falcor_manager import (
            BaseLineRenderer,
            FalcorBaseLineConfig,
            FalcorParticleFilterConfig,
            FalcorParticelFilterRenderer,
            FalcorRealTimeWaterConfig,
            FalcorRealTimeWaterRenderer,
        )
        from src_v3.models import CovDecoderModel, DEFAULT_COV_DIM
        from src_v3.training.config import InferConfig

        self.cfg = cfg
        self.device = self._resolve_device(cfg.device)
        self.InferConfig = InferConfig
        self.CovDecoderModel = CovDecoderModel
        self.DEFAULT_COV_DIM = DEFAULT_COV_DIM
        self.GaussianProjector = GaussianProjector

        self.infer_cfg = self._build_infer_cfg(cfg)
        self.model = CovDecoderModel(self.infer_cfg.to_net_config(), cov_dim=DEFAULT_COV_DIM).to(self.device)
        self.model.eval()
        self.projector = GaussianProjector(
            width=self.infer_cfg.width,
            height=self.infer_cfg.height,
            device=self.device,
            hit_threshold=0.5,
        )
        render_config = FalcorRealTimeWaterConfig(
            width=cfg.width,
            height=cfg.height,
            create_window=cfg.create_window,
            data_path=cfg.data_path,
            scene=cfg.scene,
        )
        self.falcor_render = FalcorRealTimeWaterRenderer(render_config)
        self.particle_filter = FalcorParticelFilterRenderer(FalcorParticleFilterConfig())
        self.baseline_renderer = BaseLineRenderer(
            FalcorBaseLineConfig(width=cfg.width, height=cfg.height, create_window=cfg.create_window)
        )
        if cfg.model:
            self._load_checkpoint(cfg.model)

    @staticmethod
    def _resolve_device(device: str) -> torch.device:
        d = (device or "cpu").strip().lower()
        if d.startswith("cuda") and not torch.cuda.is_available():
            print("[eval_foam] CUDA unavailable, fallback to CPU")
            return torch.device("cpu")
        return torch.device(device)

    def _build_infer_cfg(self, cfg: EvalFoamConfig):
        layers = [int(x) for x in cfg.net_decoder_layers.split(",") if x.strip()]
        if not layers:
            layers = [256, 512]
        return self.InferConfig(
            output_dir="OutputEvalFoam",
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
            net_decoder_layers=layers,
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
        print(f"[eval_foam] loaded checkpoint: {ckpt_path}")

    def save_result(self, frame_id: int, render_result: Optional[torch.Tensor]) -> None:
        if render_result is None:
            return
        out_dir = Path(self.cfg.save_dir).expanduser().resolve()
        out_dir.mkdir(parents=True, exist_ok=True)
        out_path = out_dir / f"frame_{int(frame_id):04d}.exr"
        try:
            import pyexr
        except ImportError:
            print("[eval_foam] pyexr is not installed; skip EXR export")
            return
        pyexr.write(str(out_path), render_result.detach().float().cpu().numpy())
        print(f"[eval_foam] saved result: {out_path}")

    def prepare_sample(self, sample: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        from src_v3.data.camera_from_particles import camera_from_particles

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

    def cull_surface_particles(self, pos: torch.Tensor, radius: float):
        self.particle_filter.setCamera(self.falcor_render.get_FalcorCamInstance())
        surface_index = self.particle_filter.filterParticle(pos, radius)
        return surface_index, self.particle_filter.getDownSampleX()

    def _sample_new_foam(
        self,
        gs_pos: torch.Tensor,
        gs_vel: torch.Tensor,
        foam_gt_y: Optional[torch.Tensor],
        factor: float,
        sample_times: int,
        noise_threshold: float,
    ) -> torch.Tensor:
        from src_v3.data.foam_density import sample_foam_from_gt_network_output_adjustV

        return sample_foam_from_gt_network_output_adjustV(
            gs_pos,
            gs_vel,
            foam_gt_y,
            alpha=float(self.infer_cfg.foam_density_log_alpha),
            d_max_reference=float(self.infer_cfg.foam_density_log_d_max),
            factor=float(factor),
            noiseThreshold=float(noise_threshold),
            sampleTimes=int(sample_times),
        )

    def _run_search_cull_model_splat(
        self,
        sample: Dict[str, Any],
        falcor_camera: Dict[str, Any],
    ) -> Optional[Dict[str, torch.Tensor]]:
        from src_v3.core.Searching import search

        cfg = self.infer_cfg
        pos = sample["positions"]
        vel = sample.get("vel")
        particle_radius = float(sample["radius"])
        radius = cfg.search_factor * particle_radius
        min_radius = particle_radius * 2.0

        surface_index, down_sample_x = self.cull_surface_particles(pos, particle_radius)
        if surface_index.shape[0] == 0:
            surface_index = torch.tensor([0], dtype=torch.uint32, device=self.device)
        surface_index = surface_index.long()
        pos = pos[surface_index]
        if vel is not None:
            vel = vel[surface_index]

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
                radius=float(particle_radius * down_sample_x),
                kernel_size=float(cfg.search_factor),
            )
            if vel is not None:
                vel_t = vel.to(device=self.device, dtype=torch.float32)
                gs_num = int(cfg.net_gs_num)
                gs_vel = vel_t.unsqueeze(1).repeat(1, gs_num, 1).reshape(-1, 3)
            else:
                gs_vel = torch.zeros_like(gs_pos, device=self.device)

        normal, depth, hit, vel_img, foam_prob_culled, gs_pos_culled, foam_prob_raw_culled, gs_vel_culled = (
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

        foam_density = self.falcor_render.getFoamDensity()
        sample_times, noise_threshold = self.falcor_render.getSampleTimesAndNoiseThreshold()
        if getattr(self.cfg, "foam_loss_use_culled_gaussians", True):
            foam_pos, foam_vel, foam_prob_used = gs_pos_culled, gs_vel_culled, foam_prob_culled
        else:
            foam_pos, foam_vel, foam_prob_used = gs_pos, gs_vel, foam_prob
        new_foam = self._sample_new_foam(
            foam_pos,
            foam_vel,
            foam_prob_used,
            factor=float(foam_density),
            sample_times=int(sample_times),
            noise_threshold=float(noise_threshold),
        )

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

    def baseline_output(self, sample: Dict[str, Any]) -> Dict[str, torch.Tensor]:
        self.baseline_renderer.setCamera(self.falcor_render.get_FalcorCamInstance())
        pos = sample["positions"]
        radius = sample["radius"]
        normal_depth = self.baseline_renderer.renderNormalDepth(pos, radius)
        hit = torch.all(normal_depth != 0, dim=-1)
        z1 = torch.zeros((0, 1), device=self.device, dtype=torch.float32)
        z3 = torch.zeros((0, 3), device=self.device, dtype=torch.float32)
        z6 = torch.zeros((0, 6), device=self.device, dtype=torch.float32)
        return {
            "normal": normal_depth[:, :, :3],
            "depth": normal_depth[:, :, 3:4],
            "hit": hit,
            "vel": torch.zeros(
                (normal_depth.shape[0], normal_depth.shape[1], 3),
                device=self.device,
                dtype=torch.float32,
            ),
            "foam_prob_culled": z1,
            "foam_prob_raw": z1,
            "gs_pos_culled": z3,
            "newFoam": z6,
        }

    def process_frame(
        self,
        sample: Dict[str, Any],
        refresh: bool,
        *,
        assume_prepared: bool = False,
    ) -> Optional[Dict[str, Any]]:
        if not assume_prepared:
            sample = self.prepare_sample(sample)
        if sample is None or int(sample.get("num_particles", 0)) <= 0:
            return None

        falcor_camera = self.falcor_render.get_camera()
        normal_selected = self.falcor_render.getNormalSelected()
        if normal_selected == 0:
            outputs = self._run_search_cull_model_splat(sample, falcor_camera)
        else:
            outputs = self.baseline_output(sample)
        if outputs is None:
            return None

        pos = sample["positions"]
        radius = sample["radius"]
        frame_id = int(sample.get("meta_frame_id", -1))
        self.falcor_render.setFrameId(frame_id)

        water_nd = torch.cat((outputs["normal"], outputs["depth"]), dim=-1)
        surface_vel_depth = torch.cat((outputs["vel"], outputs["depth"]), dim=-1)
        new_foam = outputs["newFoam"]
        gt_foam_xyz = sample_gt_foam_positions_xyz(sample, self.device)
        gt_newfoam_xyz = sample_gt_newfoam_positions_np(sample)
        render_result = self.falcor_render.render_real_time_water(
            pos,
            radius,
            water_nd,
            surface_vel_depth,
            new_foam,
            refresh,
            gt_foam_positions=gt_foam_xyz,
            gtNewFoamNum=int(gt_newfoam_xyz.shape[0]),
        )
        outputs["render_result"] = render_result
        outputs["meta_frame_id"] = frame_id
        outputs["pred_newfoam_xyz"] = (
            new_foam[:, :3].detach().cpu().numpy()
            if int(new_foam.shape[0]) > 0
            else np.zeros((0, 3), dtype=np.float32)
        )
        outputs["gt_newfoam_xyz"] = gt_newfoam_xyz
        return outputs


def run_eval_loop(cfg: EvalFoamConfig, provider: Any, runner: EvalFoamRunner) -> None:
    """
    简单顺序循环:
    - 每次直接取下一帧
    - 不处理 pause / save 开关切换
    - 默认 scene 跑一轮，simulation 需指定 `max_frames`
    """
    if cfg.mode == "scene":
        dataset_len = len(getattr(provider, "dataset", []))
        frame_limit = dataset_len if cfg.max_frames <= 0 else min(dataset_len, cfg.max_frames)
    else:
        frame_limit = cfg.max_frames if cfg.max_frames > 0 else 100

    print(f"[eval_foam] start mode={cfg.mode}, frames={frame_limit}, device={runner.device}")
    refresh = False
    metric_rows: list[FoamVoxelEvalMetrics] = []

    for loop_idx in range(frame_limit):
        t0 = time.perf_counter()
        sample = provider.next_sample()
        if sample is None:
            print(f"[eval_foam] frame={loop_idx} sample is None, skip")
            continue
        sample = runner.prepare_sample(sample)
        if sample is None:
            print(f"[eval_foam] frame={loop_idx} invalid sample, skip")
            continue

        outputs = runner.process_frame(sample, refresh=refresh, assume_prepared=True)
        if outputs is None:
            print(f"[eval_foam] frame={loop_idx} failed")
            continue

        if cfg.save_exr:
            runner.save_result(loop_idx, outputs.get("render_result"))

        pred_xyz = outputs["pred_newfoam_xyz"]
        gt_xyz = outputs["gt_newfoam_xyz"]
        pred_n = int(pred_xyz.shape[0])
        gt_n = int(gt_xyz.shape[0])
        refresh = bool(sample.get("meta_next_is_loop", False))

        msg = (
            f"[eval_foam] frame={loop_idx} meta_frame_id={sample.get('meta_frame_id', loop_idx)} "
            f"fluid={int(sample.get('num_particles', 0))} pred_newfoam={pred_n} gt_newfoam={gt_n}"
        )
        if cfg.eval_voxel:
            try:
                metrics = FoamVoxelEvaluator(
                    gt_xyz,
                    pred_xyz,
                    corner_min=cfg.voxel_corner_min,
                    corner_max=cfg.voxel_corner_max,
                    voxel_size=cfg.voxel_size,
                ).compute_metrics()
                metric_rows.append(metrics)
                msg += (
                    f" voxel_count_mae_union={metrics.count_mae_union:.6g}"
                    f" density_mae_union={metrics.density_mae_union:.6g}"
                )
            except Exception as exc:
                msg += f" voxel_eval_error={exc!r}"

        dt_ms = (time.perf_counter() - t0) * 1000.0
        fps = 1000.0 / max(dt_ms, 1e-6)
        print(f"{msg} fps={fps:.2f}")

    if cfg.eval_voxel and metric_rows:
        mean_count_mae = sum(m.count_mae_union for m in metric_rows if math.isfinite(m.count_mae_union))
        mean_density_mae = sum(m.density_mae_union for m in metric_rows if math.isfinite(m.density_mae_union))
        denom_count = max(1, sum(1 for m in metric_rows if math.isfinite(m.count_mae_union)))
        denom_density = max(1, sum(1 for m in metric_rows if math.isfinite(m.density_mae_union)))
        print(
            "[eval_foam] voxel_summary "
            f"frames={len(metric_rows)} "
            f"mean_count_mae_union={mean_count_mae / denom_count:.6g} "
            f"mean_density_mae_union={mean_density_mae / denom_density:.6g}"
        )


def parse_args() -> EvalFoamConfig:
    p = argparse.ArgumentParser(description="Simplified RealTimeWater non-timing copy for foam evaluation")
    p.add_argument("--mode", type=str, default="scene", choices=["scene", "simulation"])
    p.add_argument("--data_path", type=str, default="")
    p.add_argument("--scene", type=str, default="")
    p.add_argument("--model", type=str, required=True)
    p.add_argument("--device", type=str, default="cuda:0")
    p.add_argument("--width", type=int, default=1920)
    p.add_argument("--height", type=int, default=1080)
    p.add_argument("--max_frames", type=int, default=0, help="scene: 0=全部一轮; simulation: 0=100")
    p.add_argument("--output_dir", type=str, default="")
    p.add_argument("--create_window", action="store_true")
    p.add_argument("--require_mesh", action="store_true")
    p.add_argument("--no_preload_scene", action="store_true")
    p.add_argument("--save_exr", action="store_true")

    p.add_argument("--factor", type=float, default=4.0)
    p.add_argument("--workers", type=int, default=-1)
    p.add_argument("--search_optimized", action="store_true")
    p.add_argument("--cov_method", type=int, default=0)
    p.add_argument("--search_exclude_self", type=int, default=1, choices=(0, 1))
    p.add_argument("--search_splash_threshold", type=int, default=2)
    p.add_argument("--surface_neighbor_threshold", type=int, default=0)
    p.add_argument("--surface_flatness_threshold", type=float, default=0.45)
    p.add_argument("--surface_splash_neighbor", type=int, default=6)

    p.add_argument("--gs_num", type=int, default=24)
    p.add_argument("--decoder_variant", type=str, default="split", choices=["split", "direct"])
    p.add_argument("--decoder_layers", type=str, default="256,512")
    p.add_argument("--sim_radius", type=float, default=0.01)
    p.add_argument("--foam_density_log_alpha", type=float, default=200.0)
    p.add_argument("--foam_density_log_d_max", type=float, default=1.0)
    p.add_argument("--foam_loss_unculled", action="store_true")

    p.add_argument("--eval_voxel", action="store_true")
    p.add_argument("--voxel_corner_min", nargs=3, type=float, default=(-5.0, -5.0, -5.0))
    p.add_argument("--voxel_corner_max", nargs=3, type=float, default=(5.0, 5.0, 5.0))
    p.add_argument("--voxel_size", type=float, default=0.1)

    a = p.parse_args()
    default_output_dir = str(Path(a.data_path) / a.scene / "EvalFoam") if a.data_path and a.scene else "output/eval_foam"
    output_dir = a.output_dir if str(a.output_dir).strip() else default_output_dir
    return EvalFoamConfig(
        mode=a.mode,
        data_path=a.data_path,
        scene=a.scene,
        model=a.model,
        device=a.device,
        width=a.width,
        height=a.height,
        save_dir=output_dir,
        max_frames=int(a.max_frames),
        create_window=bool(a.create_window),
        preload_scene=not bool(a.no_preload_scene),
        require_mesh=bool(a.require_mesh),
        save_exr=bool(a.save_exr),
        search_factor=float(a.factor),
        search_workers=int(a.workers),
        search_timing=False,
        search_optimized=bool(a.search_optimized),
        search_cov_method=int(a.cov_method),
        search_exclude_self=bool(a.search_exclude_self),
        search_splash_threshold=int(a.search_splash_threshold),
        surface_neighbor_threshold=int(a.surface_neighbor_threshold),
        surface_flatness_threshold=float(a.surface_flatness_threshold),
        surface_splash_neighbor=int(a.surface_splash_neighbor),
        net_gs_num=int(a.gs_num),
        net_decoder_variant=str(a.decoder_variant),
        net_decoder_layers=str(a.decoder_layers),
        sim_radius=float(a.sim_radius),
        foam_density_log_alpha=float(a.foam_density_log_alpha),
        foam_density_log_d_max=float(a.foam_density_log_d_max),
        foam_loss_use_culled_gaussians=not bool(a.foam_loss_unculled),
        eval_voxel=bool(a.eval_voxel),
        voxel_corner_min=tuple(float(x) for x in a.voxel_corner_min),
        voxel_corner_max=tuple(float(x) for x in a.voxel_corner_max),
        voxel_size=float(a.voxel_size),
    )


def main() -> None:
    from src_v3.demo.sample_provider import build_provider

    cfg = parse_args()
    provider = build_provider(
        cfg.mode,
        cfg.data_path,
        cfg.scene,
        cfg.sim_radius,
        preload_scene=cfg.preload_scene,
        require_mesh=cfg.require_mesh,
    )
    runner = EvalFoamRunner(cfg)
    run_eval_loop(cfg, provider, runner)


if __name__ == "__main__":
    main()
