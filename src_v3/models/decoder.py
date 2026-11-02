# -*- coding: utf-8 -*-
"""
解码器：由特征预测高斯参数（仅 normal，无 SH、无 opacity，泡沫输出 foam_prob 与 foam_prob_raw）。

输出 per 粒子: offset(3k) + scale_raw(3k) + theta(1k) + normal(3k) + foam_prob(1k) = 11k。
"""

import torch
import torch.nn as nn
import torch.nn.functional as F
from typing import List, Tuple, Optional

from .config import NetConfig


def _build_mlp(
    layer_dims: List[int],
    activation: str = "LeakyReLU",
    alpha: float = 0.01,
    dropout: float = 0.0,
    use_layer_norm: bool = True,
) -> nn.Sequential:
    """构建 MLP：layer_dims = [input, h1, h2, ..., output]，最后一层无激活。"""
    if activation in ("LeakyReLU", "LeakReLU"):
        act = lambda: nn.LeakyReLU(alpha)
    elif activation == "ReLU":
        act = lambda: nn.ReLU()
    else:
        act = lambda: nn.LeakyReLU(alpha)
    layers = []
    for i in range(len(layer_dims) - 1):
        layers.append(nn.Linear(layer_dims[i], layer_dims[i + 1], bias=True))
        if i < len(layer_dims) - 2:
            if use_layer_norm:
                layers.append(nn.LayerNorm(layer_dims[i + 1]))
            if dropout > 0:
                layers.append(nn.Dropout(p=dropout))
            layers.append(act())
    return nn.Sequential(*layers)


class GaussianNormalFoamSplit(nn.Module):
    """
    将解码器原始输出拆分为高斯参数 + 泡沫概率。
    无 opacity、无 SH；法线约束的 scale/rotation，泡沫仅 foam_prob。
    布局: offset 3k, scale_raw 3k, theta 1k, normal 3k, foam_prob 1k = 11k。
    """

    def __init__(self, gs_num: int):
        super().__init__()
        self.k = gs_num
        self.tanh = nn.Tanh()
        self.sigmoid = nn.Sigmoid()
        self.thickness_factor = 0.1

    def forward(
        self,
        gs: torch.Tensor,
        pos: torch.Tensor,
        radius: float,
        kernel_size: float,
    ) -> Tuple[torch.Tensor, torch.Tensor, torch.Tensor, torch.Tensor, torch.Tensor, torch.Tensor]:
        """
        gs: [N, 11*k]
        pos: [N, 3]
        Returns: gs_pos [N*k,3], gs_scale [N*k,3], gs_rotation [N*k,4], gs_normal [N*k,3], foam_prob [N*k,1], foam_prob_raw [N*k,1]
        """
        k = self.k
        N = pos.shape[0]
        device = gs.device

        # 1) position offsets / centers
        gs_offsets = gs[:, 0 : 3 * k].reshape(-1, 3)
        gs_offsets = self.tanh(gs_offsets) * radius * kernel_size
        gs_pos = pos.unsqueeze(1).repeat(1, k, 1).reshape(-1, 3) + gs_offsets

        # 2) scale + theta
        gs_s_raw = gs[:, 3 * k : 6 * k].reshape(-1, 3)
        gs_theta = gs[:, 6 * k : 7 * k].reshape(-1, 1)
        gs_theta = self.tanh(gs_theta) * torch.pi

        base_scale = radius
        scale_uv = self.sigmoid(gs_s_raw[:, :2]) * base_scale
        min_uv, _ = torch.min(scale_uv, dim=1, keepdim=True)
        raw_z_ctrl = gs_s_raw[:, 2:3]
        scale_z = min_uv * self.sigmoid(raw_z_ctrl) * self.thickness_factor + 1e-6
        gs_scale = torch.cat([scale_uv, scale_z], dim=-1)

        # 3) normal + rotation
        gs_normal = self.tanh(gs[:, 7 * k : 10 * k]).reshape(-1, 3)
        target_n = F.normalize(gs_normal, dim=-1)
        z_axis = torch.tensor([0.0, 0.0, 1.0], device=device, dtype=gs.dtype).unsqueeze(0).expand(N * k, 3)
        dot = torch.sum(z_axis * target_n, dim=1, keepdim=True)
        cross = torch.cross(z_axis, target_n, dim=1)
        q_align = torch.cat([1.0 + dot, cross], dim=-1)
        q_align = F.normalize(q_align, dim=-1)

        mask_singular = (dot.squeeze(-1) < -0.99)
        if mask_singular.any():
            fallback = torch.tensor([0.0, 1.0, 0.0, 0.0], device=device, dtype=gs.dtype).unsqueeze(0)
            fallback = fallback.expand(mask_singular.sum().item(), 4)
            q_align[mask_singular] = fallback

        half_theta = gs_theta * 0.5
        cos_h = torch.cos(half_theta)
        sin_h = torch.sin(half_theta)
        zeros = torch.zeros_like(half_theta)
        q_plane = torch.cat([cos_h, zeros, zeros, sin_h], dim=-1)

        w1, x1, y1, z1 = q_align.unbind(-1)
        w2, x2, y2, z2 = q_plane.unbind(-1)
        w = w1 * w2 - x1 * x2 - y1 * y2 - z1 * z2
        x = w1 * x2 + x1 * w2 + y1 * z2 - z1 * y2
        y = w1 * y2 - x1 * z2 + y1 * w2 + z1 * x2
        z = w1 * z2 + x1 * y2 - y1 * x2 + z1 * w2
        gs_rotation = torch.stack((w, x, y, z), dim=-1)

        # 4) foam prob
        foam_prob_raw = gs[:, 10 * k : 11 * k].reshape(-1, 1)
        foam_prob = self.sigmoid(foam_prob_raw)

        return gs_pos, gs_scale, gs_rotation, target_n, foam_prob, foam_prob_raw


