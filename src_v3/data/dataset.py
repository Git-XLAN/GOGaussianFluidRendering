# -*- coding: utf-8 -*-
"""
DataSet 管理：基于 FrameIndex 的懒加载 + 可选缓存，输出与 v2 兼容的样本字典。
"""

from pathlib import Path
from typing import Any, Dict, List, Optional, Sequence
import numpy as np
import torch

from .layout import FrameIndex, FramePaths, build_frame_index
from .vtk_loader import load_fluid_vtk, load_foam_vtk
from .schema import sample_output_from_fluid_and_foam
from .camera_from_particles import camera_from_particles
from .foam_density import compute_Foam_Density

NEWFOAM_DENSITY_CORNER_MIN = (-5.0, -5.0, -5.0)
NEWFOAM_DENSITY_CORNER_MAX = (5.0, 5.0, 5.0)
NEWFOAM_DENSITY_GRID_MODE_ADAPTIVE = "adaptive"
NEWFOAM_DENSITY_GRID_MODE_FIXED = "fixed"


def _default_radius_from_scene(scene: str, fallback: float = 0.01) -> float:
    """从场景名解析默认半径（与 v2 一致：末尾数字/1000）。"""
    try:
        return float(scene.split("_")[-1]) / 1000.0
    except (ValueError, IndexError):
        return fallback


def _foam_to_sample_dict(raw: Dict[str, Any], default_radius: float) -> Dict[str, Any]:
    """将泡沫 VTK 字典转为样本中 foam/newfoam 子字典（与 v2 键一致）。"""
    return {
        "positions": raw["positions"],
        "vel": raw.get("vel"),
        "lifetime": raw.get("lifetime"),
        "id": raw.get("id"),
        "radius": raw["radius"],
        "num_particles": raw["nums"],
        "born": raw.get("is_born"),  # v2 使用 key "born"
    }


def _grid_num_from_voxel_size(
    corner_min: Sequence[float],
    corner_max: Sequence[float],
    voxel_size: float,
) -> tuple[int, int, int]:
    """根据体素边长计算覆盖固定盒子的 GridDim。"""
    vs = float(voxel_size)
    if vs <= 0.0:
        raise ValueError("voxel_size must be positive")
    cmin = np.asarray(corner_min, dtype=np.float32)
    cmax = np.asarray(corner_max, dtype=np.float32)
    extent = np.maximum(cmax - cmin, 0.0)
    grid = np.maximum(np.ceil(extent / vs).astype(np.int64), 1)
    return int(grid[0]), int(grid[1]), int(grid[2])


def _voxel_size_cache_token(voxel_size: float) -> str:
    token = f"{float(voxel_size):.8g}"
    return token.replace("-", "m").replace(".", "p")


def _normalize_grid_dim(grid_dim: Optional[Sequence[int]]) -> Optional[tuple[int, int, int]]:
    if grid_dim is None:
        return None
    values = [int(v) for v in grid_dim]
    if len(values) == 1:
        values = values * 3
    if len(values) != 3:
        raise ValueError("foam_density_grid_dim must contain 1 or 3 integers")
    if any(v <= 0 for v in values):
        raise ValueError("foam_density_grid_dim values must be positive")
    return int(values[0]), int(values[1]), int(values[2])


def _resolve_newfoam_density_grid(
    *,
    fluid_radius: float,
    kernel_size: float,
    grid_mode: str,
    fixed_grid_dim: Optional[Sequence[int]],
) -> tuple[tuple[int, int, int], str, str]:
    mode = str(grid_mode).strip().lower()
    if mode == NEWFOAM_DENSITY_GRID_MODE_ADAPTIVE:
        voxel_size = float(fluid_radius) * float(kernel_size)
        grid_num = _grid_num_from_voxel_size(
            NEWFOAM_DENSITY_CORNER_MIN,
            NEWFOAM_DENSITY_CORNER_MAX,
            voxel_size,
        )
        token = f"voxel_{_voxel_size_cache_token(voxel_size)}"
        desc = f"grid_mode: adaptive voxel_size: {voxel_size}"
        return grid_num, token, desc

    if mode == NEWFOAM_DENSITY_GRID_MODE_FIXED:
        grid_num = _normalize_grid_dim(fixed_grid_dim)
        if grid_num is None:
            raise ValueError("foam_density_grid_dim is required when foam_density_grid_mode='fixed'")
        token = f"grid_{grid_num[0]}x{grid_num[1]}x{grid_num[2]}"
        desc = f"grid_mode: fixed grid_dim: {grid_num}"
        return grid_num, token, desc

    raise ValueError(
        "foam_density_grid_mode must be "
        f"'{NEWFOAM_DENSITY_GRID_MODE_ADAPTIVE}' or '{NEWFOAM_DENSITY_GRID_MODE_FIXED}'"
    )


