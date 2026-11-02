# -*- coding: utf-8 -*-
"""
泡沫密度场计算工具（3D 体素密度）。

compute_Foam_Density：对每个泡沫点做三线性 splat 到周围 8 个体素，再**整体**除以
``MaxFoamNum``（默认 100）并乘以 ``Densityfactor``（不按全图体素密度总和归一化）；原
``histogramdd`` + ``max_num`` 逻辑已注释保留。

在此基础上：
  - 返回值改为 torch.FloatTensor
  - 默认对归一化后的密度 d 做 log 映射作为 GT 监督（d=0 保持 0；d>0 映射到约 (0,1]）
"""

import math
from typing import Optional, Sequence, Tuple, Union

import torch

import numpy as np

# 与 ``dataset._ensure_newfoam_density`` 中 newFoamDensity 计算一致（固定场景体素盒）
NEWFOAM_DENSITY_CORNER_MIN: Tuple[float, float, float] = (-5.0, -5.0, -5.0)
NEWFOAM_DENSITY_CORNER_MAX: Tuple[float, float, float] = (5.0, 5.0, 5.0)
NEWFOAM_DENSITY_GRID_NUM: Tuple[int, int, int] = (100, 100, 100)


def map_foam_density_to_gt_log(
    d: torch.Tensor,
    alpha: float = 1.0,
    *,
    d_max_reference: float = 1.0,
) -> torch.Tensor:
    r"""
    将非负密度 d 映射为 GT 监督值 y（与体素一一对应）：

    .. math::

        y = \begin{cases}
            0 & d = 0 \\
            \dfrac{\log(1 + \alpha d)}{\log(1 + \alpha d_{\mathrm{ref}})} & d > 0
        \end{cases}

    其中 :math:`d_{\mathrm{ref}}` 为**固定的理论/约定上界**（默认 ``1.0``），**不用**当前样本的
    :math:`\max(d)`，避免映射曲线随帧变化，保证训练与推理侧形状一致、可复现。

    若 ``compute_Foam_Density`` 中 ``Densityfactor != 1``，单格密度尺度与 ``Densityfactor``
    成正比；``log_map_d_max`` 应取与期望密度上界一致的固定 ``d_{\mathrm{ref}}``（见
    ``compute_Foam_Density``）。
    """
    d = d.to(dtype=torch.float32)
    out = torch.zeros_like(d, dtype=torch.float32)
    alpha_t = float(alpha)
    d_ref = float(d_max_reference)
    if d_ref <= 0.0 or alpha_t < 0.0:
        return out
    # 标量分母：不依赖本帧 max(d)，推理时可完全复现
    denom = math.log1p(alpha_t * d_ref)
    if denom <= 1e-20:
        return d.clone()
    mask = d > 0
    out[mask] =(torch.log1p(d[mask] * alpha_t) / denom)
    return out


def inverse_map_gt_log_to_density(
    y: torch.Tensor,
    alpha: float,
    *,
    d_max_reference: float = 1.0,
) -> torch.Tensor:
    r"""
    :func:`map_foam_density_to_gt_log` 的逆（在正向使用的 log 分式定义上与之一致）。

    当 :math:`y>0` 时：

    .. math::

        d = \frac{(1+\alpha d_{\mathrm{ref}})^{y}-1}{\alpha}

    并裁剪到 :math:`[0,d_{\mathrm{ref}}]`。:math:`y\le 0` 时 :math:`d=0`（与正向 ``d=0\Rightarrow y=0`` 一致）。
    """
    y = y.to(dtype=torch.float32).clamp(0.0, 1.0)
    alpha_t = float(alpha)
    d_ref = float(d_max_reference)
    out = torch.zeros_like(y)
    if d_ref <= 0.0 or alpha_t <= 0.0:
        return out
    log1p_ad = math.log1p(alpha_t * d_ref)
    if log1p_ad <= 1e-20:
        return out
    exp_arg = torch.clamp(y * log1p_ad, min=-80.0, max=80.0)
    d = (torch.exp(exp_arg) - 1.0) / alpha_t
    d = torch.clamp(d, min=0.0, max=d_ref)
    d = torch.where(y <= 0.0, torch.zeros_like(d), d)
    return d


