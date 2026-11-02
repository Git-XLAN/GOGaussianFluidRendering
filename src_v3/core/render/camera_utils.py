# -*- coding: utf-8 -*-
"""
相机工具：从 (origin/target/up/fov) 或已有矩阵生成光栅化所需矩阵。存储均为行优先 (row-major)。

两个核心矩阵（与 3DGS 官方约定一致）：
  A) View Matrix (World-to-Camera): V = [R | t; 0 1]，世界坐标 -> 相机坐标，右手系 Z 向前。
  B) Full Projection (World-to-NDC): FullProj = Proj x View，世界坐标一步到 NDC；由调用方传入 projmatrix。
"""

from __future__ import annotations

from typing import Any, Dict, Optional, Tuple, Union

import torch
import torch.nn.functional as F


def camera_params_to_matrices(
    camera: Union[Dict[str, Any], Any],
    width: int,
    height: int,
    device: Optional[torch.device] = None,
    dtype: torch.dtype = torch.float32,
) -> Tuple[torch.Tensor, torch.Tensor, torch.Tensor, float, float]:
    """
    将相机表示转为光栅化所需的 view [4,4]、proj [4,4]、cam_pos [3]、tanfovx、tanfovy。

    支持的 camera 形式：
    1) 字典：{"origin": [x,y,z], "target": [x,y,z], "up": [x,y,z], "fov": 度数}
       - 使用 look_at + 垂直 fov 推导 view/proj；tanfov 由 fov 与宽高比得到。
    2) 对象：具有属性 viewmatrix/view_matrix, projmatrix/proj_matrix, campos/cam_pos,
       tanFovx, tanFovy（或 tanfovx, tanfovy）
       - 直接读取并转为 tensor（若已是 tensor 则只做 device/dtype 对齐）。

    Returns
    -------
    view_matrix : [4, 4]
    proj_matrix : [4, 4]
    cam_pos     : [3]
    tanfovx, tanfovy : float
    """
    if device is None:
        device = torch.device("cpu")

    # 1) 字典：origin, target, up, fov
    if isinstance(camera, dict):
        return _from_dict(camera, width, height, device, dtype)

    # 2) 对象：viewmatrix, projmatrix, campos, tanFovx, tanFovy
    return _from_object(camera, width, height, device, dtype)


def _from_dict(
    cam: Dict[str, Any],
    width: int,
    height: int,
    device: torch.device,
    dtype: torch.dtype,
) -> Tuple[torch.Tensor, torch.Tensor, torch.Tensor, float, float]:
    """
    (origin, target, up, fov) -> View (World-to-Camera), Proj (Camera-to-NDC)。
    存储行优先 (row-major)，与 3DGS 官方/PyTorch 一致。
    """
    origin = _to_list(cam.get("origin", [0.0, 0.0, 5.0]))
    target = _to_list(cam.get("target", [0.0, 0.0, 0.0]))
    up = _to_list(cam.get("up", [0.0, 1.0, 0.0]))
    fov_deg = float(cam.get("fov", 60))

    view = _look_at(origin, target, up, device, dtype)
    proj = _perspective(fov_deg, width / max(height, 1), device, dtype)
    cam_pos = torch.tensor(origin, device=device, dtype=dtype)
    fov_rad = fov_deg * 3.141592653589793 / 180.0
    tanfovy = float(torch.tensor(fov_rad / 2.0).tan().item())
    aspect = width / max(height, 1)
    tanfovx = tanfovy * aspect

    return view, proj, cam_pos, tanfovx, tanfovy


def _to_list(x: Any) -> list:
    if isinstance(x, (list, tuple)):
        return list(x)[:3]
    if hasattr(x, "tolist"):
        return x.tolist()[:3]
    return [float(x)] * 3


def _look_at(
    origin: list,
    target: list,
    up: list,
    device: torch.device,
    dtype: torch.dtype,
) -> torch.Tensor:
    """
    View Matrix (World-to-Camera), row-major. V = [R | t; 0 1], right-handed:
    X right, Y up, Z forward; visible points have p_view.z > 0. R rows = right, up_cam, fwd.
    """
    o = torch.tensor(origin, device=device, dtype=dtype)
    t = torch.tensor(target, device=device, dtype=dtype)
    u = torch.tensor(up, device=device, dtype=dtype)
    fwd = torch.nn.functional.normalize(t - o, dim=0)
    right = torch.nn.functional.normalize(torch.linalg.cross(u, fwd), dim=0)
    up_cam = torch.linalg.cross(fwd, right)
    # World-to-camera 旋转：行 = (right, up_cam, fwd)，V = [R | t; 0 1]
    R_w2c = torch.stack([right, up_cam, fwd], dim=0)  # 3x3
    t_vec = -R_w2c @ o
    view = torch.eye(4, device=device, dtype=dtype)
    view[:3, :3] = R_w2c
    view[:3, 3] = t_vec
    return view


