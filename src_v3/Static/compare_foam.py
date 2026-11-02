# -*- coding: utf-8 -*-
"""
独立简化入口：内置 ``CompareFoamRunner`` + ``run_compare_foam_loop``，逻辑与
``src_v3.demo.RealTimeWater.RealTimeWaterRunner`` / ``run_loop_realtime`` 对齐，
**不** 从 ``RealTimeWater.py`` 导入 Runner（``RealTimeWater.py`` 中的 ``RealTimeWaterRunner`` 保持不变）。

使用前修改 ``DEFAULT_CHECKPOINT``。

    python -m src_v3.Static.compare_foam -d <数据根> -s <场景名>
"""

from __future__ import annotations

import argparse
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, Optional

import numpy as np
import torch

from src_v3.core.Searching import search
from src_v3.core.render import GaussianProjector
from src_v3.core.render.falcor_manager import (
    BaseLineRenderer,
    FalcorBaseLineConfig,
    FalcorParticleFilterConfig,
    FalcorParticelFilterRenderer,
    FalcorRealTimeWaterConfig,
    FalcorRealTimeWaterRenderer,
)
from src_v3.data.camera_from_particles import camera_from_particles
from src_v3.data.foam_density import sample_foam_from_gt_network_output
from src_v3.demo.sample_provider import build_provider
from src_v3.models import CovDecoderModel, DEFAULT_COV_DIM
from src_v3.training.config import InferConfig

# ---------------------------------------------------------------------------
# 本机 checkpoint（写死）
# ---------------------------------------------------------------------------
DEFAULT_CHECKPOINT: str = str(Path(__file__).resolve().parents[2] / "weights" / "latest.pth")
DEFAULT_DEVICE: str = "cuda:0"
DEFAULT_WIDTH: int = 1920
DEFAULT_HEIGHT: int = 1080


def sample_gt_foam_positions_xyz(sample: Dict[str, Any], device: torch.device) -> Optional[torch.Tensor]:
    """与 RealTimeWater 一致：GT 泡沫 ``foam.positions`` xyz。"""
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
    """GT newFoam xyz（与 RealTimeWater 一致）。"""
    nf = sample.get("newfoam") or {}
    pos = nf.get("positions")
    if pos is None:
        return np.zeros((0, 3), dtype=np.float32)
    t = np.asarray(pos, dtype=np.float32)
    if t.ndim != 2 or t.shape[1] < 3:
        return np.zeros((0, 3), dtype=np.float32)
    return np.ascontiguousarray(t[:, :3])


@dataclass
class CompareFoamConfig:
    """与 ``RealTimeWater.DemoConfig`` 同字段子集，供本模块 Runner 使用。"""

    data_path: str = ""
    scene: str = ""
    model: Optional[str] = None
    device: str = "cuda:0"
    width: int = 1920
    height: int = 1080
    loop: bool = True
    pause: bool = False
    save_dir: str = "output/realTime"

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
    net_decoder_variant: str = "direct"
    net_decoder_layers: str = "256,512"

    sim_radius: float = 0.01
    preload_scene: bool = True
    require_mesh: bool = False

    foam_density_log_alpha: float = 200.0
    foam_density_log_d_max: float = 1.0
    foam_loss_use_culled_gaussians: bool = True


