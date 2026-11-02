# -*- coding: utf-8 -*-
"""
src_v3.core.render — 高斯投影（normal/depth/hit）与 Falcor 实时合成
"""

from src_v3.core.render.camera_utils import camera_params_to_matrices
from src_v3.core.render.gaussian_projector import (
    GaussianProjector,
    get_shortest_axis_normals,
)

__all__ = [
    "camera_params_to_matrices",
    "GaussianProjector",
    "get_shortest_axis_normals",
]
