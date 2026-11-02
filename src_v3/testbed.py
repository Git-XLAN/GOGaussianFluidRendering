"""
按帧用 IhmsenFoam.GenerateFoam 生成泡沫，并写入
  <data_root>/<scene>/foam/<与 particle 同名的 .vtk>
以便与 ``load_foam_vtk`` / ``build_frame_index`` 的帧对齐方式一致。

VTK 点属性约定（与 ``vtk_loader`` / ``NewCacheFoam`` 对齐）：
  - 坐标：Points（xyz）
  - ``radius``：每粒子半径（使用 ``radius`` 而非 ``pscale``，避免泡沫分支的 0.5×0.25 缩放）
  - ``v``：速度 [M,3]（优先名 ``v``）
  - ``born``：是否本帧新生（0/1，与 ``FLAG_ATTRS``）
  - ``lifetime``：写入**原始标量**；读取时会被规范化为 ``(raw - 0.2) / (9.0 - 0.2)``
  - ``counts``：可选，当前 loader 不读，便于后续使用
"""
from __future__ import annotations

import sys
from pathlib import Path

_project_root = Path(__file__).resolve().parent.parent
if str(_project_root) not in sys.path:
    sys.path.insert(0, str(_project_root))

import numpy as np
import pysplishsplash
import torch

from src_v3.data.dataset import SceneDataset


def write_foam_vtk(
    out_path: Path,
    xyz: np.ndarray,
    velocity: np.ndarray,
    is_new: np.ndarray,
    counts: np.ndarray | None,
    lifetime_raw: np.ndarray,
    *,
    foam_radius: float = 0.05,
) -> None:
    """写出与 ``load_foam_vtk`` 兼容的 legacy VTK PolyData（二进制）。"""
    try:
        import vtk
        from vtk.util import numpy_support
    except ImportError as e:
        raise RuntimeError("写出泡沫 VTK 需要安装 vtk（python-vtk）。") from e

    out_path = Path(out_path)
    out_path.parent.mkdir(parents=True, exist_ok=True)

    xyz = np.asarray(xyz, dtype=np.float32, order="C")
    m = int(xyz.shape[0])
    if m == 0:
        return

    if xyz.ndim != 2 or xyz.shape[1] < 3:
        raise ValueError("xyz 形状应为 (M, 3)")

    pts3 = np.ascontiguousarray(xyz[:, :3])
    vtk_points = vtk.vtkPoints()
    vtk_points.SetData(numpy_support.numpy_to_vtk(pts3, deep=1))

    poly = vtk.vtkPolyData()
    poly.SetPoints(vtk_points)
    pd = poly.GetPointData()

    r = np.full((m, 1), float(foam_radius), dtype=np.float32)
    arr_r = numpy_support.numpy_to_vtk(r, deep=1)
    arr_r.SetName("radius")
    pd.AddArray(arr_r)

    vel = np.asarray(velocity, dtype=np.float32, order="C").reshape(m, 3)
    arr_v = numpy_support.numpy_to_vtk(vel, deep=1)
    arr_v.SetName("v")
    pd.AddArray(arr_v)

    born_i = np.asarray(is_new, dtype=np.int32).ravel()
    if born_i.size != m:
        born_i = np.resize(born_i, (m,))
    arr_b = numpy_support.numpy_to_vtk(born_i.reshape(m, 1), deep=1)
    arr_b.SetName("born")
    pd.AddArray(arr_b)

    life = np.asarray(lifetime_raw, dtype=np.float32).ravel()
    if life.size != m:
        life = np.resize(life, (m,))
    arr_l = numpy_support.numpy_to_vtk(life.reshape(m, 1), deep=1)
    arr_l.SetName("lifetime")
    pd.AddArray(arr_l)

    if counts is not None:
        c = np.asarray(counts, dtype=np.float32).ravel()
        if c.size != m:
            c = np.resize(c, (m,))
        arr_c = numpy_support.numpy_to_vtk(c.reshape(m, 1), deep=1)
        arr_c.SetName("counts")
        pd.AddArray(arr_c)

    writer = vtk.vtkPolyDataWriter()
    writer.SetFileName(str(out_path))
    writer.SetInputData(poly)
    writer.SetFileTypeToBinary()
    writer.Write()


