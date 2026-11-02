# -*- coding: utf-8 -*-
"""
VTK 加载器（与 src_v2 读取逻辑一致，接口更清晰）

读取 key：
- 流体: nums, positions [N,4], vel?, radius, maxPos, minPos
- 泡沫: 同上 + lifetime?, id?, is_born?
"""

import os
import numpy as np
from typing import Optional, Dict, Any

try:
    import vtk
except ImportError:
    vtk = None


class VTKLoadError(Exception):
    """VTK 加载错误"""
    pass


# 属性名与 v2 一致
RADIUS_ATTRS = ["pscale", "radius"]
VELOCITY_ATTRS = ["v", "velocity"]
LIFETIME_ATTRS = ["lifetime"]
ID_ATTRS = ["id", "particle_id", "foam_id"]
FLAG_ATTRS = ["born"]


def _get_array(point_data, names):
    for name in names:
        arr = point_data.GetArray(name)
        if arr is not None:
            return arr, name
    return None, None


def load_fluid_vtk(
    file_path: str,
    default_radius: float = 0.01,
) -> Optional[Dict[str, Any]]:
    """
    加载流体粒子 VTK。

    Returns:
        字典: nums, positions [N,4], vel?, radius, maxPos, minPos, sph；
        ``sph``: 0 表示 VTK 点数据含 ``pscale``（SPH 粒子尺度），1 表示不含 ``pscale``
        （半径来自 ``radius`` 字段或默认值）。
        失败返回 None。
    """
    return _load_vtk(file_path, default_radius=default_radius, is_foam=False)


def load_foam_vtk(
    file_path: str,
    default_radius: float = 0.01,
) -> Optional[Dict[str, Any]]:
    """
    加载泡沫粒子 VTK。

    Returns:
        字典: 流体 key + lifetime?, id?, is_born?；
        失败返回 None。
    """
    return _load_vtk(file_path, default_radius=default_radius, is_foam=True)


def _load_vtk(
    file_path: str,
    default_radius: float,
    is_foam: bool,
) -> Optional[Dict[str, Any]]:
    if vtk is None:
        raise VTKLoadError("未安装 python-vtk")
    if not os.path.exists(file_path):
        return None

    try:
        reader = vtk.vtkGenericDataObjectReader()
        reader.SetFileName(str(file_path))
        reader.Update()
        output = reader.GetOutput()
        if output is None:
            return None
        vtk_points = output.GetPoints()
        if vtk_points is None:
            return None
        num_points = vtk_points.GetNumberOfPoints()
        if num_points == 0:
            return None

        point_data = output.GetPointData()
        raw_positions = np.array(vtk_points.GetData(), copy=False)
        if raw_positions.ndim == 1:
            raw_positions = raw_positions.reshape((num_points, 3))

        data = {
            "nums": num_points,
            "maxPos": np.max(raw_positions, axis=0).astype(np.float64),
            "minPos": np.min(raw_positions, axis=0).astype(np.float64),
        }

        # 半径
        radius_arr, rname = _get_array(point_data, RADIUS_ATTRS)
        if radius_arr is not None:
            raw_radii = np.array(radius_arr, copy=False)
            if raw_radii.ndim == 1:
                raw_radii = raw_radii.reshape((num_points, 1))
            if rname == "pscale":
                if not is_foam:
                    raw_radii = raw_radii * 0.5
                else:
                    raw_radii = raw_radii * 0.5 * 0.25
            data["radius"] = float(raw_radii.flat[0]) if num_points else default_radius
        else:
            actual = default_radius / 10.0 if is_foam else default_radius
            data["radius"] = actual
            raw_radii = np.full((num_points, 1), actual, dtype=raw_positions.dtype)
        data["positions"] = np.concatenate((raw_positions, raw_radii), axis=1)

        # 速度
        vel_arr, _ = _get_array(point_data, VELOCITY_ATTRS)
        data["vel"] = np.array(vel_arr, copy=False) if vel_arr is not None else None

        if is_foam:
            life_arr, _ = _get_array(point_data, LIFETIME_ATTRS)
            if life_arr is not None:
                data["lifetime"] = (np.array(life_arr, copy=False) - 0.2) / (9.0 - 0.2)
            else:
                data["lifetime"] = None
            id_arr, _ = _get_array(point_data, ID_ATTRS)
            data["id"] = np.array(id_arr, copy=False).astype(np.int64) if id_arr is not None else None
            born_arr, _ = _get_array(point_data, FLAG_ATTRS)
            data["is_born"] = np.array(born_arr, copy=False).astype(bool) if born_arr is not None else None
        else:
            data["lifetime"] = None
            data["id"] = None
            # 无 pscale → sph=1；存在 pscale（作为半径来源）→ sph=0
            data["sph"] = 0 if rname == "pscale" else 1

        return data
    except Exception as e:
        print(f"[Error] VTK 加载失败 {file_path}: {e}")
        return None


def get_particle_count(file_path: str) -> int:
    """仅读取粒子数量，不加载完整数据。"""
    if vtk is None or not os.path.exists(file_path):
        return 0
    try:
        reader = vtk.vtkGenericDataObjectReader()
        reader.SetFileName(str(file_path))
        reader.Update()
        out = reader.GetOutput()
        if out is None:
            return 0
        pts = out.GetPoints()
        return pts.GetNumberOfPoints() if pts else 0
    except Exception:
        return 0
