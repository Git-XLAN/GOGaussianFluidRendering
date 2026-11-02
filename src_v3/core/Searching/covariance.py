# -*- coding: utf-8 -*-
"""
各向异性协方差：由边 (src, dst) 与位置/速度计算每粒子 cov_pos(9 通道)、cov_vel(9 通道)。
位置协方差可做归一化（除以 pos_scale）；邻居过少的粒子（飞溅）用单位矩阵以保证数值稳定。

协方差计算方法可通过 method 参数选择（全局或 search 调用处均可指定）：
  COV_METHOD_DEFAULT = 0  当前默认实现：邻域质心 + 相对向量外积，可选 pos_scale 归一化
  COV_METHOD_CUSTOM_1  = 1  TODO: 预留自定义实现 1
  COV_METHOD_CUSTOM_2  = 2  TODO: 预留自定义实现 2
  ... 后续按需扩展，在下方 _covariance_* 与 dispatch 中补充即可
"""

import time
import numpy as np
from typing import Tuple, Optional

# 邻居数低于此阈值视为飞溅粒子，协方差用单位矩阵
SPLASH_NEIGHBOR_THRESHOLD = 2

# 协方差计算方法（整数，用于全局/局部参数）
COV_METHOD_DEFAULT = 0   # 当前默认：质心 + 相对向量外积，可选 pos_scale 归一化
COV_METHOD_CUSTOM_1 = 1  # TODO: 预留自定义协方差实现 1
COV_METHOD_CUSTOM_2 = 2  # TODO: 预留自定义协方差实现 2


def _covariance_default(
    positions: np.ndarray,
    src: np.ndarray,
    dst: np.ndarray,
    N: int,
    E: int,
    neighbor_counts: np.ndarray,
    neighbor_counts_safe: np.ndarray,
    vel: Optional[np.ndarray],
    pos_scale: Optional[float],
    splash_threshold: int,
    eps: float,
) -> Tuple[np.ndarray, np.ndarray]:
    """默认实现：邻域位置/速度质心 + 相对向量外积，位置可选 pos_scale 归一化。返回 (cov_pos [N,9], cov_vel [N,9])。"""
    # 位置质心
    neighbor_sum_pos = np.zeros((N, 3), dtype=np.float64)
    np.add.at(neighbor_sum_pos, src, positions[dst])
    centroids_pos = neighbor_sum_pos / neighbor_counts_safe[:, None]

    # 位置协方差：diff 可选归一化后外积
    diff_pos = positions[dst] - centroids_pos[src]  # [E, 3]
    if pos_scale is not None and pos_scale > 0:
        diff_pos = diff_pos / pos_scale
    outer_pos = np.einsum("ei,ej->eij", diff_pos, diff_pos)  # [E, 3, 3]
    cov_pos_flat = np.zeros((N, 9), dtype=np.float64)
    np.add.at(cov_pos_flat, src, outer_pos.reshape(E, 9))
    cov_pos_3x3 = cov_pos_flat.reshape(N, 3, 3) / neighbor_counts_safe[:, None, None]

    # 速度协方差
    if vel is not None:
        neighbor_sum_vel = np.zeros((N, 3), dtype=np.float64)
        np.add.at(neighbor_sum_vel, src, vel[dst])
        centroids_vel = neighbor_sum_vel / neighbor_counts_safe[:, None]
        diff_vel = vel[dst] - centroids_vel[src]
        outer_vel = np.einsum("ei,ej->eij", diff_vel, diff_vel)
        cov_vel_flat = np.zeros((N, 9), dtype=np.float64)
        np.add.at(cov_vel_flat, src, outer_vel.reshape(E, 9))
        cov_vel_3x3 = cov_vel_flat.reshape(N, 3, 3) / neighbor_counts_safe[:, None, None]
    else:
        cov_vel_3x3 = np.zeros((N, 3, 3), dtype=np.float64)

    # 飞溅 -> 单位矩阵；正则化
    is_splash = neighbor_counts < splash_threshold
    eye3 = np.eye(3, dtype=np.float64)
    cov_pos_3x3[is_splash] = eye3
    cov_pos_3x3 += eps * eye3
    if vel is not None:
        cov_vel_3x3[is_splash] = eye3
        cov_vel_3x3 += eps * eye3

    return cov_pos_3x3.reshape(N, 9), cov_vel_3x3.reshape(N, 9)