def compute_gs_Density(
    pos: torch.Tensor,
    cornerMin: Sequence[float],
    cornerMax: Sequence[float],
    gridSize: float,
) -> torch.Tensor:
    """
    对每个 GS 位置，统计其所在体素（轴对齐、边长 ``gridSize``）内的 GS 个数 ``N``，
    返回 ``1/N``，shape ``[N, 1]``。体素索引与 ``[cornerMin, cornerMax)`` 半开区间一致；
    落在盒外的点对应 **0**（不参与体素计数）。
    """
    p = pos.reshape(-1, 3).float()
    n = int(p.shape[0])
    if n == 0:
        return p.new_zeros((0, 1))

    vs = float(gridSize)
    if vs <= 0.0:
        raise ValueError("gridSize must be positive")

    nx = max(1, int(math.floor((float(cornerMax[0]) - float(cornerMin[0])) / vs + 1e-9)))
    ny = max(1, int(math.floor((float(cornerMax[1]) - float(cornerMin[1])) / vs + 1e-9)))
    nz = max(1, int(math.floor((float(cornerMax[2]) - float(cornerMin[2])) / vs + 1e-9)))

    cm = p.new_tensor(cornerMin, dtype=torch.float32).view(1, 3)
    cM = p.new_tensor(cornerMax, dtype=torch.float32).view(1, 3)
    inside = torch.all((p >= cm) & (p < cM), dim=1)

    ix = torch.floor((p[:, 0] - cm[0, 0]) / vs).long()
    iy = torch.floor((p[:, 1] - cm[0, 1]) / vs).long()
    iz = torch.floor((p[:, 2] - cm[0, 2]) / vs).long()
    lin = ix + nx * (iy + ny * iz)

    hist = p.new_zeros((nx * ny * nz,), dtype=torch.float32)
    if bool(inside.any().item()):
        lin_in = lin[inside]
        hist.scatter_add_(0, lin_in, torch.ones_like(lin_in, dtype=torch.float32))

    inv = torch.zeros((n,), dtype=torch.float32, device=p.device)
    if bool(inside.any().item()):
        cnt = hist[lin[inside]].clamp(min=1.0)
        inv[inside] = 1.0 / cnt
    return inv.unsqueeze(1)


def sample_foam_from_gt_network_output_adjustV(
    gs_pos: torch.Tensor,
    gs_vel: torch.Tensor,
    foam_gt_y: Optional[torch.Tensor],
    *,
    alpha: float,
    d_max_reference: float,
    factor: float = 1.0,
    sampleTimes: int = 2000,
    noiseThreshold: float = 0.002,
    cornerMin: Sequence[float] = (-15.0, -15.0, -15.0),
    cornerMax: Sequence[float] = (15.0, 15.0, 15.0),
    gridSize: float =  0.1,
    MaxFoamNum: float = 100.0,
    replacement:bool = False,
) -> torch.Tensor:
    if foam_gt_y is None:
        return gs_pos.new_zeros((0, 6))
    y = foam_gt_y.reshape(-1).float().clamp(0.0, 1.0)
    pos_flat = gs_pos.reshape(-1, 3)
    vel_flat = gs_vel.reshape(-1, 3)
    if y.numel() != pos_flat.shape[0] or vel_flat.shape[0] != pos_flat.shape[0]:
        return gs_pos.new_zeros((0, 6))

    d_ref = float(d_max_reference)
    d = inverse_map_gt_log_to_density(y, float(alpha), d_max_reference=d_ref)
    prob = d.clamp(0.0, 1.0)

    n_nonempty = int((prob > 0).sum().item())
    if n_nonempty == 0:
        return gs_pos.new_zeros((0, 6))

    st = int(sampleTimes)
    if st > 0:
        k = st
    else:
        k = int(round(float(prob.sum().item())*MaxFoamNum* float(factor)))
    
    weight = compute_gs_Density(pos_flat, cornerMin, cornerMax, gridSize)
    prob = prob * weight.view(-1)

    k = max(0, min(k, n_nonempty))

    if n_nonempty < k:
        replacement = True

    if k == 0:
        return gs_pos.new_zeros((0, 6))
    
    idx = torch.multinomial(prob, k, replacement=replacement)
    #print(idx.shape)
    return torch.cat([pos_flat[idx], vel_flat[idx]], dim=-1)
    



