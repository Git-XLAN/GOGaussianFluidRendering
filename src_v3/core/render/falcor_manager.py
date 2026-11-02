# -*- coding: utf-8 -*-
"""
Falcor GT 渲染后端（框架搭建，具体实现先写 TODO）。

目标：作为 Mitsuba GTGenerator 的可选替代后端，保持 [H,W,4] normal+depth 接口一致。

设计要点：
  - 负责 Falcor Device/Testbed/RenderGraph 的初始化与复用（单例 / 懒初始化）。
  - 提供最小接口：
      * initialize()
      * set_camera_from_dict(cam: dict)
      * set_scene_or_mesh(sample / mesh_path)
      * render_normal_depth() -> np.ndarray [H,W,4]
  - 当前仅搭建骨架，所有具体 Falcor 交互均为 TODO 占位。
"""


from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, Optional, Tuple
import torch
import os
import sys

# 优先读环境变量 FALCOR_DIR；未设置时使用本发行包自带的运行时二进制。
_PACKAGED_FALCOR_DIR = str(Path(__file__).resolve().parents[3] / "Falcor")
FALCOR_DIR = os.environ.get("FALCOR_DIR", _PACKAGED_FALCOR_DIR)
FALCOR_PY_PATH = os.path.join(FALCOR_DIR, "python")
FALCOR_PLUGINS_DIR = os.path.join(FALCOR_DIR, "plugins")

if not os.path.isdir(FALCOR_DIR):
    raise ImportError(
        f"Falcor 目录不存在: {FALCOR_DIR}\n"
        "请确认发行包内的 Falcor\\ 目录完整，或设置环境变量 FALCOR_DIR "
        r"指向 Falcor 的 build\bin\Release。"
    )

if hasattr(os, 'add_dll_directory'):
    os.add_dll_directory(FALCOR_DIR)
    #os.add_dll_directory(FALCOR_PLUGINS_DIR)
os.environ["PATH"] = FALCOR_DIR + os.pathsep + FALCOR_PLUGINS_DIR + os.pathsep + os.environ.get("PATH", "")
sys.path.insert(0, FALCOR_PY_PATH)

import falcor

import numpy as np

# 实时水 / 粒子过滤共用的 Falcor 场景；可被 ``data_path/scene/baseRender.pyscene`` 覆盖。
_SRC_V3_DIR = Path(__file__).resolve().parents[2]
_DEFAULT_BASE_RENDER_PYSCENE = str(_SRC_V3_DIR / "baseRender.pyscene")


def resolve_base_render_pyscene(data_path: str, scene: str) -> str:
    """
    优先加载 ``data_path/scene/baseRender.pyscene``（文件存在时）；
    否则使用仓库默认 ``./src_v3/baseRender.pyscene``。
    ``data_path`` 或 ``scene`` 为空时直接使用默认路径。
    """
    dp = (data_path or "").strip()
    sc = (scene or "").strip()
    if not dp or not sc:
        return _DEFAULT_BASE_RENDER_PYSCENE
    candidate = Path(dp) / sc / "baseRender.pyscene"
    if candidate.is_file():
        return str(candidate.resolve())
    else:
        print(f"baseRender.pyscene not found in {candidate}")
    return _DEFAULT_BASE_RENDER_PYSCENE


@dataclass
class FalcorGTConfig:
    """Falcor GT 渲染配置（分辨率、是否创建窗口等）。"""

    width: int = 256
    height: int = 256
    create_window: bool = False
    scene_path: str = "base.pyscene"