class CompareFoamRunner:
    """
    独立拷贝的实时泡沫管线（与 ``RealTimeWaterRunner`` 行为对齐，便于本脚本单独演进）。
    """

    def __init__(self, cfg: CompareFoamConfig):
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

        render_config = FalcorRealTimeWaterConfig(
            width=cfg.width,
            height=cfg.height,
            data_path=cfg.data_path,
            scene=cfg.scene,
        )
        self.falcor_render = FalcorRealTimeWaterRenderer(render_config)

        filter_config = FalcorParticleFilterConfig()
        self.particle_filter = FalcorParticelFilterRenderer(filter_config)

        baseline_config = FalcorBaseLineConfig(width=cfg.width, height=cfg.height, create_window=True)
        self.baseline_renderer = BaseLineRenderer(baseline_config)

        if cfg.model:
            self._load_checkpoint(cfg.model)

    @staticmethod
    def _resolve_device(device: str) -> torch.device:
        d = (device or "cpu").strip().lower()
        if d.startswith("cuda") and not torch.cuda.is_available():
            print("[compare_foam] CUDA 不可用，回退 CPU")
            return torch.device("cpu")
        return torch.device(device)

    @staticmethod
    def _build_infer_cfg(cfg: CompareFoamConfig) -> InferConfig:
        layers = [int(x) for x in cfg.net_decoder_layers.split(",") if x.strip()]
        if not layers:
            layers = [256, 512]
        return InferConfig(
            output_dir="OutputCompareFoam",
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
        print(f"[compare_foam] loaded checkpoint: {ckpt_path}")

    def save_result(self, frame_id: int, render_result: Optional[torch.Tensor]) -> None:
        if render_result is None:
            print(f"[compare_foam] skip save frame {frame_id}: render_result is None")
            return
        out_dir = Path(self.cfg.save_dir).expanduser().resolve()
        out_dir.mkdir(parents=True, exist_ok=True)
        out_path = out_dir / f"frame_{int(frame_id):04d}.exr"
        try:
            import pyexr
        except ImportError:
            print("[compare_foam] pyexr 未安装，无法保存 EXR。请 pip install pyexr")
            return
        img = render_result.detach().float().cpu().numpy()
        pyexr.write(str(out_path), img)
        print(f"[compare_foam] saved result: {out_path}")

    def _sample_new_foam(
        self,
        gs_pos: torch.Tensor,
        gs_vel: torch.Tensor,
        foam_gt_y: Optional[torch.Tensor],
        factor=1.0,
        sample_times: int = 2000,
        noise_threshold: float = 0.002,
    ) -> torch.Tensor:
        cfg = self.infer_cfg
        return sample_foam_from_gt_network_output(
            gs_pos,
            gs_vel,
            foam_gt_y,
            alpha=float(getattr(cfg, "foam_density_log_alpha", 1.0)),
            d_max_reference=float(getattr(cfg, "foam_density_log_d_max", 1.0)),
            factor=float(factor),
            noiseThreshold=noise_threshold,
            sampleTimes=sample_times,
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
        if int(sample["num_particles"]) <= 0:
            return None
        return sample

    def cull_surface_particles(self, pos: torch.Tensor, radius: float):
        self.particle_filter.setCamera(self.falcor_render.get_FalcorCamInstance())
        surface_index = self.particle_filter.filterParticle(pos, radius)
        return surface_index, self.particle_filter.getDownSampleX()

    def _run_search_cull_model_splat(
        self,
        sample: Dict[str, Any],
        falcor_camera: Dict[str, Any],
    ) -> Optional[Dict[str, torch.Tensor]]:
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
        center_delta_t = center_delta.to(device=self.device, dtype=torch.float32) if center_delta is not None else None
        pos_t = pos.to(device=self.device, dtype=torch.float32)
        if center_delta_t is None:
            center_delta_t = torch.zeros((cov_pos.shape[0], 3), dtype=torch.float32, device=self.device)

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

        camera = falcor_camera
        normal, depth, hit, vel_img, foam_prob_culled, gs_pos_culled, foam_prob_raw_culled, gs_vel_culled = (
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
            )
        )

        foam_density = self.falcor_render.getFoamDensity()
        sample_times, noise_threshold = self.falcor_render.getSampleTimesAndNoiseThreshold()
        if getattr(self.cfg, "foam_loss_use_culled_gaussians", True):
            _fp, _fv, _fprob = gs_pos_culled, gs_vel_culled, foam_prob_culled
        else:
            _fp, _fv, _fprob = gs_pos, gs_vel, foam_prob
        new_foam = self._sample_new_foam(_fp, _fv, _fprob, foam_density, sample_times, noise_threshold)

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

    def baseline_output(
        self,
        sample: Dict[str, Any],
        falcor_camera: Dict[str, Any],
    ) -> Optional[Dict[str, torch.Tensor]]:
        self.baseline_renderer.setCamera(self.falcor_render.get_FalcorCamInstance())
        pos = sample["positions"]
        radius = sample["radius"]
        normal_depth = self.baseline_renderer.renderNormalDepth(pos, radius)
        hit = torch.all(normal_depth != 0, dim=-1)
        _z1 = torch.zeros((0, 1), device=self.device, dtype=torch.float32)
        _z3 = torch.zeros((0, 3), device=self.device, dtype=torch.float32)
        _z6 = torch.zeros((0, 6), device=self.device, dtype=torch.float32)
        return {
            "normal": normal_depth[:, :, :3],
            "depth": normal_depth[:, :, 3:4],
            "hit": hit,
            "vel": torch.zeros(
                (normal_depth.shape[0], normal_depth.shape[1], 3),
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

        falcor_camera = self.falcor_render.get_camera()
        normal_selected = self.falcor_render.getNormalSelected()
        if normal_selected == 0:
            outputs = self._run_search_cull_model_splat(sample, falcor_camera)
        else:
            outputs = self.baseline_output(sample, falcor_camera)

        if outputs is None:
            return None

        gt_newfoam_xyz = sample_gt_newfoam_positions_np(sample)

        pos = sample["positions"]
        radius = sample["radius"]
        frame_id = sample.get("meta_frame_id", -1)
        self.falcor_render.setFrameId(frame_id)

        water_nd = torch.cat((outputs["normal"], outputs["depth"]), dim=-1)
        surface_vel_depth = torch.cat((outputs["vel"], outputs["depth"]), dim=-1)
        new_foam = outputs["newFoam"]
        gt_foam_xyz = sample_gt_foam_positions_xyz(sample, self.device)

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
        outputs["meta_next_is_loop"] = bool(sample.get("meta_next_is_loop", False))
        outputs["meta_is_last_frame_in_scene"] = bool(sample.get("meta_is_last_frame_in_scene", False))
        outputs["meta_provider_idx"] = int(sample.get("meta_provider_idx", -1))
        outputs["meta_total_frames"] = int(sample.get("meta_total_frames", -1))
        if self.falcor_render.getSaveResult():
            outputs["render_result"] = render_result
        outputs["timing_info"] = None
        return outputs


def run_compare_foam_loop(cfg: CompareFoamConfig, provider: Any, runner: CompareFoamRunner) -> None:
    """与 ``RealTimeWater.run_loop_realtime`` 同结构，日志前缀为 ``[compare_foam]``。"""
    frame_count = 0
    saved_count = 0
    refresh = False
    paused_sample: Optional[Dict[str, Any]] = None
    last_saved_frame = -1
    prev_save_result_enabled = bool(runner.falcor_render.getSaveResult())
    force_loop_boundary = False
    while True:
        cfg.pause = runner.falcor_render.getPause()
        save_result_enabled = bool(runner.falcor_render.getSaveResult())

        if save_result_enabled and not prev_save_result_enabled:
            if hasattr(provider, "reset"):
                provider.reset()
            paused_sample = None
            frame_count = 0
            saved_count = 0
            last_saved_frame = -1
            refresh = True
            force_loop_boundary = True
            print("[compare_foam] SaveResult enabled: reset provider to first frame.")
        prev_save_result_enabled = save_result_enabled
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

        outputs = runner.process_frame_realtime(sample, refresh, assume_prepared=True)

        if runner.device.type == "cuda":
            torch.cuda.synchronize(runner.device)
        t_loop1 = time.perf_counter()
        loop_ms = (t_loop1 - t_loop0) * 1000.0
        fps = 1000.0 / max(loop_ms, 1e-6)
        print(
            f"[compare_foam] fps={fps:.2f}, next_loop={sample.get('meta_next_is_loop', False)}, pause={cfg.pause}"
        )

        if (not cfg.pause) and sample.get("meta_next_is_loop", False):
            refresh = True
        else:
            refresh = False

        if save_result_enabled and frame_count != last_saved_frame:
            render_result = outputs.get("render_result") if isinstance(outputs, dict) else None
            runner.save_result(frame_count, render_result)
            if isinstance(outputs, dict):
                outputs.pop("render_result", None)
            last_saved_frame = frame_count
            saved_count += 1

        save_target_frames = int(runner.falcor_render.getSaveFrames())
        if save_result_enabled and saved_count >= save_target_frames:
            print(f"[compare_foam] save_result: wrote {saved_count} frame(s), disabling save mode.")
            runner.falcor_render.setSaveResult(False)
            saved_count = 0
            last_saved_frame = -1

        if not cfg.pause:
            frame_count += 1
        if not save_result_enabled:
            loop_target_frames = int(runner.falcor_render.getSaveFrames())
            if not cfg.loop and frame_count >= loop_target_frames:
                break
            if cfg.loop and frame_count >= loop_target_frames:
                frame_count = 0


def _parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="独立 CompareFoamRunner（不依赖 demo.RealTimeWater 的 Runner 类）")
    p.add_argument("-d", "--data_path", type=str, required=True)
    p.add_argument("-s", "--scene", type=str, required=True)
    p.add_argument("-D", "--device", type=str, default=DEFAULT_DEVICE)
    p.add_argument("--no_loop", action="store_true", help="播完一轮后退出")
    return p.parse_args()


def _make_config(args: argparse.Namespace) -> CompareFoamConfig:
    ckpt = str(Path(DEFAULT_CHECKPOINT).expanduser().resolve())
    save_dir = str(Path(args.data_path).expanduser().resolve() / str(args.scene).strip() / "OurResult")
    return CompareFoamConfig(
        data_path=str(Path(args.data_path).expanduser().resolve()),
        scene=str(args.scene).strip(),
        model=ckpt,
        device=str(args.device).strip(),
        width=int(DEFAULT_WIDTH),
        height=int(DEFAULT_HEIGHT),
        loop=not bool(args.no_loop),
        pause=False,
        save_dir=save_dir,
        search_factor=4.0,
        search_workers=-1,
        search_timing=False,
        search_optimized=True,
        search_cov_method=0,
        search_exclude_self=True,
        search_splash_threshold=2,
        surface_neighbor_threshold=0,
        surface_flatness_threshold=0.45,
        surface_splash_neighbor=6,
        net_gs_num=24,
        net_decoder_variant="direct",
        net_decoder_layers="256,512",
        sim_radius=0.01,
        preload_scene=True,
        require_mesh=False,
        foam_density_log_alpha=200.0,
        foam_density_log_d_max=1.0,
        foam_loss_use_culled_gaussians=True,
    )


def main() -> None:
    args = _parse_args()
    ckpt_path = Path(DEFAULT_CHECKPOINT).expanduser().resolve()
    if not ckpt_path.is_file():
        raise SystemExit(
            f"[compare_foam] 找不到 checkpoint：{ckpt_path}\n"
            f"  请编辑 compare_foam.py 顶部的 DEFAULT_CHECKPOINT。"
        )

    cfg = _make_config(args)
    provider = build_provider(
        "scene",
        cfg.data_path,
        cfg.scene,
        cfg.sim_radius,
        preload_scene=cfg.preload_scene,
        require_mesh=cfg.require_mesh,
    )
    runner = CompareFoamRunner(cfg)

    print(
        "[compare_foam] 独立 Runner（CompareFoamRunner），未使用 demo.RealTimeWater.RealTimeWaterRunner\n"
        f"  checkpoint = {ckpt_path}\n"
        f"  data_path  = {cfg.data_path}\n"
        f"  scene      = {cfg.scene}\n"
        f"  device     = {cfg.device}  res={cfg.width}x{cfg.height}\n"
        f"  loop       = {cfg.loop}"
    )
    run_compare_foam_loop(cfg, provider, runner)


if __name__ == "__main__":
    main()
