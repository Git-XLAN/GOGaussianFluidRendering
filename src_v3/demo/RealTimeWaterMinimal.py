# -*- coding: utf-8 -*-
"""
精简版实时水渲染：无外部配置文件，路径与超参均在下方常量区写死。

唯一对外接口：``Render(pos, radius, vel)``，完成
ParticleFilter → search → 网络推理 → Gaussian splat → Falcor 最终合成。

使用前请根据本机环境与 checkpoint 修改「硬编码常量」区块（尤其 MODEL_PATH、解码器维度与 net_gs_num）。
"""

from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, Optional

import torch

from src_v3.core.Searching import search
from src_v3.core.render import GaussianProjector
from src_v3.core.render.falcor_manager import (
    FalcorParticleFilterConfig,
    FalcorParticelFilterRenderer,
    FalcorRealTimeWaterConfig,
    FalcorRealTimeWaterRenderer,
)
from src_v3.data.foam_density import sample_foam_from_gt_network_output
from src_v3.models import CovDecoderModel, DEFAULT_COV_DIM
from src_v3.training.config import InferConfig

# ---------------------------------------------------------------------------
# 硬编码常量（按需修改）
# ---------------------------------------------------------------------------
_REPO_ROOT = Path(__file__).resolve().parents[2]

# 权重：需与 net_decoder_layers / net_gs_num / net_decoder_variant 一致
MODEL_PATH = str(_REPO_ROOT / "weights" / "latest.pth")

DEVICE = "cuda:0"
WIDTH = 1080
HEIGHT = 1080

# Falcor：data_path / scene 留空则使用仓库内 ``src_v3/baseRender.pyscene``
FALCOR_DATA_PATH = ""
FALCOR_SCENE_NAME = ""
CREATE_WINDOW = True

# 与 RealTimeWater 命令行示例对齐（见 RealTimeWater.py 文件头注释）
SEARCH_FACTOR = 4.0
SEARCH_WORKERS = -1
SEARCH_TIMING = False
SEARCH_OPTIMIZED = True
SEARCH_COV_METHOD = 0
SEARCH_EXCLUDE_SELF = False
SEARCH_SPLASH_THRESHOLD = 2

SURFACE_NEIGHBOR_THRESHOLD = 32
SURFACE_FLATNESS_THRESHOLD = 0.45
SURFACE_SPLASH_NEIGHBOR = 6

NET_GS_NUM = 24
NET_DECODER_VARIANT = "direct"
NET_DECODER_LAYERS = [256, 512]

FOAM_DENSITY_LOG_ALPHA = 200.0
FOAM_DENSITY_LOG_D_MAX = 1.0
FOAM_LOSS_USE_CULLED_GAUSSIANS = True

# 与 ``camera_from_particles`` 返回格式一致：origin/target/up 为长度 3 的 list，fov 为度（float）
DEFAULT_CAMERA: Dict[str, Any] = {
    "origin": [0.0, 0.0, 5.0],
    "target": [0.0, 0.0, 0.0],
    "up": [0.0, 1.0, 0.0],
    "fov": 60.0,
}

__all__ = ["Render"]


def _resolve_device(s: str) -> torch.device:
    d = (s or "cpu").strip().lower()
    if d.startswith("cuda") and not torch.cuda.is_available():
        return torch.device("cpu")
    return torch.device(s)


def _build_infer_cfg() -> InferConfig:
    return InferConfig(
        output_dir="OutputRealtimeMinimal",
        device=DEVICE,
        search_factor=SEARCH_FACTOR,
        search_workers=SEARCH_WORKERS,
        search_timing=SEARCH_TIMING,
        search_optimized=SEARCH_OPTIMIZED,
        search_cov_method=SEARCH_COV_METHOD,
        search_exclude_self=SEARCH_EXCLUDE_SELF,
        search_splash_threshold=SEARCH_SPLASH_THRESHOLD,
        net_gs_num=NET_GS_NUM,
        net_decoder_variant=NET_DECODER_VARIANT,
        net_decoder_layers=list(NET_DECODER_LAYERS),
        width=WIDTH,
        height=HEIGHT,
        surface_neighbor_threshold=SURFACE_NEIGHBOR_THRESHOLD,
        surface_flatness_threshold=SURFACE_FLATNESS_THRESHOLD,
        surface_splash_neighbor=SURFACE_SPLASH_NEIGHBOR,
        foam_density_log_alpha=FOAM_DENSITY_LOG_ALPHA,
        foam_density_log_d_max=FOAM_DENSITY_LOG_D_MAX,
        foam_loss_use_culled_gaussians=FOAM_LOSS_USE_CULLED_GAUSSIANS,
    )