class FalcorGTBackend:
    """
    Falcor GT 渲染后端（占位实现）。

    负责：
      - 初始化 Falcor Device/Testbed
      - 根据粒子/mesh 场景加载 Falcor 场景
      - 每帧更新相机（origin/target/up/fov）
      - 渲染出 normal+depth buffer 并读回为 [H,W,4] np.float32

    当前仅搭好接口与生命周期框架，具体 Falcor 代码留给后续实现。
    """

    def __init__(self, config: Optional[FalcorGTConfig] = None):
        self.config = config or FalcorGTConfig()
        self._initialized = False
        self.device: Optional[Any] = None
        self.testbed: Optional[Any] = None
        self.render_graph: Optional[Any] = None
        self._normal_depth_buffer: Optional[Any] = None

    def initialize(self) -> None:
        """
        初始化 Falcor 设备与测试台，并创建 GT 渲染用的 RenderGraph。

        实现策略：在 src_v3 内独立初始化 Falcor Device/Testbed，不依赖 src_v2 代码。
        """
        if self._initialized:
            return

        # 尝试直接导入 falcor；若未安装则抛出明确错误
        try:
            import falcor  # type: ignore
        except ImportError as e:
            raise ImportError("Falcor 库未安装或环境未配置，无法使用 Falcor GT 后端") from e

        print("initialize FalcorGTBackend")
        # 1) 创建 D3D12 设备
        self.device = falcor.Device(
            type=falcor.DeviceType.D3D12,
            gpu=0,
            enable_debug_layer=False,
        )

        # 2) 创建 Testbed（渲染窗口/离屏环境）
        self.testbed = falcor.Testbed(
            width=int(self.config.width),
            height=int(self.config.height),
            create_window=bool(self.config.create_window),
            device=self.device,
        )

        self.render_graph = self.testbed.create_render_graph("GTPass")
        self.render_graph.create_pass("GTPass", "GTPass", {
            "texWidth": int(self.config.width),
            "texHeight": int(self.config.height),
        })

        self.render_graph.mark_output("GTPass.NormalDepth")
        self.testbed.render_graph = self.render_graph
        try:
            bind_flags = (
                falcor.ResourceBindFlags.ShaderResource
                | falcor.ResourceBindFlags.UnorderedAccess
                | falcor.ResourceBindFlags.Shared
            )
            self._normal_depth_buffer = self.device.create_structured_buffer(
                struct_size=4 * 4,
                element_count=int(self.config.width) * int(self.config.height),
                bind_flags=bind_flags,
            )
        except Exception as e:
            raise RuntimeError(f"创建 Falcor NormalDepth structured buffer 失败: {e}") from e

        try:
            p = self.render_graph.getPass("GTPass")
            p.gtBuffer = self._normal_depth_buffer
        except Exception:
            pass
        
        #加载一个默认的场景
        self.testbed.load_scene("./src_v3/base.pyscene")

        self._initialized = True

    def set_camera_from_dict(self, camera: Dict[str, Any]) -> None:

        if not self._initialized:
            self.initialize()

        falcorCam = self.testbed.scene.camera
        falcorCam.position = falcor.float3(camera["origin"])
        falcorCam.target = falcor.float3(camera["target"])
        falcorCam.up = falcor.float3(camera["up"])
        falcorCam.aspectRatio = self.config.width / self.config.height
        falcorCam.focalLength = falcorCam.frameHeight / 2.0 / np.tan(camera["fov"] * 0.5 * np.pi / 180.0)
    

    def set_scene_from_sample(self, sample: Dict[str, Any]) -> None:
        if not self._initialized:
            self.initialize()
        mesh_path = sample.get("gt_mesh_path")
        if mesh_path is None:
            return
        mesh_path = str(Path(mesh_path).resolve())
        self.render_graph.getPass("GTPass").meshPath = mesh_path

    def render_normal_depth(self) -> np.ndarray:
        """
        执行一帧 Falcor 渲染，并返回 [H,W,4] float32（normal.xyz + depth）。

        Returns:
            np.ndarray: 形状 (height, width, 4)，dtype=float32。
        """
        import torch,time
        if not self._initialized:
            self.initialize()

        if self.testbed is None:
            raise RuntimeError("FalcorGTBackend 未初始化 testbed")
        if self._normal_depth_buffer is None:
            raise RuntimeError("FalcorGTBackend 未创建 normal_depth buffer（initialize 中应创建）")
        
        self.testbed.frame()
        self.device.render_context.wait_for_falcor()

        out = self._normal_depth_buffer.to_torch(shape=[int(self.config.height), int(self.config.width), 4], dtype=falcor.DataType.float32)
        
        return out.detach().cpu().numpy()
    
    def getIndex(self) -> int:
        return self.render_graph.getPass("GTPass").selectedIndex

    def cleanup(self) -> None:
        """清理 Falcor 资源，训练结束时可调用。"""
        self.render_graph = None
        self.testbed = None
        self.device = None
        self._normal_depth_buffer = None
        self._initialized = False


@dataclass
class FalcorParticleFilterConfig:
    width: int = 512
    height: int = 512
    max_fluid_particles: int = 10000000 #最大支持2百万个粒子
    create_window: bool = True
    scene_path: str = "base.pyscene"

