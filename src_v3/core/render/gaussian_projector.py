# -*- coding: utf-8 -*-
"""
高斯投影器：网络输出 →（可选）剔除 → 按 GT 相机与分辨率投影 → normal / depth / hit。

用法：只需传入「GT 侧」相机与输出图像宽高，其余在类内完成。
  projector = GaussianProjector(width=256, height=256)
  normal, depth, hit, vel, foam_prob_culled, gs_pos_culled, foam_prob_raw_culled, gs_vel_culled = projector.project(...)
"""

from __future__ import annotations

from typing import Any, Dict, Optional, Tuple, Union

import torch
import torch.nn.functional as F

from .camera_utils import camera_params_to_matrices

try:
    from diff_gaussian_rasterization import GaussianRasterizationSettings, GaussianRasterizer
    _HAS_RASTERIZER = True
except ImportError:
    _HAS_RASTERIZER = False
    GaussianRasterizationSettings = None
    GaussianRasterizer = None


def get_shortest_axis_normals(
    scales: torch.Tensor,
    rotations: torch.Tensor,
    front: torch.Tensor,
) -> torch.Tensor:
    """
    从高斯的 scale 与 rotation 得到最短轴方向作为法线（无显式法线时用）。
    scales [N,3], rotations [N,4] 四元数, front [3] 相机前向。
    返回 [N,3]，朝向相机。
    """
    quat = F.normalize(rotations, p=2, dim=-1)
    w, x, y, z = quat.unbind(-1)
    R00 = 1 - 2 * (y * y + z * z)
    R01 = 2 * (x * y - w * z)
    R02 = 2 * (x * z + w * y)
    R10 = 2 * (x * y + w * z)
    R11 = 1 - 2 * (x * x + z * z)
    R12 = 2 * (y * z - w * x)
    R20 = 2 * (x * z - w * y)
    R21 = 2 * (y * z + w * x)
    R22 = 1 - 2 * (x * x + y * y)
    R = torch.stack([
        torch.stack([R00, R01, R02], dim=-1),
        torch.stack([R10, R11, R12], dim=-1),
        torch.stack([R20, R21, R22], dim=-1),
    ], dim=-2)
    min_axis_idx = torch.argmin(scales, dim=1)
    normals = R[torch.arange(R.shape[0], device=R.device), :, min_axis_idx]
    front = F.normalize(front.view(1, 3).to(scales.device), p=2, dim=-1)
    dots = (normals * front).sum(dim=1, keepdim=True)
    flip = -torch.sign(dots)
    flip[flip == 0] = 1.0
    return normals * flip


