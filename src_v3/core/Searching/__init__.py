# -*- coding: utf-8 -*-
"""
邻域搜索（对外 torch 接口）：半径图 (src, dst) + 位置协方差 cov_pos [N, 9]、速度协方差 cov_vel [N, 9]。

统一入口：
    search(positions: torch.Tensor[N,3], radius: float, vel: Optional[torch.Tensor[N,3]], ...)
返回：
    src: torch.LongTensor[E]
    dst: torch.LongTensor[E]
    cov_pos: torch.FloatTensor[N,9]
    cov_vel: torch.FloatTensor[N,9]
    center_delta: torch.FloatTensor[N,3]

内部实现仍可使用 numpy/scipy/cunnsearch，在此函数内部做 torch↔numpy 的转换。
"""

from typing import Tuple, Optional

import numpy as np
import torch

from .radius_search import radius_graph
from .covariance import (
    covariance_matrices,
    SPLASH_NEIGHBOR_THRESHOLD,
    COV_METHOD_DEFAULT,
)
from . import backend_default


def search(
    positions: torch.Tensor,
    radius: float,
    *,
    vel: Optional[torch.Tensor] = None,
    minRadius: Optional[float] = None,
    pos_scale: Optional[float] = None,
    exclude_self: bool = True,
    splash_threshold: int = SPLASH_NEIGHBOR_THRESHOLD,
    workers: int = -1,
    timing: bool = False,
    use_optimized: bool = False,
    cov_method: int = COV_METHOD_DEFAULT,
) -> Tuple[torch.Tensor, torch.Tensor, torch.Tensor, torch.Tensor, torch.Tensor]:
    """
    输入位置（torch）、搜索半径与可选速度（torch），输出边 (src, dst) 与
    每粒子 cov_pos [N,9]、cov_vel [N,9]、center_delta [N,3]。

    注意：本函数的 **对外接口完全使用 torch.Tensor**。
    内部会在需要时将数据 `.cpu().numpy()` 传给 numpy/scipy/cunnsearch，再将结果转回 torch。
    """
    if not isinstance(positions, torch.Tensor):
        raise TypeError("Searching.search 现在要求 positions 为 torch.Tensor[N,3]")
    if vel is not None and not isinstance(vel, torch.Tensor):
        raise TypeError("Searching.search 现在要求 vel 为 torch.Tensor[N,3] 或 None")

    if use_optimized:
        try:
            from . import backend_optimized
            return backend_optimized.search(
                positions,
                radius,
                vel=vel,
                minRadius=minRadius,
                pos_scale=pos_scale,
                exclude_self=exclude_self,
                splash_threshold=splash_threshold,
                workers=workers,
                timing=timing,
                cov_method=cov_method,
            )
        except (ImportError, AttributeError, NotImplementedError, Exception):
            if timing:
                print("[Searching] 优化后端不可用，回退默认实现")
            pass
    # 默认后端仍基于 numpy/scipy：在此转换为 numpy，再将结果转回 torch
    pos_np = positions.detach().cpu().numpy()
    vel_np = vel.detach().cpu().numpy() if vel is not None else None
    src, dst, cov_pos, cov_vel, center_delta = backend_default.search(
        pos_np,
        radius,
        vel=vel_np,
        pos_scale=pos_scale,
        exclude_self=exclude_self,
        splash_threshold=splash_threshold,
        workers=workers,
        timing=timing,
        cov_method=cov_method,
    )
    return (
        torch.as_tensor(src, dtype=torch.int64),
        torch.as_tensor(dst, dtype=torch.int64),
        torch.as_tensor(cov_pos, dtype=torch.float32),
        torch.as_tensor(cov_vel, dtype=torch.float32),
        torch.as_tensor(center_delta, dtype=torch.float32),
    )


__all__ = [
    "radius_graph",
    "covariance_matrices",
    "search",
    "SPLASH_NEIGHBOR_THRESHOLD",
    "COV_METHOD_DEFAULT",
]