class _MinimalRunner:
    """内部实现：首次 ``Render`` 时构造。"""

    def __init__(self) -> None:
        self.device = _resolve_device(DEVICE)
        self.infer_cfg = _build_infer_cfg()
        self.model = CovDecoderModel(self.infer_cfg.to_net_config(), cov_dim=DEFAULT_COV_DIM).to(self.device)
        self.model.eval()

        self.projector = GaussianProjector(
            width=self.infer_cfg.width,
            height=self.infer_cfg.height,
            device=self.device,
            hit_threshold=0.5,
        )

        render_cfg = FalcorRealTimeWaterConfig(
            width=WIDTH,
            height=HEIGHT,
            create_window=CREATE_WINDOW,
            data_path=FALCOR_DATA_PATH,
            scene=FALCOR_SCENE_NAME,
        )
        self.falcor_render = FalcorRealTimeWaterRenderer(render_cfg)

        filter_cfg = FalcorParticleFilterConfig()
        self.particle_filter = FalcorParticelFilterRenderer(filter_cfg)

        ckpt = torch.load(MODEL_PATH, map_location=self.device)
        state = ckpt.get("model_state_dict", ckpt)
        self.model.load_state_dict(state, strict=True)
        self.model.eval()

    def _sample_new_foam(
        self,
        gs_pos: torch.Tensor,
        gs_vel: torch.Tensor,
        foam_gt_y: Optional[torch.Tensor],
        factor: float,
        sample_times: int,
        noise_threshold: float,
    ) -> torch.Tensor:
        return sample_foam_from_gt_network_output(
            gs_pos,
            gs_vel,
            foam_gt_y,
            alpha=float(self.infer_cfg.foam_density_log_alpha),
            d_max_reference=float(self.infer_cfg.foam_density_log_d_max),
            factor=float(factor),
            noiseThreshold=noise_threshold,
            sampleTimes=sample_times,
        )

    def _cull_surface(self, pos: torch.Tensor, particle_radius: float):
        self.particle_filter.setCamera(self.falcor_render.get_FalcorCamInstance())
        surface_index = self.particle_filter.filterParticle(pos, particle_radius)
        return surface_index, self.particle_filter.getDownSampleX()

    def _pipeline(self, pos_full: torch.Tensor, vel_full: torch.Tensor, particle_radius: float,dt:float, simTime:float) -> torch.Tensor:
        cfg = self.infer_cfg
        falcor_camera = self.falcor_render.get_camera()

        # 与 RealTimeWater 一致：Falcor 最终 pass 使用全体粒子；剔除仅作用于 search / 网络输入
        surface_index, down_sample_x = self._cull_surface(pos_full, particle_radius)
        if surface_index.shape[0] == 0:
            surface_index = torch.tensor([0], dtype=torch.uint32, device=self.device)
        surface_index = surface_index.long()
        pos = pos_full[surface_index]
        vel = vel_full[surface_index]

        radius = cfg.search_factor * particle_radius
        min_radius = particle_radius * 2.0

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
            vel_t = vel.to(device=self.device, dtype=torch.float32)
            gs_num = int(cfg.net_gs_num)
            gs_vel = vel_t.unsqueeze(1).repeat(1, gs_num, 1).reshape(-1, 3)

        normal, depth, _hit, vel_img, foam_prob_culled, gs_pos_culled, foam_prob_raw_culled, gs_vel_culled = (
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
        if getattr(self.infer_cfg, "foam_loss_use_culled_gaussians", True):
            fp, fv, fprob = gs_pos_culled, gs_vel_culled, foam_prob_culled
        else:
            fp, fv, fprob = gs_pos, gs_vel, foam_prob
        new_foam = self._sample_new_foam(fp, fv, fprob, foam_density, sample_times, noise_threshold)

        water_nd = torch.cat((normal, depth), dim=-1)
        surface_vel_depth = torch.cat((vel_img, depth), dim=-1)

        # 与 process_frame_realtime 一致：refresh=True；无 GT 泡沫；厚度用全体粒子
        self.falcor_render.setTimeStep(dt)
        refresh = simTime <dt
        return self.falcor_render.render_real_time_water(
            pos_full,
            particle_radius,
            water_nd,
            surface_vel_depth,
            new_foam,
            refresh,
            gt_foam_positions=None,
        )

    def run(
        self,
        pos: Any,
        radius: float,
        vel: Any,
        dt:float,
        simTime:float
    ) -> torch.Tensor:
        pos_t = torch.as_tensor(pos, dtype=torch.float32)
        vel_t = torch.as_tensor(vel, dtype=torch.float32)
        if pos_t.ndim != 2 or pos_t.shape[1] != 3:
            raise ValueError("pos 须为 [N,3]")
        if vel_t.shape != pos_t.shape:
            raise ValueError("vel 须与 pos 同形状 [N,3]")
        n = int(pos_t.shape[0])
        if n <= 0:
            return torch.zeros((HEIGHT, WIDTH, 4), dtype=torch.float32, device=self.device)

        pos_t = pos_t.to(self.device, non_blocking=True)
        vel_t = vel_t.to(self.device, non_blocking=True)
        particle_radius = float(radius)

        sample = {
            "positions": pos_t,
            "vel": vel_t,
            "num_particles": n,
            "radius": particle_radius,
            "camera": {
                "origin": list(DEFAULT_CAMERA["origin"]),
                "target": list(DEFAULT_CAMERA["target"]),
                "up": list(DEFAULT_CAMERA["up"]),
                "fov": float(DEFAULT_CAMERA["fov"]),
            },
        }
        # 仅用于与完整 demo 一致地设置 frame 元数据（Falcor 内可能读取）
        self.falcor_render.setFrameId(int(sample.get("meta_frame_id", -1)))

        return self._pipeline(sample["positions"], sample["vel"], particle_radius, dt, simTime)


_runner: Optional[_MinimalRunner] = None


def Render(
    pos: Any,
    radius: float,
    vel: Any,
    dt:float,
    simTime:float
) -> torch.Tensor:
    """
    单帧全流程渲染。

    :param pos: 粒子位置 [N,3]，numpy 或 torch
    :param radius: 粒子半径（标量）
    :param vel: 粒子速度 [N,3]
    :return: RGBA 图像 [H,W,4]，float32（与 Falcor 读回一致）
    """
    global _runner
    if _runner is None:
        _runner = _MinimalRunner()
    return _runner.run(pos, radius, vel, dt, simTime)
