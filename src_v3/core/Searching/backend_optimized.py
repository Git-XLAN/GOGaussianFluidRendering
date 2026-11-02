# -*- coding: utf-8 -*-
"""
Searching 优化后端占位。

当实现优化版本时：
  1. 将 HAS_OPTIMIZED 设为 True
  2. 实现 search()，签名与 backend_default.search 一致：
     search(positions, radius, *, vel=None, pos_scale=None, exclude_self=True,
            splash_threshold=..., workers=-1, timing=False, cov_method=0)
    -> (src, dst, cov_pos [N,9], cov_vel [N,9], centerDelta [N,3])
     cov_method 见 covariance 模块注释（0=默认，1/2=预留）。

主入口在 use_optimized=True 时会优先调用本模块的 search；
若本模块未实现或调用失败，则自动回退到 backend_default。
"""

from __future__ import annotations

from typing import Tuple, Optional
from pathlib import Path
import sys
import time
import numpy as np
import torch

# 设为 True 且实现下方 search() 后，--search_optimized 才会使用本实现
HAS_OPTIMIZED = True


def _import_cunnsearch():
    """
    import cunnsearch，并在需要时把 `src_v3/`（放置 .pyd 的目录）加入 sys.path。

    你当前的 .pyd 放在 `.../src_v3/cunnsearch*.pyd`，而本文件在 `src_v3/core/Searching/`，
    因此需要将 `src_v3/` 加入 sys.path 才能 import。
    """
    try:
        import torch
        import cunnsearch  # type: ignore
        return cunnsearch
    except Exception:
        src_v3_dir = Path(__file__).resolve().parents[2]  # .../src_v3
        p = str(src_v3_dir)
        if p not in sys.path:
            sys.path.insert(0, p)
        import cunnsearch  # type: ignore
        return cunnsearch


def search(
    positions: torch.Tensor,
    radius: float,
    *,
    vel: Optional[torch.Tensor] = None,
    minRadius: Optional[float] = None,
    pos_scale: Optional[float] = None,
    exclude_self: bool = True,
    splash_threshold: int = 6,
    workers: int = -1,
    timing: bool = False,
    cov_method: int = 0,
) -> Tuple[torch.Tensor, torch.Tensor, torch.Tensor, torch.Tensor, torch.Tensor]:
    """
    优化后端：完全基于 torch / CUDA。
    要求传入的 positions / vel 已经是 CUDA Tensor，输出同样是 CUDA Tensor。
    """
    if not isinstance(positions, torch.Tensor):
        raise TypeError("backend_optimized.search 现在要求 positions 为 torch.Tensor[N,3]")
    if vel is not None and not isinstance(vel, torch.Tensor):
        raise TypeError("backend_optimized.search 现在要求 vel 为 torch.Tensor[N,3] 或 None")

    if not positions.is_cuda:
        raise RuntimeError("backend_optimized.search 要求 positions 为 CUDA Tensor，请在调用前先 .to('cuda')")
    if vel is not None and not vel.is_cuda:
        raise RuntimeError("backend_optimized.search 要求 vel 为 CUDA Tensor，请在调用前先 .to('cuda')")

    cunnsearch = _import_cunnsearch()

    t0 = time.perf_counter() if timing else 0.0
    # 直接调用 pyd 中的 torch 版本接口（minRadius 仅 optimized 使用）
    min_radius_value = float(minRadius) if minRadius is not None else 0.0
    ret = cunnsearch.radius_neighbors_with_covariances_torch(positions, vel, radius, min_radius_value)
    if isinstance(ret, tuple) and len(ret) == 5:
        src, dst, cov_pos, cov_vel, center_delta = ret
    elif isinstance(ret, tuple) and len(ret) == 4:
        # 兼容旧版 pyd
        src, dst, cov_pos, cov_vel = ret
        center_delta = torch.zeros((positions.shape[0], 3), dtype=torch.float32, device=positions.device)
    else:
        raise RuntimeError("cunnsearch 返回值数量异常，期望 4 或 5 项")
    t1 = time.perf_counter() if timing else 0.0

    if timing:
        print(f"[cuNSearchTiming] torch_call={(t1 - t0)*1000.0:.2f} ms")

    return src, dst, cov_pos.reshape(-1, 9), cov_vel.reshape(-1, 9), center_delta.reshape(-1, 3)
