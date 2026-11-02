# -*- coding: utf-8 -*-
"""
推理配置与 InferRunner（本发行包不含训练器）。
"""

from .config import InferConfig
from .infer import InferRunner

__all__ = ["InferConfig", "InferRunner"]
