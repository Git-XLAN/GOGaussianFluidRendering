# -*- coding: utf-8 -*-
"""
体素/图像张量上的空间滤波（与 ``RealTimeWater`` 等 demo 共用）。

- ``gaussian_filter_image``：**图像/特征图** ``(W,H,K)`` / ``(H,W,K)``，仅 2D 空间高斯、通道独立；
  可选 ``exclude_zero``；``iterations`` 为同一核/σ 下的滤波轮次。
- ``gaussian_filter_3d``：**真体数据**：``(W, H, K)`` 三维空间体，三轴都会平滑（会沿 ``K`` 混合）。
"""

from __future__ import annotations

from typing import Literal, Optional, Tuple, Union

import torch
import torch.nn.functional as F

Int2 = Union[int, Tuple[int, int]]
Int3 = Union[int, Tuple[int, int, int]]
Float2 = Union[float, Tuple[float, float]]
Float3 = Union[float, Tuple[float, float, float]]


def _as_int2(v: Union[int, Tuple[int, int]], name: str) -> Tuple[int, int]:
    if isinstance(v, int):
        return (v, v)
    if isinstance(v, tuple) and len(v) == 2:
        return int(v[0]), int(v[1])
    raise TypeError(f"{name} must be int or tuple[int, int]")


def _as_int3(v: Union[int, Tuple[int, int, int]], name: str) -> Tuple[int, int, int]:
    if isinstance(v, int):
        return (v, v, v)
    if isinstance(v, tuple) and len(v) == 3:
        return int(v[0]), int(v[1]), int(v[2])
    raise TypeError(f"{name} must be int or tuple[int, int, int]")


def _to_odd_kernel(k: int) -> int:
    """可分离高斯用对称 replicate 填充时需要奇数核；偶数统一为向上取到下一个奇数。"""
    if k <= 1:
        return k
    return k if (k % 2 == 1) else k + 1


def _default_sigma(kernel_size: int) -> float:
    if kernel_size <= 1:
        return 1.0
    # 约 99% 权重落在核半宽内
    return float(kernel_size) / 6.0


def _gaussian_kernel_1d(
    kernel_size: int,
    sigma: float,
    *,
    device: torch.device,
    dtype: torch.dtype,
) -> torch.Tensor:
    if kernel_size <= 1:
        return torch.ones(1, device=device, dtype=dtype)
    t = torch.arange(kernel_size, device=device, dtype=dtype)
    t = t - (kernel_size - 1) / 2.0
    g = torch.exp(-(t * t) / (2.0 * sigma * sigma))
    return g / g.sum()


def _x3d_to_vol(x3d: torch.Tensor, spatial_layout: Literal["whc", "hwc"]) -> torch.Tensor:
    if spatial_layout == "whc":
        return x3d.permute(2, 1, 0).unsqueeze(0)
    if spatial_layout == "hwc":
        return x3d.permute(2, 0, 1).unsqueeze(0)
    raise ValueError('spatial_layout must be "whc" or "hwc"')


def _vol_to_x3d(vol: torch.Tensor, spatial_layout: Literal["whc", "hwc"]) -> torch.Tensor:
    v = vol.squeeze(0)
    if spatial_layout == "whc":
        return v.permute(2, 1, 0).contiguous()
    return v.permute(1, 2, 0).contiguous()