class GaussianProjector:
    """
    将网络输出的高斯参数，按给定相机与分辨率投影为 normal / depth / hit 图。
    只需传入与 GT 一致的相机及输出宽高，内部完成：相机→矩阵、可选剔除、拼通道、光栅化、拆通道与 hit 掩码。
    """

    def __init__(
        self,
        width: int,
        height: int,
        device: Optional[torch.device] = None,
        hit_threshold: float = 0.5,
        cull_scale_threshold: float = 0.01,
    ):
        """
        Args:
            width, height: 输出图像宽高（与 GT 一致）。
            device: 若为 None，则从首次传入的 gs_pos 推断。
            hit_threshold: hit < 该值的像素将 normal/depth 置 0。
            cull_scale_threshold: 小于这个值 被culling
        """
        if not _HAS_RASTERIZER:
            raise ImportError("需要安装 diff_gaussian_rasterization 才能使用 GaussianProjector")
        self.width = int(width)
        self.height = int(height)
        self._device = device
        self.hit_threshold = hit_threshold
        self.cull_scale_threshold = cull_scale_threshold

    def project(
        self,
        camera: Union[Dict[str, Any], Any],
        gs_pos: torch.Tensor,
        gs_scale: torch.Tensor,
        gs_rotation: torch.Tensor,
        gs_normal: Optional[torch.Tensor] = None,
        gs_opacity: Optional[torch.Tensor] = None,
        gs_foam_prob: Optional[torch.Tensor] = None,
        gs_vel: Optional[torch.Tensor] = None,
        gs_foam_prob_raw: Optional[torch.Tensor] = None,
        gs_anchor_pos: Optional[torch.Tensor] = None,
    ) -> Tuple[
        torch.Tensor,
        torch.Tensor,
        torch.Tensor,
        torch.Tensor,
        torch.Tensor,
        torch.Tensor,
        torch.Tensor,
        torch.Tensor,
    ]:
        """
        一次投影：用当前相机与实例的 width/height 渲染。

        Args:
            camera: 与 GT 对应的相机。支持：
                - 字典 {"origin", "target", "up", "fov"}（与 GTGenerator 一致）
                - 或对象含 viewmatrix, projmatrix, campos, tanFovx, tanFovy
            gs_pos: [N, 3]
            gs_scale: [N, 3]
            gs_rotation: [N, 4] 四元数
            gs_normal: [N, 3] 可选；为 None 时用最短轴法线
            gs_opacity: [N, 1] 或 [N] 可选；用于 hit 通道，为 None 时用 1
            gs_foam_prob: [N, 1] 或 [N] 可选；用于泡沫概率通道，为 None 时用 0
            gs_foam_prob_raw: [N, 1] 或 [N] 可选；用于泡沫 raw logit，为 None 时用 0
            gs_anchor_pos: [N, 3] 可选；每个高斯所属的父流体粒子位置，用于训练侧泡沫 GT 采样

        Returns:
            normal: [H, W, 3]，已归一化，无效区为 0
            depth: [H, W, 1]
            hit: [H, W, 1]
            vel: [H, W, 3]
            foam_prob_culled: [N_culled, 1]（剔除后，与参与投影的高斯一一对应）
            gs_pos_culled: [N_culled, 3]（剔除后，与参与投影的高斯一一对应）
            foam_prob_raw_culled: [N_culled, 1]（剔除后，与参与投影的高斯一一对应）
            gs_vel_culled: [N_culled, 3]（剔除后每高斯速度，与 gs_pos_culled 对齐）
            gs_anchor_pos_culled: [N_culled, 3]（仅传入 gs_anchor_pos 时追加返回）
        """
        device = self._device or gs_pos.device
        gs_pos = gs_pos.to(device).float()
        gs_scale = gs_scale.to(device).float()
        gs_rotation = gs_rotation.to(device).float()
        return_anchor_pos = gs_anchor_pos is not None
        if gs_anchor_pos is not None:
            gs_anchor_pos = gs_anchor_pos.to(device).float()
            if gs_anchor_pos.dim() != 2 or gs_anchor_pos.shape[1] != 3:
                gs_anchor_pos = gs_anchor_pos.reshape(-1, 3)
        if gs_vel is not None:
            gs_vel = gs_vel.to(device).float()
            # 期望 [N,3]
            if gs_vel.dim() != 2 or gs_vel.shape[1] != 3:
                gs_vel = gs_vel.reshape(-1, 3)
        else:
            # 默认速度为 0
            gs_vel = torch.zeros((gs_pos.shape[0], 3), device=device, dtype=gs_pos.dtype)

        view_mat, proj_mat, cam_pos, tanfovx, tanfovy = camera_params_to_matrices(
            camera, self.width, self.height, device=device
        )
        # 矩阵 A: viewmatrix = View (World-to-Camera)，用于 p_view 与近平面剔除
        # 矩阵 B: projmatrix = FullProj = Proj x View (World-to-NDC)，行优先，一步到 NDC
        full_proj_mat = (proj_mat @ view_mat).contiguous()

        view_mat[0:1,:] = -view_mat[0:1,:]
        view_mat[1:2,:] = -view_mat[1:2,:]
        view_mat = view_mat.T

        full_proj_mat[0:1,:] = -full_proj_mat[0:1,:]
        full_proj_mat[1:2,:] = -full_proj_mat[1:2,:]
        full_proj_mat = full_proj_mat.T

        if gs_opacity is not None:
            gs_opacity = gs_opacity.to(device).float()
            if gs_opacity.dim() == 1:
                gs_opacity = gs_opacity.unsqueeze(-1)
        else:
            gs_opacity = torch.ones((gs_pos.shape[0], 1), device=device, dtype=gs_pos.dtype)
        
        if gs_foam_prob is not None:
            gs_foam_prob = gs_foam_prob.to(device).float()
            if gs_foam_prob.dim() == 1:
                gs_foam_prob = gs_foam_prob.unsqueeze(-1)
        else:
            gs_foam_prob = torch.zeros((gs_pos.shape[0], 1), device=device, dtype=gs_pos.dtype)
        if gs_foam_prob_raw is not None:
            gs_foam_prob_raw = gs_foam_prob_raw.to(device).float()
            if gs_foam_prob_raw.dim() == 1:
                gs_foam_prob_raw = gs_foam_prob_raw.unsqueeze(-1)
        else:
            gs_foam_prob_raw = torch.zeros((gs_pos.shape[0], 1), device=device, dtype=gs_pos.dtype)

        if self.cull_scale_threshold > 0:
            n_before = gs_pos.shape[0]
            max_scale = gs_scale.max(dim=-1)[0]
            valid = max_scale > self.cull_scale_threshold
            gs_pos = gs_pos[valid]
            gs_scale = gs_scale[valid]
            gs_rotation = gs_rotation[valid]
            gs_opacity = gs_opacity[valid]
            gs_normal = gs_normal[valid] if gs_normal is not None else None
            gs_vel = gs_vel[valid] if gs_vel is not None else None
            gs_foam_prob = gs_foam_prob[valid] if gs_foam_prob is not None else None
            gs_foam_prob_raw = gs_foam_prob_raw[valid] if gs_foam_prob_raw is not None else None
            gs_anchor_pos = gs_anchor_pos[valid] if gs_anchor_pos is not None else None
            n_after = gs_pos.shape[0]
            #print(f"[GSCull] gaussians: before={n_before}, after={n_after}, threshold={self.cull_scale_threshold}")

        if gs_pos.shape[0] == 0:
            h, w = self.height, self.width
            normal = torch.zeros(h, w, 3, device=device, dtype=gs_pos.dtype)
            depth = torch.zeros(h, w, 1, device=device, dtype=gs_pos.dtype)
            hit = torch.zeros(h, w, 1, device=device, dtype=gs_pos.dtype)
            vel = torch.zeros(h, w, 3, device=device, dtype=gs_pos.dtype)
            foam_prob_culled = torch.zeros((0, 1), device=device, dtype=gs_pos.dtype)
            gs_pos_culled = torch.zeros((0, 3), device=device, dtype=gs_pos.dtype)
            foam_prob_raw_culled = torch.zeros((0, 1), device=device, dtype=gs_pos.dtype)
            gs_vel_culled = torch.zeros((0, 3), device=device, dtype=gs_pos.dtype)
            if return_anchor_pos:
                gs_anchor_pos_culled = torch.zeros((0, 3), device=device, dtype=gs_pos.dtype)
                return (
                    normal,
                    depth,
                    hit,
                    vel,
                    foam_prob_culled,
                    gs_pos_culled,
                    foam_prob_raw_culled,
                    gs_vel_culled,
                    gs_anchor_pos_culled,
                )
            return normal, depth, hit, vel, foam_prob_culled, gs_pos_culled, foam_prob_raw_culled, gs_vel_culled

        # 法线：显式或最短轴
        front = F.normalize(cam_pos - gs_pos.mean(dim=0), dim=0)
        if gs_normal is not None:
            colors_n = F.normalize(gs_normal.to(device).float(), dim=-1)
        else:
            colors_n = get_shortest_axis_normals(gs_scale, gs_rotation, front)

        # 深度与 hit
        d = torch.norm(gs_pos - cam_pos, dim=1, keepdim=True)
        # 8 通道：normal(3) + opacity(1) + depth(1) + vel(3)
        surface_feature = torch.cat([colors_n, gs_opacity, d, gs_vel], dim=-1)  # [N, 8]

        # 数值稳定
        surface_feature = torch.nan_to_num(surface_feature, nan=0.0, posinf=0.0, neginf=0.0)
        pos2d = torch.zeros_like(gs_pos, device=device, dtype=gs_pos.dtype)

        raster_settings = GaussianRasterizationSettings(
            image_height=self.height,
            image_width=self.width,
            tanfovx=tanfovx,
            tanfovy=tanfovy,
            # bg 的维度必须与 colors_precomp 的通道数一致，否则后续通道会出现异常值
            bg=torch.zeros(8, device=device),
            scale_modifier=1.0,
            viewmatrix=view_mat,
            projmatrix=full_proj_mat,
            sh_degree=0,
            campos=cam_pos,
            prefiltered=False,
            debug=False,
        )

        rasterizer = GaussianRasterizer(raster_settings)
        out = rasterizer(
            means3D=gs_pos,
            means2D=pos2d,
            shs=None,
            colors_precomp=surface_feature,
            opacities=gs_opacity,
            scales=gs_scale,
            rotations=gs_rotation,
            cov3D_precomp=None,
        )[0]
        surface = out.permute(1, 2, 0)  # [H, W, 8]

        normal = surface[:, :, 0:3].clone()
        normal = F.normalize(normal, dim=-1)
        hit = surface[:, :, 3:4]
        depth = surface[:, :, 4:5]
        vel = surface[:, :, 5:8]
        
        invalid = hit[:, :, 0] < self.hit_threshold
        normal[invalid] = 0
        depth[invalid] = 0
        vel[invalid] = 0

        foam_prob_culled = gs_foam_prob if gs_foam_prob is not None else torch.zeros((gs_pos.shape[0], 1), device=device, dtype=gs_pos.dtype)
        gs_pos_culled = gs_pos
        foam_prob_raw_culled = gs_foam_prob_raw if gs_foam_prob_raw is not None else torch.zeros((gs_pos.shape[0], 1), device=device, dtype=gs_pos.dtype)
        gs_vel_culled = gs_vel
        if return_anchor_pos:
            gs_anchor_pos_culled = gs_anchor_pos if gs_anchor_pos is not None else gs_pos
            return (
                normal,
                depth,
                hit,
                vel,
                foam_prob_culled,
                gs_pos_culled,
                foam_prob_raw_culled,
                gs_vel_culled,
                gs_anchor_pos_culled,
            )
        return normal, depth, hit, vel, foam_prob_culled, gs_pos_culled, foam_prob_raw_culled, gs_vel_culled