def _ensure_newfoam_density(
    newfoam: Optional[Dict[str, Any]],
    foam_path: Optional[str],
    newfoam_path: Optional[str],
    *,
    fluid_radius: float,
    kernel_size: float,
    grid_mode: str = NEWFOAM_DENSITY_GRID_MODE_ADAPTIVE,
    fixed_grid_dim: Optional[Sequence[int]] = None,
    log_map_alpha: float = 1.0,
    log_map_d_max: float = 1.0,
) -> None:
    """
    检查并确保 newfoam 字典中存在 newFoamDensity（torch.Tensor）。

    策略：
      - 若 newfoam 为空或无粒子，直接返回；
      - 若磁盘上已存在缓存文件，则直接加载；
      - 否则调用 compute_Foam_Density 计算并写回到磁盘与 newfoam 字典。
    GridDim 支持两种模式：
      - adaptive：由 ``fluid_radius * kernel_size`` 作为体素边长动态计算；
      - fixed：直接使用传入的 ``fixed_grid_dim``。
    缓存文件名：优先基于 newfoam_path，其次退回 foam_path，后缀包含 grid 配置，避免复用旧缓存。
    这里缓存的是原始归一化 density（不做 GT log 映射），映射在 loss 中三线性插值后再进行。
    """
    grid_num, cache_token, grid_desc = _resolve_newfoam_density_grid(
        fluid_radius=float(fluid_radius),
        kernel_size=float(kernel_size),
        grid_mode=grid_mode,
        fixed_grid_dim=fixed_grid_dim,
    )
    base_path: Optional[Path] = None
    if newfoam_path is not None:
        base_path = Path(newfoam_path)
    elif foam_path is not None:
        base_path = Path(foam_path)
    if base_path is None:
        return

    density_path = base_path.with_suffix("")  # 去掉 .vtk
    density_path = density_path.parent / (
        density_path.name + f"_newFoamDensityRaw_{cache_token}.pt"
    )

    if density_path.exists():
        try:
            density = torch.load(density_path)
            if newfoam is not None:
                newfoam["newFoamDensity"] = density
            return
        except Exception:
            # 若读取失败则重新计算
            pass

    # 即使没有新泡沫，也缓存一个全 0 density 并用于监督
    if newfoam is None:
        density = torch.zeros(grid_num, dtype=torch.float32)
        try:
            density_path.parent.mkdir(parents=True, exist_ok=True)
            torch.save(density, density_path)
        except Exception:
            pass
        return

    n = int(newfoam.get("num_particles") or 0)
    if n <= 0:
        density = torch.zeros(grid_num, dtype=torch.float32)
        newfoam["newFoamDensity"] = density
        try:
            density_path.parent.mkdir(parents=True, exist_ok=True)
            torch.save(density, density_path)
        except Exception:
            pass
        return

    positions = newfoam.get("positions")[:, :3]
    radius = float(fluid_radius)
    if positions is None or radius <= 0.0:
        return

    density = compute_Foam_Density(
        positions=positions,
        radius=radius,
        cornerMin=NEWFOAM_DENSITY_CORNER_MIN,
        cornerMax=NEWFOAM_DENSITY_CORNER_MAX,
        gridNum=grid_num,
        apply_gt_log_map=False,
        log_map_alpha=float(log_map_alpha),
        log_map_d_max=float(log_map_d_max),
    )
    newfoam["newFoamDensity"] = density
    print(
        f"newFoamDensity: {density.shape} {grid_desc} "
        f"max: {density.max()}, min: {density.min()}"
    )
    try:
        density_path.parent.mkdir(parents=True, exist_ok=True)
        torch.save(density, density_path)
    except Exception:
        # 保存失败不影响训练流程，密度仍在当前进程的 newfoam 中可用
        pass


