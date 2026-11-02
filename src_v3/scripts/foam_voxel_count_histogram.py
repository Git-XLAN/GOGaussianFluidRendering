# -*- coding: utf-8 -*-
"""
训练集 newFoam：用 ``compute_Foam_Density``（8 角 splat + 全图归一化）对**每一帧**计算体素密度
（无粒子时为全零场），并按 **场景 × 帧 × voxel-size** 各导出两张图（中心正交切片、非零体素 Density 一维直方图）。
未指定 ``--train-scenes`` 时处理数据根下全部场景；``--train-max-frames`` 限制每场景参与计算的帧数上限。

数据加载与 ``train_foam_density_stats`` 一致：``build_frame_index`` +
``_resolve_newfoam_like_dataset``（foam / Newfoam VTK）。

运行示例::

    python -m src_v3.scripts.foam_voxel_count_histogram --train-root F:/DataSet/TrainData \\
        --voxel-size 0.2 0.1 0.05

    python -m src_v3.scripts.foam_voxel_count_histogram --train-root F:/DataSet/TrainData \\
        --train-scenes WaterFall DoubleDamBreakSPH --voxel-size 0.1 --train-max-frames 200
"""

from __future__ import annotations

import argparse
import os
import re
import sys
from pathlib import Path
from typing import Any, Dict, Optional, Sequence, Tuple

import numpy as np

_REPO_ROOT = Path(__file__).resolve().parents[2]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

_LOG = "[foam_voxel_count_histogram]"


def _safe_scene_tag(scene_name: str) -> str:
    """文件名用场景名片段（去掉 Windows 非法字符与空白）。"""
    s = re.sub(r'[<>:"/\\|?*]+', "_", str(scene_name).strip())
    s = re.sub(r"\s+", "_", s)
    return s or "scene"


def _set_matplotlib_cjk_font() -> bool:
    """
    尝试将 Matplotlib 设为可显示中文的字体（Windows 下优先从 Fonts 目录加载 .ttc/.ttf）。
    返回是否认为已成功选中中文字体（失败时应用英文标签）。
    """
    import matplotlib.pyplot as plt
    from matplotlib import font_manager

    if sys.platform == "win32":
        windir = os.environ.get("WINDIR", r"C:\Windows")
        fonts_dir = os.path.join(windir, "Fonts")
        for fn in ("msyh.ttc", "msyhbd.ttc", "simhei.ttf", "simsun.ttc", "msyh.ttf"):
            path = os.path.join(fonts_dir, fn)
            if os.path.isfile(path):
                try:
                    font_manager.fontManager.addfont(path)
                    prop = font_manager.FontProperties(fname=path)
                    name = prop.get_name()
                    plt.rcParams["font.family"] = name
                    plt.rcParams["font.sans-serif"] = [name]
                    return True
                except Exception:
                    continue

    preferred = (
        "Microsoft YaHei",
        "Microsoft YaHei UI",
        "SimHei",
        "SimSun",
        "Noto Sans CJK SC",
        "Source Han Sans SC",
        "WenQuanYi Micro Hei",
        "PingFang SC",
        "Arial Unicode MS",
    )
    available = {f.name for f in font_manager.fontManager.ttflist}
    for p in preferred:
        if p in available:
            plt.rcParams["font.sans-serif"] = [p]
            plt.rcParams["font.family"] = "sans-serif"
            return True
    for p in preferred:
        for n in available:
            if len(p) >= 4 and (p in n or n.startswith(p.split()[0])):
                plt.rcParams["font.sans-serif"] = [n]
                plt.rcParams["font.family"] = "sans-serif"
                return True

    return False


def _init_matplotlib_backend() -> None:
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    plt.rcParams["axes.unicode_minus"] = False


def _grid_num_from_voxel_size(
    corner_min: Sequence[float],
    corner_max: Sequence[float],
    voxel_size: float,
) -> Tuple[int, int, int]:
    """各轴独立：gridNum_i = round((max_i - min_i) / voxel_size)，至少为 1。"""
    cmin = np.asarray(corner_min, dtype=np.float64)
    cmax = np.asarray(corner_max, dtype=np.float64)
    scene = cmax - cmin
    vs = float(voxel_size)
    if vs <= 0:
        raise ValueError("voxel_size 必须为正数")
    return tuple(max(1, int(round(scene[i] / vs))) for i in range(3))