def sample_foam_from_gt_network_output(
    gs_pos: torch.Tensor,
    gs_vel: torch.Tensor,
    foam_gt_y: Optional[torch.Tensor],
    *,
    alpha: float,
    d_max_reference: float,
    factor: float = 1.0,
    sampleTimes: int = 2000,
    noiseThreshold: float = 0.002,
    MaxFoamNum: float = 100.0,
) -> torch.Tensor:
    """
    将网络 foam 输出视为 GT log 空间 ``y``，逆映射得 ``d``，``p = (d/d_ref).clamp(0,1)``，
    对小概率做 ``noiseThreshold`` 截断后，在全体高斯索引上按 ``p`` **无放回** 抽样，
    输出命中行 ``[pos | vel]``，shape ``[M, 6]``。

    - ``sampleTimes > 0``：抽样 ``min(sampleTimes, 非零概率个数)`` 次；
    - ``sampleTimes <= 0``：抽样次数为 ``round(sum(p) * factor)``，再与上式同样封顶。
    """
    if foam_gt_y is None:
        return gs_pos.new_zeros((0, 6))
    y = foam_gt_y.reshape(-1).float().clamp(0.0, 1.0)
    pos_flat = gs_pos.reshape(-1, 3)
    vel_flat = gs_vel.reshape(-1, 3)
    if y.numel() != pos_flat.shape[0] or vel_flat.shape[0] != pos_flat.shape[0]:
        return gs_pos.new_zeros((0, 6))
    d_ref = float(d_max_reference)

    #print(y.max())
    d = inverse_map_gt_log_to_density(y, float(alpha), d_max_reference=d_ref)
    if d_ref > 1e-20:
        prob = (d / d_ref).clamp(0.0, 1.0)
    else:
        prob = torch.zeros_like(d)
    
    prob = torch.where(prob < 1e-3, torch.zeros_like(prob), prob)

    n_nonempty = int((prob > 0).sum().item())
    if n_nonempty == 0:
        return gs_pos.new_zeros((0, 6))

    st = int(sampleTimes)
    #print(st)
    if st > 0:
        k = st
    else:
        k = int(round(float(prob.sum().item())*MaxFoamNum*float(factor)))
    #大场景扩大MaxFoamNum（HardCoding。BigBeach MaxFoamNum = 3000）
    k = max(0, min(k, n_nonempty))
    if k == 0:
        return gs_pos.new_zeros((0, 6))
    
    #print((prob>0).sum())
    idx = torch.multinomial(prob, k, replacement=False)
    #print(idx.shape)
    return torch.cat([pos_flat[idx], vel_flat[idx]], dim=-1)