def _covariance_custom_1(
    positions: np.ndarray,
    src: np.ndarray,
    dst: np.ndarray,
    N: int,
    E: int,
    neighbor_counts: np.ndarray,
    neighbor_counts_safe: np.ndarray,
    vel: Optional[np.ndarray],
    pos_scale: Optional[float],
    splash_threshold: int,
    eps: float,
) -> Tuple[np.ndarray, np.ndarray]:
    # TODO: 在此实现自定义协方差方法 1；输入输出形状与 _covariance_default 一致
    raise NotImplementedError("COV_METHOD_CUSTOM_1 尚未实现，请在 covariance.py 中实现 _covariance_custom_1")


def _covariance_custom_2(
    positions: np.ndarray,
    src: np.ndarray,
    dst: np.ndarray,
    N: int,
    E: int,
    neighbor_counts: np.ndarray,
    neighbor_counts_safe: np.ndarray,
    vel: Optional[np.ndarray],
    pos_scale: Optional[float],
    splash_threshold: int,
    eps: float,
) -> Tuple[np.ndarray, np.ndarray]:
    # TODO: 在此实现自定义协方差方法 2；输入输出形状与 _covariance_default 一致
    raise NotImplementedError("COV_METHOD_CUSTOM_2 尚未实现，请在 covariance.py 中实现 _covariance_custom_2")


_IMPLEMENTATIONS = {
    COV_METHOD_DEFAULT: _covariance_default,
    COV_METHOD_CUSTOM_1: _covariance_custom_1,
    COV_METHOD_CUSTOM_2: _covariance_custom_2,
}


def covariance_matrices(
    positions: np.ndarray,
    src: np.ndarray,
    dst: np.ndarray,
    vel: Optional[np.ndarray] = None,
    pos_scale: Optional[float] = None,
    splash_threshold: int = SPLASH_NEIGHBOR_THRESHOLD,
    eps: float = 1e-6,
    timing: bool = False,
    method: int = COV_METHOD_DEFAULT,
) -> Tuple[np.ndarray, np.ndarray]:
    """
    根据邻域边 (src, dst) 计算每个粒子的位置协方差 [N, 9] 与速度协方差 [N, 9]。
    具体计算由 method 指定，见模块顶部注释（COV_METHOD_*）。

    Args:
        positions: [N, 3]
        src, dst: 边索引 [E]
        vel: [N, 3]，可选；为 None 时 cov_vel 输出为 0
        pos_scale: 位置归一化尺度（如 radius），为 None 则不归一化（仅对默认方法生效）
        splash_threshold: 邻居数低于此用单位矩阵
        eps: 对角正则化
        timing: 是否打印耗时
        method: 协方差计算方法，0=默认，1/2=预留自定义（见 COV_METHOD_*）

    Returns:
        cov_pos: [N, 9]，float64，行优先展平 3x3
        cov_vel: [N, 9]，float64
    """
    positions = np.asarray(positions, dtype=np.float64)
    src = np.asarray(src, dtype=np.int64)
    dst = np.asarray(dst, dtype=np.int64)
    N = positions.shape[0]
    E = src.size
    t0 = time.perf_counter()

    # 每个点的邻居数（所有 method 共用）
    neighbor_counts = np.zeros(N, dtype=np.float64)
    np.add.at(neighbor_counts, src, 1.0)
    neighbor_counts_safe = np.maximum(neighbor_counts, 1.0)

    if vel is not None:
        vel = np.asarray(vel, dtype=np.float64)
        if vel.shape[0] != N or vel.ndim != 2 or vel.shape[1] != 3:
            vel = None

    impl = _IMPLEMENTATIONS.get(method)
    if impl is None:
        raise ValueError(f"未知的协方差方法 method={method}，可选: {list(_IMPLEMENTATIONS.keys())}")
    cov_pos, cov_vel = impl(
        positions, src, dst, N, E,
        neighbor_counts, neighbor_counts_safe,
        vel, pos_scale, splash_threshold, eps,
    )

    if timing:
        elapsed = time.perf_counter() - t0
        print(f"[Searching] covariance_matrices (method={method}): {elapsed*1000:.2f} ms (N={N})")
    return cov_pos, cov_vel