def _resolve_newfoam_like_dataset(paths: Any) -> Dict[str, Any]:
    from src_v3.data.dataset import (
        _default_radius_from_scene,
        _foam_to_sample_dict,
        _load_newfoam_from_foam,
    )
    from src_v3.data.vtk_loader import load_foam_vtk

    default_r = _default_radius_from_scene(paths.scene)
    foam = None
    if paths.foam_path:
        foam_raw = load_foam_vtk(paths.foam_path, default_radius=default_r)
        if foam_raw is not None:
            foam = _foam_to_sample_dict(foam_raw, default_r)

    newfoam = None
    if paths.newfoam_path:
        new_raw = load_foam_vtk(paths.newfoam_path, default_radius=default_r)
        if new_raw is not None:
            newfoam = _foam_to_sample_dict(new_raw, default_r)
    elif foam is not None:
        newfoam = _load_newfoam_from_foam(foam)

    if newfoam is None:
        newfoam = {
            "positions": np.zeros((0, 3), dtype=np.float32),
            "vel": None,
            "lifetime": None,
            "id": None,
            "radius": float(default_r),
            "num_particles": 0,
            "born": None,
        }
    return newfoam


def _safe_frame_tag(frame_id: int) -> str:
    """文件名用帧号（固定宽度便于排序）。"""
    return f"{int(frame_id):06d}"


