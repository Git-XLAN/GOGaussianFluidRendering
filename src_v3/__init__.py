# -*- coding: utf-8 -*-
"""
src_v3 — 流体高斯实时渲染 / 推理（不含训练）。

当前实现:
- data: VTK 加载、目录布局约定、DataSet 管理（索引 + 懒加载 + 可选缓存）
- demo: RealTimeWater / Simulation
- models: 协方差解码网络
"""

from src_v3.data import (
    load_fluid_vtk,
    load_foam_vtk,
    FluidDataset,
    SceneDataset,
    FrameIndex,
    FramePaths,
    build_frame_index,
)

__all__ = [
    "load_fluid_vtk",
    "load_foam_vtk",
    "FluidDataset",
    "SceneDataset",
    "FrameIndex",
    "FramePaths",
    "build_frame_index",
]
