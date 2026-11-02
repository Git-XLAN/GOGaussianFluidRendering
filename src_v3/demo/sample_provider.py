#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
RealTimeWater 的输入源模块：
- scene: 从 SceneDataset 按帧读取
- simulation: 占位接口（后续对接外部模拟器）
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional

import torch

from src_v3.data import SceneDataset
from src_v3.data.camera_from_particles import camera_from_particles


class BaseSampleProvider:
    """
    统一输入接口：每次返回一个 sample 字典，字段尽量与 infer 对齐。
    必需键：positions, vel, radius, camera（camera 可缺省，runner 内补齐）。
    """

    def next_sample(self) -> Optional[Dict[str, Any]]:
        raise NotImplementedError

    def reset(self) -> None:
        """回到序列起点；默认无操作。"""
        return


class SceneSampleProvider(BaseSampleProvider):
    def __init__(
        self,
        root: str,
        scene: str,
        *,
        preload: bool = True,
        require_mesh: bool = False,
        ensure_newfoam_density: bool = False,
    ):
        """
        Args:
            require_mesh: True 时只索引「同时有 particle 与 mesh」的帧（与训练 --require_mesh 一致）。
                RealTime 演示默认 False，否则会因 mesh 不全而只剩极少数帧（例如 300 个 vtk 只有 1 个 obj）。
            ensure_newfoam_density: 是否在加载样本时计算/读取 newFoamDensity。RealTimeWater 默认关闭以加速加载。
        """
        self.dataset = SceneDataset(
            root=root,
            scene=scene,
            require_mesh=require_mesh,
            cache_size=0,
            ensure_newfoam_density=ensure_newfoam_density,
        )
        self._idx = 0
        self._n = len(self.dataset)
        self._preload = bool(preload)
        self._samples: List[Dict[str, Any]] = []
        if self._n <= 0:
            raise RuntimeError(f"SceneDataset 为空: root={root}, scene={scene}")
        if self._preload:
            self._warmup_all_samples()

    def _warmup_all_samples(self) -> None:
        """
        启动时把场景全部帧读入内存，避免实时循环中触发磁盘 I/O。
        """
        samples: List[Dict[str, Any]] = []
        for i in range(self._n):
            s = self.dataset[i]
            if s is None:
                continue
            # 固定读取到的相机，循环时可选择再更新
            samples.append(s)
        if len(samples) == 0:
            raise RuntimeError("预加载后无有效样本")
        self._samples = samples
        self._n = len(self._samples)
        self._idx = 0
        print(f"[SceneSampleProvider] preload enabled, cached_frames={self._n}")

    def next_sample(self) -> Optional[Dict[str, Any]]:
        current_idx = self._idx
        if self._preload:
            base = self._samples[current_idx]
            # 浅拷贝一份，避免每帧覆盖同一 dict 的 camera 字段
            sample = dict(base)
        else:
            sample = self.dataset[current_idx]
        self._idx = (self._idx + 1) % self._n
        if sample is None:
            return None
        is_last = bool(current_idx == self._n - 1)
        sample["meta_total_frames"] = int(self._n)
        sample["meta_provider_idx"] = int(current_idx)
        sample["meta_is_last_frame_in_scene"] = is_last
        sample["meta_next_is_loop"] = is_last

        return sample

    def reset(self) -> None:
        self._idx = 0


class SimulationSampleProvider(BaseSampleProvider):
    """
    TODO: 对接外部 Simulation。
    这里先保留统一接口，后续可把模拟器每帧输出映射成同样的 sample 字典。
    """

    def __init__(self, radius: float = 0.01):
        self.radius = float(radius)
        self._frame_id = 0

    def next_sample(self) -> Optional[Dict[str, Any]]:
        # TODO: 把这里替换为真实 Simulation 数据输入：
        # pos: torch.Tensor[N,3], vel: torch.Tensor[N,3]
        n = 2048
        pos = torch.rand(n, 3, dtype=torch.float32) * 2.0 - 1.0
        vel = torch.randn(n, 3, dtype=torch.float32) * 0.1
        camera = camera_from_particles(pos)
        sample = {
            "positions": pos,
            "vel": vel,
            "radius": self.radius,
            "num_particles": int(n),
            "camera": camera,
            "meta_frame_id": self._frame_id,
            "meta_scene": "simulation_todo",
            "meta_total_frames": -1,
            "meta_provider_idx": self._frame_id,
            "meta_is_last_frame_in_scene": False,
            "meta_next_is_loop": False,
        }
        self._frame_id += 1
        return sample

    def reset(self) -> None:
        self._frame_id = 0


def build_provider(
    mode: str,
    data_path: str,
    scene: str,
    sim_radius: float,
    *,
    preload_scene: bool = True,
    require_mesh: bool = False,
    ensure_newfoam_density: bool = False,
) -> BaseSampleProvider:
    if mode == "scene":
        if not data_path or not scene:
            raise ValueError("scene 模式需要 --data_path 与 --scene")
        return SceneSampleProvider(
            data_path,
            scene,
            preload=preload_scene,
            require_mesh=require_mesh,
            ensure_newfoam_density=ensure_newfoam_density,
        )
    if mode == "simulation":
        return SimulationSampleProvider(radius=sim_radius)
    raise ValueError(f"未知 mode: {mode}")

