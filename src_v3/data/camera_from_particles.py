# -*- coding: utf-8 -*-
"""
根据粒子位置生成相机参数（origin/target/up/fov），供 GT 渲染与高斯投影共用。
bbox 模式：以包围盒中心为球心、对角线长度×系数的球面上采样相机位置，相机看向中心。
"""

from __future__ import annotations

from typing import Any, Dict, Optional, Union

import numpy as np


def camera_from_particles(
    positions: np.ndarray,
    mode: str = "bbox",
    *,
    fov: float = 60,
    up: Optional[Union[list, tuple, np.ndarray]] = None,
    random: bool = True,
    rng: Optional[np.random.Generator] = None,
    fix_sphere_scale_to_min: bool = False,
    **kwargs: Any,
) -> Dict[str, Any]:
    """
    由粒子位置得到相机描述 dict（origin, target, up, fov），与 GTGenerator / GaussianProjector 一致。

    Args:
        positions: [N, 3] 或 [N, 4]（第 4 列忽略），世界坐标。
        mode: 生成策略："bbox" = 在包围盒外接球面上采样相机，看向包围盒中心。
        fov: 垂直方向 fov（度）；random 时可为范围中心。
        up: 相机 up 向量 [x,y,z]，None 则 (0,1,0)。
        random: 是否随机化轴、距离比例；默认 True。fov 不参与随机，始终用固定值。
        rng: 随机数生成器，None 则每次用 default_rng()（非固定种子）。
        fix_sphere_scale_to_min: bbox 模式下为 True 时，球面直径系数固定为
            [sphere_diameter_scale, sphere_diameter_scale_max] 区间的**下限**（削弱距离随机）；
            球面方向仍可在 random=True 时随机。
            训练路径请保持 False；Compare 由 FluidDataset 显式传入 sphere_* 与 True。
        **kwargs: 传给 _camera_bbox（与历史一致：未显式 sphere_* 时默认 1.2～3.5，distance_scale 等为兼容占位）。

    Returns:
        {"origin": [x,y,z], "target": [x,y,z], "up": [x,y,z], "fov": float}
    """
    positions = np.asarray(positions, dtype=np.float64)
    if positions.ndim != 2 or positions.shape[1] < 3:
        raise ValueError("positions 需为 [N, 3] 或 [N, 4]")
    xyz = positions[:, :3]
    up_vec = _to_list3(up) if up is not None else [0.0, 1.0, 0.0]
    if rng is None and random:
        rng = np.random.default_rng()

    if mode == "bbox":
        out = _camera_bbox(
            xyz,
            fov=fov,
            up=up_vec,
            random=random,
            rng=rng,
            fix_sphere_scale_to_min=fix_sphere_scale_to_min,
            **kwargs,
        )
    else:
        raise ValueError(f"未知 camera mode: {mode}，当前支持: bbox")

    return {
        "origin": list(out["origin"]),
        "target": list(out["target"]),
        "up": list(out["up"]),
        "fov": float(out["fov"]),
    }


def _to_list3(x: Any) -> list:
    if isinstance(x, (list, tuple)):
        return list(x)[:3]
    if isinstance(x, np.ndarray):
        return x.flatten()[:3].tolist()
    return [float(x)] * 3


def _camera_bbox(
    xyz: np.ndarray,
    *,
    fov: float = 60,
    up: Optional[list] = None,
    sphere_diameter_scale: float = 1.2,
    sphere_diameter_scale_max: float = 3.5,
    random: bool = True,
    rng: Optional[np.random.Generator] = None,
    fix_sphere_scale_to_min: bool = False,
    # 以下保留兼容，不再使用
    distance_scale: float = 1.5,
    distance_scale_max: Optional[float] = None,
    axis: str = "z",
    fov_max: Optional[float] = None,
) -> Dict[str, Any]:
    """
    以包围盒中心为球心、包围盒对角线长度 * sphere_diameter_scale 为直径的球面上取相机位置，相机看向中心。
    random=True 时：
      - 球面方向均匀随机；
      - 球直径系数在 [sphere_diameter_scale, sphere_diameter_scale_max] 间随机；
        fix_sphere_scale_to_min=True 时系数固定为区间**下限**（相机到中心距离取随机范围中的最小）。
    random=False 时使用固定方向 (0,0,1) 与固定 sphere_diameter_scale。
    """
    if xyz.size == 0:
        center = np.zeros(3, dtype=np.float64)
        diagonal = 1.0
    else:
        mn = xyz.min(axis=0)
        mx = xyz.max(axis=0)
        center = (mn + mx) * 0.5
        extent = mx - mn
        diagonal = float(np.sqrt(np.sum(extent * extent)))
        if diagonal <= 0.0:
            diagonal = 1.0

    if random and rng is not None:
        scale_min = float(sphere_diameter_scale)
        scale_max = float(sphere_diameter_scale_max)
        if scale_max < scale_min:
            scale_min, scale_max = scale_max, scale_min
        if fix_sphere_scale_to_min:
            scale = scale_min
        else:
            scale = float(rng.uniform(scale_min, scale_max))
    else:
        scale = float(sphere_diameter_scale)

    radius = 0.5 * diagonal * scale  # 直径 = diagonal * scale，半径 = 直径/2

    if random and rng is not None:
        # 球面均匀采样单位方向：高斯归一化法
        d = rng.standard_normal(3)
        d = d.astype(np.float64)
        n = np.sqrt(np.sum(d * d))
        if n <= 1e-10:
            d = np.array([0.0, 0.0, 1.0])
        else:
            d = d / n
    else:
        d = np.array([0.0, 0.0, 1.0], dtype=np.float64)

    origin = center + radius * d

    up_vec = up or [0.0, 1.0, 0.0]
    up_vec = np.asarray(up_vec, dtype=np.float64).ravel()[:3]
    if np.allclose(up_vec, 0.0):
        up_vec = np.array([0.0, 1.0, 0.0])

    return {
        "origin": origin.tolist(),
        "target": center.tolist(),
        "up": up_vec.tolist(),
        "fov": fov,
    }