def _perspective(
    fov_deg: float,
    aspect: float,
    device: torch.device,
    dtype: torch.dtype,
    near: float = 0.1,
    far: float = 1000.0,
) -> torch.Tensor:
    """
    Projection Matrix (Camera-to-NDC)，行优先。
    透视矩阵，fov 为垂直方向（度）；NDC z 从 near 映射到 -1、far 到 +1。
    """
    fov_rad = fov_deg * 3.141592653589793 / 180.0
    tan_half = float(torch.tensor(fov_rad / 2.0).tan().item())
    sy = 1.0 / tan_half
    sx = sy / aspect
    n, f = near, far
    proj = torch.zeros(4, 4, device=device, dtype=dtype)
    proj[0, 0] = -sx
    proj[1, 1] = -sy
    proj[2, 2] = -(f + n) / (f - n)
    proj[2, 3] = -2.0 * f * n / (f - n)
    proj[3, 2] = -1.0
    return proj


def _from_object(
    cam: Any,
    width: int,
    height: int,
    device: torch.device,
    dtype: torch.dtype,
) -> Tuple[torch.Tensor, torch.Tensor, torch.Tensor, float, float]:
    def get(name: str, default: Any = None):
        for key in (name, name.replace("matrix", "Matrix").replace("pos", "pos")):
            if hasattr(cam, key):
                return getattr(cam, key)
        return default

    view = get("viewmatrix") or get("view_matrix")
    proj = get("projmatrix") or get("proj_matrix")
    campos = get("campos") or get("cam_pos")
    tanfovx = get("tanFovx") or get("tanfovx")
    tanfovy = get("tanFovy") or get("tanfovy")

    if view is None or proj is None or campos is None:
        raise ValueError("camera 对象缺少 viewmatrix/view_matrix, projmatrix/proj_matrix, campos/cam_pos")
    if tanfovx is None or tanfovy is None:
        raise ValueError("camera 对象缺少 tanFovx/tanfovx, tanFovy/tanfovy")

    def to_t4x4(x):
        t = x if isinstance(x, torch.Tensor) else torch.tensor(x, device=device, dtype=dtype)
        if t.dim() == 1 and t.numel() >= 16:
            return t[:16].reshape(4, 4).to(device=device, dtype=dtype)
        return t.to(device=device, dtype=dtype)

    def to_t3(x):
        t = x if isinstance(x, torch.Tensor) else torch.tensor(x, device=device, dtype=dtype)
        return t.flatten()[:3].to(device=device, dtype=dtype)

    view_t = to_t4x4(view)
    proj_t = to_t4x4(proj)
    cam_pos_t = to_t3(campos)
    tx = float(tanfovx) if not isinstance(tanfovx, torch.Tensor) else tanfovx.item()
    ty = float(tanfovy) if not isinstance(tanfovy, torch.Tensor) else tanfovy.item()
    return view_t, proj_t, cam_pos_t, tx, ty


def world_xyz_from_radial_depth_dict_camera(
    camera: Dict[str, Any],
    width: int,
    height: int,
    depth: torch.Tensor,
    hit: torch.Tensor,
    *,
    hit_threshold: float = 0.5,
) -> torch.Tensor:
    """
    由 dict 相机（origin/target/up/fov）与每像素径向深度 ``depth``（与 GaussianProjector 中
    ``||p - cam||`` 语义一致）近似还原世界坐标 ``xyz``，shape ``[H, W, 3]``。
    ``hit < hit_threshold`` 的像素置零。
    """
    if not isinstance(camera, dict):
        raise TypeError("world_xyz_from_radial_depth_dict_camera 当前仅支持 dict camera")
    device = depth.device
    dtype = depth.dtype
    H, W = int(height), int(width)
    origin = torch.tensor(_to_list(camera.get("origin", [0.0, 0.0, 5.0])), device=device, dtype=dtype)
    target = torch.tensor(_to_list(camera.get("target", [0.0, 0.0, 0.0])), device=device, dtype=dtype)
    up = torch.tensor(_to_list(camera.get("up", [0.0, 1.0, 0.0])), device=device, dtype=dtype)
    fov_deg = float(camera.get("fov", 60.0))
    aspect = W / max(H, 1)
    fov_rad = fov_deg * 3.141592653589793 / 180.0
    tan_fovy = float(torch.tensor(fov_rad / 2.0).tan().item())
    tan_fovx = tan_fovy * aspect

    fwd = F.normalize(target - origin, dim=0)
    right = F.normalize(torch.linalg.cross(up, fwd), dim=0)
    up_c = F.normalize(torch.linalg.cross(fwd, right), dim=0)

    v_grid, u_grid = torch.meshgrid(
        torch.arange(H, device=device, dtype=dtype),
        torch.arange(W, device=device, dtype=dtype),
        indexing="ij",
    )
    ndc_x = (u_grid + 0.5) / float(W) * 2.0 - 1.0
    ndc_y = -((v_grid + 0.5) / float(H) * 2.0 - 1.0)
    dirs = (
        fwd
        + ndc_x.unsqueeze(-1) * float(tan_fovx) * right
        + ndc_y.unsqueeze(-1) * float(tan_fovy) * up_c
    )
    dirs = F.normalize(dirs, dim=-1)

    d = depth.squeeze(-1).to(dtype=dtype)
    xyz = origin + d.unsqueeze(-1) * dirs
    invalid = hit.squeeze(-1) < float(hit_threshold)
    xyz = xyz.clone()
    xyz[invalid] = 0.0
    return xyz