def _load_newfoam_from_foam(foam: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """从 foam 中按 born 掩码拆出 newfoam（与 v2 一致）。"""
    born = foam.get("born")
    if born is None or not np.any(born):
        return None
    out = {}
    n = foam["num_particles"]
    for k, v in foam.items():
        if k == "num_particles":
            out[k] = int(np.sum(born))
        elif isinstance(v, np.ndarray) and v.shape[0] == n:
            out[k] = v[born]
        elif k == "born":
            out[k] = v[born]
        elif k == "radius":
            out[k] = v  # 标量，直接复制
    return out


class FluidDataset:
    """
    多场景流体数据集：索引为懒构建，按需加载，输出与 v2 兼容的样本字典。
    """

    def __init__(
        self,
        root: str,
        *,
        require_mesh: bool = False,
        cache_size: int = 0,
        foam_density_log_alpha: float = 1.0,
        foam_density_log_d_max: float = 1.0,
        foam_density_kernel_size: float = 1.0,
        foam_density_grid_mode: str = NEWFOAM_DENSITY_GRID_MODE_ADAPTIVE,
        foam_density_grid_dim: Optional[Sequence[int]] = None,
        ensure_newfoam_density: bool = True,
        camera_mode: str = "bbox",
        camera_fov: float = 60,
        camera_distance_scale: float = 1.5,
        camera_axis: str = "z",
        camera_random: bool = True,
        camera_distance_scale_max: Optional[float] = None,
        camera_fov_max: Optional[float] = None,
        camera_fix_sphere_scale_to_min: bool = False,
        camera_seed: Optional[int] = None,
    ):
        """
        Args:
            root: 数据根目录（如 F:/DataSet）
            require_mesh: 是否仅保留有 mesh 的帧
            cache_size: 样本缓存条数，0 表示不缓存
            foam_density_log_alpha: newFoamDensity GT log 映射系数 α（见 foam_density）
            foam_density_log_d_max: 映射分母中的固定 d_ref（与训练/推理逆映射一致）
            foam_density_kernel_size: newFoamDensity 体素边长系数，voxel_size = fluid_radius * kernel_size
            foam_density_grid_mode: "adaptive" 使用体素边长计算 GridDim；"fixed" 使用 foam_density_grid_dim
            foam_density_grid_dim: fixed 模式下的固定 GridDim，可为 (N,) 或 (Nx,Ny,Nz)
            ensure_newfoam_density: 是否在加载时计算/读取 ``newFoamDensity``（RealTimeWater 可关闭以加速场景加载）
            camera_mode: 相机生成策略（如 "bbox"：看向粒子中心、相机在包围盒外）
            camera_fov: 垂直 fov（度），固定值，不参与随机
            camera_distance_scale: bbox 下相机距中心倍数；random 时与 camera_distance_scale_max 构成范围
            camera_axis: bbox 下固定轴；camera_random=True 时在 x/y/z 中随机，此项忽略
            camera_random: 是否随机化轴、距离（默认 True）；fov 始终固定
            camera_distance_scale_max: random 时距离比例上界，None 则用 camera_distance_scale * 1.4
            camera_fov_max: 保留兼容，未使用；fov 固定不随机
            camera_fix_sphere_scale_to_min: True 时球面直径系数固定为区间下限（削弱距离随机），方向仍可随机。
            camera_seed: ``camera_random=True`` 时若给定，则用 ``numpy.random.default_rng(camera_seed)`` 采样相机，
                与 ``random.seed`` 独立；``None`` 则每次调用 ``camera_from_particles`` 仍用无种子的 ``default_rng()``。
        """
        self.root = Path(root)
        self.require_mesh = require_mesh
        self.cache_size = cache_size
        self.foam_density_log_alpha = float(foam_density_log_alpha)
        self.foam_density_log_d_max = float(foam_density_log_d_max)
        self.foam_density_kernel_size = float(foam_density_kernel_size)
        self.foam_density_grid_mode = str(foam_density_grid_mode).strip().lower()
        if self.foam_density_grid_mode not in (
            NEWFOAM_DENSITY_GRID_MODE_ADAPTIVE,
            NEWFOAM_DENSITY_GRID_MODE_FIXED,
        ):
            raise ValueError(
                "foam_density_grid_mode must be "
                f"'{NEWFOAM_DENSITY_GRID_MODE_ADAPTIVE}' or '{NEWFOAM_DENSITY_GRID_MODE_FIXED}'"
            )
        self.foam_density_grid_dim = _normalize_grid_dim(foam_density_grid_dim)
        if (
            self.foam_density_grid_mode == NEWFOAM_DENSITY_GRID_MODE_FIXED
            and self.foam_density_grid_dim is None
        ):
            raise ValueError("foam_density_grid_dim is required when foam_density_grid_mode='fixed'")
        self.ensure_newfoam_density = bool(ensure_newfoam_density)
        self.camera_mode = camera_mode
        self.camera_fov = camera_fov
        self.camera_distance_scale = camera_distance_scale
        self.camera_axis = camera_axis
        self.camera_random = camera_random
        self.camera_distance_scale_max = camera_distance_scale_max
        self.camera_fov_max = camera_fov_max
        self.camera_fix_sphere_scale_to_min = bool(camera_fix_sphere_scale_to_min)
        self.camera_seed = camera_seed
        if self.camera_random and camera_seed is not None:
            self._camera_rng: Optional[np.random.Generator] = np.random.default_rng(int(camera_seed))
        else:
            self._camera_rng = None
        self._index = build_frame_index(self.root, require_mesh=require_mesh)
        self._cache: Dict[int, Dict[str, Any]] = {}

    def _camera_for_positions(self, positions: Any) -> Dict[str, Any]:
        """
        训练（默认）：与历史一致，仅传 distance_scale 等；球面直径系数由 _camera_bbox 默认 [1.2, 3.5]。
        Compare（camera_fix_sphere_scale_to_min=True）：显式传入 sphere_diameter_*，并固定为区间下限。
        """
        if self.camera_fix_sphere_scale_to_min:
            dsm = self.camera_distance_scale_max
            if dsm is None:
                dsm = self.camera_distance_scale * 1.4
            return camera_from_particles(
                positions,
                mode=self.camera_mode,
                fov=self.camera_fov,
                random=self.camera_random,
                rng=self._camera_rng,
                fix_sphere_scale_to_min=True,
                sphere_diameter_scale=float(self.camera_distance_scale),
                sphere_diameter_scale_max=float(dsm),
                axis=self.camera_axis,
                fov_max=self.camera_fov_max,
            )
        return camera_from_particles(
            positions,
            mode=self.camera_mode,
            fov=self.camera_fov,
            distance_scale=self.camera_distance_scale,
            axis=self.camera_axis,
            random=self.camera_random,
            rng=self._camera_rng,
            distance_scale_max=self.camera_distance_scale_max,
            fov_max=self.camera_fov_max,
            fix_sphere_scale_to_min=False,
        )

    @property
    def index(self) -> FrameIndex:
        return self._index

    def __len__(self) -> int:
        return len(self._index)

    def __getitem__(self, idx: int) -> Dict[str, Any]:
        if idx < 0 or idx >= len(self._index):
            raise IndexError(f"索引越界: {idx}")
        if self.cache_size > 0 and idx in self._cache:
            return self._cache[idx]
        paths = self._index[idx]
        sample = self._load_one(paths)
        if self.cache_size > 0 and sample is not None:
            if len(self._cache) >= self.cache_size:
                self._cache.pop(next(iter(self._cache)))
            self._cache[idx] = sample
        return sample

    def _load_one(self, paths: FramePaths) -> Optional[Dict[str, Any]]:
        default_r = _default_radius_from_scene(paths.scene)
        fluid = load_fluid_vtk(paths.particle_path, default_radius=default_r)
        if fluid is None:
            return None

        foam: Optional[Dict[str, Any]] = None
        if paths.foam_path:
            foam_raw = load_foam_vtk(paths.foam_path, default_radius=default_r)
            if foam_raw is not None:
                foam = _foam_to_sample_dict(foam_raw, default_r)

        newfoam: Optional[Dict[str, Any]] = None
        if paths.newfoam_path:
            new_raw = load_foam_vtk(paths.newfoam_path, default_radius=default_r)
            if new_raw is not None:
                newfoam = _foam_to_sample_dict(new_raw, default_r)
        elif foam is not None:
            newfoam = _load_newfoam_from_foam(foam)

        # 若该帧没有 newfoam，也提供一个空 newfoam 容器，便于挂载全 0 newFoamDensity 监督
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

        # 训练/评估默认开启：确保 newfoam 的密度已存在（若无则计算并写回）
        if self.ensure_newfoam_density:
            _ensure_newfoam_density(
                newfoam,
                paths.foam_path,
                paths.newfoam_path,
                fluid_radius=float(fluid["radius"]),
                kernel_size=self.foam_density_kernel_size,
                grid_mode=self.foam_density_grid_mode,
                fixed_grid_dim=self.foam_density_grid_dim,
                log_map_alpha=self.foam_density_log_alpha,
                log_map_d_max=self.foam_density_log_d_max,
            )

        sample = sample_output_from_fluid_and_foam(
            fluid=fluid,
            meta_scene=paths.scene,
            meta_frame_id=paths.frame_id,
            gt_mesh_path=paths.mesh_path,
            foam=foam,
            newfoam=newfoam,
        )
        # 根据粒子位置生成相机（与 GT 渲染 / 高斯投影共用）
        sample["camera"] = self._camera_for_positions(fluid["positions"])
        return sample

    def update_sample_camera(self, sample: Dict[str, Any]) -> None:
        """
        按当前 dataset 的 camera_mode 等，根据 sample["positions"] 重新生成 camera，
        并写回 sample["camera"]（与加载时逻辑一致；camera_random=True 时每次随机）。
        """
        positions = sample.get("positions")
        if positions is None:
            return
        sample["camera"] = self._camera_for_positions(positions)

    def scene_names(self) -> List[str]:
        return self._index.scene_names()

    


    def filter_by_scene(self, scene: str) -> "FluidDataset":
        """返回仅包含指定场景的“视图”（共享同一 root，但索引不同）。"""
        out = FluidDataset.__new__(FluidDataset)
        out.root = self.root
        out.require_mesh = self.require_mesh
        out.cache_size = self.cache_size
        out.foam_density_log_alpha = float(getattr(self, "foam_density_log_alpha", 1.0))
        out.foam_density_log_d_max = float(getattr(self, "foam_density_log_d_max", 1.0))
        out.foam_density_kernel_size = float(getattr(self, "foam_density_kernel_size", 1.0))
        out.foam_density_grid_mode = str(
            getattr(self, "foam_density_grid_mode", NEWFOAM_DENSITY_GRID_MODE_ADAPTIVE)
        )
        out.foam_density_grid_dim = getattr(self, "foam_density_grid_dim", None)
        out.ensure_newfoam_density = bool(getattr(self, "ensure_newfoam_density", True))
        out.camera_mode = self.camera_mode
        out.camera_fov = self.camera_fov
        out.camera_distance_scale = self.camera_distance_scale
        out.camera_axis = self.camera_axis
        out.camera_random = self.camera_random
        out.camera_distance_scale_max = self.camera_distance_scale_max
        out.camera_fov_max = self.camera_fov_max
        out.camera_fix_sphere_scale_to_min = bool(
            getattr(self, "camera_fix_sphere_scale_to_min", False)
        )
        out.camera_seed = getattr(self, "camera_seed", None)
        out._camera_rng = getattr(self, "_camera_rng", None)
        out._index = self._index.filter_by_scene(scene)
        out._cache = {}
        return out

    def filter_by_scenes(self, scenes: Sequence[str]) -> "FluidDataset":
        """返回仅包含若干指定场景的并集视图（帧在各自场景内保留原顺序）。"""
        out = FluidDataset.__new__(FluidDataset)
        out.root = self.root
        out.require_mesh = self.require_mesh
        out.cache_size = self.cache_size
        out.foam_density_log_alpha = float(getattr(self, "foam_density_log_alpha", 1.0))
        out.foam_density_log_d_max = float(getattr(self, "foam_density_log_d_max", 1.0))
        out.foam_density_kernel_size = float(getattr(self, "foam_density_kernel_size", 1.0))
        out.foam_density_grid_mode = str(
            getattr(self, "foam_density_grid_mode", NEWFOAM_DENSITY_GRID_MODE_ADAPTIVE)
        )
        out.foam_density_grid_dim = getattr(self, "foam_density_grid_dim", None)
        out.ensure_newfoam_density = bool(getattr(self, "ensure_newfoam_density", True))
        out.camera_mode = self.camera_mode
        out.camera_fov = self.camera_fov
        out.camera_distance_scale = self.camera_distance_scale
        out.camera_axis = self.camera_axis
        out.camera_random = self.camera_random
        out.camera_distance_scale_max = self.camera_distance_scale_max
        out.camera_fov_max = self.camera_fov_max
        out.camera_fix_sphere_scale_to_min = bool(
            getattr(self, "camera_fix_sphere_scale_to_min", False)
        )
        out.camera_seed = getattr(self, "camera_seed", None)
        out._camera_rng = getattr(self, "_camera_rng", None)
        out._index = self._index.filter_by_scenes(scenes)
        out._cache = {}
        return out


class SceneDataset(FluidDataset):
    """
    单场景数据集：构造时指定 scene，仅包含该场景的帧。
    相机参数与 FluidDataset 一致（camera_mode / camera_fov 等）。
    """

    def __init__(
        self,
        root: str,
        scene: str,
        *,
        require_mesh: bool = False,
        cache_size: int = 0,
        foam_density_log_alpha: float = 1.0,
        foam_density_log_d_max: float = 1.0,
        foam_density_kernel_size: float = 1.0,
        foam_density_grid_mode: str = NEWFOAM_DENSITY_GRID_MODE_ADAPTIVE,
        foam_density_grid_dim: Optional[Sequence[int]] = None,
        ensure_newfoam_density: bool = True,
        camera_mode: str = "bbox",
        camera_fov: float = 60,
        camera_distance_scale: float = 1.5,
        camera_axis: str = "z",
        camera_random: bool = True,
        camera_distance_scale_max: Optional[float] = None,
        camera_fov_max: Optional[float] = None,
        camera_fix_sphere_scale_to_min: bool = False,
        camera_seed: Optional[int] = None,
    ):
        super().__init__(
            root,
            require_mesh=require_mesh,
            cache_size=cache_size,
            foam_density_log_alpha=foam_density_log_alpha,
            foam_density_log_d_max=foam_density_log_d_max,
            foam_density_kernel_size=foam_density_kernel_size,
            foam_density_grid_mode=foam_density_grid_mode,
            foam_density_grid_dim=foam_density_grid_dim,
            ensure_newfoam_density=ensure_newfoam_density,
            camera_mode=camera_mode,
            camera_fov=camera_fov,
            camera_distance_scale=camera_distance_scale,
            camera_axis=camera_axis,
            camera_random=camera_random,
            camera_distance_scale_max=camera_distance_scale_max,
            camera_fov_max=camera_fov_max,
            camera_fix_sphere_scale_to_min=camera_fix_sphere_scale_to_min,
            camera_seed=camera_seed,
        )
        self.scene = scene
        self._index = self._index.filter_by_scene(scene)

    @property
    def scene_name(self) -> str:
        return self.scene
