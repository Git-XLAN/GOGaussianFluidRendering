# -*- coding: utf-8 -*-
"""
半径邻域搜索：基于 scipy.spatial.cKDTree，输入位置与半径，输出边 (src, dst)。
"""

import time
import numpy as np
from typing import Tuple, Union

try:
    from scipy.spatial import cKDTree
    HAS_SCIPY = True
except ImportError:
    cKDTree = None
    HAS_SCIPY = False


def radius_graph(
    positions: np.ndarray,
    radius: float,
    *,
    exclude_self: bool = True,
    workers: int = -1,
    timing: bool = False,
) -> Tuple[np.ndarray, np.ndarray]:
    """
    在给定半径内查找所有点对，返回边的 (src, dst)。

    使用 scipy.spatial.cKDTree.query_ball_point 做半径搜索。
    约定：边 (src[i], dst[i]) 表示 src[i] 与 dst[i] 在半径内相邻；
    src 为“中心”粒子索引，dst 为邻居索引。

    Args:
        positions: 粒子位置 [N, 3]，float
        radius: 搜索半径（与 positions 同一尺度）
        exclude_self: 是否排除自身（距离 0），默认 True
        workers: 并行数，-1 表示用全部 CPU
        timing: 是否打印耗时（测速模式）

    Returns:
        src: 边源索引 [E]，dtype int64
        dst: 边目标索引 [E]，dtype int64
    """
    if not HAS_SCIPY:
        raise ImportError("需要 scipy，请安装: pip install scipy")
    positions = np.asarray(positions, dtype=np.float64)
    if positions.ndim != 2 or positions.shape[1] != 3:
        raise ValueError("positions 应为 [N, 3]")
    if radius <= 0:
        raise ValueError("radius 必须为正数")
    N = positions.shape[0]
    t0 = time.perf_counter()
    tree = cKDTree(positions)
    neighbors_list = tree.query_ball_point(positions, radius, workers=workers)
    src_list = []
    dst_list = []
    for i in range(N):
        for j in neighbors_list[i]:
            if exclude_self and j == i:
                continue
            src_list.append(i)
            dst_list.append(j)
    src = np.array(src_list, dtype=np.int64)
    dst = np.array(dst_list, dtype=np.int64)
    if timing:
        elapsed = time.perf_counter() - t0
        print(f"[Searching] radius_graph: {elapsed*1000:.2f} ms (N={N}, edges={len(src)})")
    return src, dst
