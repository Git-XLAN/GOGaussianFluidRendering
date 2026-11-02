# -*- coding: utf-8 -*-
"""
顶层模型：由协方差特征 (cov_pos, cov_vel, center_delta) 解码为高斯 + 泡沫概率。
"""

import torch
import torch.nn as nn
from typing import Tuple

from .config import NetConfig, DECODER_VARIANT_DIRECT
from .decoder import CovDecoder, CovDecoderDirect


# 当前默认：cov_pos [N,9] + cov_vel [N,9] + center_delta [N,3] = 21 维
DEFAULT_COV_DIM = 21


class CovDecoderModel(nn.Module):
    """
    协方差解码模型：输入 cov_pos [N,9]、cov_vel [N,9]、center_delta [N,3]，
    输出高斯参数与泡沫概率。
    无 SH、无 opacity；泡沫保留 foam_prob 与 foam_prob_raw。
    decoder_variant: "split" 时 scale/rotation 在 Split 中计算；"direct" 时由 MLP 直接输出。
    """

    def __init__(self, net_config: NetConfig, cov_dim: int = DEFAULT_COV_DIM):
        super().__init__()
        self.cov_dim = cov_dim
        if getattr(net_config, "decoder_variant", "split") == DECODER_VARIANT_DIRECT:
            self.decoder = CovDecoderDirect(net_config, input_dim=cov_dim)
        else:
            self.decoder = CovDecoder(net_config, input_dim=cov_dim)

    def forward(
        self,
        cov_pos: torch.Tensor,
        cov_vel: torch.Tensor,
        center_delta: torch.Tensor,
        pos: torch.Tensor,
        radius: float,
        kernel_size: float,
    ) -> Tuple[torch.Tensor, torch.Tensor, torch.Tensor, torch.Tensor, torch.Tensor, torch.Tensor]:
        """
        cov_pos: [N, 9], cov_vel: [N, 9], center_delta: [N, 3]
        pos: [N, 3]
        Returns: gs_pos [N*k,3], gs_scale [N*k,3], gs_rotation [N*k,4], gs_normal [N*k,3], foam_prob [N*k,1], foam_prob_raw [N*k,1]
        """
        cov = torch.cat([cov_pos, cov_vel, center_delta], dim=-1)
        return self.decoder(cov, pos, radius, kernel_size)