def _plot_density_map_spatial_slices(
    fig,
    density: np.ndarray,
    *,
    corner_min: Tuple[float, float, float],
    corner_max: Tuple[float, float, float],
    title: str,
    subtitle: str,
    labels_zh: bool,
    scatter_max_points: int = 40000,
) -> None:
    """
    非零支撑上的可视化：
      - 三视图：先取 density>eps 的体素 AABB，加边距后裁剪；切片取过 AABB 中心（细网格时不再用整域中心）。
      - 第四块：仅非零体素中心的三维散点（过多时随机子采样），避免大网格整域切片「看不见」泡沫。
    """
    from matplotlib import gridspec

    d = np.asarray(density, dtype=np.float64)
    nx, ny, nz = d.shape
    cm = np.asarray(corner_min, dtype=np.float64)
    cx = np.asarray(corner_max, dtype=np.float64)
    dx = (cx[0] - cm[0]) / max(nx, 1)
    dy = (cx[1] - cm[1]) / max(ny, 1)
    dz = (cx[2] - cm[2]) / max(nz, 1)

    dmax = float(d.max())
    eps = max(dmax * 1e-12, 1e-20)
    mask_nz = d > eps

    gs = gridspec.GridSpec(2, 3, figure=fig, height_ratios=[1.0, 1.05], hspace=0.35, wspace=0.32)
    axes = [fig.add_subplot(gs[0, i]) for i in range(3)]
    ax3d = fig.add_subplot(gs[1, :], projection="3d")
    fig.subplots_adjust(top=0.88)

    if labels_zh:
        cbl = "Density"
        cb_empty = "全零密度"
        note_crop = "裁剪至非零 AABB"
        sc_title = f"非零体素 3D（≤{scatter_max_points} 点）"
    else:
        cbl = "Density"
        cb_empty = "All-zero density"
        note_crop = "cropped to nonzero AABB"
        sc_title = f"Non-zero voxels 3D (≤{scatter_max_points} pts)"

    if not np.any(mask_nz):
        for ax in axes:
            ax.set_axis_off()
            ax.text(0.5, 0.5, cb_empty, ha="center", va="center", transform=ax.transAxes)
        ax3d.set_axis_off()
        ax3d.set_title(cb_empty)
        fig.suptitle(title, fontsize=11)
        fig.text(0.5, 0.94, subtitle, ha="center", fontsize=9, color="dimgray")
        return

    ii, jj, kk = np.where(mask_nz)
    i0, i1 = int(ii.min()), int(ii.max())
    j0, j1 = int(jj.min()), int(jj.max())
    k0, k1 = int(kk.min()), int(kk.max())
    pad = max(2, int(round(0.06 * max(i1 - i0, j1 - j0, k1 - k0, 1))))

    def clip_span(lo: int, hi: int, n: int, p: int) -> Tuple[int, int]:
        a = max(0, lo - p)
        b = min(n - 1, hi + p)
        if a > b:
            return 0, max(0, n - 1)
        return a, b

    x0, x1 = clip_span(i0, i1, nx, pad)
    y0, y1 = clip_span(j0, j1, ny, pad)
    z0, z1 = clip_span(k0, k1, nz, pad)

    ix = int(np.clip((i0 + i1) // 2, 0, nx - 1))
    iy = int(np.clip((j0 + j1) // 2, 0, ny - 1))
    iz = int(np.clip((k0 + k1) // 2, 0, nz - 1))

    pos = d[mask_nz]
    vmax = float(np.percentile(pos, 99.0)) if pos.size else 1.0
    if vmax <= 0.0:
        vmax = float(pos.max()) if pos.size else 1.0
    vmin = 0.0

    y_lo = float(cm[1] + y0 * dy)
    y_hi = float(cm[1] + (y1 + 1) * dy)
    z_lo = float(cm[2] + z0 * dz)
    z_hi = float(cm[2] + (z1 + 1) * dz)
    x_lo = float(cm[0] + x0 * dx)
    x_hi = float(cm[0] + (x1 + 1) * dx)

    xw_c = float(cm[0] + (ix + 0.5) * dx)
    yw_c = float(cm[1] + (iy + 0.5) * dy)
    zw_c = float(cm[2] + (iz + 0.5) * dz)

    if labels_zh:
        t_x = f"X={xw_c:.4g} · {note_crop}"
        t_y = f"Y={yw_c:.4g} · {note_crop}"
        t_z = f"Z={zw_c:.4g} · {note_crop}"
    else:
        t_x = f"X={xw_c:.4g} · {note_crop}"
        t_y = f"Y={yw_c:.4g} · {note_crop}"
        t_z = f"Z={zw_c:.4g} · {note_crop}"

    im0 = axes[0].imshow(
        d[ix, y0 : y1 + 1, z0 : z1 + 1],
        origin="lower",
        extent=(y_lo, y_hi, z_lo, z_hi),
        aspect="auto",
        vmin=vmin,
        vmax=vmax,
        cmap="magma",
    )
    axes[0].set_xlabel("Y")
    axes[0].set_ylabel("Z")
    axes[0].set_title(t_x)

    im1 = axes[1].imshow(
        d[x0 : x1 + 1, iy, z0 : z1 + 1],
        origin="lower",
        extent=(x_lo, x_hi, z_lo, z_hi),
        aspect="auto",
        vmin=vmin,
        vmax=vmax,
        cmap="magma",
    )
    axes[1].set_xlabel("X")
    axes[1].set_ylabel("Z")
    axes[1].set_title(t_y)

    im2 = axes[2].imshow(
        d[x0 : x1 + 1, y0 : y1 + 1, iz].T,
        origin="lower",
        extent=(x_lo, x_hi, y_lo, y_hi),
        aspect="auto",
        vmin=vmin,
        vmax=vmax,
        cmap="magma",
    )
    axes[2].set_xlabel("X")
    axes[2].set_ylabel("Y")
    axes[2].set_title(t_z)

    cbar = fig.colorbar(im2, ax=axes, shrink=0.82, pad=0.02)
    cbar.set_label(cbl)

    n_pts = int(mask_nz.sum())
    if n_pts > scatter_max_points:
        rng = np.random.default_rng(0)
        flat_idx = np.flatnonzero(mask_nz.ravel())
        sel = rng.choice(flat_idx, size=scatter_max_points, replace=False)
        i_s = sel // (ny * nz)
        rem = sel % (ny * nz)
        j_s = rem // nz
        k_s = rem % nz
    else:
        i_s, j_s, k_s = ii, jj, kk

    vals = d[i_s, j_s, k_s]
    xw = cm[0] + (i_s.astype(np.float64) + 0.5) * dx
    yw = cm[1] + (j_s.astype(np.float64) + 0.5) * dy
    zw = cm[2] + (k_s.astype(np.float64) + 0.5) * dz
    ax3d.scatter(
        xw,
        yw,
        zw,
        c=vals,
        cmap="magma",
        s=max(2.0, min(12.0, 2000.0 / max(n_pts, 1) ** (1.0 / 3.0))),
        alpha=0.55,
        vmin=vmin,
        vmax=vmax,
        edgecolors="none",
    )
    mx0 = float(cm[0] + x0 * dx)
    mx1 = float(cm[0] + (x1 + 1) * dx)
    my0 = float(cm[1] + y0 * dy)
    my1 = float(cm[1] + (y1 + 1) * dy)
    mz0 = float(cm[2] + z0 * dz)
    mz1 = float(cm[2] + (z1 + 1) * dz)
    ax3d.set_xlim(mx0, mx1)
    ax3d.set_ylim(my0, my1)
    ax3d.set_zlim(mz0, mz1)
    ax3d.set_xlabel("X")
    ax3d.set_ylabel("Y")
    ax3d.set_zlabel("Z")
    ax3d.set_title(sc_title)
    try:
        ax3d.set_box_aspect((mx1 - mx0, my1 - my0, mz1 - mz0))
    except Exception:
        pass

    fig.suptitle(title, fontsize=11)
    fig.text(0.5, 0.94, subtitle, ha="center", fontsize=9, color="dimgray")


def _plot_density_map_nonzero_1d(
    fig,
    density: np.ndarray,
    *,
    title: str,
    subtitle: str,
    labels_zh: bool,
    bins: int = 80,
) -> None:
    """非零体素上的 Density 拉直为一维后画直方图（可选对数纵轴）。"""
    d = np.asarray(density, dtype=np.float64).ravel()
    nz = d[d > 0]
    ax = fig.add_subplot(1, 1, 1)
    if nz.size == 0:
        msg = "无非零体素" if labels_zh else "No non-zero voxels"
        ax.text(0.5, 0.5, msg, ha="center", va="center", transform=ax.transAxes)
        ax.set_title(title)
        fig.text(0.5, 0.94, subtitle, ha="center", fontsize=9, color="dimgray")
        return

    lo, hi = float(nz.min()), float(np.percentile(nz, 99.5))
    if hi <= lo:
        hi = lo + 1e-12
    edges = np.linspace(lo, hi, int(max(2, bins)) + 1)
    counts, _, _ = ax.hist(
        nz,
        bins=edges,
        color="teal",
        edgecolor="#0a3d3d",
        linewidth=0.6,
        alpha=0.88,
    )
    ax.set_title(title)
    if labels_zh:
        ax.set_xlabel("Density（非零体素）")
        ax.set_ylabel("体素个数")
    else:
        ax.set_xlabel("Density (non-zero voxels)")
        ax.set_ylabel("# voxels")
    ax.grid(True, alpha=0.35, axis="y")
    fig.text(0.5, 0.94, subtitle, ha="center", fontsize=9, color="dimgray")

    if counts.size and np.max(counts) > 0:
        pos = counts > 0
        if pos.any():
            ratio = float(np.max(counts) / np.min(counts[pos]))
            if ratio > 80.0:
                ax.set_yscale("log")
                if labels_zh:
                    ax.set_ylabel("体素个数（对数）")
                else:
                    ax.set_ylabel("# voxels (log)")


def _save_density_map_figures(
    density: np.ndarray,
    *,
    corner_min: Tuple[float, float, float],
    corner_max: Tuple[float, float, float],
    grid_num: Tuple[int, int, int],
    voxel_size: float,
    out_dir: Path,
    labels_zh: bool,
    safe_vs: str,
    safe_scene: str,
    safe_frame: str,
    frame_label: str,
    radius: float,
) -> None:
    import matplotlib.pyplot as plt

    out_dir = Path(out_dir).resolve()
    out_dir.mkdir(parents=True, exist_ok=True)

    if labels_zh:
        st = (
            f"compute_Foam_Density（8 角 splat + 全图归一化×Densityfactor）· "
            f"grid={grid_num} voxel_size≈{voxel_size} radius={radius:.5g} 帧≈{frame_label}"
        )
        t_sp = "密度场：中心切片（每体素 Density）"
        t_1d = "非零体素 Density 分布（1D 直方图）"
    else:
        st = (
            f"compute_Foam_Density (8-corner splat + global norm) · "
            f"grid={grid_num} voxel_size≈{voxel_size} radius={radius:.5g} frame≈{frame_label}"
        )
        t_sp = "Density field: mid-grid orthogonal slices"
        t_1d = "Non-zero voxel density (1D histogram)"

    fig1 = plt.figure(figsize=(14.5, 9.6), dpi=120)
    _plot_density_map_spatial_slices(
        fig1,
        density,
        corner_min=corner_min,
        corner_max=corner_max,
        title=t_sp,
        subtitle=st,
        labels_zh=labels_zh,
    )
    p1 = (
        out_dir
        / f"foam_density_map_spatial_slices_scene_{safe_scene}_frame_{safe_frame}_voxel_{safe_vs}.png"
    )
    fig1.savefig(p1, dpi=180, bbox_inches="tight")
    plt.close(fig1)

    fig2 = plt.figure(figsize=(9.5, 5.2), dpi=120)
    _plot_density_map_nonzero_1d(
        fig2,
        density,
        title=t_1d,
        subtitle=st,
        labels_zh=labels_zh,
    )
    p2 = (
        out_dir
        / f"foam_density_map_nonzero_1d_scene_{safe_scene}_frame_{safe_frame}_voxel_{safe_vs}.png"
    )
    fig2.savefig(p2, dpi=180, bbox_inches="tight")
    plt.close(fig2)

    print(f"{_LOG} DensityMap 可视化已保存: {p1.name} , {p2.name}", flush=True)


def run_density_map_visualization(
    train_root: Path,
    scenes: Optional[Sequence[str]],
    out_dir: Path,
    voxel_sizes: Sequence[float],
    *,
    corner_min: Tuple[float, float, float],
    corner_max: Tuple[float, float, float],
    max_frames_per_scene: int = 0,
    english_labels: bool = False,
    density_factor: float = 1.0,
) -> None:
    from src_v3.data.foam_density import compute_Foam_Density
    from src_v3.data.layout import build_frame_index

    _init_matplotlib_backend()
    if english_labels:
        labels_zh = False
    else:
        labels_zh = _set_matplotlib_cjk_font()
        if not labels_zh:
            print(
                f"{_LOG} 未找到可用的中文字体，图内文字已改为英文（可安装系统字体或传 --english-labels）",
                flush=True,
            )

    train_root = train_root.resolve()
    if not train_root.is_dir():
        print(f"{_LOG} --train-root 不存在: {train_root}")
        return

    out_dir = out_dir.resolve()
    out_dir.mkdir(parents=True, exist_ok=True)

    idx = build_frame_index(train_root, require_mesh=False)
    if len(idx) == 0:
        print(f"{_LOG} 无帧: {train_root}（需要 <scene>/particle/*.vtk）")
        return

    if not scenes:
        scene_names = sorted(idx.scene_names())
        print(
            f"{_LOG} 未指定 --train-scenes：共 {len(scene_names)} 个场景，将**逐场景、逐帧**出图: {scene_names}",
            flush=True,
        )
    else:
        scene_names = list(scenes)

    if not scene_names:
        print(f"{_LOG} 没有可处理的场景")
        return

    cm = tuple(float(x) for x in corner_min)
    cx = tuple(float(x) for x in corner_max)

    for vs in voxel_sizes:
        grid_num = _grid_num_from_voxel_size(cm, cx, float(vs))
        scene_extent = np.asarray(cx, dtype=np.float64) - np.asarray(cm, dtype=np.float64)
        eff_voxel = tuple(float(scene_extent[i] / grid_num[i]) for i in range(3))
        safe_vs = f"{vs:g}".replace(".", "p")

        for scene_name in scene_names:
            rows = [r for r in idx.rows if r.scene == scene_name]
            if not rows:
                print(f"{_LOG} 场景下无帧: {scene_name!r}", flush=True)
                continue
            if max_frames_per_scene > 0:
                rows = rows[: int(max_frames_per_scene)]

            safe_scene = _safe_scene_tag(scene_name)
            for paths in rows:
                newfoam = _resolve_newfoam_like_dataset(paths)
                pos = newfoam.get("positions")
                n_parts = int(newfoam.get("num_particles") or 0)
                if pos is None or n_parts <= 0:
                    pos_s = np.zeros((0, 3), dtype=np.float32)
                else:
                    pos_s = np.asarray(pos, dtype=np.float32)[:, :3]
                r_s = float(newfoam.get("radius") or 1.0)
                fid = int(paths.frame_id)
                fr_lbl = f"{scene_name}:frame{fid}"
                safe_frame = _safe_frame_tag(fid)

                d_tensor = compute_Foam_Density(
                    pos_s,
                    float(r_s),
                    cornerMin=cm,
                    cornerMax=cx,
                    gridNum=grid_num,
                    Densityfactor=float(density_factor),
                    apply_gt_log_map=True,
                    log_map_alpha = 200.0,
                    verbose=False,
                )
                d_np = d_tensor.detach().cpu().float().numpy()
                _save_density_map_figures(
                    d_np,
                    corner_min=cm,
                    corner_max=cx,
                    grid_num=grid_num,
                    voxel_size=float(vs),
                    out_dir=out_dir,
                    labels_zh=labels_zh,
                    safe_vs=safe_vs,
                    safe_scene=safe_scene,
                    safe_frame=safe_frame,
                    frame_label=fr_lbl,
                    radius=float(r_s),
                )
                nz = int(np.sum(d_np > 0))
                print(
                    f"{_LOG} scene={scene_name!r} voxel_size={vs} grid={grid_num} eff_voxel≈{eff_voxel}  "
                    f"frame={fr_lbl}  n_particles={n_parts}  nonzero_voxels={nz}  "
                    f"max_density={float(d_np.max()):.4g}",
                    flush=True,
                )


def main() -> None:
    parser = argparse.ArgumentParser(
        description="训练集 newFoam：compute_Foam_Density 体素密度图可视化（切片 + 非零 1D 直方图）",
    )
    parser.add_argument(
        "--train-root",
        type=Path,
        default=None,
        help="数据根目录；默认 <repo>/TrainData",
    )
    parser.add_argument(
        "--train-scenes",
        nargs="*",
        default=None,
        dest="train_scenes",
        metavar="SCENE",
        help="只处理列出的场景；省略则全部。输出按场景×帧区分（文件名含场景名与帧号）",
    )
    parser.add_argument(
        "--train-out-dir",
        type=Path,
        default=None,
        dest="train_out_dir",
        help="输出目录，默认 <repo>/output/foam_density_map_vis",
    )
    parser.add_argument(
        "--train-max-frames",
        type=int,
        default=0,
        dest="train_max_frames",
        help="每场景最多处理的帧数（每帧都计算密度并出图），0 为不限制",
    )
    parser.add_argument(
        "--voxel-size",
        type=float,
        nargs="+",
        required=True,
        dest="voxel_size",
        metavar="L",
        help="物理体素边长（世界单位）；可多个值各出一套图",
    )
    parser.add_argument(
        "--corner-min",
        type=float,
        nargs=3,
        default=(-5.0, -5.0, -5.0),
        dest="corner_min",
        metavar=("X", "Y", "Z"),
        help="体素盒 min",
    )
    parser.add_argument(
        "--corner-max",
        type=float,
        nargs=3,
        default=(5.0, 5.0, 5.0),
        dest="corner_max",
        metavar=("X", "Y", "Z"),
        help="体素盒 max",
    )
    parser.add_argument(
        "--english-labels",
        action="store_true",
        dest="english_labels",
        help="图中标题/坐标轴强制使用英文（不依赖本机中文字体）",
    )
    parser.add_argument(
        "--density-factor",
        type=float,
        default=1.0,
        dest="density_factor",
        help="compute_Foam_Density 的 Densityfactor（默认 1）",
    )

    args = parser.parse_args()

    tr = args.train_root
    if tr is None:
        tr = _REPO_ROOT / "TrainData"
    tout = args.train_out_dir
    if tout is None:
        tout = _REPO_ROOT / "output" / "foam_density_map_vis"
    ts = args.train_scenes
    if ts is not None and len(ts) == 0:
        ts = None

    run_density_map_visualization(
        tr,
        ts,
        tout,
        args.voxel_size,
        corner_min=tuple(args.corner_min),
        corner_max=tuple(args.corner_max),
        max_frames_per_scene=int(args.train_max_frames),
        english_labels=bool(args.english_labels),
        density_factor=float(args.density_factor),
    )


if __name__ == "__main__":
    main()
