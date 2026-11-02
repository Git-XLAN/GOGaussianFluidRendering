# -*- coding: utf-8 -*-
"""
推理器：与 Trainer 使用相同的 Searching / 模型 / 高斯投影流程，
但不计算 GT / 损失，只输出 normal / depth / hit / vel 四个 buffer。

预留 TensorRT 开关：当前仅在 InferConfig 中保留 use_tensorrt / tensorrt_engine_path，
实际 TensorRT 推理逻辑留待后续实现。
"""

from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, Optional, Tuple
import time

import torch

from .config import InferConfig
from src_v3.models import CovDecoderModel, DEFAULT_COV_DIM
from src_v3.core.render import GaussianProjector
from src_v3.core.render.camera_utils import world_xyz_from_radial_depth_dict_camera
from src_v3.core.Searching import search
from src_v3.data.foam_density import sample_foam_from_gt_network_output


class InferRunner:
    """
    推理器：给定 SceneDataset 与 InferConfig，对每个 sample 输出
    normal/depth/hit/vel 四张 buffer（以 tensor 形式返回，或后续保存为图像）。
    """

    def __init__(self, dataset: Any, config: InferConfig):
        self.dataset = dataset
        self.config = config
        self._device = self._resolve_device(config.device)
        self.model: Optional[torch.nn.Module] = None
        self.projector: Optional[GaussianProjector] = None
        self._build_model_and_projector()

    def _resolve_device(self, device: str) -> torch.device:
        d = device.strip().lower() if device else "cpu"
        if d == "cpu":
            return torch.device("cpu")
        if d.startswith("cuda"):
            if not torch.cuda.is_available():
                print("  [Warn] CUDA 不可用，使用 CPU")
                return torch.device("cpu")
            return torch.device(d)
        return torch.device(device)

    @property
    def output_dir(self) -> Path:
        out = Path(self.config.output_dir)
        out.mkdir(parents=True, exist_ok=True)
        return out

    def _build_model_and_projector(self) -> None:
        """根据 InferConfig 创建 PyTorch 模型与 GaussianProjector。"""
        cfg = self.config
        # 预留 TensorRT 开关，当前仅使用 PyTorch 模型
        if cfg.use_tensorrt:
            print("[InferRunner] use_tensorrt=True，TensorRT 推理逻辑 TODO，暂时仍使用 PyTorch 模型。")

        net_config = cfg.to_net_config()
        self.model = CovDecoderModel(net_config, cov_dim=DEFAULT_COV_DIM).to(self._device)
        # 权重加载留给调用方在创建 InferRunner 后自行完成
        self.projector = GaussianProjector(width=cfg.width, height=cfg.height, device=self._device,hit_threshold = 0.9) #Infer 使用的剔除 要更高

    def load_checkpoint(self, ckpt_path: str) -> None:
        """从训练保存的 checkpoint 加载模型权重。"""
        if self.model is None:
            raise RuntimeError("模型尚未创建，无法加载权重")
        ckpt = torch.load(ckpt_path, map_location=self._device)
        state = ckpt.get("model_state_dict", ckpt)
        self.model.load_state_dict(state)
        self.model.eval()
        print(f"[InferRunner] 已从 {ckpt_path} 加载模型权重")

    def _sync_infer_device(self) -> None:
        if self._device.type == "cuda":
            torch.cuda.synchronize(self._device)

    def infer_sample(
        self, sample: Dict[str, Any]
    ) -> Tuple[Optional[Dict[str, torch.Tensor]], Dict[str, float]]:
        """
        对单个 sample 做一次推理，返回 (buffers 字典, 耗时毫秒)。

        耗时字段（CUDA 下段间会 synchronize，便于 GPU 计时）：
          - search_ms: 仅邻域搜索（Searching.search）
          - cull_ms: 表面粒子筛选（compute_surface_particle_mask + mask）；未启用时为 0
          - model_ms: 解码网络 + gs_vel 展开
          - splat_ms: Gaussian 投影 + 泡沫采样 + world_xyz
        """
        empty_timing: Dict[str, float] = {
            "search_ms": 0.0,
            "cull_ms": 0.0,
            "model_ms": 0.0,
            "splat_ms": 0.0,
        }
        if self.model is None or self.projector is None:
            raise RuntimeError("InferRunner 尚未初始化模型或投影器")

        n = sample.get("num_particles", 0)
        if n == 0:
            return None, empty_timing

        cfg = self.config
        self._sync_infer_device()
        pos = sample["positions"]
        vel = sample.get("vel")
        particle_radius = float(sample["radius"])
        radius = cfg.search_factor * particle_radius
        minRadius = particle_radius*2
        # 若使用优化搜索，希望整条链路在 GPU 上：先把 pos/vel 搬到推理 device
        if cfg.search_optimized:
            pos = pos.to(self._device)
            if vel is not None:
                vel = vel.to(self._device)

        self._sync_infer_device()
        t_search0 = time.perf_counter()

        # 邻域搜索（与训练一致）
        src, dst, cov_pos, cov_vel, center_delta = search(
            pos,
            radius,
            vel=vel,
            minRadius=minRadius,
            pos_scale=radius,
            exclude_self=cfg.search_exclude_self,
            splash_threshold=cfg.search_splash_threshold,
            workers=cfg.search_workers,
            timing=cfg.search_timing,
            use_optimized=cfg.search_optimized,
            cov_method=cfg.search_cov_method,
        )

        self._sync_infer_device()
        t_search1 = time.perf_counter()
        search_ms = (t_search1 - t_search0) * 1000.0

        # 表面粒子剔除（可选，与 v2 detect_surface_particles：扁平度 + 飞溅）
        cull_ms = 0.0
        threshold = getattr(cfg, "surface_neighbor_threshold", 0)
        if threshold > 0 and src is not None:
            self._sync_infer_device()
            t_cull0 = time.perf_counter()
            from src_v3.core.surface_particles import compute_surface_particle_mask

            flatness = float(getattr(cfg, "surface_flatness_threshold", 0.45))
            splash_n = int(getattr(cfg, "surface_splash_neighbor", 6))
            surface_mask = compute_surface_particle_mask(
                pos.float(),
                src,
                dst,
                flatness_threshold=flatness,
                splash_neighbor_threshold=splash_n,
            )
            n_surface = int(surface_mask.sum().item())
            if n_surface == 0:
                self._sync_infer_device()
                t_cull1 = time.perf_counter()
                cull_ms = (t_cull1 - t_cull0) * 1000.0
                return None, {
                    "search_ms": search_ms,
                    "cull_ms": cull_ms,
                    "model_ms": 0.0,
                    "splat_ms": 0.0,
                }
            # pos/vel 在上面已按需搬到 device，这里直接按 mask 过滤
            pos = pos[surface_mask]
            if vel is not None:
                vel = vel[surface_mask]
            cov_pos = cov_pos[surface_mask]
            cov_vel = cov_vel[surface_mask]
            center_delta = center_delta[surface_mask]
            self._sync_infer_device()
            t_cull1 = time.perf_counter()
            cull_ms = (t_cull1 - t_cull0) * 1000.0
            if cfg.search_timing:
                print(
                    f"[InferSurface] before={n}, after={n_surface} "
                    f"(flatness<{flatness}, splash_neighbors<{splash_n}), cull_ms={cull_ms:.2f}"
                )

        self._sync_infer_device()
        t_model0 = time.perf_counter()
        cov_pos_t = cov_pos.to(device=self._device, dtype=torch.float32)
        cov_vel_t = cov_vel.to(device=self._device, dtype=torch.float32)
        center_delta_t = center_delta.to(device=self._device, dtype=torch.float32)
        pos_t = pos.to(device=self._device, dtype=torch.float32)
        world_xyz: Optional[torch.Tensor] = None
        with torch.no_grad():
            gs_pos, gs_scale, gs_rotation, target_n, foam_prob, foam_prob_raw = self.model(
                cov_pos_t,
                cov_vel_t,
                center_delta_t,
                pos_t,
                radius=float(particle_radius),
                kernel_size=float(cfg.search_factor),
            )

            # 速度复制为 [N*gs_num,3]
            if vel is not None:
                vel_t = vel.to(device=self._device, dtype=torch.float32)
                gs_num = int(getattr(cfg, "net_gs_num", 36))
                gs_vel = vel_t.unsqueeze(1).repeat(1, gs_num, 1).reshape(-1, 3)
            else:
                gs_vel = torch.zeros_like(gs_pos, device=self._device)

            camera = sample.get("camera")
            if camera is None:
                # 若 sample 中无 camera，可根据需要在外部先调用 dataset.update_sample_camera
                raise ValueError("sample 中缺少 camera，请先为 sample 生成相机参数")

            self._sync_infer_device()
            t_model1 = time.perf_counter()
            model_ms = (t_model1 - t_model0) * 1000.0

            self._sync_infer_device()
            t_proj0 = time.perf_counter()
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

            use_culled = getattr(cfg, "foam_loss_use_culled_gaussians", True)
            if use_culled:
                foam_sample = sample_foam_from_gt_network_output(
                    gs_pos_culled,
                    gs_vel_culled,
                    foam_prob_culled,
                    alpha=float(getattr(cfg, "foam_density_log_alpha", 1.0)),
                    d_max_reference=float(getattr(cfg, "foam_density_log_d_max", 1.0)),
                    factor=float(cfg.foam_sample_factor),
                )
                foam_prob_raw_out = foam_prob_raw_culled
            else:
                foam_sample = sample_foam_from_gt_network_output(
                    gs_pos,
                    gs_vel,
                    foam_prob,
                    alpha=float(getattr(cfg, "foam_density_log_alpha", 1.0)),
                    d_max_reference=float(getattr(cfg, "foam_density_log_d_max", 1.0)),
                    factor=float(cfg.foam_sample_factor),
                )
                foam_prob_raw_out = foam_prob_raw

            if isinstance(camera, dict):
                world_xyz = world_xyz_from_radial_depth_dict_camera(
                    camera,
                    int(cfg.width),
                    int(cfg.height),
                    depth,
                    hit,
                    hit_threshold=float(self.projector.hit_threshold),
                )

            self._sync_infer_device()
            t_proj1 = time.perf_counter()
            splat_ms = (t_proj1 - t_proj0) * 1000.0

        timing_ms = {
            "search_ms": search_ms,
            "cull_ms": cull_ms,
            "model_ms": model_ms,
            "splat_ms": splat_ms,
        }

        if cfg.search_timing:
            total_ms = search_ms + cull_ms + model_ms + splat_ms
            print(
                f"[InferTiming] search={search_ms:.2f} ms, "
                f"cull={cull_ms:.2f} ms, "
                f"model={model_ms:.2f} ms, "
                f"splat={splat_ms:.2f} ms, "
                f"sum={total_ms:.2f} ms"
            )

        outputs: Dict[str, torch.Tensor] = {
            "normal": normal,
            "depth": depth,
            "hit": hit,
            "vel": vel_img,
            "foam_prob_raw": foam_prob_raw_out,
        }
        if world_xyz is not None:
            outputs["world_xyz"] = world_xyz
        # foam_sample: [M,6] pos+vel，与 RealTimeWater newFoam 语义一致
        outputs["foam_sample"] = foam_sample
        outputs["foam_positions"] = foam_sample[:, :3]

        return outputs, timing_ms

