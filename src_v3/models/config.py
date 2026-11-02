# -*- coding: utf-8 -*-
"""
网络配置：通过 NetConfig 动态控制解码器每一层的维度。

与 v2 GdLayer 对应：decoder_layers 为隐藏层维度列表，首维由输入特征维自动填充，
最后一维由 11*gs_num（split）或 14*gs_num（direct）自动填充。
"""

from dataclasses import dataclass, field
from typing import List


# "split" = scale/rotation 在 Split 中由 normal+theta 等计算；"direct" = scale 3 维、rotation 4 维由 MLP 直接输出
DECODER_VARIANT_SPLIT = "split"
DECODER_VARIANT_DIRECT = "direct"


@dataclass
class NetConfig:
    """
    解码网络配置，可动态控制每一层维度。

    - decoder_layers: 解码 MLP 的隐藏层维度列表，如 [256, 512, 512]。
      实际构建时为 [input_dim] + decoder_layers + [output_dim]。
    - decoder_variant: "split" 时 output_dim = 11*gs_num（offset 3 + scale_raw 3 + theta 1 + normal 3 + foam 1）；
      "direct" 时 output_dim = 14*gs_num（offset 3 + scale 3 + rotation 4 + normal 3 + foam 1），scale/rotation 由 MLP 直接输出。
    - gs_num: 每粒子高斯个数（与 v2 GdLayer.maxGSNum 一致）。
    """
    decoder_layers: List[int] = field(default_factory=lambda: [])
    gs_num: int = 36
    decoder_variant: str = DECODER_VARIANT_SPLIT  # "split" | "direct"
    activation: str = "LeakyReLU"
    alpha: float = 0.01
    dropout: float = 0.0
    use_layer_norm: bool = True

    def get_decoder_output_dim(self) -> int:
        """Split: 11*gs_num；Direct: 14*gs_num。"""
        if getattr(self, "decoder_variant", DECODER_VARIANT_SPLIT) == DECODER_VARIANT_DIRECT:
            return 14 * self.gs_num
        return 11 * self.gs_num

    def get_decoder_layer_dims(self, input_dim: int) -> List[int]:
        """返回完整解码器层维度：[input_dim] + decoder_layers + [output_dim]。"""
        output_dim = self.get_decoder_output_dim()
        return [input_dim] + list(self.decoder_layers) + [output_dim]