class FalcorParticelFilterRenderer:
    """Falcor to Process Particles"""
    def __init__(self, config: Optional[FalcorParticleFilterConfig] = None):
        self.config = config or FalcorParticleFilterConfig()
        self._initialized = False
        self.device: Optional[Any] = None
        self.testbed: Optional[Any] = None
        self.render_graph: Optional[Any] = None
        self.camera: Optional[Any] = None
        """
        Buffer For python-Falcor interaction
        """
        self._fluid_particle_buffer: Optional[Any] = None
        self._surfaceIndex_buffer: Optional[Any] = None
    

    def initialize(self) -> None:
        """
        Initialize Falcor Device/Testbed
        """
        if self._initialized:
            return
        try:
            import falcor
        except ImportError as e:
            raise ImportError("Falcor 库未安装或环境未配置，无法使用 Falcor Particle Filter 后端") from e
        
        self.device = falcor.Device(
            type=falcor.DeviceType.D3D12,
            gpu=0,
            enable_debug_layer=False,
        )

        self.testbed = falcor.Testbed(
            width=int(self.config.width),
            height=int(self.config.height),
            create_window=bool(self.config.create_window),
            device=self.device,
        )

        self.renderpass = {}

        self.render_graph = self.testbed.create_render_graph("ParticleFilterPass")

        self.render_graph.create_pass("ParticleFilterPass", "ParticleFilterPass", {
            "texWidth": int(self.config.width),
            "texHeight": int(self.config.height),
            "maxFluidParticles": int(self.config.max_fluid_particles),
        })

        self.renderpass["particleFilterPass"] = self.render_graph.getPass("ParticleFilterPass")
        
        self.render_graph.mark_output("ParticleFilterPass.ResultTex")
        self.testbed.render_graph = self.render_graph

        try:
            bind_flags = (
                falcor.ResourceBindFlags.ShaderResource
                | falcor.ResourceBindFlags.UnorderedAccess
                | falcor.ResourceBindFlags.Shared
            )
            self._fluid_particle_buffer = self.device.create_structured_buffer(
                struct_size=4 * 3,#float *3
                element_count= self.config.max_fluid_particles,
                bind_flags=bind_flags,
            )

            self._surfaceIndex_buffer = self.device.create_structured_buffer(
                struct_size=4,#uint Index 
                element_count= self.config.max_fluid_particles,
                bind_flags=bind_flags,
            )#返回 index
        except Exception as e:
            raise RuntimeError(f"创建 Falcor NormalDepth structured buffer 失败: {e}") from e
        
        try:
            self.renderpass["particleFilterPass"].fluidParticle = self._fluid_particle_buffer
            self.renderpass["particleFilterPass"].surfaceIndex = self._surfaceIndex_buffer
        except Exception:
            pass

        pyscene = getattr(self.config, "scene_path", None) or "./src_v3/baseRender.pyscene"
        if not Path(pyscene).is_file():
            pyscene = "./src_v3/baseRender.pyscene"
        self.testbed.load_scene(pyscene)
        self._initialized = True

    def reload_pyscene(self, scene_path: str) -> None:
        """切换场景时重载 pyscene，复用已有 Device/Testbed（不整套重建）。"""
        if not self._initialized:
            self.initialize()
        if self.testbed is None:
            raise RuntimeError("FalcorParticelFilterRenderer 未初始化 testbed")
        p = (scene_path or "").strip() or "./src_v3/baseRender.pyscene"
        if not Path(p).is_file():
            p = "./src_v3/baseRender.pyscene"
        self.testbed.load_scene(p)
        self.config.scene_path = p

    def setCamera(self,camera):
        self.camera = camera

    def setCameraFromDict(self, camera: Dict[str, Any]) -> None:
        """使用与 GT/Projector 一致的 camera dict 设置过滤 pass 相机。"""
        if not self._initialized:
            self.initialize()
        if self.testbed is None or self.testbed.scene is None:
            raise RuntimeError("FalcorParticelFilterRenderer 未初始化 scene")
        
        falcorCam = self.testbed.scene.camera
        falcorCam.position = falcor.float3(camera["origin"])
        falcorCam.target = falcor.float3(camera["target"])
        falcorCam.up = falcor.float3(camera["up"])
        falcorCam.aspectRatio = self.config.width / self.config.height
        falcorCam.focalLength = falcorCam.frameHeight / 2.0 / np.tan(camera["fov"] * 0.5 * np.pi / 180.0)

        self.camera = falcorCam
    
    def set_camera_for_renderPass(self) -> None:
        if not self._initialized:
            self.initialize()
        if self.camera is None:
            raise RuntimeError("FalcorGTBackend 未初始化 camera")
        for mpass in self.renderpass:
            self.renderpass[mpass].camera = self.camera

    def filterParticle(self, fluid_particlePos: torch.Tensor,radius:float) -> None:
        if not self._initialized:
            self.initialize()
        if self.testbed is None:
            raise RuntimeError("FalcorGTBackend 未初始化 testbed")
        if self._fluid_particle_buffer is None:
            raise RuntimeError("FalcorGTBackend 未创建 fluid_particle_buffer（initialize 中应创建）")
        
        self._fluid_particle_buffer.from_torch(fluid_particlePos.contiguous())
        self.renderpass["particleFilterPass"].particleNum = fluid_particlePos.shape[0]
        self.renderpass["particleFilterPass"].radius = radius
        self.set_camera_for_renderPass()
        torch.cuda.synchronize()
        self.device.render_context.wait_for_falcor()
        self.testbed.frame()
        self.device.render_context.wait_for_falcor()
        surfaceNum = self.renderpass["particleFilterPass"].surfaceNum

        index = self._surfaceIndex_buffer.to_torch(shape=[int(surfaceNum)], dtype=falcor.DataType.uint32)

        return index
    
    def getDownSampleX(self) -> float:
        if not self._initialized:
            self.initialize()
        
        return self.renderpass["particleFilterPass"].downSampleX


@dataclass
class FalcorBaseLineConfig:
    width: int = 1060
    height: int = 1060
    max_fluid_particles: int = 10000000
    create_window: bool = True
    scene_path: str = "./src_v3/baseRender.pyscene"


