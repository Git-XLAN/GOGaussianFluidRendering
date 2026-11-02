# -*- coding: utf-8 -*-
"""
目录布局约定与帧索引构建

约定结构:
  <root>/
    <scene_name>/
      particle/   *.vtk   (流体)
      mesh/       *.obj   (GT mesh，可选)
      foam/       *.vtk   (泡沫，可选)
      Newfoam/    *.vtk   (当前帧新生泡沫，可选)

帧 ID 从文件名中提取（第一个连续数字）。
"""

import re
from pathlib import Path
from typing import List, Optional, Sequence, Tuple
from dataclasses import dataclass, field


def extract_frame_id(filename: str) -> Optional[int]:
    """从文件名中提取帧 ID（第一个连续数字）。"""
    m = re.search(r"(\d+)", filename)
    return int(m.group(1)) if m else None


@dataclass
class FramePaths:
    """单帧对应的文件路径（仅路径，不加载数据；不含下一帧路径）。"""
    scene: str
    frame_id: int
    particle_path: str
    mesh_path: Optional[str] = None
    foam_path: Optional[str] = None
    newfoam_path: Optional[str] = None


@dataclass
class FrameIndex:
    """
    帧索引：所有可访问帧的列表（多场景合并）。
    每个元素为 FramePaths，按 (scene, frame_id) 排序。
    """
    rows: List[FramePaths] = field(default_factory=list)

    def __len__(self) -> int:
        return len(self.rows)

    def __getitem__(self, idx: int) -> FramePaths:
        return self.rows[idx]

    def scene_names(self) -> List[str]:
        return sorted({r.scene for r in self.rows})

    def filter_by_scene(self, scene: str) -> "FrameIndex":
        return FrameIndex(rows=[r for r in self.rows if r.scene == scene])

    def filter_by_scenes(self, scenes: Sequence[str]) -> "FrameIndex":
        """仅保留 scene 属于给定集合的帧（顺序与原始 rows 一致）。"""
        allowed = set(scenes)
        return FrameIndex(rows=[r for r in self.rows if r.scene in allowed])


def build_frame_index(
    root: Path,
    require_mesh: bool = False,
    particle_glob: str = "*.vtk",
    mesh_glob: str = "*.obj",
) -> FrameIndex:
    """
    扫描 root 下所有场景，构建帧索引。

    Args:
        root: 数据根目录（例如 F:/DataSet）
        require_mesh: 若 True，仅保留同时存在 particle 与 mesh 的帧
        particle_glob: 粒子 VTK 匹配
        mesh_glob: mesh 文件匹配

    Returns:
        FrameIndex 按 (scene, frame_id) 排序
    """
    root = Path(root)
    if not root.exists():
        return FrameIndex()

    rows: List[FramePaths] = []
    for scene_path in sorted(root.iterdir()):
        if not scene_path.is_dir():
            continue
        scene = scene_path.name
        particle_dir = scene_path / "particle"
        if not particle_dir.exists():
            continue
        mesh_dir = scene_path / "mesh"
        foam_dir = scene_path / "foam"
        newfoam_dir = scene_path / "Newfoam"

        vtk_files = list(particle_dir.glob(particle_glob))
        vtk_map = {extract_frame_id(f.name): f for f in vtk_files if extract_frame_id(f.name) is not None}
        mesh_map = {}
        if mesh_dir.exists():
            mesh_map = {extract_frame_id(f.name): f for f in mesh_dir.glob(mesh_glob) if extract_frame_id(f.name) is not None}
        foam_map = {}
        if foam_dir.exists():
            foam_map = {extract_frame_id(f.name): f for f in foam_dir.glob("*.vtk") if extract_frame_id(f.name) is not None}
        newfoam_map = {}
        if newfoam_dir.exists():
            newfoam_map = {extract_frame_id(f.name): f for f in newfoam_dir.glob("*.vtk") if extract_frame_id(f.name) is not None}

        valid_ids = set(vtk_map.keys())
        if require_mesh:
            valid_ids &= set(mesh_map.keys())
        sorted_ids = sorted(valid_ids)

        for fid in sorted_ids:
            rows.append(FramePaths(
                scene=scene,
                frame_id=fid,
                particle_path=str(vtk_map[fid]),
                mesh_path=str(mesh_map[fid]) if fid in mesh_map else None,
                foam_path=str(foam_map[fid]) if fid in foam_map else None,
                newfoam_path=str(newfoam_map[fid]) if fid in newfoam_map else None,
            ))

    return FrameIndex(rows=rows)
