# -*- coding: utf-8 -*-
"""
src_v3 网络模型：由 NetConfig 动态控制解码器每层维度，仅 normal、无 SH/opacity，泡沫仅 foam_prob。
"""

from .config import NetConfig, DECODER_VARIANT_SPLIT, DECODER_VARIANT_DIRECT
from .decoder import CovDecoder, CovDecoderDirect, GaussianNormalFoamSplit, GaussianNormalFoamSplitDirect
from .model import CovDecoderModel, DEFAULT_COV_DIM

__all__ = [
    "NetConfig",
    "DECODER_VARIANT_SPLIT",
    "DECODER_VARIANT_DIRECT",
    "CovDecoder",
    "CovDecoderDirect",
    "GaussianNormalFoamSplit",
    "GaussianNormalFoamSplitDirect",
    "CovDecoderModel",
    "DEFAULT_COV_DIM",
]
