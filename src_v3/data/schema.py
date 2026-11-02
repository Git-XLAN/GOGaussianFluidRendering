# -*- coding: utf-8 -*-
"""
数据 schema：明确 VTK 与 Dataset 的 key 约定，便于类型提示与文档。
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional, Dict, Any
import numpy as np
import torch


# ---------------------------------------------------------------------------
# VTK 层：loader 返回的原始字典 key
# ---------------------------------------------------------------------------

# 流体 VTK 必须/可选 key
VTK_FLUID_KEYS = {
    "nums": int,
    "positions": np.ndarray,   # [N, 4] (x, y, z, radius)
    "radius": float,
    "maxPos": np.ndarray,      # [3]
    "minPos": np.ndarray,      # [3]
    "vel": Optional[np.ndarray],  # [N, 3]
    "lifetime": Optional[np.ndarray],  # 流体通常 None
    "id": Optional[np.ndarray],
}

# 泡沫 VTK 额外 key
VTK_FOAM_KEYS_EXTRA = {
    "lifetime": Optional[np.ndarray],  # [N]
    "id": Optional[np.ndarray],        # [N]
    "is_born": Optional[np.ndarray],  # [N] bool
}


@dataclass
class FluidRaw:
    """流体 VTK 加载后的结构化视图（只读）。"""
    nums: int
    positions: np.ndarray   # [N, 4]
    radius: float
    max_pos: np.ndarray     # [3]
    min_pos: np.ndarray     # [3]
    vel: Optional[np.ndarray] = None  # [N, 3]

    @classmethod
    def from_vtk_dict(cls, d: Dict[str, Any]) -> "FluidRaw":
        return cls(
            nums=d["nums"],
            positions=d["positions"],
            radius=d["radius"],
            max_pos=d["maxPos"],
            min_pos=d["minPos"],
            vel=d.get("vel"),
        )


@dataclass
class FoamRaw:
    """泡沫 VTK 加载后的结构化视图。"""
    nums: int
    positions: np.ndarray   # [N, 4]
    radius: float
    max_pos: np.ndarray
    min_pos: np.ndarray
    vel: Optional[np.ndarray] = None
    lifetime: Optional[np.ndarray] = None
    id: Optional[np.ndarray] = None
    is_born: Optional[np.ndarray] = None  # bool [N]

    @classmethod
    def from_vtk_dict(cls, d: Dict[str, Any]) -> "FoamRaw":
        return cls(
            nums=d["nums"],
            positions=d["positions"],
            radius=d["radius"],
            max_pos=d["maxPos"],
            min_pos=d["minPos"],
            vel=d.get("vel"),
            lifetime=d.get("lifetime"),
            id=d.get("id"),
            is_born=d.get("is_born"),
        )


# ---------------------------------------------------------------------------
# Dataset 层：单帧样本提供给训练器的 key（与 v2 兼容）
# ---------------------------------------------------------------------------

# 单样本输出 key（供 Trainer 使用，不含下一帧相关）
SAMPLE_OUTPUT_KEYS = [
    "input_particles",   # [N, 4]
    "positions",         # [N, 3]
    "radii",             # [N, 1]
    "vel",
    "maxPos",
    "minPos",
    "num_particles",
    "radius",
    "gt_mesh_path",
    "meta_scene",
    "meta_frame_id",
    "foam",              # FoamRaw dict or None
    "newfoam",
    "camera",             # 由粒子位置生成：origin, target, up, fov（GT/投影共用）
    "sph",                # 0: VTK 含 pscale；1: 无 pscale（见 vtk_loader.load_fluid_vtk）
]


def sample_output_from_fluid_and_foam(
    fluid: Dict[str, Any],
    meta_scene: str,
    meta_frame_id: int,
    gt_mesh_path: Optional[str] = None,
    foam: Optional[Dict[str, Any]] = None,
    newfoam: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """
    从流体 + 泡沫原始数据拼出单样本字典（不含 next_* 字段）。

    约定：src_v3 的 Dataset/Trainer/Infer “对外”优先使用 torch.Tensor（CPU），
    若输入仍为 numpy，会在此处转换为 torch。
    """
    positions_np = fluid["positions"]
    positions = torch.as_tensor(positions_np, dtype=torch.float32) if not isinstance(positions_np, torch.Tensor) else positions_np
    vel = fluid.get("vel")
    if vel is not None and not isinstance(vel, torch.Tensor):
        vel = torch.as_tensor(vel, dtype=torch.float32)
    maxPos = fluid["maxPos"]
    minPos = fluid["minPos"]
    if not isinstance(maxPos, torch.Tensor):
        maxPos = torch.as_tensor(maxPos, dtype=torch.float32)
    if not isinstance(minPos, torch.Tensor):
        minPos = torch.as_tensor(minPos, dtype=torch.float32)
    return {
        "input_particles": positions,
        "positions": positions[:, :3],
        "radii": positions[:, 3:4],
        "vel": vel,
        "maxPos": maxPos,
        "minPos": minPos,
        "num_particles": int(fluid["nums"]),
        "radius": float(fluid["radius"]),
        "gt_mesh_path": gt_mesh_path,
        "meta_scene": meta_scene,
        "meta_frame_id": meta_frame_id,
        "foam": foam,
        "newfoam": newfoam,
        "sph": int(fluid.get("sph", 1)),
    }