class BaseLineRenderer:
    """Falcor baseline：BaseLinePass；粒子路径与 ``FalcorParticelFilterRenderer`` 一致（fluidParticle / particleNum / radius）。"""

    def __init__(self, config: Optional[FalcorBaseLineConfig] = None):
        self.config = config or FalcorBaseLineConfig()
        self._initialized = False
        self.device: Optional[Any] = None
        self.testbed: Optional[Any] = None
        self.render_graph: Optional[Any] = None
        self.camera: Optional[Any] = None
        self.renderpass: Dict[str, Any] = {}
        self._fluid_particle_buffer: Optional[Any] = None
        self._normalDepth_buffer: Optional[Any] = None

    def initialize(self) -> None:
        if self._initialized:
            return
        try:
            import falcor
        except ImportError as e:
            raise ImportError("Falcor 库未安装或环境未配置，无法使用 Falcor BaseLine 后端") from e

        self.device = falcor.Device(
            type=falcor.DeviceType.D3D12,
            gpu=0,
            enable_debug_layer=False,
        )

        self.testbed = falcor.Testbed(
            width=int(self.config.width),
            height=int(self.config.height),
            create_window=bool(self.config.create_window),
            device=self.device,
        )

        self.renderpass = {}
        self.render_graph = self.testbed.create_render_graph("BaseLine")

        # 类名须与插件注册一致；若 C++ 侧仅接受 tex 字段，可删掉 maxFluidParticles 项。
        self.render_graph.create_pass(
            "BaseLine",
            "BaseLinePass",
            {
                "texWidth": int(self.config.width),
                "texHeight": int(self.config.height),
                "maxFluidParticles": int(self.config.max_fluid_particles),
            },
        )

        self.renderpass["baseLinePass"] = self.render_graph.getPass("BaseLine")

        self.render_graph.mark_output("BaseLine.ResultTex")
        self.testbed.render_graph = self.render_graph

        try:
            bind_flags = (
                falcor.ResourceBindFlags.ShaderResource
                | falcor.ResourceBindFlags.UnorderedAccess
                | falcor.ResourceBindFlags.Shared
            )
            self._fluid_particle_buffer = self.device.create_structured_buffer(
                struct_size=4 * 3,
                element_count=int(self.config.max_fluid_particles),
                bind_flags=bind_flags,
            )
            self._normalDepth_buffer = self.device.create_structured_buffer(
                struct_size=4 * 4,
                element_count=self.config.width * self.config.height,
                bind_flags=bind_flags,
            )
        except Exception as e:
            raise RuntimeError(f"BaseLineRenderer 创建粒子 structured buffer 失败: {e}") from e

        try:
            p = self.renderpass["baseLinePass"]
            p.fluidParticle = self._fluid_particle_buffer
            p.normalDepth = self._normalDepth_buffer
        except Exception:
            pass

        self.testbed.load_scene(self.config.scene_path or "./src_v3/baseRender.pyscene")
        self._initialized = True

    def reload_pyscene(self, scene_path: str) -> None:
        """切换场景时重载 pyscene，复用已有 Device/Testbed。"""
        if not self._initialized:
            self.initialize()
        if self.testbed is None:
            raise RuntimeError("BaseLineRenderer 未初始化 testbed")
        p = (scene_path or "").strip() or "./src_v3/baseRender.pyscene"
        if not Path(p).is_file():
            p = "./src_v3/baseRender.pyscene"
        self.testbed.load_scene(p)
        self.config.scene_path = p

    def setCamera(self, camera: Any) -> None:
        self.camera = camera

    def setCameraFromDict(self, camera: Dict[str, Any]) -> None:
        if not self._initialized:
            self.initialize()
        if self.testbed is None or self.testbed.scene is None:
            raise RuntimeError("BaseLineRenderer 未初始化 scene")

        falcorCam = self.testbed.scene.camera
        falcorCam.position = falcor.float3(camera["origin"])
        falcorCam.target = falcor.float3(camera["target"])
        falcorCam.up = falcor.float3(camera["up"])
        falcorCam.aspectRatio = self.config.width / self.config.height
        falcorCam.focalLength = falcorCam.frameHeight / 2.0 / np.tan(
            camera["fov"] * 0.5 * np.pi / 180.0
        )

        self.camera = falcorCam

    def set_camera_for_renderPass(self) -> None:
        if not self._initialized:
            self.initialize()
        if self.camera is None:
            raise RuntimeError("BaseLineRenderer 未设置 camera")
        for mpass in self.renderpass:
            self.renderpass[mpass].camera = self.camera

    def set_gt_path(self, gtPath:str) -> None:
        if not self._initialized:
            self.initialize()
        if self.testbed is None:
            raise RuntimeError("BaseLineRenderer 未初始化 testbed")
        if gtPath == None:
            gtPath = ""
        self.renderpass["baseLinePass"].gtPath = gtPath


    def renderNormalDepth(self, fluid_particlePos: torch.Tensor, radius: float,gtPath:str) -> None:
        """与 ``FalcorParticelFilterRenderer.filterParticle`` 相同：上传粒子、写 particleNum/radius、执行一帧并读回 surface 索引。"""
        if not self._initialized:
            self.initialize()
        if self.testbed is None:
            raise RuntimeError("BaseLineRenderer 未初始化 testbed")
        if self._fluid_particle_buffer is None or self._normalDepth_buffer is None:
            raise RuntimeError("BaseLineRenderer 未创建粒子 buffer")

        self._fluid_particle_buffer.from_torch(fluid_particlePos.contiguous())
        bp = self.renderpass["baseLinePass"]
        bp.particleNum = int(fluid_particlePos.shape[0])
        bp.radius = float(radius)
        self.set_camera_for_renderPass()
        self.set_gt_path(gtPath)
        torch.cuda.synchronize()
        self.device.render_context.wait_for_falcor()
        self.testbed.frame()
        self.device.render_context.wait_for_falcor()
        normalDepth = self._normalDepth_buffer.to_torch(shape=[int(self.config.height), int(self.config.width), 4], dtype=falcor.DataType.float32)
        return normalDepth

    def getDownSampleX(self) -> float:
        if not self._initialized:
            self.initialize()
        return float(self.renderpass["baseLinePass"].downSampleX)

    def render_frame(self) -> None:
        """无粒子时仅按当前相机渲染一帧。"""
        if not self._initialized:
            self.initialize()
        if self.testbed is None:
            raise RuntimeError("BaseLineRenderer 未初始化 testbed")
        self.set_camera_for_renderPass()
        search.device.render_context.wait_for_falcor()
        self.testbed.frame()
        self.device.render_context.wait_for_falcor()