def compute_Foam_Density(
    positions: np.ndarray,
    radius: float,
    cornerMin: Sequence[float] = (-5.0, -5.0, -5.0),
    cornerMax: Sequence[float] = (5.0, 5.0, 5.0),
    gridNum: Sequence[int] = (100, 100, 100),
    Densityfactor: float = 1,
    MaxFoamNum: float = 100.0,
    *,
    apply_gt_log_map: bool = True,
    log_map_alpha: float = 1.0,
    log_map_d_max: float = 1.0,
    verbose: bool = True,
) -> torch.Tensor:
    """
    计算泡沫三维密度场，返回 torch.FloatTensor（shape 与 np.histogramdd 一致，为 [Nx, Ny, Nz]）。

    CornerMin/CornerMax、gridNum 与原先一致；密度由 8 邻角 splat 再除以 ``MaxFoamNum`` 得到。

    新逻辑（替代原 ``histogramdd``）：
      1. 每个泡沫点的连续体素坐标上做三线性 splat，质量分配到周围 **8** 个角点体素（权重与
         到各角点的三线性权重一致，单点权重和为 1）；
      2. 对整张 ``DensityMap``：**每个体素**除以 ``MaxFoamNum``（>0），再乘以
         ``Densityfactor``；**不**再除以全图密度总和。

    若 ``apply_gt_log_map=True``（默认），对缩放后的密度应用 :func:`map_foam_density_to_gt_log`，
    作为训练 GT；``log_map_d_max`` 为映射分母中的固定 :math:`d_{\mathrm{ref}}`（默认 ``1.0``；
    请按实际密度上界调整，例如与 ``Densityfactor``、泡沫点数上界联合考虑）。
    设为 False 可得到原始归一化密度（如可视化脚本）。
    """
    # 空输入直接返回零张量

    if verbose:
        print(
            f"compute_Foam_Density: positions: {positions.shape} radius: {radius} "
            f"cornerMin: {cornerMin} cornerMax: {cornerMax} gridNum: {gridNum} "
            f"Densityfactor: {Densityfactor} MaxFoamNum: {MaxFoamNum}"
        )
    if positions is None:
        g = np.asarray(gridNum, dtype=np.int32)
        if g.size == 1:
            g = np.repeat(g[0], 3)
        return torch.zeros(
            (int(g[0]), int(g[1]), int(g[2])),
            dtype=torch.float32,
        )

    pos = np.asarray(positions, dtype=np.float32)
    if pos.ndim != 2 or pos.shape[1] != 3 or pos.shape[0] == 0:
        if verbose:
            print(f"compute_Foam_Density: pos: {pos.shape} is not valid")
        g = np.asarray(gridNum, dtype=np.int32)
        if g.size == 1:
            g = np.repeat(g[0], 3)
        return torch.zeros(
            (int(g[0]), int(g[1]), int(g[2])),
            dtype=torch.float32,
        )

    # CornerMin/Max 标量或三维向量均可
    if isinstance(cornerMin, (float, int)):
        cornerMin = np.array([cornerMin] * 3, dtype=np.float32)
    else:
        cornerMin = np.asarray(cornerMin, dtype=np.float32)
    if isinstance(cornerMax, (float, int)):
        cornerMax = np.array([cornerMax] * 3, dtype=np.float32)
    else:
        cornerMax = np.asarray(cornerMax, dtype=np.float32)

    # GridNum 允许标量或长度为 3 的序列
    g = np.asarray(gridNum, dtype=np.int32)
    if g.size == 1:
        g = np.repeat(g[0], 3)

    SceneSize = cornerMax - cornerMin
    GridSize = SceneSize / g.astype(np.float32)

    # 过滤掉范围外的点
    mask = np.all((pos >= cornerMin) & (pos < cornerMax), axis=1)
    valid_pos = pos[mask]

    if verbose:
        print(f"compute_Foam_Density: valid_pos: {valid_pos.shape}")

    # ----- 原 histogramdd + max_num clip 逻辑（保留备查）-----
    # max_num = float((GridSize[0] / (2.0 * radius)) ** 3)
    # if verbose:
    #     print(f"compute_Foam_Density: max_num: {max_num}")
    # grid_range = [(float(cornerMin[i]), float(cornerMax[i])) for i in range(3)]
    # density_np, _ = np.histogramdd(
    #     valid_pos,
    #     bins=(int(g[0]), int(g[1]), int(g[2])),
    #     range=grid_range,
    # )
    # density_np = np.clip(density_np, 0, max_num).astype(np.float32)
    # density_np = Densityfactor * density_np / max_num
    # ----------------------------------------------------------

    nx, ny, nz = int(g[0]), int(g[1]), int(g[2])
    density_np = np.zeros((nx, ny, nz), dtype=np.float32)
    if valid_pos.shape[0] > 0:
        t = (valid_pos - cornerMin) / GridSize.astype(np.float32)
        t_hi = np.asarray([nx, ny, nz], dtype=np.float32) - 1e-4
        t = np.clip(t, 0.0, t_hi)
        tx, ty, tz = t[:, 0], t[:, 1], t[:, 2]
        ix = np.floor(tx).astype(np.int64)
        iy = np.floor(ty).astype(np.int64)
        iz = np.floor(tz).astype(np.int64)
        ix = np.clip(ix, 0, nx - 1)
        iy = np.clip(iy, 0, ny - 1)
        iz = np.clip(iz, 0, nz - 1)
        fx = tx - ix.astype(np.float32)
        fy = ty - iy.astype(np.float32)
        fz = tz - iz.astype(np.float32)
        ix1 = np.clip(ix + 1, 0, nx - 1)
        iy1 = np.clip(iy + 1, 0, ny - 1)
        iz1 = np.clip(iz + 1, 0, nz - 1)
        wx = np.stack([1.0 - fx, fx], axis=-1)
        wy = np.stack([1.0 - fy, fy], axis=-1)
        wz = np.stack([1.0 - fz, fz], axis=-1)
        ix2 = np.stack([ix, ix1], axis=-1)
        iy2 = np.stack([iy, iy1], axis=-1)
        iz2 = np.stack([iz, iz1], axis=-1)
        for a in range(2):
            for b in range(2):
                for c in range(2):
                    w = wx[:, a] * wy[:, b] * wz[:, c]
                    np.add.at(
                        density_np,
                        (ix2[:, a], iy2[:, b], iz2[:, c]),
                        w.astype(np.float32),
                    )
        mfn = float(MaxFoamNum)
        if mfn > 0.0:
            density_np = (density_np / mfn) * float(Densityfactor)
        else:
            density_np.fill(0.0)

    density_t = torch.from_numpy(density_np)
    if apply_gt_log_map:
        density_t = map_foam_density_to_gt_log(
            density_t,
            alpha=log_map_alpha,
            d_max_reference=float(log_map_d_max),
        )
    return density_t