def export_scene_foam(
    data_root: str | Path,
    scene: str,
    *,
    require_mesh: bool = False,
    time_step: float = 1.0/30,
    k_ta: float = 0.2,
    k_wc: float = 0.2,
    foam_scale: float = 1000.0,
    seed: int = 42,
    foam_radius: float = 0.05,
    default_lifetime_raw: float = 5.0,
) -> None:
    """
    遍历 ``SceneDataset`` 的每一帧，生成泡沫并写入
    ``<data_root>/<scene>/foam/<与 particle 目录中该帧 vtk 同名>``。
    """
    data_root = Path(data_root)
    foam_dir = data_root / scene / "foam"
    foam_dir.mkdir(parents=True, exist_ok=True)

    ds = SceneDataset(
        root=str(data_root),
        scene=scene,
        require_mesh=require_mesh,
        cache_size=0,
        ensure_newfoam_density=False,
    )

    fpos = fvel = flt = None
    gen = pysplishsplash.IhmsenFoam.GenerateFoam

    for i in range(len(ds)):
        paths = ds.index[i]
        out_vtk = foam_dir / Path(paths.particle_path).name

        sample = ds[i]
        pos = sample["positions"]
        vel_t = sample["vel"]
        if pos is None:
            continue
        pos_np = pos.detach().cpu().numpy() if isinstance(pos, torch.Tensor) else np.asarray(pos)
        if vel_t is None:
            vel_np = np.zeros((pos_np.shape[0], 3), dtype=np.float32)
        else:
            vel_np = (
                vel_t.detach().cpu().numpy()
                if isinstance(vel_t, torch.Tensor)
                else np.asarray(vel_t)
            ).astype(np.float32, copy=False)
        #print(sample["radius"])
        kwargs = dict(
            timeStep=time_step,
            radius=float(sample["radius"]),
            k_ta=k_ta,
            k_wc=k_wc,
            foam_scale=foam_scale,
            seed=seed,
        )
        if fpos is not None and fvel is not None:
            kwargs["foam_pos_prev"] = fpos
            kwargs["foam_vel_prev"] = fvel
        if flt is not None:
            kwargs["foam_lifetime_prev"] = flt

        ret = gen(pos_np, vel_np, **kwargs)
        if len(ret) == 5:
            fpos, is_new, foam_counts, fvel, flt = ret
        else:
            fpos, is_new, foam_counts, fvel = ret
            flt = None

        fpos = np.asarray(fpos, dtype=np.float32)
        fvel = np.asarray(fvel, dtype=np.float32)
        is_new = np.asarray(is_new)
        counts_arr = np.asarray(foam_counts) if foam_counts is not None else None

        m = int(fpos.shape[0])
        if m == 0:
            print(f"[skip] frame index {i} (id={paths.frame_id}): 0 foam particles")
            continue

        life_raw = np.full((m,), float(default_lifetime_raw), dtype=np.float32)
        if flt is not None:
            flt_np = np.asarray(flt, dtype=np.float32).ravel()
            if flt_np.size == m:
                life_raw = flt_np.astype(np.float32, copy=False)

        write_foam_vtk(
            out_vtk,
            fpos,
            fvel,
            is_new,
            counts_arr,
            life_raw,
            foam_radius=foam_radius,
        )
        print(f"[ok] frame_id={paths.frame_id} -> {out_vtk} ({m} particles)")


if __name__ == "__main__":
    import argparse

    ap = argparse.ArgumentParser(description="导出 Ihmsen 泡沫 VTK 到 <root>/<scene>/foam/")
    ap.add_argument("--root", type=Path, default=Path(r"F:\DataSet\ShowData"))
    ap.add_argument("--scene", type=str, default="DownWater_SPH_18")
    ap.add_argument("--require-mesh", action="store_true")
    a = ap.parse_args()
    export_scene_foam(a.root, a.scene, require_mesh=a.require_mesh)