class GaussianNormalFoamSplitDirect(nn.Module):
    """
    Scale 三参数与 rotation 四参数由 MLP 直接给出，Split 阶段只做合法性处理（正尺度、单位四元数）。
    布局: offset 3k, scale 3k, rotation 4k, normal 3k, foam_prob 1k = 14k。
    """

    def __init__(self, gs_num: int):
        super().__init__()
        self.k = gs_num
        self.tanh = nn.Tanh()
        self.sigmoid = nn.Sigmoid()
        self.thickness_factor = 0.1

    def forward(
        self,
        gs: torch.Tensor,
        pos: torch.Tensor,
        radius: float,
        kernel_size: float,
    ) -> Tuple[torch.Tensor, torch.Tensor, torch.Tensor, torch.Tensor, torch.Tensor, torch.Tensor]:
        """
        gs: [N, 14*k]
        Returns: gs_pos [N*k,3], gs_scale [N*k,3], gs_rotation [N*k,4], gs_normal [N*k,3], foam_prob [N*k,1], foam_prob_raw [N*k,1]
        """
        k = self.k
        base_scale = radius

        # 1) position offsets
        gs_offsets = gs[:, 0 : 3 * k].reshape(-1, 3)
        gs_offsets = self.tanh(gs_offsets) * radius * kernel_size
        gs_pos = pos.unsqueeze(1).repeat(1, k, 1).reshape(-1, 3) + gs_offsets

        # 2) scale：直接使用 MLP 的 3 维，仅做正数约束
        gs_scale_raw = gs[:, 3 * k : 6 * k].reshape(-1, 3)
        gs_scale = F.softplus(gs_scale_raw) * base_scale + 1e-6

        # 3) rotation：直接使用 MLP 的 4 维，仅做单位四元数归一化
        gs_rotation_raw = gs[:, 6 * k : 10 * k].reshape(-1, 4)
        gs_rotation = F.normalize(gs_rotation_raw, dim=-1)

        # 4) normal + foam
        gs_normal = self.tanh(gs[:, 10 * k : 13 * k]).reshape(-1, 3)
        target_n = F.normalize(gs_normal, dim=-1)
        foam_prob_raw = gs[:, 13 * k : 14 * k].reshape(-1, 1)
        foam_prob = self.sigmoid(foam_prob_raw)

        return gs_pos, gs_scale, gs_rotation, target_n, foam_prob, foam_prob_raw


class CovDecoder(nn.Module):
    """
    从协方差特征解码为高斯参数 + 泡沫概率。
    输入: cov [N, cov_dim]（如 cov_pos+cov_vel 拼接为 18 维）。
    输出: gs_pos, gs_scale, gs_rotation, gs_normal, foam_prob, foam_prob_raw。
    无 SH、无 opacity；泡沫同时保留 sigmoid 后概率与 raw logit。
    """

    def __init__(self, net_config: NetConfig, input_dim: int):
        super().__init__()
        self.k = net_config.gs_num
        layer_dims = net_config.get_decoder_layer_dims(input_dim)
        self.mlp = _build_mlp(
            layer_dims,
            activation=net_config.activation,
            alpha=net_config.alpha,
            dropout=net_config.dropout,
            use_layer_norm=net_config.use_layer_norm,
        )
        self.split = GaussianNormalFoamSplit(net_config.gs_num)

    def forward(
        self,
        cov: torch.Tensor,
        pos: torch.Tensor,
        radius: float,
        kernel_size: float,
    ) -> Tuple[torch.Tensor, torch.Tensor, torch.Tensor, torch.Tensor, torch.Tensor, torch.Tensor]:
        """
        cov: [N, cov_dim]
        pos: [N, 3]
        Returns: gs_pos, gs_scale, gs_rotation, gs_normal, foam_prob, foam_prob_raw
        """
        gs_raw = self.mlp(cov)
        return self.split(gs_raw, pos, radius, kernel_size)


class CovDecoderDirect(nn.Module):
    """
    Scale 三参数与 rotation 四参数由 MLP 直接输出，Split 仅做合法性处理。
    MLP 输出维度 14*gs_num（offset 3 + scale 3 + rotation 4 + normal 3 + foam 1）。
    """

    def __init__(self, net_config: NetConfig, input_dim: int):
        super().__init__()
        self.k = net_config.gs_num
        layer_dims = net_config.get_decoder_layer_dims(input_dim)
        self.mlp = _build_mlp(
            layer_dims,
            activation=net_config.activation,
            alpha=net_config.alpha,
            dropout=net_config.dropout,
            use_layer_norm=net_config.use_layer_norm,
        )
        self.split = GaussianNormalFoamSplitDirect(net_config.gs_num)

    def forward(
        self,
        cov: torch.Tensor,
        pos: torch.Tensor,
        radius: float,
        kernel_size: float,
    ) -> Tuple[torch.Tensor, torch.Tensor, torch.Tensor, torch.Tensor, torch.Tensor, torch.Tensor]:
        """与 CovDecoder 相同的接口与返回值。"""
        gs_raw = self.mlp(cov)
        return self.split(gs_raw, pos, radius, kernel_size)
