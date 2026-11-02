# -*- coding: utf-8 -*-
"""
表面粒子检测（与 src_v2/graph/anisotropic.py 一致）

基于 **位置协方差矩阵特征值扁平度** + **飞溅粒子（邻居数过少）** 判定表面，
不再单独用「邻居数上限」区分内外。
"""

from __future__ import annotations

import torch


def compute_neighbor_counts(src: torch.Tensor, num_nodes: int, device: torch.device) -> torch.Tensor:
    """每个节点的邻居数量 [N]（与 v2 一致：对 src 聚合）。"""
    ones = torch.ones(src.size(0), device=device, dtype=torch.float32)
    neighbor_counts = torch.zeros(num_nodes, device=device, dtype=torch.float32)
    if src.numel() > 0:
        neighbor_counts.index_add_(0, src.long(), ones)
    return neighbor_counts


def compute_covariance_matrices(
    pos: torch.Tensor,
    src: torch.Tensor,
    dst: torch.Tensor,
    neighbor_counts: torch.Tensor,
    is_splash: torch.Tensor,
) -> torch.Tensor:
    """
    由邻域图计算每个粒子的 **位置** 协方差 [N,3,3]（与 v2 一致）。
    飞溅粒子用单位阵替代以保证稳定。
    """
    N = pos.size(0)
    E = src.size(0)
    device = pos.device
    dtype_f = torch.float32

    neighbor_counts_safe = neighbor_counts.clone()
    neighbor_counts_safe[neighbor_counts_safe == 0] = 1.0

    neighbor_sum = torch.zeros(N, 3, device=device, dtype=dtype_f)
    if E > 0:
        neighbor_sum.index_add_(0, src.long(), pos[dst.long()].float())

    centroids = neighbor_sum / neighbor_counts_safe.unsqueeze(1)

    cov_matrices_flat = torch.zeros(N, 9, device=device, dtype=dtype_f)
    if E > 0:
        diff_vec = pos[dst.long()].float() - centroids[src.long()]
        outer_products = torch.bmm(diff_vec.unsqueeze(2), diff_vec.unsqueeze(1))
        cov_matrices_flat.index_add_(0, src.long(), outer_products.view(E, 9))

    cov_matrices = cov_matrices_flat.view(N, 3, 3) / neighbor_counts_safe.view(N, 1, 1)

    identity = torch.eye(3, device=device, dtype=dtype_f).unsqueeze(0).repeat(N, 1, 1)
    mask_splash_exp = is_splash.view(N, 1, 1).expand(-1, 3, 3)
    cov_matrices = torch.where(mask_splash_exp, identity, cov_matrices)
    cov_matrices = cov_matrices + 1e-6 * torch.eye(3, device=device, dtype=dtype_f).unsqueeze(0)
    return cov_matrices


def detect_surface_particles(
    cov_matrices: torch.Tensor,
    is_splash: torch.Tensor,
    surface_threshold: float = 0.6,
) -> torch.Tensor:
    """
    协方差特征值扁平度 + 飞溅 → 表面掩码 [N] bool。

    flatness_ratio = λ_min / λ_max，小于 surface_threshold 视为几何表面；
    is_splash 的粒子始终视为表面（与 v2 一致）。
    """
    L, _ = torch.linalg.eigh(cov_matrices)
    L = torch.abs(L)
    flatness_ratio = L[:, 0] / torch.clamp(L[:, 2], min=1e-6)
    is_geometric_surface = flatness_ratio < surface_threshold
    surface_mask = is_geometric_surface | is_splash
    return surface_mask


def compute_surface_particle_mask(
    pos: torch.Tensor,
    src: torch.Tensor,
    dst: torch.Tensor,
    *,
    flatness_threshold: float,
    splash_neighbor_threshold: int,
) -> torch.Tensor:
    """
    由搜索得到的 (src, dst) 与位置计算表面粒子掩码。

    Args:
        pos: [N, 3]
        src, dst: 边索引，与 Searching.search 一致
        flatness_threshold: 扁平度阈值（越小越「平」的表面），同 v2 surface_threshold
        splash_neighbor_threshold: 邻居数 **严格小于** 此值视为飞溅（表面），同 v2 splash_threshold

    Returns:
        surface_mask: [N] bool，True 表示保留的表面粒子
    """
    if pos.ndim != 2 or pos.shape[1] < 3:
        raise ValueError("pos 需为 [N,3]")
    N = int(pos.shape[0])
    device = pos.device
    src_i = src.to(device=device, dtype=torch.long).view(-1)
    dst_i = dst.to(device=device, dtype=torch.long).view(-1)

    neighbor_counts = compute_neighbor_counts(src_i, N, device)
    is_splash = neighbor_counts < float(splash_neighbor_threshold)

    cov_matrices = compute_covariance_matrices(
        pos, src_i, dst_i, neighbor_counts, is_splash
    )
    return detect_surface_particles(
        cov_matrices, is_splash.bool(), float(flatness_threshold)
    )
