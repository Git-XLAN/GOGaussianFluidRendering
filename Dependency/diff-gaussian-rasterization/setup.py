#
# Copyright (C) 2023, Inria
# GRAPHDECO research group, https://team.inria.fr/graphdeco
# All rights reserved.
#
# This software is free for non-commercial, research and evaluation use 
# under the terms of the LICENSE.md file.
#
# For inquiries contact  george.drettakis@inria.fr
#

from setuptools import setup
from torch.utils.cpp_extension import CUDAExtension, BuildExtension
import os
os.path.dirname(os.path.abspath(__file__))

# 调试模式：设置为 True 启用 CUDA 调试（会显著降低性能）
DEBUG_MODE = False
nvcc_args = ["-I" + os.path.join(os.path.dirname(os.path.abspath(__file__)), "third_party/glm/")]

if DEBUG_MODE:
    # 添加调试编译选项
    nvcc_args.extend([
        "-G",           # 生成设备代码调试信息
        "-g",           # 生成主机代码调试信息
        "-lineinfo",    # 生成行号信息
        "-O0",          # 禁用优化
    ])

setup(
    name="diff_gaussian_rasterization",
    packages=['diff_gaussian_rasterization'],
    ext_modules=[
        CUDAExtension(
            name="diff_gaussian_rasterization._C",
            sources=[
            "cuda_rasterizer/rasterizer_impl.cu",
            "cuda_rasterizer/forward.cu",
            "cuda_rasterizer/backward.cu",
            "rasterize_points.cu",
            "ext.cpp"],
            extra_compile_args={"nvcc": nvcc_args})
        ],
    cmdclass={
        'build_ext': BuildExtension
    }
)