def _separable_gaussian_blur_vol(
    vol: torch.Tensor,
    k0: int,
    k1: int,
    s0: float,
    s1: float,
    spatial_layout: Literal["whc", "hwc"],
) -> torch.Tensor:
    """``vol``: ``(1, C, H, W)``；布局与 :func:`gaussian_filter_image` 一致。"""
    comp_dtype = vol.dtype
    dev = vol.device
    c_chan = int(vol.shape[1])

    if spatial_layout == "whc":
        g_w = _gaussian_kernel_1d(k0, s0, device=dev, dtype=comp_dtype).view(1, 1, 1, k0).repeat(
            c_chan, 1, 1, 1
        )
        vol = F.pad(vol, (k0 // 2, k0 // 2, 0, 0), mode="replicate")
        vol = F.conv2d(vol, g_w, groups=c_chan)
        g_h = _gaussian_kernel_1d(k1, s1, device=dev, dtype=comp_dtype).view(1, 1, k1, 1).repeat(
            c_chan, 1, 1, 1
        )
        vol = F.pad(vol, (0, 0, k1 // 2, k1 // 2), mode="replicate")
        vol = F.conv2d(vol, g_h, groups=c_chan)
    else:
        g_h = _gaussian_kernel_1d(k0, s0, device=dev, dtype=comp_dtype).view(1, 1, k0, 1).repeat(
            c_chan, 1, 1, 1
        )
        vol = F.pad(vol, (0, 0, k0 // 2, k0 // 2), mode="replicate")
        vol = F.conv2d(vol, g_h, groups=c_chan)
        g_w = _gaussian_kernel_1d(k1, s1, device=dev, dtype=comp_dtype).view(1, 1, 1, k1).repeat(
            c_chan, 1, 1, 1
        )
        vol = F.pad(vol, (k1 // 2, k1 // 2, 0, 0), mode="replicate")
        vol = F.conv2d(vol, g_w, groups=c_chan)
    return vol


def _one_pass_gaussian_conv3d(
    vol: torch.Tensor,
    kw: int,
    kh: int,
    kk: int,
    sw: float,
    sh: float,
    sk: float,
) -> torch.Tensor:
    """对 ``(N=1,C=1,D,H,W)`` 做一次可分离 3D 高斯（与 :func:`gaussian_filter_3d` 一致）。"""
    comp_dtype = vol.dtype
    gw = _gaussian_kernel_1d(kw, sw, device=vol.device, dtype=comp_dtype).view(1, 1, kw, 1, 1)
    vol = F.pad(vol, (0, 0, 0, 0, kw // 2, kw // 2), mode="replicate")
    vol = F.conv3d(vol, gw)
    gh = _gaussian_kernel_1d(kh, sh, device=vol.device, dtype=comp_dtype).view(1, 1, 1, kh, 1)
    vol = F.pad(vol, (0, 0, kh // 2, kh // 2, 0, 0), mode="replicate")
    vol = F.conv3d(vol, gh)
    gk = _gaussian_kernel_1d(kk, sk, device=vol.device, dtype=comp_dtype).view(1, 1, 1, 1, kk)
    vol = F.pad(vol, (kk // 2, kk // 2, 0, 0, 0, 0), mode="replicate")
    vol = F.conv3d(vol, gk)
    return vol


def gaussian_filter_image(
    x: torch.Tensor,
    kernel_size: Int2 = 5,
    sigma: Optional[Float2] = None,
    spatial_layout: Literal["whc", "hwc"] = "whc",
    *,
    exclude_zero: bool = False,
    zero_eps: float = 1e-12,
    iterations: int = 1,
) -> torch.Tensor:
    """
    对 **图像空间** 做 2D 可分离高斯：前两维为空间分辨率，最后一维为通道 ``K``，**各通道独立**，
    不在通道之间混合。

    Parameters
    ----------
    x :
        - ``spatial_layout="whc"``：``(W, H, K)``，与 ``x[w, h, c]`` 一致。
        - ``spatial_layout="hwc"``：``(H, W, K)``，与常见 ``H×W`` 图像 + ``K`` 通道一致。
    kernel_size :
        沿 **输入前两维** 的核大小：标量表示两维相同，或 ``(沿 dim0, 沿 dim1)``。
        大于 1 的 **偶数** 会改为 **下一个奇数**（与对称边界填充一致；如 Falcor 返回 2 时按 3 处理）。
    sigma :
        各空间维标准差；``None`` 时对应该维 ``kernel_size / 6``。标量或二元组。
    spatial_layout :
        ``"whc"`` 或 ``"hwc"``，见 ``x``。
    exclude_zero :
        为 True 时：按像素忽略「全通道近似为 0」的格点（``sum_c |x| > zero_eps`` 为有效）。
        有效区为归一化掩膜高斯 ``blur(x·mask)/blur(mask)``；无效区输出为 0，且无效邻居不参与加权。
    zero_eps :
        与 ``exclude_zero`` 联用的有效像素阈值。
    iterations :
        使用当前 ``kernel_size`` / ``sigma`` 连续做 **完整 2D 可分离高斯** 的次数（≥1）。
        ``exclude_zero=True`` 时，``valid`` 掩膜只在 **第一轮前** 由输入 ``x`` 决定，每轮结束后再乘该掩膜。

    Returns
    -------
    与 ``x`` 相同 shape / layout；dtype 规则同 :func:`gaussian_filter_3d`。

    Note
    ----
    若把 ``(W, H, K)`` 误用 :func:`gaussian_filter_3d`，第三维会被当作深度并 **跨通道平滑**，
    一般不适用于图像/法线等多通道平面数据。
    """
    if x.ndim != 3:
        raise ValueError(f"gaussian_filter_image expects 3D tensor; got shape {tuple(x.shape)}")

    it = int(iterations)
    if it < 1:
        raise ValueError("iterations must be >= 1")

    k0, k1 = _as_int2(kernel_size, "kernel_size")
    k0, k1 = _to_odd_kernel(k0), _to_odd_kernel(k1)
    for k in (k0, k1):
        if k < 1:
            raise ValueError("kernel_size must be >= 1")

    if k0 == k1 == 1:
        return x.clone()

    c = int(x.shape[2])
    if c < 1:
        raise ValueError("channel dimension K must be >= 1")

    if sigma is None:
        s0, s1 = _default_sigma(k0), _default_sigma(k1)
    elif isinstance(sigma, (int, float)):
        s0 = s1 = float(sigma)
    else:
        s0, s1 = float(sigma[0]), float(sigma[1])
    if s0 <= 0 or s1 <= 0:
        raise ValueError("sigma must be positive")

    orig_dtype = x.dtype
    if torch.is_floating_point(x):
        comp_dtype = torch.float64 if x.dtype == torch.float64 else torch.float32
    else:
        comp_dtype = torch.float32

    x_work = x.to(dtype=comp_dtype)
    tiny = 1e-18 if comp_dtype == torch.float64 else 1e-12

    if exclude_zero:
        if zero_eps < 0:
            raise ValueError("zero_eps must be non-negative")
        valid = (x_work.abs().sum(dim=-1, keepdim=True) > zero_eps).to(dtype=comp_dtype)
        work = x_work
        for _ in range(it):
            vol_m = _x3d_to_vol(work * valid, spatial_layout)
            vol_v = _x3d_to_vol(valid, spatial_layout)
            numer = _separable_gaussian_blur_vol(vol_m, k0, k1, s0, s1, spatial_layout)
            denom = _separable_gaussian_blur_vol(vol_v, k0, k1, s0, s1, spatial_layout)
            work = _vol_to_x3d(numer / denom.clamp_min(tiny), spatial_layout) * valid
        out = work
    else:
        work = x_work
        for _ in range(it):
            vol = _x3d_to_vol(work, spatial_layout)
            vol = _separable_gaussian_blur_vol(vol, k0, k1, s0, s1, spatial_layout)
            work = _vol_to_x3d(vol, spatial_layout)
        out = work

    if torch.is_floating_point(x):
        return out.to(orig_dtype)
    return out


def gaussian_filter_3d(
    x: torch.Tensor,
    kernel_size: Int3 = 5,
    sigma: Optional[Float3] = None,
    *,
    iterations: int = 1,
) -> torch.Tensor:
    """
    对形状 ``(W, H, K)`` 的体积做三维高斯滤波（可分离卷积）。

    与 PyTorch ``conv3d`` 的布局一致：内部将 ``x`` 视为 ``(N=1, C=1, D=W, H=H, W=K)``，
    即在最后一个维度对应用户的 ``K``。

    Parameters
    ----------
    x :
        ``(W, H, K)``。非浮点类型按 float32 计算，返回 ``float32``；浮点输入保持原 dtype（``float64`` 用双精度累加）。
    kernel_size :
        各轴核边长；单个 ``int`` 表示三轴相同，或 ``(kw, kh, kk)``。
        大于 1 的偶数会改为下一个奇数。
    sigma :
        高斯标准差；``None`` 时各轴为 ``kernel_size_axis / 6``。可给标量或三元组。
    iterations :
        同一核/Sigma 下完整 3D 可分离高斯的次数（≥1）。

    Returns
    -------
    torch.Tensor
        与 ``x`` 同 shape；浮点 dtype 与输入一致（内部 ``float32`` / ``float64`` 累加），
        整数/布尔输入得到 ``float32``。
    """
    if x.ndim != 3:
        raise ValueError(f"gaussian_filter_3d expects a (W,H,K) tensor; got shape {tuple(x.shape)}")

    it = int(iterations)
    if it < 1:
        raise ValueError("iterations must be >= 1")

    kw, kh, kk = _as_int3(kernel_size, "kernel_size")
    kw, kh, kk = _to_odd_kernel(kw), _to_odd_kernel(kh), _to_odd_kernel(kk)
    for k in (kw, kh, kk):
        if k < 1:
            raise ValueError("kernel_size components must be >= 1")

    if kw == kh == kk == 1:
        return x.clone()

    if sigma is None:
        sw, sh, sk = _default_sigma(kw), _default_sigma(kh), _default_sigma(kk)
    elif isinstance(sigma, (int, float)):
        sw = sh = sk = float(sigma)
    else:
        sw, sh, sk = float(sigma[0]), float(sigma[1]), float(sigma[2])
    if sw <= 0 or sh <= 0 or sk <= 0:
        raise ValueError("sigma must be positive")

    orig_dtype = x.dtype
    if torch.is_floating_point(x):
        comp_dtype = torch.float64 if x.dtype == torch.float64 else torch.float32
    else:
        comp_dtype = torch.float32

    vol = x.to(dtype=comp_dtype).unsqueeze(0).unsqueeze(0)
    for _ in range(it):
        vol = _one_pass_gaussian_conv3d(vol, kw, kh, kk, sw, sh, sk)

    out = vol.squeeze(0).squeeze(0)
    if torch.is_floating_point(x):
        return out.to(orig_dtype)
    return out
