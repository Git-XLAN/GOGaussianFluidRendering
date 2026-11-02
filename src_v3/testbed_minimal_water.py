# -*- coding: utf-8 -*-
"""
烟测：加载 ``RealTimeWaterMinimal.Render``，10 个粒子沿 x 轴等距排列，零速，半径 0.05；
在 while 循环中持续调用 ``Render``（不保存图像）。

依赖：与本项目 RealTimeWater 相同（PyTorch、Falcor、权重路径见 ``demo/RealTimeWaterMinimal.py``）。

运行::

    python -m src_v3.testbed_minimal_water

Ctrl+C 结束。
"""

from __future__ import annotations

import sys
import time
from pathlib import Path


_REPO_ROOT = Path(__file__).resolve().parents[1]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))


def main() -> None:
    import torch

    from src_v3.demo.RealTimeWaterMinimal import Render

    n = 10
    x_spacing = 0.15
    pos = torch.zeros(n, 3, dtype=torch.float32)
    pos[:, 0] = torch.arange(n, dtype=torch.float32) * x_spacing
    vel = torch.zeros_like(pos)
    radius = 0.05

    print(
        f"[testbed_minimal_water] {n} particles on x-axis (spacing={x_spacing}), "
        f"radius={radius}, vel=0; while True: Render(...) — Ctrl+C to stop"
    )

    dt = 1.0 / 60.0
    frame = 0
    t0 = time.perf_counter()
    try:
        while True:
            img = Render(pos, radius, vel, dt, frame * dt)
            frame += 1
            if frame == 1 or frame % 60 == 0:
                elapsed = time.perf_counter() - t0
                fps = frame / elapsed if elapsed > 0 else 0.0
                print(
                    f"[testbed_minimal_water] frame={frame} "
                    f"shape={tuple(img.shape)} fps≈{fps:.2f}"
                )
    except KeyboardInterrupt:
        print(f"\n[testbed_minimal_water] stopped after {frame} frames")


if __name__ == "__main__":
    main()