def pair_foam_density_mae_on_union_support(
    positions_pred: np.ndarray,
    positions_gt: np.ndarray,
    radius: float,
    *,
    cornerMin: Sequence[float] = NEWFOAM_DENSITY_CORNER_MIN,
    cornerMax: Sequence[float] = NEWFOAM_DENSITY_CORNER_MAX,
    gridNum: Union[int, Sequence[int]] = NEWFOAM_DENSITY_GRID_NUM[0],
    Densityfactor: float = 1.0,
    MaxFoamNum: float = 100.0,
    log_map_alpha: float = 1.0,
    log_map_d_max: float = 1.0,
) -> Tuple[float, int]:
    """
    对两套泡沫点云分别做与数据集 ``newFoamDensity`` 相同的体素密度缩放（见
    ``dataset._ensure_newfoam_density``：固定 ``cornerMin/Max``、``gridNum``、``MaxFoamNum``、
    ``apply_gt_log_map=False``），仅在 ``(d_\mathrm{pred}>0) \vee (d_\mathrm{gt}>0)`` 的体素上取
    ``|d_\mathrm{pred}-d_\mathrm{gt}|`` 的平均。

    默认 ``cornerMin=(-5,-5,-5)``, ``cornerMax=(5,5,5)``, ``gridNum=100``（与工程内 GT 一致）。

    Returns:
        (mae, voxel_count)；无有效体素时 ``(nan, 0)``。
    """
    g = gridNum
    if isinstance(g, int):
        grid_num_t: Sequence[int] = (g, g, g)
    else:
        grid_num_t = g

    d_pred = compute_Foam_Density(
        positions_pred,
        radius,
        cornerMin,
        cornerMax,
        grid_num_t,
        Densityfactor,
        MaxFoamNum,
        apply_gt_log_map=False,
        log_map_alpha=float(log_map_alpha),
        log_map_d_max=float(log_map_d_max),
        verbose=False,
    )
    d_gt = compute_Foam_Density(
        positions_gt,
        radius,
        cornerMin,
        cornerMax,
        grid_num_t,
        Densityfactor,
        MaxFoamNum,
        apply_gt_log_map=False,
        log_map_alpha=float(log_map_alpha),
        log_map_d_max=float(log_map_d_max),
        verbose=False,
    )
    d_pred = d_pred.float()
    d_gt = d_gt.float()
    mask = (d_pred > 0) | (d_gt > 0)
    n = int(mask.sum().item())
    if n == 0:
        return float("nan"), 0
    mae = (d_pred - d_gt).abs()[mask].mean().item()
    return float(mae), n