@dataclass
class FalcorRealTimeWaterConfig:
    """Falcor GT 渲染配置（分辨率、是否创建窗口等）。"""

    width: int = 1920
    height: int = 1080
    create_window: bool = True
    scene_path: str = "base.pyscene"
    data_path: str = ""
    scene: str = ""
    max_fluid_particles: int = 10000000 #最大支持2百万个粒子


class FalcorRealTimeWaterRenderer:
    """
    Falcor 实时水渲染后端。

    负责：
      - 初始化 Falcor Device/Testbed
      - 根据粒子/mesh 场景加载 Falcor 场景
      - 每帧更新相机（origin/target/up/fov）
      - 渲染出 normal+depth buffer 并读回为 [H,W,4] np.float32
    """
    def __init__(self, config: Optional[FalcorGTConfig] = None):
        self.config = config or FalcorRealTimeWaterConfig()
        self._initialized = False
        self.device: Optional[Any] = None
        self.testbed: Optional[Any] = None
        self.render_graph: Optional[Any] = None
        self.camera: Optional[Any] = None
        self.frame_id: int = -1
        """
        Buffers For python-Falcor interaction
        """
        self._save_result_buffer: Optional[Any] = None
        self._fluid_particle_buffer: Optional[Any] = None
        self._newFoam_buffer: Optional[Any] = None
        self._gt_foam_buffer: Optional[Any] = None
        self._surfaceVel_buffer: Optional[Any] = None
        self._waterND_buffer: Optional[Any] = None

    def initialize(self) -> None:
        """
        初始化 Falcor 设备与测试台，并创建 GT 渲染用的 RenderGraph。

        """
        if self._initialized:
            return
        try:
            import falcor
        except ImportError as e:
            raise ImportError("Falcor 库未安装或环境未配置，无法使用 Falcor GT 后端") from e

        self.device = falcor.Device(
            type=falcor.DeviceType.D3D12,
            gpu=0,
            enable_debug_layer=False,
        )

        # 2) 创建 Testbed（渲染窗口/离屏环境）
        self.testbed = falcor.Testbed(
            width=int(self.config.width),
            height=int(self.config.height),
            create_window=bool(self.config.create_window),
            device=self.device,
        )
        self.renderpass = {}

        self.render_graph = self.testbed.create_render_graph("RealTimeFluidRendering")

        self.render_graph.create_pass("ThicknessPass", "ThicknessPass", {
                "texWidth": int(self.config.width), 
                "texHeight": int(self.config.height)})

        self.render_graph.create_pass("BgPass", "BgPass", {
                "texWidth": int(self.config.width), 
                "texHeight": int(self.config.height)})

        self.render_graph.create_pass("ShadingPass", "ShadingPass", {
            "texWidth": int(self.config.width),
            "texHeight": int(self.config.height)})
        
        self.render_graph.create_pass("FoamPass", "FoamPass", {
            "texWidth": int(self.config.width),
            "texHeight": int(self.config.height)})
        
        self.render_graph.add_edge("BgPass.Depth", "ThicknessPass.BgDepthTex")
        self.render_graph.add_edge("BgPass.Depth","ShadingPass.BgDepthTex")
        self.render_graph.add_edge("BgPass.Color","ShadingPass.BgColorTex")
        self.render_graph.add_edge("BgPass.Depth","FoamPass.BgDepthTex")
        self.render_graph.add_edge("FoamPass.FoamColorTex","ShadingPass.FoamColorTex")
        self.render_graph.add_edge("ThicknessPass.ThicknessTex","ShadingPass.ThicknessTex")

        self.renderpass["thicknessPass"] = self.render_graph.getPass("ThicknessPass")
        self.renderpass["bgPass"] = self.render_graph.getPass("BgPass")
        self.renderpass["shadingPass"] = self.render_graph.getPass("ShadingPass")
        self.renderpass["foamPass"] = self.render_graph.getPass("FoamPass")
        #self.render_graph.mark_output("BgPass.Depth")
        #self.render_graph.mark_output("ThicknessPass.ThicknessTex")
        #self.render_graph.mark_output("FoamPass.FoamColorTex")
        self.render_graph.mark_output("ShadingPass.ResultTex")

        
        
        self.testbed.render_graph = self.render_graph

        try:
        #Create Buffers
            bind_flags = (
                falcor.ResourceBindFlags.ShaderResource
                | falcor.ResourceBindFlags.UnorderedAccess
                | falcor.ResourceBindFlags.Shared
            )

            #RGNA For RenderResult
            self._save_result_buffer = self.device.create_structured_buffer(
                struct_size=4 * 4,
                element_count=int(self.config.width) * int(self.config.height),
                bind_flags=bind_flags,
            )

            #Passing Fluid Position in float16 
            self._fluid_particle_buffer = self.device.create_structured_buffer(
                struct_size=2 * 3,
                element_count= self.config.max_fluid_particles,
                bind_flags=bind_flags,
            )

            self._waterND_buffer = self.device.create_structured_buffer(
                struct_size=2 * 4,
                element_count=int(self.config.width) * int(self.config.height),
                bind_flags=bind_flags,
            )

            self._newFoam_buffer = self.device.create_structured_buffer(
                struct_size=2 * 6,
                element_count=500000,
                bind_flags=bind_flags
                )

            # GT 泡沫位置 [M,3] float16，与 ThicknessPass 流体粒子格式一致（half3）
            self._gt_foam_buffer = self.device.create_structured_buffer(
                struct_size=2 * 3,
                element_count=5000000,
                bind_flags=bind_flags,
            )
            
            self._surfaceVelDepth_buffer = self.device.create_structured_buffer(
                struct_size=4 * 2,
                element_count=int(self.config.width) * int(self.config.height),
                bind_flags=bind_flags
                )

            self._result_buffer = self.device.create_structured_buffer(
                struct_size=4 *4,
                element_count=int(self.config.width) * int(self.config.height),
                bind_flags=bind_flags
            )
            

        except Exception as e:
            raise RuntimeError(f"创建 Falcor NormalDepth structured buffer 失败: {e}") from e

        try:
            #Bind Buffer
            self.renderpass["thicknessPass"].fluidParticle = self._fluid_particle_buffer
            #Bind Texture
            self.renderpass["shadingPass"].waterSurfaceND = self._waterND_buffer

            self.renderpass["foamPass"].newFoam = self._newFoam_buffer
            self.renderpass["foamPass"].surfaceVelDepth = self._surfaceVelDepth_buffer
            self.renderpass["shadingPass"].result = self._result_buffer

        except Exception:
            pass

        try:
            self.renderpass["foamPass"].gtFoam = self._gt_foam_buffer
        except Exception:
            pass

        pyscene = resolve_base_render_pyscene(self.config.data_path, self.config.scene)
        self.testbed.load_scene(pyscene)

        self._initialized = True

    def UpdataFrameId(self) -> None:
        if not self._initialized:
            self.initialize()
        if self.testbed is None:
            raise RuntimeError("FalcorGTBackend 未初始化 testbed")
        if self.testbed.scene is None:
            raise RuntimeError("FalcorGTBackend 未加载场景")
        self.renderpass["bgPass"].frame = self.frame_id

    def setFrameId(self, frame_id: int) -> None:
        if not self._initialized:
            self.initialize()
        if self.testbed is None:
            raise RuntimeError("FalcorGTBackend 未初始化 testbed")
        if self.testbed.scene is None:
            raise RuntimeError("FalcorGTBackend 未加载场景")
        self.frame_id = frame_id
        self.UpdataFrameId()
    
    def set_camera_from_dict(self, camera: Dict[str, Any]) -> None:

        if not self._initialized:
            self.initialize()

        falcorCam = self.testbed.scene.camera
        falcorCam.position = falcor.float3(camera["origin"])
        falcorCam.target = falcor.float3(camera["target"])
        falcorCam.up = falcor.float3(camera["up"])
        falcorCam.aspectRatio = self.config.width / self.config.height
        falcorCam.focalLength = falcorCam.frameHeight / 2.0 / np.tan(camera["fov"] * 0.5 * np.pi / 180.0)

    def set_camera_for_renderPass(self) -> None:
        if not self._initialized:
            self.initialize()
        if self.camera is None:
            raise RuntimeError("FalcorGTBackend 未初始化 camera")
        for mpass in self.renderpass:
            self.renderpass[mpass].camera = self.camera

    def render_real_time_water(
        self,
        fluid_particlePos: torch.Tensor,
        radius: float,
        waterND: torch.Tensor,
        surfaceVelDepth: torch.Tensor,
        newFoam: torch.Tensor,
        refresh: bool,
        gt_foam_positions: Optional[torch.Tensor] = None,
        gtNewFoamNum: int = 0,
    ):
        if not self._initialized:
            self.initialize()

        if self.testbed is None:
            raise RuntimeError("FalcorGTBackend 未初始化 testbed")
        if self._fluid_particle_buffer is None:
            raise RuntimeError("FalcorGTBackend 未创建 fluid_particle_buffer（initialize 中应创建）")

        if fluid_particlePos.dtype != torch.float16:
            fluid_particlePos = fluid_particlePos.to(torch.float16)
        if fluid_particlePos.shape[0] > self.config.max_fluid_particles:
            raise RuntimeError("粒子数量超过最大支持数量")
        if fluid_particlePos.ndim != 2 or fluid_particlePos.shape[1] != 3:
            raise RuntimeError("需要输入 Position 的形状为 [N,3]")
        
        if newFoam.dtype != torch.float16:
            newFoam = newFoam.to(torch.float16)
        if newFoam.shape[0] > 500000:
            raise RuntimeError("泡沫数量超过最大支持数量")
        if newFoam.shape[1] != 6:
            raise RuntimeError("泡沫的形状应为 [N,6]")
        
        if surfaceVelDepth.dtype != torch.float16:
            surfaceVelDepth = surfaceVelDepth.to(torch.float16)
        if surfaceVelDepth.shape[2] != 4 or surfaceVelDepth.shape[0] != self.config.height or surfaceVelDepth.shape[1] != self.config.width:
            raise RuntimeError("surfaceVelDepth的形状为[{},{},{}],当前为 [{},{},{}]".format(surfaceVelDepth.shape[0],surfaceVelDepth.shape[1],surfaceVelDepth.shape[2]))
        

        if waterND.dtype != torch.float16:
            waterND = waterND.to(torch.float16)
        if waterND.shape[2] != 4 or waterND.shape[0] != self.config.height or waterND.shape[1] != self.config.width:
            raise RuntimeError("水ND的形状为 [H,W,4],当前为 [{},{},{}]".format(waterND.shape[0],waterND.shape[1],waterND.shape[2]))
        

        if gt_foam_positions is not None:
            if gt_foam_positions.dtype != torch.float16:
                gt_foam_positions = gt_foam_positions.to(torch.float16)
            if gt_foam_positions.shape[0] > 5000000:
                raise RuntimeError("GT泡沫数量超过最大支持数量")
            if gt_foam_positions.shape[1] != 3:
                raise RuntimeError("GT泡沫的形状应为 [M,3]")

            if gt_foam_positions.shape[0] > 5:
                self._gt_foam_buffer.from_torch(gt_foam_positions.contiguous())
                self.renderpass["foamPass"].gtFoamNum = gt_foam_positions.shape[0]
            else:
                self.renderpass["foamPass"].gtFoamNum = 0
        else:
            self.renderpass["foamPass"].gtFoamNum = 0

        self._fluid_particle_buffer.from_torch(fluid_particlePos.contiguous())
        self._surfaceVelDepth_buffer.from_torch(surfaceVelDepth.contiguous())
        if newFoam.shape[0] > 5:
            self._newFoam_buffer.from_torch(newFoam.contiguous())
        self._waterND_buffer.from_torch(waterND.contiguous())
        self.renderpass["thicknessPass"].fluidParticleNum = fluid_particlePos.shape[0]
        self.renderpass["thicknessPass"].fluidParticleRadius = radius
        if newFoam.shape[0] > 5:
            self.renderpass["foamPass"].newFoamNum = newFoam.shape[0]
        else:
            self.renderpass["foamPass"].newFoamNum = 0


        self.renderpass["foamPass"].waterTrColor = self.renderpass["shadingPass"].waterTrColor
        self.renderpass["foamPass"].waterTrStrenth = self.renderpass["shadingPass"].waterTrStrenth
        self.renderpass["foamPass"].mode = self.renderpass["shadingPass"].mode
        self.renderpass["foamPass"].refresh = refresh
        self.renderpass["foamPass"].gtNewFoamNum = gtNewFoamNum
        self.set_camera_for_renderPass()
        torch.cuda.synchronize()
        self.device.render_context.wait_for_falcor()
        self.testbed.frame()
        self.device.render_context.wait_for_falcor()

        result = self._result_buffer.to_torch(shape=[int(self.config.height), int(self.config.width), 4], dtype=falcor.DataType.float32)

        return result
    

    def get_camera(self) -> Dict[str, Any]:
        if not self._initialized:
            self.initialize()
        if self.testbed is None:
            raise RuntimeError("FalcorGTBackend 未初始化 testbed")
        if self.testbed.scene is None:
            raise RuntimeError("FalcorGTBackend 未加载场景")
        
        camera = {}
        cam = self.testbed.scene.camera
        cam.aspectRatio = self.config.width / self.config.height
        camera["origin"] = [cam.posX,cam.posY,cam.posZ]
        camera["target"] = [cam.lookatX,cam.lookatY,cam.lookatZ]
        camera["up"] = [cam.upX,cam.upY,cam.upZ]
        f = self.testbed.scene.camera.focalLength
        h = self.testbed.scene.camera.frameHeight
        fov = cam.fovy * 180.0 / np.pi
        camera["fov"] = fov
        self.camera = cam

        return camera
    
    def get_FalcorCamInstance(self):
        _ = self.get_camera()
        return self.camera
    
    def getFoamDensity(self) -> torch.Tensor:
        if not self._initialized:
            self.initialize()
        if self.testbed is None:
            raise RuntimeError("FalcorGTBackend 未初始化 testbed")
        if self.testbed.scene is None:
            raise RuntimeError("FalcorGTBackend 未加载场景")
        if self.renderpass["foamPass"] is None:
            raise RuntimeError("FalcorGTBackend 未创建 foamPass")
        
        return self.renderpass["foamPass"].foamDensity

    
    def getPause(self) -> bool:
        if not self._initialized:
            self.initialize()
        if self.testbed is None:
            raise RuntimeError("FalcorGTBackend 未初始化 testbed")
        if self.testbed.scene is None:
            raise RuntimeError("FalcorGTBackend 未加载场景")
        return self.renderpass["foamPass"].pause

    def getSaveResult(self) -> bool:
        """
        从 Falcor foamPass 读取“是否保存结果”的开关。
        兼容不同命名（saveResult/save_result）；不存在时返回 False。
        """
        if not self._initialized:
            self.initialize()
        if self.testbed is None:
            raise RuntimeError("FalcorGTBackend 未初始化 testbed")
        if self.testbed.scene is None:
            raise RuntimeError("FalcorGTBackend 未加载场景")
        return self.renderpass["shadingPass"].saveResult

    def setSaveResult(self, enabled: bool) -> None:
        """设置 Falcor foamPass 的保存开关。"""
        if not self._initialized:
            self.initialize()
        if self.testbed is None:
            raise RuntimeError("FalcorGTBackend 未初始化 testbed")
        if self.testbed.scene is None:
            raise RuntimeError("FalcorGTBackend 未加载场景")
        self.renderpass["shadingPass"].saveResult = enabled

    def getSaveFrames(self) -> int:
        """
        从 Falcor shadingPass 读取保存张数配置。
        兼容字段名：saveFrames / saveFrameNum / save_frames。
        若不存在或非法，返回 1。
        """
        if not self._initialized:
            self.initialize()
        if self.testbed is None:
            raise RuntimeError("FalcorGTBackend 未初始化 testbed")
        if self.testbed.scene is None:
            raise RuntimeError("FalcorGTBackend 未加载场景")
        return self.renderpass["shadingPass"].saveFrames
    
    def getSaveFrameStart(self) -> int:
        if not self._initialized:
            self.initialize()
        if self.testbed is None:
            raise RuntimeError("FalcorGTBackend 未初始化 testbed")
        if self.testbed.scene is None:
            raise RuntimeError("FalcorGTBackend 未加载场景")
        return self.renderpass["shadingPass"].saveStartFrames
        #return 0
    

    def SaveResult(self,path:str,id) -> None:
        if not self._initialized:
            self.initialize()
        if self.testbed is None:
            raise RuntimeError("FalcorGTBackend 未初始化 testbed")
        if self.testbed.scene is None:
            raise RuntimeError("FalcorGTBackend 未加载场景")
        if self.renderpass["foamPass"] is None:
            raise RuntimeError("FalcorGTBackend 未创建 foamPass")
        
        self.testbed.capture_output(path,id)

    def getSampleTimesAndNoiseThreshold(self) -> Tuple[int,float]:
        if not self._initialized:
            self.initialize()
        if self.testbed is None:
            raise RuntimeError("FalcorGTBackend 未初始化 testbed")
        if self.testbed.scene is None:
            raise RuntimeError("FalcorGTBackend 未加载场景")
        if self.renderpass["foamPass"] is None:
            raise RuntimeError("FalcorGTBackend 未创建 foamPass")
        return int(self.renderpass["foamPass"].sampleTimes),float(self.renderpass["foamPass"].noiseThreshold)
    

    def getNormalSelected(self):
        if not self._initialized:
            self.initialize()
        if self.testbed is None:
            raise RuntimeError("FalcorGTBackend 未初始化 testbed")
        if self.testbed.scene is None:
            raise RuntimeError("FalcorGTBackend 未加载场景")
        if self.renderpass["shadingPass"] is None:
            raise RuntimeError("FalcorGTBackend 未创建 shadingPass")
        
        return self.renderpass["shadingPass"].method
    

    def setTimeStep(self, dt: float) -> None:
       #print(dt)
        self.renderpass["foamPass"].pause = False
        self.renderpass["foamPass"].timeStep = dt
    
    def getNeedRefresh(self)->bool:
        mode = self.renderpass["shadingPass"].mode
        return mode==0 or mode==2
    
    def getSaveCur(self)->bool:
        return self.renderpass["shadingPass"].saveCur
    
    def savedCur(self)->None:
        self.renderpass["shadingPass"].saveCur = False
    
    def UseGTNewFoam(self)->bool:
        return self.renderpass["foamPass"].useGTNewFoam
    
    def getGaussianFilterKernelSize(self)->int:
        return self.renderpass["shadingPass"].gaussianFilterKernelSize
    

    def getGaussianFilterSigma(self)->float:
        return self.renderpass["shadingPass"].gaussianFilterSigma

    def getGaussianFilterIterations(self) -> int:
        """滤波轮次；Falcor 未暴露 ``gaussianFilterIterations`` 时默认为 1。"""
        sp = self.renderpass["shadingPass"]
        return int(getattr(sp, "gaussianFilterIterations", 1))