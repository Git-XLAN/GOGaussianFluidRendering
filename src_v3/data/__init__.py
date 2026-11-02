# -*- coding: utf-8 -*-
"""
src_v3.data — 数据加载与 DataSet 管理

- vtk_loader: load_fluid_vtk, load_foam_vtk（与 v2 读取逻辑一致）
- layout: 目录约定、FrameIndex、FramePaths、build_frame_index
- schema: FluidRaw, FoamRaw, sample_output_from_fluid_and_foam
- dataset: FluidDataset, SceneDataset
"""

from .vtk_loader import (
    load_fluid_vtk,
    load_foam_vtk,
    get_particle_count,
    VTKLoadError,
)
from .layout import (
    FrameIndex,
    FramePaths,
    build_frame_index,
    extract_frame_id,
)
from .schema import (
    FluidRaw,
    FoamRaw,
    sample_output_from_fluid_and_foam,
    SAMPLE_OUTPUT_KEYS,
)
from .camera_from_particles import camera_from_particles
from .dataset import FluidDataset, SceneDataset

__all__ = [
    "load_fluid_vtk",
    "load_foam_vtk",
    "get_particle_count",
    "VTKLoadError",
    "FrameIndex",
    "FramePaths",
    "build_frame_index",
    "extract_frame_id",
    "FluidRaw",
    "FoamRaw",
    "sample_output_from_fluid_and_foam",
    "SAMPLE_OUTPUT_KEYS",
    "camera_from_particles",
    "FluidDataset",
    "SceneDataset",
]
