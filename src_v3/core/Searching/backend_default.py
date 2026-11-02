# -*- coding: utf-8 -*-
"""
Searching 默认实现：scipy cKDTree 半径图 + 位置/速度协方差 (cov_pos [N,9], cov_vel [N,9])。
并返回 centerDelta [N,3]（默认后端暂无该量时返回全 0，保证接口对齐）。
输入输出与 search() 接口一致，供统一入口回退使用。
"""

import time
from typing import Tuple, Optional

import numpy as np

from .radius_search import radius_graph
from .covariance import covariance_matrices, SPLASH_NEIGHBOR_THRESHOLD, COV_METHOD_DEFAULT


def search(
    positions: np.ndarray,
    radius: float,
    *,
    vel: Optional[np.ndarray] = None,
    pos_scale: Optional[float] = None,
    exclude_self: bool = True,
    splash_threshold: int = SPLASH_NEIGHBOR_THRESHOLD,
    workers: int = -1,
    timing: bool = False,
    cov_method: int = COV_METHOD_DEFAULT,
) -> Tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
    """
    默认实现：输入输出与 Searching.search 接口一致。
    返回 (src, dst, cov_pos [N,9], cov_vel [N,9], centerDelta [N,3])。
    cov_method 见 covariance 模块注释。
    """
    t_total = time.perf_counter()
    src, dst = radius_graph(
        positions,
        radius,
        exclude_self=exclude_self,
        workers=workers,
        timing=timing,
    )
    cov_pos, cov_vel = covariance_matrices(
        positions,
        src,
        dst,
        vel=vel,
        pos_scale=pos_scale,
        splash_threshold=splash_threshold,
        timing=timing,
        method=cov_method,
    )
    if timing:
        elapsed = time.perf_counter() - t_total
        print(f"[Searching] search 总耗时: {elapsed*1000:.2f} ms")
    center_delta = np.zeros((positions.shape[0], 3), dtype=np.float32)
    return src, dst, cov_pos, cov_vel, center_delta
