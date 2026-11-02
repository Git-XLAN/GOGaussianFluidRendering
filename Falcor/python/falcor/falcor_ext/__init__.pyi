"""Falcor python bindings"""
from __future__ import annotations
import falcor.falcor_ext
import typing
import os
import pathlib

__all__ = [
    "AABB",
    "AccumulatePass",
    "AdapterInfo",
    "AlphaMode",
    "Alt",
    "AnalyticAreaLight",
    "Animatable",
    "Animation",
    "AssertionError",
    "AssetCategory",
    "AssetResolver",
    "BSDFOptimizer",
    "BackGroundPass",
    "BaseLinePass",
    "BasicMaterial",
    "BgPass",
    "BlendState",
    "BlitPass",
    "Buffer",
    "Camera",
    "Clock",
    "ClothMaterial",
    "ComparePass",
    "CompareSwapPass",
    "ComparisonFunc",
    "CompositionOrder",
    "ComputeContext",
    "ComputePass",
    "ComputeState",
    "CopyContext",
    "Ctrl",
    "DLSSPass",
    "DataType",
    "DepthStencilState",
    "DepthStencilView",
    "Device",
    "DeviceType",
    "DiffMode",
    "DirectionalLight",
    "DiscLight",
    "DistantLight",
    "EnvMap",
    "Fbo",
    "FoamParticleProcess",
    "FoamPass",
    "FoamShadingPass",
    "GTPass",
    "GTRenderingPass",
    "GaussianBlur",
    "GpuTimer",
    "GradConfig",
    "GradientType",
    "GraphicsState",
    "Grid",
    "GridVolume",
    "HairMaterial",
    "IMaterial",
    "ImporterError",
    "Key",
    "KeyboardEvent",
    "Light",
    "Logger",
    "MATERIAL_PARAM_LAYOUTS",
    "MERLMaterial",
    "MERLMixMaterial",
    "Material",
    "MaterialTextureSlot",
    "MaterialType",
    "MemoryType",
    "MeshDesc",
    "ModifierFlags",
    "MouseButton",
    "MouseEvent",
    "None",
    "ObjectID",
    "PBRTCoatedConductorMaterial",
    "PBRTCoatedDiffuseMaterial",
    "PBRTConductorMaterial",
    "PBRTDielectricMaterial",
    "PBRTDiffuseMaterial",
    "PBRTDiffuseTransmissionMaterial",
    "ParameterBlockReflection",
    "ParticleFilterPass",
    "PathTracer",
    "PixelStats",
    "PointLight",
    "Profiler",
    "ProfilerEvent",
    "Program",
    "ProgramDesc",
    "ProgramReflection",
    "RGLMaterial",
    "RasterizerState",
    "RectLight",
    "Rectangle",
    "ReflectionArrayType",
    "ReflectionBasicType",
    "ReflectionInterfaceType",
    "ReflectionResourceType",
    "ReflectionStructType",
    "ReflectionType",
    "ReflectionVar",
    "RenderContext",
    "RenderGraph",
    "RenderPass",
    "RenderTargetView",
    "Resource",
    "ResourceBindFlags",
    "ResourceFormat",
    "RuntimeError",
    "SDFGrid",
    "SSFR",
    "SSRShading",
    "Sampler",
    "Scene",
    "SceneBuilder",
    "SceneBuilderFlags",
    "SceneDebugger",
    "SceneGradients",
    "SceneRenderSettings",
    "SearchPathPriority",
    "Settings",
    "ShaderModel",
    "ShaderResourceView",
    "ShaderVar",
    "ShadingModel",
    "ShadingPass",
    "Shift",
    "SimplePostFX",
    "SlangCompilerFlags",
    "SphereLight",
    "StandardMaterial",
    "SwapPass",
    "TAA",
    "TestPyTorchPass",
    "TestRtProgram",
    "Testbed",
    "Texture",
    "TextureAddressingMode",
    "TextureChannelFlags",
    "TextureFilteringMode",
    "TextureReductionMode",
    "ThicknessPass",
    "ToneMapper",
    "TrainGTBuffer",
    "Transform",
    "TriangleMesh",
    "TriangleMeshImportFlags",
    "UnorderedAccessView",
    "Vao",
    "VertexLayout",
    "Volume",
    "WARDiffPathTracer",
    "WaterFoamShading",
    "WaterParticleProcess",
    "WaterShadingPass",
    "WhittedRayTracer",
    "Window",
    "WindowMode",
    "bool2",
    "bool3",
    "bool4",
    "createPass",
    "float16",
    "float16_t",
    "float16_t2",
    "float16_t3",
    "float16_t4",
    "float2",
    "float3",
    "float32",
    "float3x3",
    "float3x4",
    "float4",
    "float4x4",
    "float64",
    "get_material_param_layout",
    "inspect_ndarray",
    "int16",
    "int2",
    "int3",
    "int32",
    "int4",
    "int64",
    "int8",
    "loadPlugin",
    "load_plugin",
    "ui",
    "uint16",
    "uint2",
    "uint3",
    "uint32",
    "uint4",
    "uint64",
    "uint8"
]


class AABB():
    def __and__(self, arg0: AABB) -> AABB: ...
    def __eq__(self, arg0: AABB) -> bool: ...
    def __iand__(self, arg0: AABB) -> AABB: ...
    @typing.overload
    def __init__(self) -> None: ...
    @typing.overload
    def __init__(self, min_point: float3, max_point: float3) -> None: ...
    @typing.overload
    def __init__(self, p: float3) -> None: ...
    def __ior__(self, arg0: AABB) -> AABB: ...
    def __ne__(self, arg0: AABB) -> bool: ...
    def __or__(self, arg0: AABB) -> AABB: ...
    def __repr__(self) -> str: ...
    def __str__(self) -> str: ...
    @typing.overload
    def include(self, b: AABB) -> AABB: ...
    @typing.overload
    def include(self, p: float3) -> AABB: ...
    def intersection(self, arg0: AABB) -> AABB: ...
    def invalidate(self) -> None: ...
    @property
    def area(self) -> float:
        """
        :type: float
        """
    @property
    def center(self) -> float3:
        """
        :type: float3
        """
    @property
    def extent(self) -> float3:
        """
        :type: float3
        """
    @property
    def maxPoint(self) -> float3:
        """
        :type: float3
        """
    @maxPoint.setter
    def maxPoint(self, arg0: float3) -> None:
        pass
    @property
    def max_point(self) -> float3:
        """
        :type: float3
        """
    @max_point.setter
    def max_point(self, arg0: float3) -> None:
        pass
    @property
    def minPoint(self) -> float3:
        """
        :type: float3
        """
    @minPoint.setter
    def minPoint(self, arg0: float3) -> None:
        pass
    @property
    def min_point(self) -> float3:
        """
        :type: float3
        """
    @min_point.setter
    def min_point(self, arg0: float3) -> None:
        pass
    @property
    def radius(self) -> float:
        """
        :type: float
        """
    @property
    def valid(self) -> bool:
        """
        :type: bool
        """
    @property
    def volume(self) -> float:
        """
        :type: float
        """
    __hash__ = None
    pass
class RenderPass():
    def getDictionary(self) -> dict: ...
    def set_properties(self, arg0: dict) -> None: ...
    @property
    def desc(self) -> str:
        """
        :type: str
        """
    @property
    def name(self) -> str:
        """
        :type: str
        """
    @property
    def properties(self) -> dict:
        """
        :type: dict
        """
    @property
    def type(self) -> str:
        """
        :type: str
        """
    pass
class AdapterInfo():
    @property
    def device_id(self) -> int:
        """
        :type: int
        """
    @property
    def luid(self) -> Falcor::AdapterLUID:
        """
        :type: Falcor::AdapterLUID
        """
    @property
    def name(self) -> str:
        """
        :type: str
        """
    @property
    def vendor_id(self) -> int:
        """
        :type: int
        """
    pass
class AlphaMode():
    """
    Members:

      Opaque

      Mask
    """
    def __eq__(self, other: object) -> bool: ...
    def __getstate__(self) -> int: ...
    def __hash__(self) -> int: ...
    def __index__(self) -> int: ...
    def __init__(self, value: int) -> None: ...
    def __int__(self) -> int: ...
    def __ne__(self, other: object) -> bool: ...
    def __repr__(self) -> str: ...
    def __setstate__(self, state: int) -> None: ...
    @property
    def name(self) -> str:
        """
        :type: str
        """
    @property
    def value(self) -> int:
        """
        :type: int
        """
    Mask: falcor.falcor_ext.AlphaMode # value = AlphaMode.Mask
    Opaque: falcor.falcor_ext.AlphaMode # value = AlphaMode.Opaque
    __members__: dict # value = {'Opaque': AlphaMode.Opaque, 'Mask': AlphaMode.Mask}
    pass
class Animatable():
    @property
    def animated(self) -> bool:
        """
        :type: bool
        """
    @animated.setter
    def animated(self, arg1: bool) -> None:
        pass
    @property
    def hasAnimation(self) -> bool:
        """
        :type: bool
        """
    pass
class Light(Animatable):
    @property
    def active(self) -> bool:
        """
        :type: bool
        """
    @active.setter
    def active(self, arg1: bool) -> None:
        pass
    @property
    def animated(self) -> bool:
        """
        :type: bool
        """
    @animated.setter
    def animated(self, arg1: bool) -> None:
        pass
    @property
    def intensity(self) -> float3:
        """
        :type: float3
        """
    @intensity.setter
    def intensity(self, arg1: float3) -> None:
        pass
    @property
    def name(self) -> str:
        """
        :type: str
        """
    @name.setter
    def name(self, arg1: str) -> None:
        pass
    pass
class Animation():
    class Behavior():
        """
        Members:

          Constant

          Linear

          Cycle

          Oscillate
        """
        def __eq__(self, other: object) -> bool: ...
        def __getstate__(self) -> int: ...
        def __hash__(self) -> int: ...
        def __index__(self) -> int: ...
        def __init__(self, value: int) -> None: ...
        def __int__(self) -> int: ...
        def __ne__(self, other: object) -> bool: ...
        def __repr__(self) -> str: ...
        def __setstate__(self, state: int) -> None: ...
        @property
        def name(self) -> str:
            """
            :type: str
            """
        @property
        def value(self) -> int:
            """
            :type: int
            """
        Constant: falcor.falcor_ext.Animation.Behavior # value = Behavior.Constant
        Cycle: falcor.falcor_ext.Animation.Behavior # value = Behavior.Cycle
        Linear: falcor.falcor_ext.Animation.Behavior # value = Behavior.Linear
        Oscillate: falcor.falcor_ext.Animation.Behavior # value = Behavior.Oscillate
        __members__: dict # value = {'Constant': Behavior.Constant, 'Linear': Behavior.Linear, 'Cycle': Behavior.Cycle, 'Oscillate': Behavior.Oscillate}
        pass
    class InterpolationMode():
        """
        Members:

          Linear

          Hermite
        """
        def __eq__(self, other: object) -> bool: ...
        def __getstate__(self) -> int: ...
        def __hash__(self) -> int: ...
        def __index__(self) -> int: ...
        def __init__(self, value: int) -> None: ...
        def __int__(self) -> int: ...
        def __ne__(self, other: object) -> bool: ...
        def __repr__(self) -> str: ...
        def __setstate__(self, state: int) -> None: ...
        @property
        def name(self) -> str:
            """
            :type: str
            """
        @property
        def value(self) -> int:
            """
            :type: int
            """
        Hermite: falcor.falcor_ext.Animation.InterpolationMode # value = InterpolationMode.Hermite
        Linear: falcor.falcor_ext.Animation.InterpolationMode # value = InterpolationMode.Linear
        __members__: dict # value = {'Linear': InterpolationMode.Linear, 'Hermite': InterpolationMode.Hermite}
        pass
    def __init__(self, name: str, nodeID: ObjectID, duration: float) -> None: ...
    def addKeyframe(self, arg0: float, arg1: Transform) -> None: ...
    @property
    def duration(self) -> float:
        """
        :type: float
        """
    @property
    def enableWarping(self) -> bool:
        """
        :type: bool
        """
    @enableWarping.setter
    def enableWarping(self, arg1: bool) -> None:
        pass
    @property
    def interpolationMode(self) -> Animation.InterpolationMode:
        """
        :type: Animation.InterpolationMode
        """
    @interpolationMode.setter
    def interpolationMode(self, arg1: Animation.InterpolationMode) -> None:
        pass
    @property
    def name(self) -> str:
        """
        :type: str
        """
    @property
    def nodeID(self) -> ObjectID:
        """
        :type: ObjectID
        """
    @property
    def postInfinityBehavior(self) -> Animation.Behavior:
        """
        :type: Animation.Behavior
        """
    @postInfinityBehavior.setter
    def postInfinityBehavior(self, arg1: Animation.Behavior) -> None:
        pass
    @property
    def preInfinityBehavior(self) -> Animation.Behavior:
        """
        :type: Animation.Behavior
        """
    @preInfinityBehavior.setter
    def preInfinityBehavior(self, arg1: Animation.Behavior) -> None:
        pass
    pass
class AssertionError(Exception, BaseException):
    pass
class AssetCategory():
    """
    Members:

      Any

      Scene

      Texture
    """
    def __eq__(self, other: object) -> bool: ...
    def __getstate__(self) -> int: ...
    def __hash__(self) -> int: ...
    def __index__(self) -> int: ...
    def __init__(self, value: int) -> None: ...
    def __int__(self) -> int: ...
    def __ne__(self, other: object) -> bool: ...
    def __repr__(self) -> str: ...
    def __setstate__(self, state: int) -> None: ...
    @property
    def name(self) -> str:
        """
        :type: str
        """
    @property
    def value(self) -> int:
        """
        :type: int
        """
    Any: falcor.falcor_ext.AssetCategory # value = AssetCategory.Any
    Scene: falcor.falcor_ext.AssetCategory # value = AssetCategory.Scene
    Texture: falcor.falcor_ext.AssetCategory # value = AssetCategory.Texture
    __members__: dict # value = {'Any': AssetCategory.Any, 'Scene': AssetCategory.Scene, 'Texture': AssetCategory.Texture}
    pass
class AssetResolver():
    def add_search_path(self, path: os.PathLike, priority: SearchPathPriority = SearchPathPriority.Last, category: AssetCategory = AssetCategory.Any) -> None: ...
    def resolve_path(self, path: os.PathLike, category: AssetCategory = AssetCategory.Any) -> os.PathLike: ...
    def resolve_path_pattern(self, path: os.PathLike, pattern: str, first_match_only: bool = False, category: AssetCategory = AssetCategory.Any) -> typing.List[os.PathLike]: ...
    default_resolver: falcor.falcor_ext.AssetResolver
    pass
class BSDFOptimizer(RenderPass):
    def compute_bsdf_grads(self) -> Buffer: ...
    @property
    def bsdf_slice_resolution(self) -> int:
        """
        :type: int
        """
    @bsdf_slice_resolution.setter
    def bsdf_slice_resolution(self, arg1: int) -> None:
        pass
    @property
    def init_material_id(self) -> int:
        """
        :type: int
        """
    @property
    def ref_material_id(self) -> int:
        """
        :type: int
        """
    pass
class BackGroundPass(RenderPass):
    @property
    def frame(self) -> int:
        """
        :type: int
        """
    @frame.setter
    def frame(self, arg1: int) -> None:
        pass
    pass
class BaseLinePass(RenderPass):
    @property
    def camera(self) -> Camera:
        """
        :type: Camera
        """
    @camera.setter
    def camera(self, arg1: Camera) -> None:
        pass
    @property
    def fluidParticle(self) -> Buffer:
        """
        :type: Buffer
        """
    @fluidParticle.setter
    def fluidParticle(self, arg1: Buffer) -> None:
        pass
    @property
    def normalDepth(self) -> Buffer:
        """
        :type: Buffer
        """
    @normalDepth.setter
    def normalDepth(self, arg1: Buffer) -> None:
        pass
    @property
    def particleNum(self) -> int:
        """
        :type: int
        """
    @particleNum.setter
    def particleNum(self, arg1: int) -> None:
        pass
    @property
    def particles(self) -> Buffer:
        """
        :type: Buffer
        """
    @particles.setter
    def particles(self, arg1: Buffer) -> None:
        pass
    @property
    def radius(self) -> float:
        """
        :type: float
        """
    @radius.setter
    def radius(self, arg1: float) -> None:
        pass
    pass
class IMaterial():
    def clearTexture(self, slot: MaterialTextureSlot) -> None: ...
    def getTexture(self, slot: MaterialTextureSlot) -> Texture: ...
    def loadTexture(self, slot: MaterialTextureSlot, path: os.PathLike, useSrgb: bool = True) -> bool: ...
    def load_texture(self, slot: MaterialTextureSlot, path: os.PathLike, use_srgb: bool = True) -> bool: ...
    def setRoughnessMollification(self, value: float) -> None: ...
    def setTexture(self, slot: MaterialTextureSlot, texture: Texture) -> bool: ...
    @property
    def alphaMode(self) -> AlphaMode:
        """
        :type: AlphaMode
        """
    @alphaMode.setter
    def alphaMode(self, arg1: AlphaMode) -> None:
        pass
    @property
    def alphaThreshold(self) -> float:
        """
        :type: float
        """
    @alphaThreshold.setter
    def alphaThreshold(self, arg1: float) -> None:
        pass
    @property
    def doubleSided(self) -> bool:
        """
        :type: bool
        """
    @doubleSided.setter
    def doubleSided(self, arg1: bool) -> None:
        pass
    @property
    def emissive(self) -> bool:
        """
        :type: bool
        """
    @property
    def name(self) -> str:
        """
        :type: str
        """
    @name.setter
    def name(self, arg1: str) -> None:
        pass
    @property
    def nestedPriority(self) -> int:
        """
        :type: int
        """
    @nestedPriority.setter
    def nestedPriority(self, arg1: int) -> None:
        pass
    @property
    def textureTransform(self) -> Transform:
        """
        :type: Transform
        """
    @textureTransform.setter
    def textureTransform(self, arg1: Transform) -> None:
        pass
    @property
    def thinSurface(self) -> bool:
        """
        :type: bool
        """
    @thinSurface.setter
    def thinSurface(self, arg1: bool) -> None:
        pass
    @property
    def type(self) -> MaterialType:
        """
        :type: MaterialType
        """
    PARAM_COUNT = 20
    pass
class BgPass(RenderPass):
    @property
    def camera(self) -> Camera:
        """
        :type: Camera
        """
    @camera.setter
    def camera(self, arg1: Camera) -> None:
        pass
    @property
    def frame(self) -> int:
        """
        :type: int
        """
    @frame.setter
    def frame(self, arg1: int) -> None:
        pass
    pass
class BlendState():
    pass
class BlitPass(RenderPass):
    @property
    def filter(self) -> str:
        """
        :type: str
        """
    @filter.setter
    def filter(self, arg1: str) -> None:
        pass
    pass
class Resource():
    pass
class Camera(Animatable):
    def __init__(self, name: str = '') -> None: ...
    @property
    def ISOSpeed(self) -> float:
        """
        :type: float
        """
    @ISOSpeed.setter
    def ISOSpeed(self, arg1: float) -> None:
        pass
    @property
    def apertureRadius(self) -> float:
        """
        :type: float
        """
    @apertureRadius.setter
    def apertureRadius(self, arg1: float) -> None:
        pass
    @property
    def aspectRatio(self) -> float:
        """
        :type: float
        """
    @aspectRatio.setter
    def aspectRatio(self, arg1: float) -> None:
        pass
    @property
    def farPlane(self) -> float:
        """
        :type: float
        """
    @farPlane.setter
    def farPlane(self, arg1: float) -> None:
        pass
    @property
    def focalDistance(self) -> float:
        """
        :type: float
        """
    @focalDistance.setter
    def focalDistance(self, arg1: float) -> None:
        pass
    @property
    def focalLength(self) -> float:
        """
        :type: float
        """
    @focalLength.setter
    def focalLength(self, arg1: float) -> None:
        pass
    @property
    def fovx(self) -> float:
        """
        :type: float
        """
    @property
    def fovy(self) -> float:
        """
        :type: float
        """
    @property
    def frameHeight(self) -> float:
        """
        :type: float
        """
    @frameHeight.setter
    def frameHeight(self, arg1: float) -> None:
        pass
    @property
    def frameWidth(self) -> float:
        """
        :type: float
        """
    @frameWidth.setter
    def frameWidth(self, arg1: float) -> None:
        pass
    @property
    def lookatX(self) -> float:
        """
        :type: float
        """
    @property
    def lookatY(self) -> float:
        """
        :type: float
        """
    @property
    def lookatZ(self) -> float:
        """
        :type: float
        """
    @property
    def name(self) -> str:
        """
        :type: str
        """
    @name.setter
    def name(self, arg1: str) -> None:
        pass
    @property
    def nearPlane(self) -> float:
        """
        :type: float
        """
    @nearPlane.setter
    def nearPlane(self, arg1: float) -> None:
        pass
    @property
    def posX(self) -> float:
        """
        :type: float
        """
    @property
    def posY(self) -> float:
        """
        :type: float
        """
    @property
    def posZ(self) -> float:
        """
        :type: float
        """
    @property
    def position(self) -> float3:
        """
        :type: float3
        """
    @position.setter
    def position(self, arg1: float3) -> None:
        pass
    @property
    def projMatrix00(self) -> float:
        """
        :type: float
        """
    @property
    def projMatrix01(self) -> float:
        """
        :type: float
        """
    @property
    def projMatrix02(self) -> float:
        """
        :type: float
        """
    @property
    def projMatrix03(self) -> float:
        """
        :type: float
        """
    @property
    def projMatrix10(self) -> float:
        """
        :type: float
        """
    @property
    def projMatrix11(self) -> float:
        """
        :type: float
        """
    @property
    def projMatrix12(self) -> float:
        """
        :type: float
        """
    @property
    def projMatrix13(self) -> float:
        """
        :type: float
        """
    @property
    def projMatrix20(self) -> float:
        """
        :type: float
        """
    @property
    def projMatrix21(self) -> float:
        """
        :type: float
        """
    @property
    def projMatrix22(self) -> float:
        """
        :type: float
        """
    @property
    def projMatrix23(self) -> float:
        """
        :type: float
        """
    @property
    def projMatrix30(self) -> float:
        """
        :type: float
        """
    @property
    def projMatrix31(self) -> float:
        """
        :type: float
        """
    @property
    def projMatrix32(self) -> float:
        """
        :type: float
        """
    @property
    def projMatrix33(self) -> float:
        """
        :type: float
        """
    @property
    def shutterSpeed(self) -> float:
        """
        :type: float
        """
    @shutterSpeed.setter
    def shutterSpeed(self, arg1: float) -> None:
        pass
    @property
    def tanFovx(self) -> float:
        """
        :type: float
        """
    @property
    def tanFovy(self) -> float:
        """
        :type: float
        """
    @property
    def target(self) -> float3:
        """
        :type: float3
        """
    @target.setter
    def target(self, arg1: float3) -> None:
        pass
    @property
    def up(self) -> float3:
        """
        :type: float3
        """
    @up.setter
    def up(self, arg1: float3) -> None:
        pass
    @property
    def upX(self) -> float:
        """
        :type: float
        """
    @property
    def upY(self) -> float:
        """
        :type: float
        """
    @property
    def upZ(self) -> float:
        """
        :type: float
        """
    @property
    def viewMatrix00(self) -> float:
        """
        :type: float
        """
    @property
    def viewMatrix01(self) -> float:
        """
        :type: float
        """
    @property
    def viewMatrix02(self) -> float:
        """
        :type: float
        """
    @property
    def viewMatrix03(self) -> float:
        """
        :type: float
        """
    @property
    def viewMatrix10(self) -> float:
        """
        :type: float
        """
    @property
    def viewMatrix11(self) -> float:
        """
        :type: float
        """
    @property
    def viewMatrix12(self) -> float:
        """
        :type: float
        """
    @property
    def viewMatrix13(self) -> float:
        """
        :type: float
        """
    @property
    def viewMatrix20(self) -> float:
        """
        :type: float
        """
    @property
    def viewMatrix21(self) -> float:
        """
        :type: float
        """
    @property
    def viewMatrix22(self) -> float:
        """
        :type: float
        """
    @property
    def viewMatrix23(self) -> float:
        """
        :type: float
        """
    @property
    def viewMatrix30(self) -> float:
        """
        :type: float
        """
    @property
    def viewMatrix31(self) -> float:
        """
        :type: float
        """
    @property
    def viewMatrix32(self) -> float:
        """
        :type: float
        """
    @property
    def viewMatrix33(self) -> float:
        """
        :type: float
        """
    pass
class Clock():
    def pause(self) -> Clock: ...
    def play(self) -> Clock: ...
    def step(self, frames: int = 1) -> Clock: ...
    def stop(self) -> Clock: ...
    @property
    def endTime(self) -> float:
        """
        :type: float
        """
    @endTime.setter
    def endTime(self, arg1: float) -> None:
        pass
    @property
    def exitFrame(self) -> int:
        """
        :type: int
        """
    @exitFrame.setter
    def exitFrame(self, arg1: int) -> None:
        pass
    @property
    def exitTime(self) -> float:
        """
        :type: float
        """
    @exitTime.setter
    def exitTime(self, arg1: float) -> None:
        pass
    @property
    def frame(self) -> int:
        """
        :type: int
        """
    @frame.setter
    def frame(self, arg1: int) -> None:
        pass
    @property
    def framerate(self) -> int:
        """
        :type: int
        """
    @framerate.setter
    def framerate(self, arg1: int) -> None:
        pass
    @property
    def startTime(self) -> float:
        """
        :type: float
        """
    @startTime.setter
    def startTime(self, arg1: float) -> None:
        pass
    @property
    def time(self) -> float:
        """
        :type: float
        """
    @time.setter
    def time(self, arg1: float) -> None:
        pass
    @property
    def timeScale(self) -> float:
        """
        :type: float
        """
    @timeScale.setter
    def timeScale(self, arg1: float) -> None:
        pass
    pass
class BasicMaterial(IMaterial):
    @property
    def baseColor(self) -> float4:
        """
        :type: float4
        """
    @baseColor.setter
    def baseColor(self, arg1: float4) -> None:
        pass
    @property
    def diffuseTransmission(self) -> float:
        """
        :type: float
        """
    @diffuseTransmission.setter
    def diffuseTransmission(self, arg1: float) -> None:
        pass
    @property
    def displacementOffset(self) -> float:
        """
        :type: float
        """
    @displacementOffset.setter
    def displacementOffset(self, arg1: float) -> None:
        pass
    @property
    def displacementScale(self) -> float:
        """
        :type: float
        """
    @displacementScale.setter
    def displacementScale(self, arg1: float) -> None:
        pass
    @property
    def indexOfRefraction(self) -> float:
        """
        :type: float
        """
    @indexOfRefraction.setter
    def indexOfRefraction(self, arg1: float) -> None:
        pass
    @property
    def specularParams(self) -> float4:
        """
        :type: float4
        """
    @specularParams.setter
    def specularParams(self, arg1: float4) -> None:
        pass
    @property
    def specularTransmission(self) -> float:
        """
        :type: float
        """
    @specularTransmission.setter
    def specularTransmission(self, arg1: float) -> None:
        pass
    @property
    def transmissionColor(self) -> float3:
        """
        :type: float3
        """
    @transmissionColor.setter
    def transmissionColor(self, arg1: float3) -> None:
        pass
    @property
    def volumeAbsorption(self) -> float3:
        """
        :type: float3
        """
    @volumeAbsorption.setter
    def volumeAbsorption(self, arg1: float3) -> None:
        pass
    @property
    def volumeAnisotropy(self) -> float:
        """
        :type: float
        """
    @volumeAnisotropy.setter
    def volumeAnisotropy(self, arg1: float) -> None:
        pass
    @property
    def volumeScattering(self) -> float3:
        """
        :type: float3
        """
    @volumeScattering.setter
    def volumeScattering(self, arg1: float3) -> None:
        pass
    pass
class ComparePass(RenderPass):
    @property
    def foamNum(self) -> int:
        """
        :type: int
        """
    @foamNum.setter
    def foamNum(self, arg1: int) -> None:
        pass
    @property
    def foamParticlesPosR(self) -> Buffer:
        """
        :type: Buffer
        """
    @foamParticlesPosR.setter
    def foamParticlesPosR(self, arg1: Buffer) -> None:
        pass
    @property
    def gt(self) -> Buffer:
        """
        :type: Buffer
        """
    @gt.setter
    def gt(self, arg1: Buffer) -> None:
        pass
    @property
    def gtResult(self) -> Buffer:
        """
        :type: Buffer
        """
    @gtResult.setter
    def gtResult(self, arg1: Buffer) -> None:
        pass
    @property
    def input(self) -> Buffer:
        """
        :type: Buffer
        """
    @input.setter
    def input(self, arg1: Buffer) -> None:
        pass
    @property
    def inputResult(self) -> Buffer:
        """
        :type: Buffer
        """
    @inputResult.setter
    def inputResult(self, arg1: Buffer) -> None:
        pass
    @property
    def renderFoam(self) -> bool:
        """
        :type: bool
        """
    @renderFoam.setter
    def renderFoam(self, arg1: bool) -> None:
        pass
    @property
    def saveNormal(self) -> bool:
        """
        :type: bool
        """
    @saveNormal.setter
    def saveNormal(self, arg1: bool) -> None:
        pass
    @property
    def saveResult(self) -> bool:
        """
        :type: bool
        """
    @saveResult.setter
    def saveResult(self, arg1: bool) -> None:
        pass
    pass
class CompareSwapPass(RenderPass):
    @property
    def gsCullNum(self) -> int:
        """
        :type: int
        """
    @gsCullNum.setter
    def gsCullNum(self, arg1: int) -> None:
        pass
    @property
    def gsNum(self) -> int:
        """
        :type: int
        """
    @gsNum.setter
    def gsNum(self, arg1: int) -> None:
        pass
    @property
    def normalDepthBuffer(self) -> Buffer:
        """
        :type: Buffer
        """
    @normalDepthBuffer.setter
    def normalDepthBuffer(self, arg1: Buffer) -> None:
        pass
    @property
    def stop(self) -> bool:
        """
        :type: bool
        """
    @property
    def stopAt(self) -> int:
        """
        :type: int
        """
    pass
class ComparisonFunc():
    """
    Members:

      Disabled

      Never

      Always

      Less

      Equal

      NotEqual

      LessEqual

      Greater

      GreaterEqual
    """
    def __eq__(self, other: object) -> bool: ...
    def __getstate__(self) -> int: ...
    def __hash__(self) -> int: ...
    def __index__(self) -> int: ...
    def __init__(self, value: int) -> None: ...
    def __int__(self) -> int: ...
    def __ne__(self, other: object) -> bool: ...
    def __repr__(self) -> str: ...
    def __setstate__(self, state: int) -> None: ...
    @property
    def name(self) -> str:
        """
        :type: str
        """
    @property
    def value(self) -> int:
        """
        :type: int
        """
    Always: falcor.falcor_ext.ComparisonFunc # value = ComparisonFunc.Always
    Disabled: falcor.falcor_ext.ComparisonFunc # value = ComparisonFunc.Disabled
    Equal: falcor.falcor_ext.ComparisonFunc # value = ComparisonFunc.Equal
    Greater: falcor.falcor_ext.ComparisonFunc # value = ComparisonFunc.Greater
    GreaterEqual: falcor.falcor_ext.ComparisonFunc # value = ComparisonFunc.GreaterEqual
    Less: falcor.falcor_ext.ComparisonFunc # value = ComparisonFunc.Less
    LessEqual: falcor.falcor_ext.ComparisonFunc # value = ComparisonFunc.LessEqual
    Never: falcor.falcor_ext.ComparisonFunc # value = ComparisonFunc.Never
    NotEqual: falcor.falcor_ext.ComparisonFunc # value = ComparisonFunc.NotEqual
    __members__: dict # value = {'Disabled': ComparisonFunc.Disabled, 'Never': ComparisonFunc.Never, 'Always': ComparisonFunc.Always, 'Less': ComparisonFunc.Less, 'Equal': ComparisonFunc.Equal, 'NotEqual': ComparisonFunc.NotEqual, 'LessEqual': ComparisonFunc.LessEqual, 'Greater': ComparisonFunc.Greater, 'GreaterEqual': ComparisonFunc.GreaterEqual}
    pass
class CompositionOrder():
    """
    Members:

      Default

      SRT

      STR

      RST

      RTS

      TRS

      TSR
    """
    def __eq__(self, other: object) -> bool: ...
    def __getstate__(self) -> int: ...
    def __hash__(self) -> int: ...
    def __index__(self) -> int: ...
    def __init__(self, value: int) -> None: ...
    def __int__(self) -> int: ...
    def __ne__(self, other: object) -> bool: ...
    def __repr__(self) -> str: ...
    def __setstate__(self, state: int) -> None: ...
    @property
    def name(self) -> str:
        """
        :type: str
        """
    @property
    def value(self) -> int:
        """
        :type: int
        """
    Default: falcor.falcor_ext.CompositionOrder # value = CompositionOrder.Default
    RST: falcor.falcor_ext.CompositionOrder # value = CompositionOrder.RST
    RTS: falcor.falcor_ext.CompositionOrder # value = CompositionOrder.RTS
    SRT: falcor.falcor_ext.CompositionOrder # value = CompositionOrder.Default
    STR: falcor.falcor_ext.CompositionOrder # value = CompositionOrder.STR
    TRS: falcor.falcor_ext.CompositionOrder # value = CompositionOrder.TRS
    TSR: falcor.falcor_ext.CompositionOrder # value = CompositionOrder.TSR
    __members__: dict # value = {'Default': CompositionOrder.Default, 'SRT': CompositionOrder.Default, 'STR': CompositionOrder.STR, 'RST': CompositionOrder.RST, 'RTS': CompositionOrder.RTS, 'TRS': CompositionOrder.TRS, 'TSR': CompositionOrder.TSR}
    pass
class CopyContext():
    def copy_buffer_region(self, dst: Buffer, dst_offset: int, src: Buffer, src_offset: int, num_bytes: int) -> None: ...
    def copy_resource(self, dst: Resource, src: Resource) -> None: ...
    def copy_subresource(self, dst: Texture, dst_subresource_idx: int, src: Texture, src_subresource_idx: int) -> None: ...
    def submit(self, wait: bool = False) -> None: ...
    def uav_barrier(self, resource: Resource) -> None: ...
    def wait_for_cuda(self, stream: int = 0) -> None: ...
    def wait_for_falcor(self, stream: int = 0) -> None: ...
    pass
class ComputePass():
    def __init__(self, device: Device, desc: typing.Optional[ProgramDesc] = None, defines: dict = {}, **kwargs) -> None: ...
    def execute(self, threads_x: int, threads_y: int = 1, threads_z: int = 1, compute_context: ComputeContext = None) -> None: ...
    @property
    def globals(self) -> ShaderVar:
        """
        :type: ShaderVar
        """
    @property
    def program(self) -> Program:
        """
        :type: Program
        """
    @property
    def root_var(self) -> ShaderVar:
        """
        :type: ShaderVar
        """
    pass
class ComputeState():
    pass
class ComputeContext(CopyContext):
    pass
class DLSSPass(RenderPass):
    pass
class DataType():
    """
    Members:

      int8

      int16

      int32

      int64

      uint8

      uint16

      uint32

      uint64

      float16

      float32

      float64
    """
    def __eq__(self, other: object) -> bool: ...
    def __getstate__(self) -> int: ...
    def __hash__(self) -> int: ...
    def __index__(self) -> int: ...
    def __init__(self, value: int) -> None: ...
    def __int__(self) -> int: ...
    def __ne__(self, other: object) -> bool: ...
    def __repr__(self) -> str: ...
    def __setstate__(self, state: int) -> None: ...
    @property
    def name(self) -> str:
        """
        :type: str
        """
    @property
    def value(self) -> int:
        """
        :type: int
        """
    __members__: dict # value = {'int8': DataType.int8, 'int16': DataType.int16, 'int32': DataType.int32, 'int64': DataType.int64, 'uint8': DataType.uint8, 'uint16': DataType.uint16, 'uint32': DataType.uint32, 'uint64': DataType.uint64, 'float16': DataType.float16, 'float32': DataType.float32, 'float64': DataType.float64}
    float16: falcor.falcor_ext.DataType # value = DataType.float16
    float32: falcor.falcor_ext.DataType # value = DataType.float32
    float64: falcor.falcor_ext.DataType # value = DataType.float64
    int16: falcor.falcor_ext.DataType # value = DataType.int16
    int32: falcor.falcor_ext.DataType # value = DataType.int32
    int64: falcor.falcor_ext.DataType # value = DataType.int64
    int8: falcor.falcor_ext.DataType # value = DataType.int8
    uint16: falcor.falcor_ext.DataType # value = DataType.uint16
    uint32: falcor.falcor_ext.DataType # value = DataType.uint32
    uint64: falcor.falcor_ext.DataType # value = DataType.uint64
    uint8: falcor.falcor_ext.DataType # value = DataType.uint8
    pass
class DepthStencilState():
    pass
class DepthStencilView():
    pass
class Device():
    class Info():
        @property
        def adapter_name(self) -> str:
            """
            :type: str
            """
        @property
        def api_name(self) -> str:
            """
            :type: str
            """
        pass
    class Limits():
        @property
        def max_compute_dispatch_thread_groups(self) -> uint3:
            """
            :type: uint3
            """
        @property
        def max_shader_visible_samplers(self) -> int:
            """
            :type: int
            """
        pass
    def __init__(self, type: DeviceType = DeviceType.Default, gpu: int = 0, enable_debug_layer: bool = False, enable_aftermath: bool = False) -> None: ...
    def create_buffer(self, size: int, bind_flags: ResourceBindFlags = ResourceBindFlags.None_, memory_type: MemoryType = MemoryType.DeviceLocal) -> Buffer: ...
    def create_program(self, desc: typing.Optional[ProgramDesc] = None, defines: dict = {}, **kwargs) -> Program: ...
    def create_sampler(self, mag_filter: TextureFilteringMode = TextureFilteringMode.Linear, min_filter: TextureFilteringMode = TextureFilteringMode.Linear, mip_filter: TextureFilteringMode = TextureFilteringMode.Linear, max_anisotropy: int = 1, min_lod: float = -1000.0, max_lod: float = 1000.0, lod_bias: float = 0.0, comparison_func: ComparisonFunc = ComparisonFunc.Disabled, reduction_mode: TextureReductionMode = TextureReductionMode.Standard, address_mode_u: TextureAddressingMode = TextureAddressingMode.Wrap, address_mode_v: TextureAddressingMode = TextureAddressingMode.Wrap, address_mode_w: TextureAddressingMode = TextureAddressingMode.Wrap, border_color_r: float4 = float4(0.000000, 0.000000, 0.000000, 0.000000)) -> Sampler: ...
    def create_structured_buffer(self, struct_size: int, element_count: int, bind_flags: ResourceBindFlags = ResourceBindFlags.None_, memory_type: MemoryType = MemoryType.DeviceLocal, create_counter: bool = False) -> Buffer: ...
    def create_texture(self, width: int, height: int = 0, depth: int = 0, format: ResourceFormat = ResourceFormat.Unknown, array_size: int = 1, mip_levels: int = 4294967295, bind_flags: ResourceBindFlags = ResourceBindFlags.None_) -> Texture: ...
    def create_typed_buffer(self, format: ResourceFormat, element_count: int, bind_flags: ResourceBindFlags = ResourceBindFlags.None_, memory_type: MemoryType = MemoryType.DeviceLocal) -> Buffer: ...
    def end_frame(self) -> None: ...
    @staticmethod
    def get_gpus(arg0: DeviceType) -> typing.List[AdapterInfo]: ...
    def wait(self) -> None: ...
    @property
    def info(self) -> Device.Info:
        """
        :type: Device.Info
        """
    @property
    def limits(self) -> Device.Limits:
        """
        :type: Device.Limits
        """
    @property
    def profiler(self) -> Profiler:
        """
        :type: Profiler
        """
    @property
    def render_context(self) -> RenderContext:
        """
        :type: RenderContext
        """
    @property
    def type(self) -> DeviceType:
        """
        :type: DeviceType
        """
    pass
class DeviceType():
    """
    Members:

      Default

      D3D12

      Vulkan
    """
    def __eq__(self, other: object) -> bool: ...
    def __getstate__(self) -> int: ...
    def __hash__(self) -> int: ...
    def __index__(self) -> int: ...
    def __init__(self, value: int) -> None: ...
    def __int__(self) -> int: ...
    def __ne__(self, other: object) -> bool: ...
    def __repr__(self) -> str: ...
    def __setstate__(self, state: int) -> None: ...
    @property
    def name(self) -> str:
        """
        :type: str
        """
    @property
    def value(self) -> int:
        """
        :type: int
        """
    D3D12: falcor.falcor_ext.DeviceType # value = DeviceType.D3D12
    Default: falcor.falcor_ext.DeviceType # value = DeviceType.Default
    Vulkan: falcor.falcor_ext.DeviceType # value = DeviceType.Vulkan
    __members__: dict # value = {'Default': DeviceType.Default, 'D3D12': DeviceType.D3D12, 'Vulkan': DeviceType.Vulkan}
    pass
class DiffMode():
    """
    Members:

      Primal

      BackwardDiff

      ForwardDiffDebug

      BackwardDiffDebug
    """
    def __eq__(self, other: object) -> bool: ...
    def __getstate__(self) -> int: ...
    def __hash__(self) -> int: ...
    def __index__(self) -> int: ...
    def __init__(self, value: int) -> None: ...
    def __int__(self) -> int: ...
    def __ne__(self, other: object) -> bool: ...
    def __repr__(self) -> str: ...
    def __setstate__(self, state: int) -> None: ...
    @property
    def name(self) -> str:
        """
        :type: str
        """
    @property
    def value(self) -> int:
        """
        :type: int
        """
    BackwardDiff: falcor.falcor_ext.DiffMode # value = DiffMode.BackwardDiff
    BackwardDiffDebug: falcor.falcor_ext.DiffMode # value = DiffMode.BackwardDiffDebug
    ForwardDiffDebug: falcor.falcor_ext.DiffMode # value = DiffMode.ForwardDiffDebug
    Primal: falcor.falcor_ext.DiffMode # value = DiffMode.Primal
    __members__: dict # value = {'Primal': DiffMode.Primal, 'BackwardDiff': DiffMode.BackwardDiff, 'ForwardDiffDebug': DiffMode.ForwardDiffDebug, 'BackwardDiffDebug': DiffMode.BackwardDiffDebug}
    pass
class DirectionalLight(Light, Animatable):
    def __init__(self, name: str = '') -> None: ...
    @property
    def direction(self) -> float3:
        """
        :type: float3
        """
    @direction.setter
    def direction(self, arg1: float3) -> None:
        pass
    pass
class AnalyticAreaLight(Light, Animatable):
    pass
class DistantLight(Light, Animatable):
    def __init__(self, name: str = '') -> None: ...
    @property
    def angle(self) -> float:
        """
        :type: float
        """
    @angle.setter
    def angle(self, arg1: float) -> None:
        pass
    @property
    def direction(self) -> float3:
        """
        :type: float3
        """
    @direction.setter
    def direction(self, arg1: float3) -> None:
        pass
    pass
class EnvMap():
    def __init__(self, path: os.PathLike) -> None: ...
    @staticmethod
    def createFromFile(path: os.PathLike) -> EnvMap: ...
    @property
    def intensity(self) -> float:
        """
        :type: float
        """
    @intensity.setter
    def intensity(self, arg1: float) -> None:
        pass
    @property
    def path(self) -> os.PathLike:
        """
        :type: os.PathLike
        """
    @property
    def rotation(self) -> float3:
        """
        :type: float3
        """
    @rotation.setter
    def rotation(self, arg1: float3) -> None:
        pass
    @property
    def tint(self) -> float3:
        """
        :type: float3
        """
    @tint.setter
    def tint(self, arg1: float3) -> None:
        pass
    pass
class Fbo():
    pass
class FoamParticleProcess(RenderPass):
    @property
    def currentParticleNum(self) -> int:
        """
        :type: int
        """
    @currentParticleNum.setter
    def currentParticleNum(self, arg1: int) -> None:
        pass
    @property
    def foamParticlesPosR(self) -> Buffer:
        """
        :type: Buffer
        """
    @foamParticlesPosR.setter
    def foamParticlesPosR(self, arg1: Buffer) -> None:
        pass
    pass
class FoamPass(RenderPass):
    @property
    def camera(self) -> Camera:
        """
        :type: Camera
        """
    @camera.setter
    def camera(self, arg1: Camera) -> None:
        pass
    @property
    def foamDensity(self) -> float:
        """
        :type: float
        """
    @foamDensity.setter
    def foamDensity(self, arg1: float) -> None:
        pass
    @property
    def gtFoam(self) -> Buffer:
        """
        :type: Buffer
        """
    @gtFoam.setter
    def gtFoam(self, arg1: Buffer) -> None:
        pass
    @property
    def gtFoamNum(self) -> int:
        """
        :type: int
        """
    @gtFoamNum.setter
    def gtFoamNum(self, arg1: int) -> None:
        pass
    @property
    def mode(self) -> int:
        """
        :type: int
        """
    @mode.setter
    def mode(self, arg1: int) -> None:
        pass
    @property
    def newFoam(self) -> Buffer:
        """
        :type: Buffer
        """
    @newFoam.setter
    def newFoam(self, arg1: Buffer) -> None:
        pass
    @property
    def newFoamNum(self) -> int:
        """
        :type: int
        """
    @newFoamNum.setter
    def newFoamNum(self, arg1: int) -> None:
        pass
    @property
    def noiseThreshold(self) -> float:
        """
        :type: float
        """
    @property
    def pause(self) -> bool:
        """
        :type: bool
        """
    @pause.setter
    def pause(self, arg1: bool) -> None:
        pass
    @property
    def refresh(self) -> bool:
        """
        :type: bool
        """
    @refresh.setter
    def refresh(self, arg1: bool) -> None:
        pass
    @property
    def sampleTimes(self) -> int:
        """
        :type: int
        """
    @property
    def surfaceVelDepth(self) -> Buffer:
        """
        :type: Buffer
        """
    @surfaceVelDepth.setter
    def surfaceVelDepth(self, arg1: Buffer) -> None:
        pass
    @property
    def waterTrColor(self) -> float3:
        """
        :type: float3
        """
    @waterTrColor.setter
    def waterTrColor(self, arg1: float3) -> None:
        pass
    @property
    def waterTrStrenth(self) -> float:
        """
        :type: float
        """
    @waterTrStrenth.setter
    def waterTrStrenth(self, arg1: float) -> None:
        pass
    pass
class FoamShadingPass(RenderPass):
    @property
    def currentParticleNum(self) -> int:
        """
        :type: int
        """
    @currentParticleNum.setter
    def currentParticleNum(self, arg1: int) -> None:
        pass
    @property
    def foamParticlesPosR(self) -> Buffer:
        """
        :type: Buffer
        """
    @foamParticlesPosR.setter
    def foamParticlesPosR(self, arg1: Buffer) -> None:
        pass
    pass
class GTPass(RenderPass):
    @property
    def gtBuffer(self) -> Buffer:
        """
        :type: Buffer
        """
    @gtBuffer.setter
    def gtBuffer(self, arg1: Buffer) -> None:
        pass
    @property
    def meshPath(self) -> str:
        """
        :type: str
        """
    @meshPath.setter
    def meshPath(self, arg1: str) -> None:
        pass
    @property
    def selectedIndex(self) -> int:
        """
        :type: int
        """
    @selectedIndex.setter
    def selectedIndex(self, arg1: int) -> None:
        pass
    pass
class GTRenderingPass(RenderPass):
    @property
    def path(self) -> str:
        """
        :type: str
        """
    @path.setter
    def path(self, arg1: str) -> None:
        pass
    pass
class GaussianBlur(RenderPass):
    @property
    def kernelWidth(self) -> int:
        """
        :type: int
        """
    @kernelWidth.setter
    def kernelWidth(self, arg1: int) -> None:
        pass
    @property
    def sigma(self) -> float:
        """
        :type: float
        """
    @sigma.setter
    def sigma(self, arg1: float) -> None:
        pass
    pass
class GpuTimer():
    pass
class GradConfig():
    @typing.overload
    def __init__(self) -> None: ...
    @typing.overload
    def __init__(self, grad_type: GradientType, dim: int, hash_size: int) -> None: ...
    pass
class GradientType():
    """
    Members:

      Material

      MeshPosition

      MeshNormal

      MeshTangent
    """
    def __eq__(self, other: object) -> bool: ...
    def __getstate__(self) -> int: ...
    def __hash__(self) -> int: ...
    def __index__(self) -> int: ...
    def __init__(self, value: int) -> None: ...
    def __int__(self) -> int: ...
    def __ne__(self, other: object) -> bool: ...
    def __repr__(self) -> str: ...
    def __setstate__(self, state: int) -> None: ...
    @property
    def name(self) -> str:
        """
        :type: str
        """
    @property
    def value(self) -> int:
        """
        :type: int
        """
    Material: falcor.falcor_ext.GradientType # value = GradientType.Material
    MeshNormal: falcor.falcor_ext.GradientType # value = GradientType.MeshNormal
    MeshPosition: falcor.falcor_ext.GradientType # value = GradientType.MeshPosition
    MeshTangent: falcor.falcor_ext.GradientType # value = GradientType.MeshTangent
    __members__: dict # value = {'Material': GradientType.Material, 'MeshPosition': GradientType.MeshPosition, 'MeshNormal': GradientType.MeshNormal, 'MeshTangent': GradientType.MeshTangent}
    pass
class GraphicsState():
    pass
class Grid():
    @staticmethod
    def createBox(width: float, height: float, depth: float, voxelSize: float, blendRange: float = 3.0) -> Grid: ...
    @staticmethod
    def createFromFile(path: os.PathLike, gridname: str) -> Grid: ...
    @staticmethod
    def createSphere(radius: float, voxelSize: float, blendRange: float = 3.0) -> Grid: ...
    def getValue(self, ijk: int3) -> float: ...
    @property
    def maxIndex(self) -> int3:
        """
        :type: int3
        """
    @property
    def maxValue(self) -> float:
        """
        :type: float
        """
    @property
    def minIndex(self) -> int3:
        """
        :type: int3
        """
    @property
    def minValue(self) -> float:
        """
        :type: float
        """
    @property
    def voxelCount(self) -> int:
        """
        :type: int
        """
    pass
class GridVolume(Animatable):
    class EmissionMode():
        """
        Members:

          Direct

          Blackbody
        """
        def __eq__(self, other: object) -> bool: ...
        def __getstate__(self) -> int: ...
        def __hash__(self) -> int: ...
        def __index__(self) -> int: ...
        def __init__(self, value: int) -> None: ...
        def __int__(self) -> int: ...
        def __ne__(self, other: object) -> bool: ...
        def __repr__(self) -> str: ...
        def __setstate__(self, state: int) -> None: ...
        @property
        def name(self) -> str:
            """
            :type: str
            """
        @property
        def value(self) -> int:
            """
            :type: int
            """
        Blackbody: falcor.falcor_ext.GridVolume.EmissionMode # value = EmissionMode.Blackbody
        Direct: falcor.falcor_ext.GridVolume.EmissionMode # value = EmissionMode.Direct
        __members__: dict # value = {'Direct': EmissionMode.Direct, 'Blackbody': EmissionMode.Blackbody}
        pass
    class GridSlot():
        """
        Members:

          Density

          Emission
        """
        def __eq__(self, other: object) -> bool: ...
        def __getstate__(self) -> int: ...
        def __hash__(self) -> int: ...
        def __index__(self) -> int: ...
        def __init__(self, value: int) -> None: ...
        def __int__(self) -> int: ...
        def __ne__(self, other: object) -> bool: ...
        def __repr__(self) -> str: ...
        def __setstate__(self, state: int) -> None: ...
        @property
        def name(self) -> str:
            """
            :type: str
            """
        @property
        def value(self) -> int:
            """
            :type: int
            """
        Density: falcor.falcor_ext.GridVolume.GridSlot # value = GridSlot.Density
        Emission: falcor.falcor_ext.GridVolume.GridSlot # value = GridSlot.Emission
        __members__: dict # value = {'Density': GridSlot.Density, 'Emission': GridSlot.Emission}
        pass
    def __init__(self, name: str) -> None: ...
    def loadGrid(self, slot: GridVolume.GridSlot, path: os.PathLike, gridname: str) -> bool: ...
    @typing.overload
    def loadGridSequence(self, slot: GridVolume.GridSlot, path: os.PathLike, gridnames: str, keepEmpty: bool = True) -> int: ...
    @typing.overload
    def loadGridSequence(self, slot: GridVolume.GridSlot, paths: typing.List[os.PathLike], gridname: str, keepEmpty: bool = True) -> int: ...
    @property
    def albedo(self) -> float3:
        """
        :type: float3
        """
    @albedo.setter
    def albedo(self, arg1: float3) -> None:
        pass
    @property
    def anisotropy(self) -> float:
        """
        :type: float
        """
    @anisotropy.setter
    def anisotropy(self, arg1: float) -> None:
        pass
    @property
    def densityGrid(self) -> Grid:
        """
        :type: Grid
        """
    @densityGrid.setter
    def densityGrid(self, arg1: Grid) -> None:
        pass
    @property
    def densityScale(self) -> float:
        """
        :type: float
        """
    @densityScale.setter
    def densityScale(self, arg1: float) -> None:
        pass
    @property
    def emissionGrid(self) -> Grid:
        """
        :type: Grid
        """
    @emissionGrid.setter
    def emissionGrid(self, arg1: Grid) -> None:
        pass
    @property
    def emissionMode(self) -> GridVolume.EmissionMode:
        """
        :type: GridVolume.EmissionMode
        """
    @emissionMode.setter
    def emissionMode(self, arg1: GridVolume.EmissionMode) -> None:
        pass
    @property
    def emissionScale(self) -> float:
        """
        :type: float
        """
    @emissionScale.setter
    def emissionScale(self, arg1: float) -> None:
        pass
    @property
    def emissionTemperature(self) -> float:
        """
        :type: float
        """
    @emissionTemperature.setter
    def emissionTemperature(self, arg1: float) -> None:
        pass
    @property
    def frameRate(self) -> float:
        """
        :type: float
        """
    @frameRate.setter
    def frameRate(self, arg1: float) -> None:
        pass
    @property
    def gridFrame(self) -> int:
        """
        :type: int
        """
    @gridFrame.setter
    def gridFrame(self, arg1: int) -> None:
        pass
    @property
    def gridFrameCount(self) -> int:
        """
        :type: int
        """
    @property
    def name(self) -> str:
        """
        :type: str
        """
    @name.setter
    def name(self, arg1: str) -> None:
        pass
    @property
    def playbackEnabled(self) -> bool:
        """
        :type: bool
        """
    @playbackEnabled.setter
    def playbackEnabled(self, arg1: bool) -> None:
        pass
    @property
    def startFrame(self) -> int:
        """
        :type: int
        """
    @startFrame.setter
    def startFrame(self, arg1: int) -> None:
        pass
    pass
class HairMaterial(BasicMaterial, IMaterial):
    def __init__(self, name: str = '') -> None: ...
    pass
class ClothMaterial(BasicMaterial, IMaterial):
    def __init__(self, name: str = '') -> None: ...
    @property
    def roughness(self) -> float:
        """
        :type: float
        """
    @roughness.setter
    def roughness(self, arg1: float) -> None:
        pass
    pass
class ImporterError(Exception, BaseException):
    pass
class Key():
    """
    Members:

      Space

      E

      R
    """
    def __eq__(self, other: object) -> bool: ...
    def __getstate__(self) -> int: ...
    def __hash__(self) -> int: ...
    def __index__(self) -> int: ...
    def __init__(self, value: int) -> None: ...
    def __int__(self) -> int: ...
    def __ne__(self, other: object) -> bool: ...
    def __repr__(self) -> str: ...
    def __setstate__(self, state: int) -> None: ...
    @property
    def name(self) -> str:
        """
        :type: str
        """
    @property
    def value(self) -> int:
        """
        :type: int
        """
    E: falcor.falcor_ext.Key # value = Key.E
    R: falcor.falcor_ext.Key # value = Key.R
    Space: falcor.falcor_ext.Key # value = Key.Space
    __members__: dict # value = {'Space': Key.Space, 'E': Key.E, 'R': Key.R}
    pass
class KeyboardEvent():
    class Type():
        """
        Members:

          KeyPressed

          KeyReleased

          KeyRepeated

          Input
        """
        def __eq__(self, other: object) -> bool: ...
        def __getstate__(self) -> int: ...
        def __hash__(self) -> int: ...
        def __index__(self) -> int: ...
        def __init__(self, value: int) -> None: ...
        def __int__(self) -> int: ...
        def __ne__(self, other: object) -> bool: ...
        def __repr__(self) -> str: ...
        def __setstate__(self, state: int) -> None: ...
        @property
        def name(self) -> str:
            """
            :type: str
            """
        @property
        def value(self) -> int:
            """
            :type: int
            """
        Input: falcor.falcor_ext.KeyboardEvent.Type # value = Type.Input
        KeyPressed: falcor.falcor_ext.KeyboardEvent.Type # value = Type.KeyPressed
        KeyReleased: falcor.falcor_ext.KeyboardEvent.Type # value = Type.KeyReleased
        KeyRepeated: falcor.falcor_ext.KeyboardEvent.Type # value = Type.KeyRepeated
        __members__: dict # value = {'KeyPressed': Type.KeyPressed, 'KeyReleased': Type.KeyReleased, 'KeyRepeated': Type.KeyRepeated, 'Input': Type.Input}
        pass
    @property
    def codepoint(self) -> int:
        """
        :type: int
        """
    @property
    def key(self) -> Key:
        """
        :type: Key
        """
    @property
    def mods(self) -> ModifierFlags:
        """
        :type: ModifierFlags
        """
    @property
    def type(self) -> KeyboardEvent.Type:
        """
        :type: KeyboardEvent.Type
        """
    pass
class DiscLight(AnalyticAreaLight, Light, Animatable):
    def __init__(self, name: str = '') -> None: ...
    pass
class Logger():
    class Level():
        """
        Members:

          Disabled

          Fatal

          Error

          Warning

          Info

          Debug
        """
        def __eq__(self, other: object) -> bool: ...
        def __getstate__(self) -> int: ...
        def __hash__(self) -> int: ...
        def __index__(self) -> int: ...
        def __init__(self, value: int) -> None: ...
        def __int__(self) -> int: ...
        def __ne__(self, other: object) -> bool: ...
        def __repr__(self) -> str: ...
        def __setstate__(self, state: int) -> None: ...
        @property
        def name(self) -> str:
            """
            :type: str
            """
        @property
        def value(self) -> int:
            """
            :type: int
            """
        Debug: falcor.falcor_ext.Logger.Level # value = Level.Debug
        Disabled: falcor.falcor_ext.Logger.Level # value = Level.Disabled
        Error: falcor.falcor_ext.Logger.Level # value = Level.Error
        Fatal: falcor.falcor_ext.Logger.Level # value = Level.Fatal
        Info: falcor.falcor_ext.Logger.Level # value = Level.Info
        Warning: falcor.falcor_ext.Logger.Level # value = Level.Warning
        __members__: dict # value = {'Disabled': Level.Disabled, 'Fatal': Level.Fatal, 'Error': Level.Error, 'Warning': Level.Warning, 'Info': Level.Info, 'Debug': Level.Debug}
        pass
    class OutputFlags():
        """
        Members:

          None_

          Console

          File

          DebugWindow
        """
        def __eq__(self, other: object) -> bool: ...
        def __getstate__(self) -> int: ...
        def __hash__(self) -> int: ...
        def __index__(self) -> int: ...
        def __init__(self, value: int) -> None: ...
        def __int__(self) -> int: ...
        def __ne__(self, other: object) -> bool: ...
        def __repr__(self) -> str: ...
        def __setstate__(self, state: int) -> None: ...
        @property
        def name(self) -> str:
            """
            :type: str
            """
        @property
        def value(self) -> int:
            """
            :type: int
            """
        Console: falcor.falcor_ext.Logger.OutputFlags # value = OutputFlags.Console
        DebugWindow: falcor.falcor_ext.Logger.OutputFlags # value = OutputFlags.DebugWindow
        File: falcor.falcor_ext.Logger.OutputFlags # value = OutputFlags.File
        None_: falcor.falcor_ext.Logger.OutputFlags # value = OutputFlags.None_
        __members__: dict # value = {'None_': OutputFlags.None_, 'Console': OutputFlags.Console, 'File': OutputFlags.File, 'DebugWindow': OutputFlags.DebugWindow}
        pass
    @staticmethod
    def log(level: Logger.Level, msg: str) -> None: ...
    log_file_path: pathlib.WindowsPath # value = WindowsPath('.')
    outputs: falcor.falcor_ext.Logger.OutputFlags # value = OutputFlags.???
    verbosity: falcor.falcor_ext.Logger.Level # value = Level.Info
    pass
class MERLMaterial(IMaterial):
    def __init__(self, name: str, path: os.PathLike) -> None: ...
    pass
class MERLMixMaterial(IMaterial):
    def __init__(self, name: str, paths: typing.List[os.PathLike]) -> None: ...
    pass
class MaterialTextureSlot():
    """
    Members:

      BaseColor

      Specular

      Emissive

      Normal

      Transmission

      Displacement

      Index
    """
    def __eq__(self, other: object) -> bool: ...
    def __getstate__(self) -> int: ...
    def __hash__(self) -> int: ...
    def __index__(self) -> int: ...
    def __init__(self, value: int) -> None: ...
    def __int__(self) -> int: ...
    def __ne__(self, other: object) -> bool: ...
    def __repr__(self) -> str: ...
    def __setstate__(self, state: int) -> None: ...
    @property
    def name(self) -> str:
        """
        :type: str
        """
    @property
    def value(self) -> int:
        """
        :type: int
        """
    BaseColor: falcor.falcor_ext.MaterialTextureSlot # value = MaterialTextureSlot.BaseColor
    Displacement: falcor.falcor_ext.MaterialTextureSlot # value = MaterialTextureSlot.Displacement
    Emissive: falcor.falcor_ext.MaterialTextureSlot # value = MaterialTextureSlot.Emissive
    Index: falcor.falcor_ext.MaterialTextureSlot # value = MaterialTextureSlot.Index
    Normal: falcor.falcor_ext.MaterialTextureSlot # value = MaterialTextureSlot.Normal
    Specular: falcor.falcor_ext.MaterialTextureSlot # value = MaterialTextureSlot.Specular
    Transmission: falcor.falcor_ext.MaterialTextureSlot # value = MaterialTextureSlot.Transmission
    __members__: dict # value = {'BaseColor': MaterialTextureSlot.BaseColor, 'Specular': MaterialTextureSlot.Specular, 'Emissive': MaterialTextureSlot.Emissive, 'Normal': MaterialTextureSlot.Normal, 'Transmission': MaterialTextureSlot.Transmission, 'Displacement': MaterialTextureSlot.Displacement, 'Index': MaterialTextureSlot.Index}
    pass
class MaterialType():
    """
    Members:

      Standard

      Cloth

      Hair

      MERL

      MERLMix

      PBRTDiffuse

      PBRTDiffuseTransmission

      PBRTConductor

      PBRTDielectric

      PBRTCoatedConductor

      PBRTCoatedDiffuse

      RGL
    """
    def __eq__(self, other: object) -> bool: ...
    def __getstate__(self) -> int: ...
    def __hash__(self) -> int: ...
    def __index__(self) -> int: ...
    def __init__(self, value: int) -> None: ...
    def __int__(self) -> int: ...
    def __ne__(self, other: object) -> bool: ...
    def __repr__(self) -> str: ...
    def __setstate__(self, state: int) -> None: ...
    @property
    def name(self) -> str:
        """
        :type: str
        """
    @property
    def value(self) -> int:
        """
        :type: int
        """
    Cloth: falcor.falcor_ext.MaterialType # value = MaterialType.Cloth
    Hair: falcor.falcor_ext.MaterialType # value = MaterialType.Hair
    MERL: falcor.falcor_ext.MaterialType # value = MaterialType.MERL
    MERLMix: falcor.falcor_ext.MaterialType # value = MaterialType.MERLMix
    PBRTCoatedConductor: falcor.falcor_ext.MaterialType # value = MaterialType.PBRTCoatedConductor
    PBRTCoatedDiffuse: falcor.falcor_ext.MaterialType # value = MaterialType.PBRTCoatedDiffuse
    PBRTConductor: falcor.falcor_ext.MaterialType # value = MaterialType.PBRTConductor
    PBRTDielectric: falcor.falcor_ext.MaterialType # value = MaterialType.PBRTDielectric
    PBRTDiffuse: falcor.falcor_ext.MaterialType # value = MaterialType.PBRTDiffuse
    PBRTDiffuseTransmission: falcor.falcor_ext.MaterialType # value = MaterialType.PBRTDiffuseTransmission
    RGL: falcor.falcor_ext.MaterialType # value = MaterialType.RGL
    Standard: falcor.falcor_ext.MaterialType # value = MaterialType.Standard
    __members__: dict # value = {'Standard': MaterialType.Standard, 'Cloth': MaterialType.Cloth, 'Hair': MaterialType.Hair, 'MERL': MaterialType.MERL, 'MERLMix': MaterialType.MERLMix, 'PBRTDiffuse': MaterialType.PBRTDiffuse, 'PBRTDiffuseTransmission': MaterialType.PBRTDiffuseTransmission, 'PBRTConductor': MaterialType.PBRTConductor, 'PBRTDielectric': MaterialType.PBRTDielectric, 'PBRTCoatedConductor': MaterialType.PBRTCoatedConductor, 'PBRTCoatedDiffuse': MaterialType.PBRTCoatedDiffuse, 'RGL': MaterialType.RGL}
    pass
class MemoryType():
    """
    Members:

      DeviceLocal

      Upload

      ReadBack
    """
    def __eq__(self, other: object) -> bool: ...
    def __getstate__(self) -> int: ...
    def __hash__(self) -> int: ...
    def __index__(self) -> int: ...
    def __init__(self, value: int) -> None: ...
    def __int__(self) -> int: ...
    def __ne__(self, other: object) -> bool: ...
    def __repr__(self) -> str: ...
    def __setstate__(self, state: int) -> None: ...
    @property
    def name(self) -> str:
        """
        :type: str
        """
    @property
    def value(self) -> int:
        """
        :type: int
        """
    DeviceLocal: falcor.falcor_ext.MemoryType # value = MemoryType.DeviceLocal
    ReadBack: falcor.falcor_ext.MemoryType # value = MemoryType.ReadBack
    Upload: falcor.falcor_ext.MemoryType # value = MemoryType.Upload
    __members__: dict # value = {'DeviceLocal': MemoryType.DeviceLocal, 'Upload': MemoryType.Upload, 'ReadBack': MemoryType.ReadBack}
    pass
class MeshDesc():
    @property
    def triangle_count(self) -> int:
        """
        :type: int
        """
    @property
    def vertex_count(self) -> int:
        """
        :type: int
        """
    pass
class ModifierFlags():
    """
    Members:

      None

      Shift

      Ctrl

      Alt
    """
    def __eq__(self, other: object) -> bool: ...
    def __ge__(self, other: object) -> bool: ...
    def __getstate__(self) -> int: ...
    def __gt__(self, other: object) -> bool: ...
    def __hash__(self) -> int: ...
    def __index__(self) -> int: ...
    def __init__(self, value: int) -> None: ...
    def __int__(self) -> int: ...
    def __le__(self, other: object) -> bool: ...
    def __lt__(self, other: object) -> bool: ...
    def __ne__(self, other: object) -> bool: ...
    def __repr__(self) -> str: ...
    def __setstate__(self, state: int) -> None: ...
    @property
    def name(self) -> str:
        """
        :type: str
        """
    @property
    def value(self) -> int:
        """
        :type: int
        """
    Alt: falcor.falcor_ext.ModifierFlags # value = ModifierFlags.Alt
    Ctrl: falcor.falcor_ext.ModifierFlags # value = ModifierFlags.Ctrl
    None: falcor.falcor_ext.ModifierFlags # value = ModifierFlags.None
    Shift: falcor.falcor_ext.ModifierFlags # value = ModifierFlags.Shift
    __members__: dict # value = {'None': ModifierFlags.None, 'Shift': ModifierFlags.Shift, 'Ctrl': ModifierFlags.Ctrl, 'Alt': ModifierFlags.Alt}
    pass
class MouseButton():
    """
    Members:

      Left

      Right

      Middle
    """
    def __eq__(self, other: object) -> bool: ...
    def __getstate__(self) -> int: ...
    def __hash__(self) -> int: ...
    def __index__(self) -> int: ...
    def __init__(self, value: int) -> None: ...
    def __int__(self) -> int: ...
    def __ne__(self, other: object) -> bool: ...
    def __repr__(self) -> str: ...
    def __setstate__(self, state: int) -> None: ...
    @property
    def name(self) -> str:
        """
        :type: str
        """
    @property
    def value(self) -> int:
        """
        :type: int
        """
    Left: falcor.falcor_ext.MouseButton # value = MouseButton.Left
    Middle: falcor.falcor_ext.MouseButton # value = MouseButton.Middle
    Right: falcor.falcor_ext.MouseButton # value = MouseButton.Right
    __members__: dict # value = {'Left': MouseButton.Left, 'Right': MouseButton.Right, 'Middle': MouseButton.Middle}
    pass
class MouseEvent():
    class Type():
        """
        Members:

          ButtonDown

          ButtonUp

          Move

          Wheel
        """
        def __eq__(self, other: object) -> bool: ...
        def __getstate__(self) -> int: ...
        def __hash__(self) -> int: ...
        def __index__(self) -> int: ...
        def __init__(self, value: int) -> None: ...
        def __int__(self) -> int: ...
        def __ne__(self, other: object) -> bool: ...
        def __repr__(self) -> str: ...
        def __setstate__(self, state: int) -> None: ...
        @property
        def name(self) -> str:
            """
            :type: str
            """
        @property
        def value(self) -> int:
            """
            :type: int
            """
        ButtonDown: falcor.falcor_ext.MouseEvent.Type # value = Type.ButtonDown
        ButtonUp: falcor.falcor_ext.MouseEvent.Type # value = Type.ButtonUp
        Move: falcor.falcor_ext.MouseEvent.Type # value = Type.Move
        Wheel: falcor.falcor_ext.MouseEvent.Type # value = Type.Wheel
        __members__: dict # value = {'ButtonDown': Type.ButtonDown, 'ButtonUp': Type.ButtonUp, 'Move': Type.Move, 'Wheel': Type.Wheel}
        pass
    @property
    def button(self) -> MouseButton:
        """
        :type: MouseButton
        """
    @property
    def mods(self) -> ModifierFlags:
        """
        :type: ModifierFlags
        """
    @property
    def pos(self) -> float2:
        """
        :type: float2
        """
    @property
    def screen_pos(self) -> float2:
        """
        :type: float2
        """
    @property
    def type(self) -> MouseEvent.Type:
        """
        :type: MouseEvent.Type
        """
    @property
    def wheel_delta(self) -> float2:
        """
        :type: float2
        """
    pass
class ObjectID():
    pass
class PBRTCoatedConductorMaterial(BasicMaterial, IMaterial):
    def __init__(self, name: str = '') -> None: ...
    @property
    def roughness(self) -> float4:
        """
        :type: float4
        """
    @roughness.setter
    def roughness(self, arg1: float4) -> None:
        pass
    pass
class PBRTCoatedDiffuseMaterial(BasicMaterial, IMaterial):
    def __init__(self, name: str = '') -> None: ...
    @property
    def roughness(self) -> float2:
        """
        :type: float2
        """
    @roughness.setter
    def roughness(self, arg1: float2) -> None:
        pass
    pass
class PBRTConductorMaterial(BasicMaterial, IMaterial):
    def __init__(self, name: str = '') -> None: ...
    @property
    def roughness(self) -> float2:
        """
        :type: float2
        """
    @roughness.setter
    def roughness(self, arg1: float2) -> None:
        pass
    pass
class PBRTDielectricMaterial(BasicMaterial, IMaterial):
    def __init__(self, name: str = '') -> None: ...
    @property
    def roughness(self) -> float2:
        """
        :type: float2
        """
    @roughness.setter
    def roughness(self, arg1: float2) -> None:
        pass
    pass
class PBRTDiffuseMaterial(BasicMaterial, IMaterial):
    @typing.overload
    def __init__(self, device: Device, name: str = '') -> None: ...
    @typing.overload
    def __init__(self, name: str = '') -> None: ...
    pass
class PBRTDiffuseTransmissionMaterial(BasicMaterial, IMaterial):
    def __init__(self, name: str = '') -> None: ...
    pass
class ParameterBlockReflection():
    def __getattr__(self, arg0: str) -> ReflectionVar: ...
    def __getitem__(self, arg0: str) -> ReflectionVar: ...
    @property
    def element_type(self) -> ReflectionType:
        """
        :type: ReflectionType
        """
    pass
class ParticleFilterPass(RenderPass):
    @property
    def camera(self) -> Camera:
        """
        :type: Camera
        """
    @camera.setter
    def camera(self, arg1: Camera) -> None:
        pass
    @property
    def downSampleX(self) -> float:
        """
        :type: float
        """
    @property
    def fluidParticle(self) -> Buffer:
        """
        :type: Buffer
        """
    @fluidParticle.setter
    def fluidParticle(self, arg1: Buffer) -> None:
        pass
    @property
    def particleNum(self) -> int:
        """
        :type: int
        """
    @particleNum.setter
    def particleNum(self, arg1: int) -> None:
        pass
    @property
    def radius(self) -> float:
        """
        :type: float
        """
    @radius.setter
    def radius(self, arg1: float) -> None:
        pass
    @property
    def surfaceIndex(self) -> Buffer:
        """
        :type: Buffer
        """
    @surfaceIndex.setter
    def surfaceIndex(self, arg1: Buffer) -> None:
        pass
    @property
    def surfaceNum(self) -> int:
        """
        :type: int
        """
    pass
class PathTracer(RenderPass):
    def reset(self) -> None: ...
    @property
    def fixedSeed(self) -> int:
        """
        :type: int
        """
    @fixedSeed.setter
    def fixedSeed(self, arg1: int) -> None:
        pass
    @property
    def pixelStats(self) -> PixelStats:
        """
        :type: PixelStats
        """
    @property
    def useFixedSeed(self) -> bool:
        """
        :type: bool
        """
    @useFixedSeed.setter
    def useFixedSeed(self, arg1: bool) -> None:
        pass
    pass
class PixelStats():
    @property
    def enabled(self) -> bool:
        """
        :type: bool
        """
    @enabled.setter
    def enabled(self, arg1: bool) -> None:
        pass
    @property
    def stats(self) -> dict:
        """
        :type: dict
        """
    pass
class PointLight(Light, Animatable):
    def __init__(self, name: str = '') -> None: ...
    @property
    def direction(self) -> float3:
        """
        :type: float3
        """
    @direction.setter
    def direction(self, arg1: float3) -> None:
        pass
    @property
    def openingAngle(self) -> float:
        """
        :type: float
        """
    @openingAngle.setter
    def openingAngle(self, arg1: float) -> None:
        pass
    @property
    def penumbraAngle(self) -> float:
        """
        :type: float
        """
    @penumbraAngle.setter
    def penumbraAngle(self, arg1: float) -> None:
        pass
    @property
    def position(self) -> float3:
        """
        :type: float3
        """
    @position.setter
    def position(self, arg1: float3) -> None:
        pass
    pass
class Profiler():
    def end_capture(self) -> typing.Optional[dict]: ...
    def end_frame(self) -> None: ...
    def event(self, arg0: str) -> ProfilerEvent: ...
    def reset_stats(self) -> None: ...
    def start_capture(self, reserved_frames: int = 1000) -> None: ...
    @property
    def enabled(self) -> bool:
        """
        :type: bool
        """
    @enabled.setter
    def enabled(self, arg1: bool) -> None:
        pass
    @property
    def events(self) -> dict:
        """
        :type: dict
        """
    @property
    def is_capturing(self) -> bool:
        """
        :type: bool
        """
    @property
    def paused(self) -> bool:
        """
        :type: bool
        """
    @paused.setter
    def paused(self, arg1: bool) -> None:
        pass
    pass
class ProfilerEvent():
    def __enter__(self) -> None: ...
    def __exit__(self, arg0: object, arg1: object, arg2: object) -> None: ...
    def __init__(self, arg0: RenderContext, arg1: str) -> None: ...
    pass
class Program():
    def add_define(self, name: str, value: str = '') -> bool: ...
    def add_type_conformance(self, type_name: str, interface_type: str, id: int) -> bool: ...
    def remove_define(self, name: str) -> bool: ...
    def remove_type_conformance(self, type_name: str, interface_type: str) -> bool: ...
    @property
    def defines(self) -> dict:
        """
        :type: dict
        """
    @defines.setter
    def defines(self, arg1: dict) -> None:
        pass
    @property
    def reflector(self) -> ProgramReflection:
        """
        :type: ProgramReflection
        """
    @property
    def type_conformances(self) -> dict:
        """
        :type: dict
        """
    @type_conformances.setter
    def type_conformances(self, arg1: dict) -> None:
        pass
    pass
class ProgramDesc():
    class EntryPointGroup():
        @property
        def type_conformances(self) -> dict:
            """
            :type: dict
            """
        @type_conformances.setter
        def type_conformances(self, arg1: dict) -> None:
            pass
        pass
    class ShaderModule():
        def add_file(self, path: os.PathLike) -> ProgramDesc.ShaderModule: ...
        def add_string(self, string: str, path: os.PathLike = WindowsPath('.')) -> ProgramDesc.ShaderModule: ...
        pass
    def __init__(self) -> None: ...
    def add_shader_module(self, name: str = '') -> ProgramDesc.ShaderModule: ...
    def cs_entry(self, name: str) -> ProgramDesc: ...
    @property
    def compiler_arguments(self) -> typing.List[str]:
        """
        :type: typing.List[str]
        """
    @compiler_arguments.setter
    def compiler_arguments(self, arg0: typing.List[str]) -> None:
        pass
    @property
    def compiler_flags(self) -> SlangCompilerFlags:
        """
        :type: SlangCompilerFlags
        """
    @compiler_flags.setter
    def compiler_flags(self, arg0: SlangCompilerFlags) -> None:
        pass
    @property
    def shader_model(self) -> ShaderModel:
        """
        :type: ShaderModel
        """
    @shader_model.setter
    def shader_model(self, arg0: ShaderModel) -> None:
        pass
    pass
class ProgramReflection():
    @property
    def default_parameter_block(self) -> ParameterBlockReflection:
        """
        :type: ParameterBlockReflection
        """
    pass
class RGLMaterial(IMaterial):
    def __init__(self, name: str, path: os.PathLike) -> None: ...
    def load(self, path: os.PathLike) -> bool: ...
    pass
class RasterizerState():
    pass
class RectLight(AnalyticAreaLight, Light, Animatable):
    def __init__(self, name: str = '') -> None: ...
    pass
class Rectangle():
    def __and__(self, arg0: Rectangle) -> Rectangle: ...
    def __eq__(self, arg0: Rectangle) -> bool: ...
    def __iand__(self, arg0: Rectangle) -> Rectangle: ...
    @typing.overload
    def __init__(self) -> None: ...
    @typing.overload
    def __init__(self, min_point: float2, max_point: float2) -> None: ...
    @typing.overload
    def __init__(self, p: float2) -> None: ...
    def __ior__(self, arg0: Rectangle) -> Rectangle: ...
    def __ne__(self, arg0: Rectangle) -> bool: ...
    def __or__(self, arg0: Rectangle) -> Rectangle: ...
    def __repr__(self) -> str: ...
    def __str__(self) -> str: ...
    @typing.overload
    def include(self, b: Rectangle) -> Rectangle: ...
    @typing.overload
    def include(self, p: float2) -> Rectangle: ...
    def intersection(self, arg0: Rectangle) -> Rectangle: ...
    def invalidate(self) -> None: ...
    @property
    def area(self) -> float:
        """
        :type: float
        """
    @property
    def center(self) -> float2:
        """
        :type: float2
        """
    @property
    def extent(self) -> float2:
        """
        :type: float2
        """
    @property
    def maxPoint(self) -> float2:
        """
        :type: float2
        """
    @maxPoint.setter
    def maxPoint(self, arg0: float2) -> None:
        pass
    @property
    def max_point(self) -> float2:
        """
        :type: float2
        """
    @max_point.setter
    def max_point(self, arg0: float2) -> None:
        pass
    @property
    def minPoint(self) -> float2:
        """
        :type: float2
        """
    @minPoint.setter
    def minPoint(self, arg0: float2) -> None:
        pass
    @property
    def min_point(self) -> float2:
        """
        :type: float2
        """
    @min_point.setter
    def min_point(self, arg0: float2) -> None:
        pass
    @property
    def radius(self) -> float:
        """
        :type: float
        """
    @property
    def valid(self) -> bool:
        """
        :type: bool
        """
    __hash__ = None
    pass
class ReflectionType():
    class Kind():
        """
        Members:

          Array

          Struct

          Basic

          Resource

          Interface
        """
        def __eq__(self, other: object) -> bool: ...
        def __getstate__(self) -> int: ...
        def __hash__(self) -> int: ...
        def __index__(self) -> int: ...
        def __init__(self, value: int) -> None: ...
        def __int__(self) -> int: ...
        def __ne__(self, other: object) -> bool: ...
        def __repr__(self) -> str: ...
        def __setstate__(self, state: int) -> None: ...
        @property
        def name(self) -> str:
            """
            :type: str
            """
        @property
        def value(self) -> int:
            """
            :type: int
            """
        Array: falcor.falcor_ext.ReflectionType.Kind # value = Kind.Array
        Basic: falcor.falcor_ext.ReflectionType.Kind # value = Kind.Basic
        Interface: falcor.falcor_ext.ReflectionType.Kind # value = Kind.Interface
        Resource: falcor.falcor_ext.ReflectionType.Kind # value = Kind.Resource
        Struct: falcor.falcor_ext.ReflectionType.Kind # value = Kind.Struct
        __members__: dict # value = {'Array': Kind.Array, 'Struct': Kind.Struct, 'Basic': Kind.Basic, 'Resource': Kind.Resource, 'Interface': Kind.Interface}
        pass
    def __repr__(self) -> str: ...
    @property
    def as_array_type(self) -> ReflectionArrayType:
        """
        :type: ReflectionArrayType
        """
    @property
    def as_basic_type(self) -> ReflectionBasicType:
        """
        :type: ReflectionBasicType
        """
    @property
    def as_interface_type(self) -> ReflectionInterfaceType:
        """
        :type: ReflectionInterfaceType
        """
    @property
    def as_resource_type(self) -> ReflectionResourceType:
        """
        :type: ReflectionResourceType
        """
    @property
    def as_struct_type(self) -> ReflectionStructType:
        """
        :type: ReflectionStructType
        """
    @property
    def kind(self) -> ReflectionType.Kind:
        """
        :type: ReflectionType.Kind
        """
    pass
class ReflectionBasicType(ReflectionType):
    class Type():
        """
        Members:

          Bool

          Bool2

          Bool3

          Bool4

          Uint8

          Uint8_2

          Uint8_3

          Uint8_4

          Uint16

          Uint16_2

          Uint16_3

          Uint16_4

          Uint

          Uint2

          Uint3

          Uint4

          Uint64

          Uint64_2

          Uint64_3

          Uint64_4

          Int8

          Int8_2

          Int8_3

          Int8_4

          Int16

          Int16_2

          Int16_3

          Int16_4

          Int

          Int2

          Int3

          Int4

          Int64

          Int64_2

          Int64_3

          Int64_4

          Float16

          Float16_2

          Float16_3

          Float16_4

          Float16_2x2

          Float16_2x3

          Float16_2x4

          Float16_3x2

          Float16_3x3

          Float16_3x4

          Float16_4x2

          Float16_4x3

          Float16_4x4

          Float

          Float2

          Float3

          Float4

          Float2x2

          Float2x3

          Float2x4

          Float3x2

          Float3x3

          Float3x4

          Float4x2

          Float4x3

          Float4x4

          Float64

          Float64_2

          Float64_3

          Float64_4

          Unknown
        """
        def __eq__(self, other: object) -> bool: ...
        def __getstate__(self) -> int: ...
        def __hash__(self) -> int: ...
        def __index__(self) -> int: ...
        def __init__(self, value: int) -> None: ...
        def __int__(self) -> int: ...
        def __ne__(self, other: object) -> bool: ...
        def __repr__(self) -> str: ...
        def __setstate__(self, state: int) -> None: ...
        @property
        def name(self) -> str:
            """
            :type: str
            """
        @property
        def value(self) -> int:
            """
            :type: int
            """
        Bool: falcor.falcor_ext.ReflectionBasicType.Type # value = Type.Bool
        Bool2: falcor.falcor_ext.ReflectionBasicType.Type # value = Type.Bool2
        Bool3: falcor.falcor_ext.ReflectionBasicType.Type # value = Type.Bool3
        Bool4: falcor.falcor_ext.ReflectionBasicType.Type # value = Type.Bool4
        Float: falcor.falcor_ext.ReflectionBasicType.Type # value = Type.Float
        Float16: falcor.falcor_ext.ReflectionBasicType.Type # value = Type.Float16
        Float16_2: falcor.falcor_ext.ReflectionBasicType.Type # value = Type.Float16_2
        Float16_2x2: falcor.falcor_ext.ReflectionBasicType.Type # value = Type.Float16_2x2
        Float16_2x3: falcor.falcor_ext.ReflectionBasicType.Type # value = Type.Float16_2x3
        Float16_2x4: falcor.falcor_ext.ReflectionBasicType.Type # value = Type.Float16_2x4
        Float16_3: falcor.falcor_ext.ReflectionBasicType.Type # value = Type.Float16_3
        Float16_3x2: falcor.falcor_ext.ReflectionBasicType.Type # value = Type.Float16_3x2
        Float16_3x3: falcor.falcor_ext.ReflectionBasicType.Type # value = Type.Float16_3x3
        Float16_3x4: falcor.falcor_ext.ReflectionBasicType.Type # value = Type.Float16_3x4
        Float16_4: falcor.falcor_ext.ReflectionBasicType.Type # value = Type.Float16_4
        Float16_4x2: falcor.falcor_ext.ReflectionBasicType.Type # value = Type.Float16_4x2
        Float16_4x3: falcor.falcor_ext.ReflectionBasicType.Type # value = Type.Float16_4x3
        Float16_4x4: falcor.falcor_ext.ReflectionBasicType.Type # value = Type.Float16_4x4
        Float2: falcor.falcor_ext.ReflectionBasicType.Type # value = Type.Float2
        Float2x2: falcor.falcor_ext.ReflectionBasicType.Type # value = Type.Float2x2
        Float2x3: falcor.falcor_ext.ReflectionBasicType.Type # value = Type.Float2x3
        Float2x4: falcor.falcor_ext.ReflectionBasicType.Type # value = Type.Float2x4
        Float3: falcor.falcor_ext.ReflectionBasicType.Type # value = Type.Float3
        Float3x2: falcor.falcor_ext.ReflectionBasicType.Type # value = Type.Float3x2
        Float3x3: falcor.falcor_ext.ReflectionBasicType.Type # value = Type.Float3x3
        Float3x4: falcor.falcor_ext.ReflectionBasicType.Type # value = Type.Float3x4
        Float4: falcor.falcor_ext.ReflectionBasicType.Type # value = Type.Float4
        Float4x2: falcor.falcor_ext.ReflectionBasicType.Type # value = Type.Float4x2
        Float4x3: falcor.falcor_ext.ReflectionBasicType.Type # value = Type.Float4x3
        Float4x4: falcor.falcor_ext.ReflectionBasicType.Type # value = Type.Float4x4
        Float64: falcor.falcor_ext.ReflectionBasicType.Type # value = Type.Float64
        Float64_2: falcor.falcor_ext.ReflectionBasicType.Type # value = Type.Float64_2
        Float64_3: falcor.falcor_ext.ReflectionBasicType.Type # value = Type.Float64_3
        Float64_4: falcor.falcor_ext.ReflectionBasicType.Type # value = Type.Float64_4
        Int: falcor.falcor_ext.ReflectionBasicType.Type # value = Type.Int
        Int16: falcor.falcor_ext.ReflectionBasicType.Type # value = Type.Int16
        Int16_2: falcor.falcor_ext.ReflectionBasicType.Type # value = Type.Int16_2
        Int16_3: falcor.falcor_ext.ReflectionBasicType.Type # value = Type.Int16_3
        Int16_4: falcor.falcor_ext.ReflectionBasicType.Type # value = Type.Int16_4
        Int2: falcor.falcor_ext.ReflectionBasicType.Type # value = Type.Int2
        Int3: falcor.falcor_ext.ReflectionBasicType.Type # value = Type.Int3
        Int4: falcor.falcor_ext.ReflectionBasicType.Type # value = Type.Int4
        Int64: falcor.falcor_ext.ReflectionBasicType.Type # value = Type.Int64
        Int64_2: falcor.falcor_ext.ReflectionBasicType.Type # value = Type.Int64_2
        Int64_3: falcor.falcor_ext.ReflectionBasicType.Type # value = Type.Int64_3
        Int64_4: falcor.falcor_ext.ReflectionBasicType.Type # value = Type.Int64_4
        Int8: falcor.falcor_ext.ReflectionBasicType.Type # value = Type.Int8
        Int8_2: falcor.falcor_ext.ReflectionBasicType.Type # value = Type.Int8_2
        Int8_3: falcor.falcor_ext.ReflectionBasicType.Type # value = Type.Int8_3
        Int8_4: falcor.falcor_ext.ReflectionBasicType.Type # value = Type.Int8_4
        Uint: falcor.falcor_ext.ReflectionBasicType.Type # value = Type.Uint
        Uint16: falcor.falcor_ext.ReflectionBasicType.Type # value = Type.Uint16
        Uint16_2: falcor.falcor_ext.ReflectionBasicType.Type # value = Type.Uint16_2
        Uint16_3: falcor.falcor_ext.ReflectionBasicType.Type # value = Type.Uint16_3
        Uint16_4: falcor.falcor_ext.ReflectionBasicType.Type # value = Type.Uint16_4
        Uint2: falcor.falcor_ext.ReflectionBasicType.Type # value = Type.Uint2
        Uint3: falcor.falcor_ext.ReflectionBasicType.Type # value = Type.Uint3
        Uint4: falcor.falcor_ext.ReflectionBasicType.Type # value = Type.Uint4
        Uint64: falcor.falcor_ext.ReflectionBasicType.Type # value = Type.Uint64
        Uint64_2: falcor.falcor_ext.ReflectionBasicType.Type # value = Type.Uint64_2
        Uint64_3: falcor.falcor_ext.ReflectionBasicType.Type # value = Type.Uint64_3
        Uint64_4: falcor.falcor_ext.ReflectionBasicType.Type # value = Type.Uint64_4
        Uint8: falcor.falcor_ext.ReflectionBasicType.Type # value = Type.Uint8
        Uint8_2: falcor.falcor_ext.ReflectionBasicType.Type # value = Type.Uint8_2
        Uint8_3: falcor.falcor_ext.ReflectionBasicType.Type # value = Type.Uint8_3
        Uint8_4: falcor.falcor_ext.ReflectionBasicType.Type # value = Type.Uint8_4
        Unknown: falcor.falcor_ext.ReflectionBasicType.Type # value = Type.Unknown
        __members__: dict # value = {'Bool': Type.Bool, 'Bool2': Type.Bool2, 'Bool3': Type.Bool3, 'Bool4': Type.Bool4, 'Uint8': Type.Uint8, 'Uint8_2': Type.Uint8_2, 'Uint8_3': Type.Uint8_3, 'Uint8_4': Type.Uint8_4, 'Uint16': Type.Uint16, 'Uint16_2': Type.Uint16_2, 'Uint16_3': Type.Uint16_3, 'Uint16_4': Type.Uint16_4, 'Uint': Type.Uint, 'Uint2': Type.Uint2, 'Uint3': Type.Uint3, 'Uint4': Type.Uint4, 'Uint64': Type.Uint64, 'Uint64_2': Type.Uint64_2, 'Uint64_3': Type.Uint64_3, 'Uint64_4': Type.Uint64_4, 'Int8': Type.Int8, 'Int8_2': Type.Int8_2, 'Int8_3': Type.Int8_3, 'Int8_4': Type.Int8_4, 'Int16': Type.Int16, 'Int16_2': Type.Int16_2, 'Int16_3': Type.Int16_3, 'Int16_4': Type.Int16_4, 'Int': Type.Int, 'Int2': Type.Int2, 'Int3': Type.Int3, 'Int4': Type.Int4, 'Int64': Type.Int64, 'Int64_2': Type.Int64_2, 'Int64_3': Type.Int64_3, 'Int64_4': Type.Int64_4, 'Float16': Type.Float16, 'Float16_2': Type.Float16_2, 'Float16_3': Type.Float16_3, 'Float16_4': Type.Float16_4, 'Float16_2x2': Type.Float16_2x2, 'Float16_2x3': Type.Float16_2x3, 'Float16_2x4': Type.Float16_2x4, 'Float16_3x2': Type.Float16_3x2, 'Float16_3x3': Type.Float16_3x3, 'Float16_3x4': Type.Float16_3x4, 'Float16_4x2': Type.Float16_4x2, 'Float16_4x3': Type.Float16_4x3, 'Float16_4x4': Type.Float16_4x4, 'Float': Type.Float, 'Float2': Type.Float2, 'Float3': Type.Float3, 'Float4': Type.Float4, 'Float2x2': Type.Float2x2, 'Float2x3': Type.Float2x3, 'Float2x4': Type.Float2x4, 'Float3x2': Type.Float3x2, 'Float3x3': Type.Float3x3, 'Float3x4': Type.Float3x4, 'Float4x2': Type.Float4x2, 'Float4x3': Type.Float4x3, 'Float4x4': Type.Float4x4, 'Float64': Type.Float64, 'Float64_2': Type.Float64_2, 'Float64_3': Type.Float64_3, 'Float64_4': Type.Float64_4, 'Unknown': Type.Unknown}
        pass
    def __repr__(self) -> str: ...
    @property
    def is_row_major(self) -> bool:
        """
        :type: bool
        """
    @property
    def type(self) -> ReflectionBasicType.Type:
        """
        :type: ReflectionBasicType.Type
        """
    pass
class ReflectionInterfaceType(ReflectionType):
    def __repr__(self) -> str: ...
    pass
class ReflectionResourceType(ReflectionType):
    class Dimensions():
        """
        Members:

          Unknown

          Texture1D

          Texture2D

          Texture3D

          TextureCube

          Texture1DArray

          Texture2DArray

          Texture2DMS

          Texture2DMSArray

          TextureCubeArray

          AccelerationStructure

          Buffer
        """
        def __eq__(self, other: object) -> bool: ...
        def __getstate__(self) -> int: ...
        def __hash__(self) -> int: ...
        def __index__(self) -> int: ...
        def __init__(self, value: int) -> None: ...
        def __int__(self) -> int: ...
        def __ne__(self, other: object) -> bool: ...
        def __repr__(self) -> str: ...
        def __setstate__(self, state: int) -> None: ...
        @property
        def name(self) -> str:
            """
            :type: str
            """
        @property
        def value(self) -> int:
            """
            :type: int
            """
        AccelerationStructure: falcor.falcor_ext.ReflectionResourceType.Dimensions # value = Dimensions.AccelerationStructure
        Buffer: falcor.falcor_ext.ReflectionResourceType.Dimensions # value = Dimensions.Buffer
        Texture1D: falcor.falcor_ext.ReflectionResourceType.Dimensions # value = Dimensions.Texture1D
        Texture1DArray: falcor.falcor_ext.ReflectionResourceType.Dimensions # value = Dimensions.Texture1DArray
        Texture2D: falcor.falcor_ext.ReflectionResourceType.Dimensions # value = Dimensions.Texture2D
        Texture2DArray: falcor.falcor_ext.ReflectionResourceType.Dimensions # value = Dimensions.Texture2DArray
        Texture2DMS: falcor.falcor_ext.ReflectionResourceType.Dimensions # value = Dimensions.Texture2DMS
        Texture2DMSArray: falcor.falcor_ext.ReflectionResourceType.Dimensions # value = Dimensions.Texture2DMSArray
        Texture3D: falcor.falcor_ext.ReflectionResourceType.Dimensions # value = Dimensions.Texture3D
        TextureCube: falcor.falcor_ext.ReflectionResourceType.Dimensions # value = Dimensions.TextureCube
        TextureCubeArray: falcor.falcor_ext.ReflectionResourceType.Dimensions # value = Dimensions.TextureCubeArray
        Unknown: falcor.falcor_ext.ReflectionResourceType.Dimensions # value = Dimensions.Unknown
        __members__: dict # value = {'Unknown': Dimensions.Unknown, 'Texture1D': Dimensions.Texture1D, 'Texture2D': Dimensions.Texture2D, 'Texture3D': Dimensions.Texture3D, 'TextureCube': Dimensions.TextureCube, 'Texture1DArray': Dimensions.Texture1DArray, 'Texture2DArray': Dimensions.Texture2DArray, 'Texture2DMS': Dimensions.Texture2DMS, 'Texture2DMSArray': Dimensions.Texture2DMSArray, 'TextureCubeArray': Dimensions.TextureCubeArray, 'AccelerationStructure': Dimensions.AccelerationStructure, 'Buffer': Dimensions.Buffer}
        pass
    class ReturnType():
        """
        Members:

          Unknown

          Float

          Double

          Int

          Uint
        """
        def __eq__(self, other: object) -> bool: ...
        def __getstate__(self) -> int: ...
        def __hash__(self) -> int: ...
        def __index__(self) -> int: ...
        def __init__(self, value: int) -> None: ...
        def __int__(self) -> int: ...
        def __ne__(self, other: object) -> bool: ...
        def __repr__(self) -> str: ...
        def __setstate__(self, state: int) -> None: ...
        @property
        def name(self) -> str:
            """
            :type: str
            """
        @property
        def value(self) -> int:
            """
            :type: int
            """
        Double: falcor.falcor_ext.ReflectionResourceType.ReturnType # value = ReturnType.Double
        Float: falcor.falcor_ext.ReflectionResourceType.ReturnType # value = ReturnType.Float
        Int: falcor.falcor_ext.ReflectionResourceType.ReturnType # value = ReturnType.Int
        Uint: falcor.falcor_ext.ReflectionResourceType.ReturnType # value = ReturnType.Uint
        Unknown: falcor.falcor_ext.ReflectionResourceType.ReturnType # value = ReturnType.Unknown
        __members__: dict # value = {'Unknown': ReturnType.Unknown, 'Float': ReturnType.Float, 'Double': ReturnType.Double, 'Int': ReturnType.Int, 'Uint': ReturnType.Uint}
        pass
    class ShaderAccess():
        """
        Members:

          Undefined

          Read

          ReadWrite
        """
        def __eq__(self, other: object) -> bool: ...
        def __getstate__(self) -> int: ...
        def __hash__(self) -> int: ...
        def __index__(self) -> int: ...
        def __init__(self, value: int) -> None: ...
        def __int__(self) -> int: ...
        def __ne__(self, other: object) -> bool: ...
        def __repr__(self) -> str: ...
        def __setstate__(self, state: int) -> None: ...
        @property
        def name(self) -> str:
            """
            :type: str
            """
        @property
        def value(self) -> int:
            """
            :type: int
            """
        Read: falcor.falcor_ext.ReflectionResourceType.ShaderAccess # value = ShaderAccess.Read
        ReadWrite: falcor.falcor_ext.ReflectionResourceType.ShaderAccess # value = ShaderAccess.ReadWrite
        Undefined: falcor.falcor_ext.ReflectionResourceType.ShaderAccess # value = ShaderAccess.Undefined
        __members__: dict # value = {'Undefined': ShaderAccess.Undefined, 'Read': ShaderAccess.Read, 'ReadWrite': ShaderAccess.ReadWrite}
        pass
    class StructuredType():
        """
        Members:

          Invalid

          Default

          Counter

          Append

          Consume
        """
        def __eq__(self, other: object) -> bool: ...
        def __getstate__(self) -> int: ...
        def __hash__(self) -> int: ...
        def __index__(self) -> int: ...
        def __init__(self, value: int) -> None: ...
        def __int__(self) -> int: ...
        def __ne__(self, other: object) -> bool: ...
        def __repr__(self) -> str: ...
        def __setstate__(self, state: int) -> None: ...
        @property
        def name(self) -> str:
            """
            :type: str
            """
        @property
        def value(self) -> int:
            """
            :type: int
            """
        Append: falcor.falcor_ext.ReflectionResourceType.StructuredType # value = StructuredType.Append
        Consume: falcor.falcor_ext.ReflectionResourceType.StructuredType # value = StructuredType.Consume
        Counter: falcor.falcor_ext.ReflectionResourceType.StructuredType # value = StructuredType.Counter
        Default: falcor.falcor_ext.ReflectionResourceType.StructuredType # value = StructuredType.Default
        Invalid: falcor.falcor_ext.ReflectionResourceType.StructuredType # value = StructuredType.Invalid
        __members__: dict # value = {'Invalid': StructuredType.Invalid, 'Default': StructuredType.Default, 'Counter': StructuredType.Counter, 'Append': StructuredType.Append, 'Consume': StructuredType.Consume}
        pass
    class Type():
        """
        Members:

          Texture

          StructuredBuffer

          RawBuffer

          TypedBuffer

          Sampler

          ConstantBuffer

          AccelerationStructure
        """
        def __eq__(self, other: object) -> bool: ...
        def __getstate__(self) -> int: ...
        def __hash__(self) -> int: ...
        def __index__(self) -> int: ...
        def __init__(self, value: int) -> None: ...
        def __int__(self) -> int: ...
        def __ne__(self, other: object) -> bool: ...
        def __repr__(self) -> str: ...
        def __setstate__(self, state: int) -> None: ...
        @property
        def name(self) -> str:
            """
            :type: str
            """
        @property
        def value(self) -> int:
            """
            :type: int
            """
        AccelerationStructure: falcor.falcor_ext.ReflectionResourceType.Type # value = Type.AccelerationStructure
        ConstantBuffer: falcor.falcor_ext.ReflectionResourceType.Type # value = Type.ConstantBuffer
        RawBuffer: falcor.falcor_ext.ReflectionResourceType.Type # value = Type.RawBuffer
        Sampler: falcor.falcor_ext.ReflectionResourceType.Type # value = Type.Sampler
        StructuredBuffer: falcor.falcor_ext.ReflectionResourceType.Type # value = Type.StructuredBuffer
        Texture: falcor.falcor_ext.ReflectionResourceType.Type # value = Type.Texture
        TypedBuffer: falcor.falcor_ext.ReflectionResourceType.Type # value = Type.TypedBuffer
        __members__: dict # value = {'Texture': Type.Texture, 'StructuredBuffer': Type.StructuredBuffer, 'RawBuffer': Type.RawBuffer, 'TypedBuffer': Type.TypedBuffer, 'Sampler': Type.Sampler, 'ConstantBuffer': Type.ConstantBuffer, 'AccelerationStructure': Type.AccelerationStructure}
        pass
    def __repr__(self) -> str: ...
    @property
    def dimensions(self) -> ReflectionResourceType.Dimensions:
        """
        :type: ReflectionResourceType.Dimensions
        """
    @property
    def return_type(self) -> ReflectionResourceType.ReturnType:
        """
        :type: ReflectionResourceType.ReturnType
        """
    @property
    def shader_access(self) -> ReflectionResourceType.ShaderAccess:
        """
        :type: ReflectionResourceType.ShaderAccess
        """
    @property
    def size(self) -> int:
        """
        :type: int
        """
    @property
    def struct_type(self) -> ReflectionType:
        """
        :type: ReflectionType
        """
    @property
    def structured_buffer_type(self) -> ReflectionResourceType.StructuredType:
        """
        :type: ReflectionResourceType.StructuredType
        """
    @property
    def type(self) -> ReflectionResourceType.Type:
        """
        :type: ReflectionResourceType.Type
        """
    pass
class ReflectionStructType(ReflectionType):
    def __getattr__(self, arg0: str) -> ReflectionVar: ...
    @typing.overload
    def __getitem__(self, arg0: int) -> ReflectionVar: ...
    @typing.overload
    def __getitem__(self, arg0: str) -> ReflectionVar: ...
    def __repr__(self) -> str: ...
    @property
    def members(self) -> dict:
        """
        :type: dict
        """
    @property
    def name(self) -> str:
        """
        :type: str
        """
    pass
class ReflectionArrayType(ReflectionType):
    def __repr__(self) -> str: ...
    @property
    def element_byte_stride(self) -> int:
        """
        :type: int
        """
    @property
    def element_count(self) -> int:
        """
        :type: int
        """
    @property
    def element_type(self) -> ReflectionType:
        """
        :type: ReflectionType
        """
    pass
class ReflectionVar():
    def __repr__(self) -> str: ...
    @property
    def name(self) -> str:
        """
        :type: str
        """
    @property
    def offset(self) -> int:
        """
        :type: int
        """
    @property
    def type(self) -> ReflectionType:
        """
        :type: ReflectionType
        """
    pass
class RenderContext(ComputeContext, CopyContext):
    pass
class RenderGraph():
    def __getitem__(self, arg0: str) -> RenderPass: ...
    def __init__(self, name: str) -> None: ...
    def addEdge(self, src: str, dst: str) -> int: ...
    def addPass(self, pass_: RenderPass, name: str) -> int: ...
    def add_edge(self, src: str, dst: str) -> int: ...
    @staticmethod
    def createFromFile(path: os.PathLike) -> RenderGraph: ...
    def createPass(self, passName: str, passType: str, dict: dict = {}) -> RenderPass: ...
    def create_pass(self, pass_name: str, pass_type: str, dict: dict = {}) -> RenderPass: ...
    def getOutput(self, name: str) -> Resource: ...
    def getPass(self, name: str) -> RenderPass: ...
    def get_output(self, name: str) -> Resource: ...
    def get_pass(self, name: str) -> RenderPass: ...
    def markOutput(self, name: str, mask: TextureChannelFlags = TextureChannelFlags.RGB) -> None: ...
    def mark_output(self, name: str, mask: TextureChannelFlags = TextureChannelFlags.RGB) -> None: ...
    def print(self) -> None: ...
    def removeEdge(self, src: str, dst: str) -> None: ...
    def removePass(self, name: str) -> None: ...
    def remove_edge(self, src: str, dst: str) -> None: ...
    def remove_pass(self, name: str) -> None: ...
    def unmarkOutput(self, name: str) -> None: ...
    def unmark_output(self, name: str) -> None: ...
    def updatePass(self, name: str, dict: dict) -> None: ...
    def update_pass(self, name: str, dict: dict) -> None: ...
    @property
    def name(self) -> str:
        """
        :type: str
        """
    @name.setter
    def name(self, arg1: str) -> None:
        pass
    pass
class AccumulatePass(RenderPass):
    def reset(self) -> None: ...
    @property
    def enabled(self) -> bool:
        """
        :type: bool
        """
    @enabled.setter
    def enabled(self, arg1: bool) -> None:
        pass
    pass
class RenderTargetView():
    pass
class Buffer(Resource):
    def copy_to_torch(self, data: torch.Tensor) -> None: ...
    def from_numpy(self, data: numpy.ndarray) -> None: ...
    def from_torch(self, data: torch.Tensor) -> None: ...
    def to_numpy(self) -> numpy.ndarray: ...
    def to_torch(self, shape: typing.List[int], dtype: DataType = DataType.float32) -> torch.Tensor: ...
    @property
    def element_count(self) -> int:
        """
        :type: int
        """
    @property
    def format(self) -> ResourceFormat:
        """
        :type: ResourceFormat
        """
    @property
    def is_structured(self) -> bool:
        """
        :type: bool
        """
    @property
    def is_typed(self) -> bool:
        """
        :type: bool
        """
    @property
    def memory_type(self) -> MemoryType:
        """
        :type: MemoryType
        """
    @property
    def size(self) -> int:
        """
        :type: int
        """
    @property
    def struct_size(self) -> int:
        """
        :type: int
        """
    pass
class ResourceBindFlags():
    """
    Members:

      None_

      Vertex

      Index

      Constant

      StreamOutput

      ShaderResource

      UnorderedAccess

      RenderTarget

      DepthStencil

      IndirectArg

      Shared

      AccelerationStructure
    """
    def __and__(self, arg0: ResourceBindFlags) -> ResourceBindFlags: ...
    def __eq__(self, other: object) -> bool: ...
    def __getstate__(self) -> int: ...
    def __hash__(self) -> int: ...
    def __index__(self) -> int: ...
    def __init__(self, value: int) -> None: ...
    def __int__(self) -> int: ...
    def __ne__(self, other: object) -> bool: ...
    def __or__(self, arg0: ResourceBindFlags) -> ResourceBindFlags: ...
    def __repr__(self) -> str: ...
    def __setstate__(self, state: int) -> None: ...
    @property
    def name(self) -> str:
        """
        :type: str
        """
    @property
    def value(self) -> int:
        """
        :type: int
        """
    AccelerationStructure: falcor.falcor_ext.ResourceBindFlags # value = ResourceBindFlags.AccelerationStructure
    Constant: falcor.falcor_ext.ResourceBindFlags # value = ResourceBindFlags.Constant
    DepthStencil: falcor.falcor_ext.ResourceBindFlags # value = ResourceBindFlags.DepthStencil
    Index: falcor.falcor_ext.ResourceBindFlags # value = ResourceBindFlags.Index
    IndirectArg: falcor.falcor_ext.ResourceBindFlags # value = ResourceBindFlags.IndirectArg
    None_: falcor.falcor_ext.ResourceBindFlags # value = ResourceBindFlags.None_
    RenderTarget: falcor.falcor_ext.ResourceBindFlags # value = ResourceBindFlags.RenderTarget
    ShaderResource: falcor.falcor_ext.ResourceBindFlags # value = ResourceBindFlags.ShaderResource
    Shared: falcor.falcor_ext.ResourceBindFlags # value = ResourceBindFlags.Shared
    StreamOutput: falcor.falcor_ext.ResourceBindFlags # value = ResourceBindFlags.StreamOutput
    UnorderedAccess: falcor.falcor_ext.ResourceBindFlags # value = ResourceBindFlags.UnorderedAccess
    Vertex: falcor.falcor_ext.ResourceBindFlags # value = ResourceBindFlags.Vertex
    __members__: dict # value = {'None_': ResourceBindFlags.None_, 'Vertex': ResourceBindFlags.Vertex, 'Index': ResourceBindFlags.Index, 'Constant': ResourceBindFlags.Constant, 'StreamOutput': ResourceBindFlags.StreamOutput, 'ShaderResource': ResourceBindFlags.ShaderResource, 'UnorderedAccess': ResourceBindFlags.UnorderedAccess, 'RenderTarget': ResourceBindFlags.RenderTarget, 'DepthStencil': ResourceBindFlags.DepthStencil, 'IndirectArg': ResourceBindFlags.IndirectArg, 'Shared': ResourceBindFlags.Shared, 'AccelerationStructure': ResourceBindFlags.AccelerationStructure}
    pass
class ResourceFormat():
    """
    Members:

      Unknown

      R8Unorm

      R8Snorm

      R16Unorm

      R16Snorm

      RG8Unorm

      RG8Snorm

      RG16Unorm

      RG16Snorm

      RGB5A1Unorm

      RGBA8Unorm

      RGBA8Snorm

      RGB10A2Unorm

      RGB10A2Uint

      RGBA16Unorm

      RGBA16Snorm

      RGBA8UnormSrgb

      R16Float

      RG16Float

      RGBA16Float

      R32Float

      RG32Float

      RGB32Float

      RGBA32Float

      R11G11B10Float

      RGB9E5Float

      R8Int

      R8Uint

      R16Int

      R16Uint

      R32Int

      R32Uint

      RG8Int

      RG8Uint

      RG16Int

      RG16Uint

      RG32Int

      RG32Uint

      RGB32Int

      RGB32Uint

      RGBA8Int

      RGBA8Uint

      RGBA16Int

      RGBA16Uint

      RGBA32Int

      RGBA32Uint

      BGRA4Unorm

      BGRA8Unorm

      BGRA8UnormSrgb

      BGRX8Unorm

      BGRX8UnormSrgb

      R5G6B5Unorm

      D32Float

      D32FloatS8Uint

      D16Unorm

      BC1Unorm

      BC1UnormSrgb

      BC2Unorm

      BC2UnormSrgb

      BC3Unorm

      BC3UnormSrgb

      BC4Unorm

      BC4Snorm

      BC5Unorm

      BC5Snorm

      BC6HS16

      BC6HU16

      BC7Unorm

      BC7UnormSrgb
    """
    def __eq__(self, other: object) -> bool: ...
    def __getstate__(self) -> int: ...
    def __hash__(self) -> int: ...
    def __index__(self) -> int: ...
    def __init__(self, value: int) -> None: ...
    def __int__(self) -> int: ...
    def __ne__(self, other: object) -> bool: ...
    def __repr__(self) -> str: ...
    def __setstate__(self, state: int) -> None: ...
    @property
    def name(self) -> str:
        """
        :type: str
        """
    @property
    def value(self) -> int:
        """
        :type: int
        """
    BC1Unorm: falcor.falcor_ext.ResourceFormat # value = ResourceFormat.BC1Unorm
    BC1UnormSrgb: falcor.falcor_ext.ResourceFormat # value = ResourceFormat.BC1UnormSrgb
    BC2Unorm: falcor.falcor_ext.ResourceFormat # value = ResourceFormat.BC2Unorm
    BC2UnormSrgb: falcor.falcor_ext.ResourceFormat # value = ResourceFormat.BC2UnormSrgb
    BC3Unorm: falcor.falcor_ext.ResourceFormat # value = ResourceFormat.BC3Unorm
    BC3UnormSrgb: falcor.falcor_ext.ResourceFormat # value = ResourceFormat.BC3UnormSrgb
    BC4Snorm: falcor.falcor_ext.ResourceFormat # value = ResourceFormat.BC4Snorm
    BC4Unorm: falcor.falcor_ext.ResourceFormat # value = ResourceFormat.BC4Unorm
    BC5Snorm: falcor.falcor_ext.ResourceFormat # value = ResourceFormat.BC5Snorm
    BC5Unorm: falcor.falcor_ext.ResourceFormat # value = ResourceFormat.BC5Unorm
    BC6HS16: falcor.falcor_ext.ResourceFormat # value = ResourceFormat.BC6HS16
    BC6HU16: falcor.falcor_ext.ResourceFormat # value = ResourceFormat.BC6HU16
    BC7Unorm: falcor.falcor_ext.ResourceFormat # value = ResourceFormat.BC7Unorm
    BC7UnormSrgb: falcor.falcor_ext.ResourceFormat # value = ResourceFormat.BC7UnormSrgb
    BGRA4Unorm: falcor.falcor_ext.ResourceFormat # value = ResourceFormat.BGRA4Unorm
    BGRA8Unorm: falcor.falcor_ext.ResourceFormat # value = ResourceFormat.BGRA8Unorm
    BGRA8UnormSrgb: falcor.falcor_ext.ResourceFormat # value = ResourceFormat.BGRA8UnormSrgb
    BGRX8Unorm: falcor.falcor_ext.ResourceFormat # value = ResourceFormat.BGRX8Unorm
    BGRX8UnormSrgb: falcor.falcor_ext.ResourceFormat # value = ResourceFormat.BGRX8UnormSrgb
    D16Unorm: falcor.falcor_ext.ResourceFormat # value = ResourceFormat.D16Unorm
    D32Float: falcor.falcor_ext.ResourceFormat # value = ResourceFormat.D32Float
    D32FloatS8Uint: falcor.falcor_ext.ResourceFormat # value = ResourceFormat.D32FloatS8Uint
    R11G11B10Float: falcor.falcor_ext.ResourceFormat # value = ResourceFormat.R11G11B10Float
    R16Float: falcor.falcor_ext.ResourceFormat # value = ResourceFormat.R16Float
    R16Int: falcor.falcor_ext.ResourceFormat # value = ResourceFormat.R16Int
    R16Snorm: falcor.falcor_ext.ResourceFormat # value = ResourceFormat.R16Snorm
    R16Uint: falcor.falcor_ext.ResourceFormat # value = ResourceFormat.R16Uint
    R16Unorm: falcor.falcor_ext.ResourceFormat # value = ResourceFormat.R16Unorm
    R32Float: falcor.falcor_ext.ResourceFormat # value = ResourceFormat.R32Float
    R32Int: falcor.falcor_ext.ResourceFormat # value = ResourceFormat.R32Int
    R32Uint: falcor.falcor_ext.ResourceFormat # value = ResourceFormat.R32Uint
    R5G6B5Unorm: falcor.falcor_ext.ResourceFormat # value = ResourceFormat.R5G6B5Unorm
    R8Int: falcor.falcor_ext.ResourceFormat # value = ResourceFormat.R8Int
    R8Snorm: falcor.falcor_ext.ResourceFormat # value = ResourceFormat.R8Snorm
    R8Uint: falcor.falcor_ext.ResourceFormat # value = ResourceFormat.R8Uint
    R8Unorm: falcor.falcor_ext.ResourceFormat # value = ResourceFormat.R8Unorm
    RG16Float: falcor.falcor_ext.ResourceFormat # value = ResourceFormat.RG16Float
    RG16Int: falcor.falcor_ext.ResourceFormat # value = ResourceFormat.RG16Int
    RG16Snorm: falcor.falcor_ext.ResourceFormat # value = ResourceFormat.RG16Snorm
    RG16Uint: falcor.falcor_ext.ResourceFormat # value = ResourceFormat.RG16Uint
    RG16Unorm: falcor.falcor_ext.ResourceFormat # value = ResourceFormat.RG16Unorm
    RG32Float: falcor.falcor_ext.ResourceFormat # value = ResourceFormat.RG32Float
    RG32Int: falcor.falcor_ext.ResourceFormat # value = ResourceFormat.RG32Int
    RG32Uint: falcor.falcor_ext.ResourceFormat # value = ResourceFormat.RG32Uint
    RG8Int: falcor.falcor_ext.ResourceFormat # value = ResourceFormat.RG8Int
    RG8Snorm: falcor.falcor_ext.ResourceFormat # value = ResourceFormat.RG8Snorm
    RG8Uint: falcor.falcor_ext.ResourceFormat # value = ResourceFormat.RG8Uint
    RG8Unorm: falcor.falcor_ext.ResourceFormat # value = ResourceFormat.RG8Unorm
    RGB10A2Uint: falcor.falcor_ext.ResourceFormat # value = ResourceFormat.RGB10A2Uint
    RGB10A2Unorm: falcor.falcor_ext.ResourceFormat # value = ResourceFormat.RGB10A2Unorm
    RGB32Float: falcor.falcor_ext.ResourceFormat # value = ResourceFormat.RGB32Float
    RGB32Int: falcor.falcor_ext.ResourceFormat # value = ResourceFormat.RGB32Int
    RGB32Uint: falcor.falcor_ext.ResourceFormat # value = ResourceFormat.RGB32Uint
    RGB5A1Unorm: falcor.falcor_ext.ResourceFormat # value = ResourceFormat.RGB5A1Unorm
    RGB9E5Float: falcor.falcor_ext.ResourceFormat # value = ResourceFormat.RGB9E5Float
    RGBA16Float: falcor.falcor_ext.ResourceFormat # value = ResourceFormat.RGBA16Float
    RGBA16Int: falcor.falcor_ext.ResourceFormat # value = ResourceFormat.RGBA16Int
    RGBA16Snorm: falcor.falcor_ext.ResourceFormat # value = ResourceFormat.RGBA16Snorm
    RGBA16Uint: falcor.falcor_ext.ResourceFormat # value = ResourceFormat.RGBA16Uint
    RGBA16Unorm: falcor.falcor_ext.ResourceFormat # value = ResourceFormat.RGBA16Unorm
    RGBA32Float: falcor.falcor_ext.ResourceFormat # value = ResourceFormat.RGBA32Float
    RGBA32Int: falcor.falcor_ext.ResourceFormat # value = ResourceFormat.RGBA32Int
    RGBA32Uint: falcor.falcor_ext.ResourceFormat # value = ResourceFormat.RGBA32Uint
    RGBA8Int: falcor.falcor_ext.ResourceFormat # value = ResourceFormat.RGBA8Int
    RGBA8Snorm: falcor.falcor_ext.ResourceFormat # value = ResourceFormat.RGBA8Snorm
    RGBA8Uint: falcor.falcor_ext.ResourceFormat # value = ResourceFormat.RGBA8Uint
    RGBA8Unorm: falcor.falcor_ext.ResourceFormat # value = ResourceFormat.RGBA8Unorm
    RGBA8UnormSrgb: falcor.falcor_ext.ResourceFormat # value = ResourceFormat.RGBA8UnormSrgb
    Unknown: falcor.falcor_ext.ResourceFormat # value = ResourceFormat.Unknown
    __members__: dict # value = {'Unknown': ResourceFormat.Unknown, 'R8Unorm': ResourceFormat.R8Unorm, 'R8Snorm': ResourceFormat.R8Snorm, 'R16Unorm': ResourceFormat.R16Unorm, 'R16Snorm': ResourceFormat.R16Snorm, 'RG8Unorm': ResourceFormat.RG8Unorm, 'RG8Snorm': ResourceFormat.RG8Snorm, 'RG16Unorm': ResourceFormat.RG16Unorm, 'RG16Snorm': ResourceFormat.RG16Snorm, 'RGB5A1Unorm': ResourceFormat.RGB5A1Unorm, 'RGBA8Unorm': ResourceFormat.RGBA8Unorm, 'RGBA8Snorm': ResourceFormat.RGBA8Snorm, 'RGB10A2Unorm': ResourceFormat.RGB10A2Unorm, 'RGB10A2Uint': ResourceFormat.RGB10A2Uint, 'RGBA16Unorm': ResourceFormat.RGBA16Unorm, 'RGBA16Snorm': ResourceFormat.RGBA16Snorm, 'RGBA8UnormSrgb': ResourceFormat.RGBA8UnormSrgb, 'R16Float': ResourceFormat.R16Float, 'RG16Float': ResourceFormat.RG16Float, 'RGBA16Float': ResourceFormat.RGBA16Float, 'R32Float': ResourceFormat.R32Float, 'RG32Float': ResourceFormat.RG32Float, 'RGB32Float': ResourceFormat.RGB32Float, 'RGBA32Float': ResourceFormat.RGBA32Float, 'R11G11B10Float': ResourceFormat.R11G11B10Float, 'RGB9E5Float': ResourceFormat.RGB9E5Float, 'R8Int': ResourceFormat.R8Int, 'R8Uint': ResourceFormat.R8Uint, 'R16Int': ResourceFormat.R16Int, 'R16Uint': ResourceFormat.R16Uint, 'R32Int': ResourceFormat.R32Int, 'R32Uint': ResourceFormat.R32Uint, 'RG8Int': ResourceFormat.RG8Int, 'RG8Uint': ResourceFormat.RG8Uint, 'RG16Int': ResourceFormat.RG16Int, 'RG16Uint': ResourceFormat.RG16Uint, 'RG32Int': ResourceFormat.RG32Int, 'RG32Uint': ResourceFormat.RG32Uint, 'RGB32Int': ResourceFormat.RGB32Int, 'RGB32Uint': ResourceFormat.RGB32Uint, 'RGBA8Int': ResourceFormat.RGBA8Int, 'RGBA8Uint': ResourceFormat.RGBA8Uint, 'RGBA16Int': ResourceFormat.RGBA16Int, 'RGBA16Uint': ResourceFormat.RGBA16Uint, 'RGBA32Int': ResourceFormat.RGBA32Int, 'RGBA32Uint': ResourceFormat.RGBA32Uint, 'BGRA4Unorm': ResourceFormat.BGRA4Unorm, 'BGRA8Unorm': ResourceFormat.BGRA8Unorm, 'BGRA8UnormSrgb': ResourceFormat.BGRA8UnormSrgb, 'BGRX8Unorm': ResourceFormat.BGRX8Unorm, 'BGRX8UnormSrgb': ResourceFormat.BGRX8UnormSrgb, 'R5G6B5Unorm': ResourceFormat.R5G6B5Unorm, 'D32Float': ResourceFormat.D32Float, 'D32FloatS8Uint': ResourceFormat.D32FloatS8Uint, 'D16Unorm': ResourceFormat.D16Unorm, 'BC1Unorm': ResourceFormat.BC1Unorm, 'BC1UnormSrgb': ResourceFormat.BC1UnormSrgb, 'BC2Unorm': ResourceFormat.BC2Unorm, 'BC2UnormSrgb': ResourceFormat.BC2UnormSrgb, 'BC3Unorm': ResourceFormat.BC3Unorm, 'BC3UnormSrgb': ResourceFormat.BC3UnormSrgb, 'BC4Unorm': ResourceFormat.BC4Unorm, 'BC4Snorm': ResourceFormat.BC4Snorm, 'BC5Unorm': ResourceFormat.BC5Unorm, 'BC5Snorm': ResourceFormat.BC5Snorm, 'BC6HS16': ResourceFormat.BC6HS16, 'BC6HU16': ResourceFormat.BC6HU16, 'BC7Unorm': ResourceFormat.BC7Unorm, 'BC7UnormSrgb': ResourceFormat.BC7UnormSrgb}
    pass
class RuntimeError(Exception, BaseException):
    pass
class SDFGrid():
    @staticmethod
    def createNDGrid(narrowBandThickness: float) -> SDFGrid: ...
    @staticmethod
    def createSBS(**kwargs) -> SDFGrid: ...
    @staticmethod
    def createSVO() -> SDFGrid: ...
    @staticmethod
    def createSVS() -> SDFGrid: ...
    def generateCheeseValues(self, gridWidth: int, seed: int) -> None: ...
    def loadPrimitivesFromFile(self, path: os.PathLike, gridWidth: int) -> int: ...
    def loadValuesFromFile(self, path: os.PathLike) -> bool: ...
    @property
    def name(self) -> str:
        """
        :type: str
        """
    @name.setter
    def name(self, arg1: str) -> None:
        pass
    pass
class SSFR(RenderPass):
    @property
    def saveOutput(self) -> bool:
        """
        :type: bool
        """
    @saveOutput.setter
    def saveOutput(self, arg1: bool) -> None:
        pass
    pass
class SSRShading(RenderPass):
    @property
    def bias(self) -> float:
        """
        :type: float
        """
    @bias.setter
    def bias(self, arg1: float) -> None:
        pass
    @property
    def foamNum(self) -> int:
        """
        :type: int
        """
    @foamNum.setter
    def foamNum(self, arg1: int) -> None:
        pass
    @property
    def foamParticlesPosR(self) -> Buffer:
        """
        :type: Buffer
        """
    @foamParticlesPosR.setter
    def foamParticlesPosR(self, arg1: Buffer) -> None:
        pass
    @property
    def renderFoam(self) -> bool:
        """
        :type: bool
        """
    @renderFoam.setter
    def renderFoam(self, arg1: bool) -> None:
        pass
    @property
    def saveNormal(self) -> bool:
        """
        :type: bool
        """
    @saveNormal.setter
    def saveNormal(self, arg1: bool) -> None:
        pass
    @property
    def saveResult(self) -> bool:
        """
        :type: bool
        """
    @saveResult.setter
    def saveResult(self, arg1: bool) -> None:
        pass
    pass
class Sampler():
    @property
    def address_mode_u(self) -> TextureAddressingMode:
        """
        :type: TextureAddressingMode
        """
    @property
    def address_mode_v(self) -> TextureAddressingMode:
        """
        :type: TextureAddressingMode
        """
    @property
    def address_mode_w(self) -> TextureAddressingMode:
        """
        :type: TextureAddressingMode
        """
    @property
    def border_color(self) -> float4:
        """
        :type: float4
        """
    @property
    def comparison_func(self) -> ComparisonFunc:
        """
        :type: ComparisonFunc
        """
    @property
    def lod_bias(self) -> float:
        """
        :type: float
        """
    @property
    def mag_filter(self) -> TextureFilteringMode:
        """
        :type: TextureFilteringMode
        """
    @property
    def max_anisotropy(self) -> int:
        """
        :type: int
        """
    @property
    def max_lod(self) -> float:
        """
        :type: float
        """
    @property
    def min_filter(self) -> TextureFilteringMode:
        """
        :type: TextureFilteringMode
        """
    @property
    def min_lod(self) -> float:
        """
        :type: float
        """
    @property
    def mip_filter(self) -> TextureFilteringMode:
        """
        :type: TextureFilteringMode
        """
    @property
    def reduction_mode(self) -> TextureReductionMode:
        """
        :type: TextureReductionMode
        """
    pass
class Scene():
    def addMaterial(self, material: IMaterial) -> ObjectID: ...
    @typing.overload
    def addViewpoint(self) -> None: ...
    @typing.overload
    def addViewpoint(self, position: float3, target: float3, up: float3, cameraIndex: int = 0) -> None: ...
    def getGeometryIDsForMaterial(self, material: IMaterial) -> typing.List[ObjectID]: ...
    def getGeometryUVTiles(self, geometryID: ObjectID) -> typing.List[Rectangle]: ...
    @typing.overload
    def getGridVolume(self, index: int) -> GridVolume: ...
    @typing.overload
    def getGridVolume(self, name: str) -> GridVolume: ...
    @typing.overload
    def getLight(self, index: int) -> Light: ...
    @typing.overload
    def getLight(self, name: str) -> Light: ...
    @typing.overload
    def getMaterial(self, index: ObjectID) -> IMaterial: ...
    @typing.overload
    def getMaterial(self, name: str) -> IMaterial: ...
    @typing.overload
    def getVolume(self, index: int) -> GridVolume: ...
    @typing.overload
    def getVolume(self, name: str) -> GridVolume: ...
    @typing.overload
    def get_material(self, index: ObjectID) -> IMaterial: ...
    @typing.overload
    def get_material(self, name: str) -> IMaterial: ...
    def get_material_params(self, arg0: Buffer, arg1: Buffer) -> None: ...
    def get_mesh(self, mesh_id: ObjectID) -> MeshDesc: ...
    def get_mesh_vertices_and_indices(self, mesh_id: ObjectID, buffers: dict) -> None: ...
    def removeViewpoint(self) -> None: ...
    def replace_material(self, index: int, replacement_material: IMaterial) -> None: ...
    def selectViewpoint(self, index: int) -> None: ...
    def setCameraBounds(self, minPoint: float3, maxPoint: float3) -> None: ...
    def setEnvMap(self, path: os.PathLike) -> bool: ...
    def set_material_params(self, arg0: Buffer, arg1: Buffer) -> None: ...
    def set_mesh_vertices(self, mesh_id: ObjectID, buffers: dict) -> None: ...
    @property
    def animated(self) -> bool:
        """
        :type: bool
        """
    @animated.setter
    def animated(self, arg1: bool) -> None:
        pass
    @property
    def animations(self) -> typing.List[Animation]:
        """
        :type: typing.List[Animation]
        """
    @property
    def bounds(self) -> AABB:
        """
        :type: AABB
        """
    @property
    def camera(self) -> Camera:
        """
        :type: Camera
        """
    @camera.setter
    def camera(self, arg1: Camera) -> None:
        pass
    @property
    def cameraSpeed(self) -> float:
        """
        :type: float
        """
    @cameraSpeed.setter
    def cameraSpeed(self, arg1: float) -> None:
        pass
    @property
    def cameras(self) -> typing.List[Camera]:
        """
        :type: typing.List[Camera]
        """
    @property
    def envMap(self) -> EnvMap:
        """
        :type: EnvMap
        """
    @envMap.setter
    def envMap(self, arg1: EnvMap) -> None:
        pass
    @property
    def gridVolumes(self) -> typing.List[GridVolume]:
        """
        :type: typing.List[GridVolume]
        """
    @property
    def lights(self) -> typing.List[Light]:
        """
        :type: typing.List[Light]
        """
    @property
    def loopAnimations(self) -> bool:
        """
        :type: bool
        """
    @loopAnimations.setter
    def loopAnimations(self, arg1: bool) -> None:
        pass
    @property
    def materials(self) -> typing.List[IMaterial]:
        """
        :type: typing.List[IMaterial]
        """
    @property
    def memory_usage(self) -> int:
        """
        :type: int
        """
    @property
    def renderSettings(self) -> SceneRenderSettings:
        """
        :type: SceneRenderSettings
        """
    @renderSettings.setter
    def renderSettings(self, arg1: SceneRenderSettings) -> None:
        pass
    @property
    def stats(self) -> dict:
        """
        :type: dict
        """
    @property
    def volumes(self) -> typing.List[GridVolume]:
        """
        :type: typing.List[GridVolume]
        """
    pass
class SceneBuilder():
    def addAnimation(self, animation: Animation) -> None: ...
    def addCamera(self, camera: Camera) -> ObjectID: ...
    def addCustomPrimitive(self, arg0: int, arg1: AABB) -> None: ...
    def addGridVolume(self, gridVolume: GridVolume, nodeID: ObjectID = 4294967295) -> ObjectID: ...
    def addLight(self, light: Light) -> ObjectID: ...
    def addMaterial(self, material: IMaterial) -> ObjectID: ...
    def addMeshInstance(self, arg0: ObjectID, arg1: ObjectID) -> None: ...
    def addNode(self, name: str, transform: Transform = Transform(), parent: ObjectID = 4294967295) -> ObjectID: ...
    def addSDFGrid(self, sdfGrid: SDFGrid, material: IMaterial) -> ObjectID: ...
    def addSDFGridInstance(self, arg0: ObjectID, arg1: ObjectID) -> None: ...
    def addTriangleMesh(self, triangleMesh: TriangleMesh, material: IMaterial, isAnimated: bool = False) -> ObjectID: ...
    def addVolume(self, gridVolume: GridVolume, nodeID: ObjectID = 4294967295) -> ObjectID: ...
    def createAnimation(self, animatable: Animatable, name: str, duration: float) -> Animation: ...
    def getGridVolume(self, name: str) -> GridVolume: ...
    def getLight(self, name: str) -> Light: ...
    def getMaterial(self, name: str) -> IMaterial: ...
    def getSettings(self) -> Settings: ...
    def getVolume(self, name: str) -> GridVolume: ...
    def importScene(self, path: os.PathLike, dict: dict = {}) -> None: ...
    def loadLightProfile(self, filename: str, normalize: bool = True) -> None: ...
    def loadMaterialTexture(self, material: IMaterial, slot: MaterialTextureSlot, path: os.PathLike) -> None: ...
    def replaceMaterial(self, material: IMaterial, replacement: IMaterial) -> None: ...
    def waitForMaterialTextureLoading(self) -> None: ...
    @property
    def animations(self) -> typing.List[Animation]:
        """
        :type: typing.List[Animation]
        """
    @property
    def assetResolver(self) -> AssetResolver:
        """
        :type: AssetResolver
        """
    @property
    def cameraSpeed(self) -> float:
        """
        :type: float
        """
    @cameraSpeed.setter
    def cameraSpeed(self, arg1: float) -> None:
        pass
    @property
    def cameras(self) -> typing.List[Camera]:
        """
        :type: typing.List[Camera]
        """
    @property
    def envMap(self) -> EnvMap:
        """
        :type: EnvMap
        """
    @envMap.setter
    def envMap(self, arg1: EnvMap) -> None:
        pass
    @property
    def flags(self) -> SceneBuilderFlags:
        """
        :type: SceneBuilderFlags
        """
    @property
    def gridVolumes(self) -> typing.List[GridVolume]:
        """
        :type: typing.List[GridVolume]
        """
    @property
    def lights(self) -> typing.List[Light]:
        """
        :type: typing.List[Light]
        """
    @property
    def materials(self) -> typing.List[IMaterial]:
        """
        :type: typing.List[IMaterial]
        """
    @property
    def renderSettings(self) -> SceneRenderSettings:
        """
        :type: SceneRenderSettings
        """
    @renderSettings.setter
    def renderSettings(self, arg1: SceneRenderSettings) -> None:
        pass
    @property
    def selectedCamera(self) -> Camera:
        """
        :type: Camera
        """
    @selectedCamera.setter
    def selectedCamera(self, arg1: Camera) -> None:
        pass
    @property
    def volumes(self) -> typing.List[GridVolume]:
        """
        :type: typing.List[GridVolume]
        """
    pass
class SceneBuilderFlags():
    """
    Members:

      Default

      DontMergeMaterials

      UseOriginalTangentSpace

      AssumeLinearSpaceTextures

      DontMergeMeshes

      UseSpecGlossMaterials

      UseMetalRoughMaterials

      NonIndexedVertices

      Force32BitIndices

      RTDontMergeStatic

      RTDontMergeDynamic

      RTDontMergeInstanced

      FlattenStaticMeshInstances

      DontOptimizeGraph

      DontOptimizeMaterials

      DontUseDisplacement

      UseCompressedHitInfo

      TessellateCurvesIntoPolyTubes

      UseCache

      RebuildCache
    """
    def __and__(self, arg0: SceneBuilderFlags) -> SceneBuilderFlags: ...
    def __eq__(self, other: object) -> bool: ...
    def __getstate__(self) -> int: ...
    def __hash__(self) -> int: ...
    def __index__(self) -> int: ...
    def __init__(self, value: int) -> None: ...
    def __int__(self) -> int: ...
    def __ne__(self, other: object) -> bool: ...
    def __or__(self, arg0: SceneBuilderFlags) -> SceneBuilderFlags: ...
    def __repr__(self) -> str: ...
    def __setstate__(self, state: int) -> None: ...
    @property
    def name(self) -> str:
        """
        :type: str
        """
    @property
    def value(self) -> int:
        """
        :type: int
        """
    AssumeLinearSpaceTextures: falcor.falcor_ext.SceneBuilderFlags # value = SceneBuilderFlags.AssumeLinearSpaceTextures
    Default: falcor.falcor_ext.SceneBuilderFlags # value = SceneBuilderFlags.Default
    DontMergeMaterials: falcor.falcor_ext.SceneBuilderFlags # value = SceneBuilderFlags.DontMergeMaterials
    DontMergeMeshes: falcor.falcor_ext.SceneBuilderFlags # value = SceneBuilderFlags.DontMergeMeshes
    DontOptimizeGraph: falcor.falcor_ext.SceneBuilderFlags # value = SceneBuilderFlags.DontOptimizeGraph
    DontOptimizeMaterials: falcor.falcor_ext.SceneBuilderFlags # value = SceneBuilderFlags.DontOptimizeMaterials
    DontUseDisplacement: falcor.falcor_ext.SceneBuilderFlags # value = SceneBuilderFlags.DontUseDisplacement
    FlattenStaticMeshInstances: falcor.falcor_ext.SceneBuilderFlags # value = SceneBuilderFlags.FlattenStaticMeshInstances
    Force32BitIndices: falcor.falcor_ext.SceneBuilderFlags # value = SceneBuilderFlags.Force32BitIndices
    NonIndexedVertices: falcor.falcor_ext.SceneBuilderFlags # value = SceneBuilderFlags.NonIndexedVertices
    RTDontMergeDynamic: falcor.falcor_ext.SceneBuilderFlags # value = SceneBuilderFlags.RTDontMergeDynamic
    RTDontMergeInstanced: falcor.falcor_ext.SceneBuilderFlags # value = SceneBuilderFlags.RTDontMergeInstanced
    RTDontMergeStatic: falcor.falcor_ext.SceneBuilderFlags # value = SceneBuilderFlags.RTDontMergeStatic
    RebuildCache: falcor.falcor_ext.SceneBuilderFlags # value = SceneBuilderFlags.RebuildCache
    TessellateCurvesIntoPolyTubes: falcor.falcor_ext.SceneBuilderFlags # value = SceneBuilderFlags.TessellateCurvesIntoPolyTubes
    UseCache: falcor.falcor_ext.SceneBuilderFlags # value = SceneBuilderFlags.UseCache
    UseCompressedHitInfo: falcor.falcor_ext.SceneBuilderFlags # value = SceneBuilderFlags.UseCompressedHitInfo
    UseMetalRoughMaterials: falcor.falcor_ext.SceneBuilderFlags # value = SceneBuilderFlags.UseMetalRoughMaterials
    UseOriginalTangentSpace: falcor.falcor_ext.SceneBuilderFlags # value = SceneBuilderFlags.UseOriginalTangentSpace
    UseSpecGlossMaterials: falcor.falcor_ext.SceneBuilderFlags # value = SceneBuilderFlags.UseSpecGlossMaterials
    __members__: dict # value = {'Default': SceneBuilderFlags.Default, 'DontMergeMaterials': SceneBuilderFlags.DontMergeMaterials, 'UseOriginalTangentSpace': SceneBuilderFlags.UseOriginalTangentSpace, 'AssumeLinearSpaceTextures': SceneBuilderFlags.AssumeLinearSpaceTextures, 'DontMergeMeshes': SceneBuilderFlags.DontMergeMeshes, 'UseSpecGlossMaterials': SceneBuilderFlags.UseSpecGlossMaterials, 'UseMetalRoughMaterials': SceneBuilderFlags.UseMetalRoughMaterials, 'NonIndexedVertices': SceneBuilderFlags.NonIndexedVertices, 'Force32BitIndices': SceneBuilderFlags.Force32BitIndices, 'RTDontMergeStatic': SceneBuilderFlags.RTDontMergeStatic, 'RTDontMergeDynamic': SceneBuilderFlags.RTDontMergeDynamic, 'RTDontMergeInstanced': SceneBuilderFlags.RTDontMergeInstanced, 'FlattenStaticMeshInstances': SceneBuilderFlags.FlattenStaticMeshInstances, 'DontOptimizeGraph': SceneBuilderFlags.DontOptimizeGraph, 'DontOptimizeMaterials': SceneBuilderFlags.DontOptimizeMaterials, 'DontUseDisplacement': SceneBuilderFlags.DontUseDisplacement, 'UseCompressedHitInfo': SceneBuilderFlags.UseCompressedHitInfo, 'TessellateCurvesIntoPolyTubes': SceneBuilderFlags.TessellateCurvesIntoPolyTubes, 'UseCache': SceneBuilderFlags.UseCache, 'RebuildCache': SceneBuilderFlags.RebuildCache}
    pass
class SceneDebugger(RenderPass):
    @property
    def mode(self) -> str:
        """
        :type: str
        """
    @mode.setter
    def mode(self, arg1: str) -> None:
        pass
    pass
class SceneGradients():
    def aggregate_all_grads(self, render_context: RenderContext) -> None: ...
    def aggregate_grads(self, render_context: RenderContext, grad_type: GradientType) -> None: ...
    def clear_all_grads(self, render_context: RenderContext) -> None: ...
    def clear_grads(self, render_context: RenderContext, grad_type: GradientType) -> None: ...
    @staticmethod
    def create(device: Device, grad_config_list: list) -> SceneGradients: ...
    def get_grad_types(self) -> list: ...
    def get_grads_buffer(self, grad_type: GradientType) -> Buffer: ...
    pass
class SceneRenderSettings():
    def __init__(self, useEnvLight: bool = True, useAnalyticLights: bool = True, useEmissiveLights: bool = True, useGridVolumes: bool = True, diffuseAlbedoMultiplier: float = 1.0) -> None: ...
    def __repr__(self) -> str: ...
    @property
    def diffuseAlbedoMultiplier(self) -> float:
        """
        :type: float
        """
    @diffuseAlbedoMultiplier.setter
    def diffuseAlbedoMultiplier(self, arg0: float) -> None:
        pass
    @property
    def useAnalyticLights(self) -> bool:
        """
        :type: bool
        """
    @useAnalyticLights.setter
    def useAnalyticLights(self, arg0: bool) -> None:
        pass
    @property
    def useEmissiveLights(self) -> bool:
        """
        :type: bool
        """
    @useEmissiveLights.setter
    def useEmissiveLights(self, arg0: bool) -> None:
        pass
    @property
    def useEnvLight(self) -> bool:
        """
        :type: bool
        """
    @useEnvLight.setter
    def useEnvLight(self, arg0: bool) -> None:
        pass
    @property
    def useGridVolumes(self) -> bool:
        """
        :type: bool
        """
    @useGridVolumes.setter
    def useGridVolumes(self, arg0: bool) -> None:
        pass
    pass
class SearchPathPriority():
    """
    Members:

      First

      Last
    """
    def __eq__(self, other: object) -> bool: ...
    def __getstate__(self) -> int: ...
    def __hash__(self) -> int: ...
    def __index__(self) -> int: ...
    def __init__(self, value: int) -> None: ...
    def __int__(self) -> int: ...
    def __ne__(self, other: object) -> bool: ...
    def __repr__(self) -> str: ...
    def __setstate__(self, state: int) -> None: ...
    @property
    def name(self) -> str:
        """
        :type: str
        """
    @property
    def value(self) -> int:
        """
        :type: int
        """
    First: falcor.falcor_ext.SearchPathPriority # value = SearchPathPriority.First
    Last: falcor.falcor_ext.SearchPathPriority # value = SearchPathPriority.Last
    __members__: dict # value = {'First': SearchPathPriority.First, 'Last': SearchPathPriority.Last}
    pass
class Settings():
    @typing.overload
    def addFilteredAttributes(self, dict: dict) -> None: ...
    @typing.overload
    def addFilteredAttributes(self, list: list) -> None: ...
    def addOptions(self, dict: dict) -> None: ...
    def clearFilteredAttributes(self) -> None: ...
    def clearOptions(self) -> None: ...
    pass
class ShaderModel():
    """
    Members:

      Unknown

      SM6_0

      SM6_1

      SM6_2

      SM6_3

      SM6_4

      SM6_5

      SM6_6

      SM6_7
    """
    def __and__(self, arg0: ShaderModel) -> ShaderModel: ...
    def __eq__(self, other: object) -> bool: ...
    def __getstate__(self) -> int: ...
    def __hash__(self) -> int: ...
    def __index__(self) -> int: ...
    def __init__(self, value: int) -> None: ...
    def __int__(self) -> int: ...
    def __ne__(self, other: object) -> bool: ...
    def __or__(self, arg0: ShaderModel) -> ShaderModel: ...
    def __repr__(self) -> str: ...
    def __setstate__(self, state: int) -> None: ...
    @property
    def name(self) -> str:
        """
        :type: str
        """
    @property
    def value(self) -> int:
        """
        :type: int
        """
    SM6_0: falcor.falcor_ext.ShaderModel # value = ShaderModel.SM6_0
    SM6_1: falcor.falcor_ext.ShaderModel # value = ShaderModel.SM6_1
    SM6_2: falcor.falcor_ext.ShaderModel # value = ShaderModel.SM6_2
    SM6_3: falcor.falcor_ext.ShaderModel # value = ShaderModel.SM6_3
    SM6_4: falcor.falcor_ext.ShaderModel # value = ShaderModel.SM6_4
    SM6_5: falcor.falcor_ext.ShaderModel # value = ShaderModel.SM6_5
    SM6_6: falcor.falcor_ext.ShaderModel # value = ShaderModel.SM6_6
    SM6_7: falcor.falcor_ext.ShaderModel # value = ShaderModel.SM6_7
    Unknown: falcor.falcor_ext.ShaderModel # value = ShaderModel.Unknown
    __members__: dict # value = {'Unknown': ShaderModel.Unknown, 'SM6_0': ShaderModel.SM6_0, 'SM6_1': ShaderModel.SM6_1, 'SM6_2': ShaderModel.SM6_2, 'SM6_3': ShaderModel.SM6_3, 'SM6_4': ShaderModel.SM6_4, 'SM6_5': ShaderModel.SM6_5, 'SM6_6': ShaderModel.SM6_6, 'SM6_7': ShaderModel.SM6_7}
    pass
class ShaderResourceView():
    pass
class ShaderVar():
    def __getattr__(self, arg0: str) -> ShaderVar: ...
    def __getitem__(self, arg0: str) -> ShaderVar: ...
    @typing.overload
    def __setattr__(self, arg0: str, arg1: Buffer) -> None: ...
    @typing.overload
    def __setattr__(self, arg0: str, arg1: Sampler) -> None: ...
    @typing.overload
    def __setattr__(self, arg0: str, arg1: Texture) -> None: ...
    @typing.overload
    def __setattr__(self, arg0: str, arg1: bool) -> None: ...
    @typing.overload
    def __setattr__(self, arg0: str, arg1: bool2) -> None: ...
    @typing.overload
    def __setattr__(self, arg0: str, arg1: bool3) -> None: ...
    @typing.overload
    def __setattr__(self, arg0: str, arg1: bool4) -> None: ...
    @typing.overload
    def __setattr__(self, arg0: str, arg1: float) -> None: ...
    @typing.overload
    def __setattr__(self, arg0: str, arg1: float2) -> None: ...
    @typing.overload
    def __setattr__(self, arg0: str, arg1: float3) -> None: ...
    @typing.overload
    def __setattr__(self, arg0: str, arg1: float3x4) -> None: ...
    @typing.overload
    def __setattr__(self, arg0: str, arg1: float4) -> None: ...
    @typing.overload
    def __setattr__(self, arg0: str, arg1: float4x4) -> None: ...
    @typing.overload
    def __setattr__(self, arg0: str, arg1: int) -> None: ...
    @typing.overload
    def __setattr__(self, arg0: str, arg1: int2) -> None: ...
    @typing.overload
    def __setattr__(self, arg0: str, arg1: int3) -> None: ...
    @typing.overload
    def __setattr__(self, arg0: str, arg1: int4) -> None: ...
    @typing.overload
    def __setattr__(self, arg0: str, arg1: uint2) -> None: ...
    @typing.overload
    def __setattr__(self, arg0: str, arg1: uint3) -> None: ...
    @typing.overload
    def __setattr__(self, arg0: str, arg1: uint4) -> None: ...
    @typing.overload
    def __setitem__(self, arg0: str, arg1: Buffer) -> None: ...
    @typing.overload
    def __setitem__(self, arg0: str, arg1: Sampler) -> None: ...
    @typing.overload
    def __setitem__(self, arg0: str, arg1: Texture) -> None: ...
    @typing.overload
    def __setitem__(self, arg0: str, arg1: bool) -> None: ...
    @typing.overload
    def __setitem__(self, arg0: str, arg1: bool2) -> None: ...
    @typing.overload
    def __setitem__(self, arg0: str, arg1: bool3) -> None: ...
    @typing.overload
    def __setitem__(self, arg0: str, arg1: bool4) -> None: ...
    @typing.overload
    def __setitem__(self, arg0: str, arg1: float) -> None: ...
    @typing.overload
    def __setitem__(self, arg0: str, arg1: float2) -> None: ...
    @typing.overload
    def __setitem__(self, arg0: str, arg1: float3) -> None: ...
    @typing.overload
    def __setitem__(self, arg0: str, arg1: float3x4) -> None: ...
    @typing.overload
    def __setitem__(self, arg0: str, arg1: float4) -> None: ...
    @typing.overload
    def __setitem__(self, arg0: str, arg1: float4x4) -> None: ...
    @typing.overload
    def __setitem__(self, arg0: str, arg1: int) -> None: ...
    @typing.overload
    def __setitem__(self, arg0: str, arg1: int2) -> None: ...
    @typing.overload
    def __setitem__(self, arg0: str, arg1: int3) -> None: ...
    @typing.overload
    def __setitem__(self, arg0: str, arg1: int4) -> None: ...
    @typing.overload
    def __setitem__(self, arg0: str, arg1: uint2) -> None: ...
    @typing.overload
    def __setitem__(self, arg0: str, arg1: uint3) -> None: ...
    @typing.overload
    def __setitem__(self, arg0: str, arg1: uint4) -> None: ...
    pass
class ShadingModel():
    """
    Members:

      MetalRough

      SpecGloss
    """
    def __eq__(self, other: object) -> bool: ...
    def __getstate__(self) -> int: ...
    def __hash__(self) -> int: ...
    def __index__(self) -> int: ...
    def __init__(self, value: int) -> None: ...
    def __int__(self) -> int: ...
    def __ne__(self, other: object) -> bool: ...
    def __repr__(self) -> str: ...
    def __setstate__(self, state: int) -> None: ...
    @property
    def name(self) -> str:
        """
        :type: str
        """
    @property
    def value(self) -> int:
        """
        :type: int
        """
    MetalRough: falcor.falcor_ext.ShadingModel # value = ShadingModel.MetalRough
    SpecGloss: falcor.falcor_ext.ShadingModel # value = ShadingModel.SpecGloss
    __members__: dict # value = {'MetalRough': ShadingModel.MetalRough, 'SpecGloss': ShadingModel.SpecGloss}
    pass
class ShadingPass(RenderPass):
    @property
    def camera(self) -> Camera:
        """
        :type: Camera
        """
    @camera.setter
    def camera(self, arg1: Camera) -> None:
        pass
    @property
    def method(self) -> int:
        """
        :type: int
        """
    @property
    def mode(self) -> int:
        """
        :type: int
        """
    @property
    def result(self) -> Buffer:
        """
        :type: Buffer
        """
    @result.setter
    def result(self, arg1: Buffer) -> None:
        pass
    @property
    def saveFrames(self) -> int:
        """
        :type: int
        """
    @property
    def saveResult(self) -> bool:
        """
        :type: bool
        """
    @saveResult.setter
    def saveResult(self, arg1: bool) -> None:
        pass
    @property
    def waterSurfaceND(self) -> Buffer:
        """
        :type: Buffer
        """
    @waterSurfaceND.setter
    def waterSurfaceND(self, arg1: Buffer) -> None:
        pass
    @property
    def waterTrColor(self) -> float3:
        """
        :type: float3
        """
    @property
    def waterTrStrenth(self) -> float:
        """
        :type: float
        """
    pass
class SimplePostFX(RenderPass):
    @property
    def barrelDistortAmount(self) -> float:
        """
        :type: float
        """
    @barrelDistortAmount.setter
    def barrelDistortAmount(self, arg1: float) -> None:
        pass
    @property
    def bloomAmount(self) -> float:
        """
        :type: float
        """
    @bloomAmount.setter
    def bloomAmount(self, arg1: float) -> None:
        pass
    @property
    def chromaticAberrationAmount(self) -> float:
        """
        :type: float
        """
    @chromaticAberrationAmount.setter
    def chromaticAberrationAmount(self, arg1: float) -> None:
        pass
    @property
    def colorOffset(self) -> float3:
        """
        :type: float3
        """
    @colorOffset.setter
    def colorOffset(self, arg1: float3) -> None:
        pass
    @property
    def colorOffsetScalar(self) -> float:
        """
        :type: float
        """
    @colorOffsetScalar.setter
    def colorOffsetScalar(self, arg1: float) -> None:
        pass
    @property
    def colorPower(self) -> float3:
        """
        :type: float3
        """
    @colorPower.setter
    def colorPower(self, arg1: float3) -> None:
        pass
    @property
    def colorPowerScalar(self) -> float:
        """
        :type: float
        """
    @colorPowerScalar.setter
    def colorPowerScalar(self, arg1: float) -> None:
        pass
    @property
    def colorScale(self) -> float3:
        """
        :type: float3
        """
    @colorScale.setter
    def colorScale(self, arg1: float3) -> None:
        pass
    @property
    def colorScaleScalar(self) -> float:
        """
        :type: float
        """
    @colorScaleScalar.setter
    def colorScaleScalar(self, arg1: float) -> None:
        pass
    @property
    def enabled(self) -> bool:
        """
        :type: bool
        """
    @enabled.setter
    def enabled(self, arg1: bool) -> None:
        pass
    @property
    def saturationCurve(self) -> float3:
        """
        :type: float3
        """
    @saturationCurve.setter
    def saturationCurve(self, arg1: float3) -> None:
        pass
    @property
    def starAmount(self) -> float:
        """
        :type: float
        """
    @starAmount.setter
    def starAmount(self, arg1: float) -> None:
        pass
    @property
    def starAngle(self) -> float:
        """
        :type: float
        """
    @starAngle.setter
    def starAngle(self, arg1: float) -> None:
        pass
    @property
    def vignetteAmount(self) -> float:
        """
        :type: float
        """
    @vignetteAmount.setter
    def vignetteAmount(self, arg1: float) -> None:
        pass
    @property
    def wipe(self) -> float:
        """
        :type: float
        """
    @wipe.setter
    def wipe(self, arg1: float) -> None:
        pass
    pass
class SlangCompilerFlags():
    """
    Members:

      None_

      TreatWarningsAsErrors

      DumpIntermediates

      FloatingPointModeFast

      FloatingPointModePrecise

      GenerateDebugInfo

      MatrixLayoutColumnMajor
    """
    def __and__(self, arg0: SlangCompilerFlags) -> SlangCompilerFlags: ...
    def __eq__(self, other: object) -> bool: ...
    def __getstate__(self) -> int: ...
    def __hash__(self) -> int: ...
    def __index__(self) -> int: ...
    def __init__(self, value: int) -> None: ...
    def __int__(self) -> int: ...
    def __ne__(self, other: object) -> bool: ...
    def __or__(self, arg0: SlangCompilerFlags) -> SlangCompilerFlags: ...
    def __repr__(self) -> str: ...
    def __setstate__(self, state: int) -> None: ...
    @property
    def name(self) -> str:
        """
        :type: str
        """
    @property
    def value(self) -> int:
        """
        :type: int
        """
    DumpIntermediates: falcor.falcor_ext.SlangCompilerFlags # value = SlangCompilerFlags.DumpIntermediates
    FloatingPointModeFast: falcor.falcor_ext.SlangCompilerFlags # value = SlangCompilerFlags.FloatingPointModeFast
    FloatingPointModePrecise: falcor.falcor_ext.SlangCompilerFlags # value = SlangCompilerFlags.FloatingPointModePrecise
    GenerateDebugInfo: falcor.falcor_ext.SlangCompilerFlags # value = SlangCompilerFlags.GenerateDebugInfo
    MatrixLayoutColumnMajor: falcor.falcor_ext.SlangCompilerFlags # value = SlangCompilerFlags.MatrixLayoutColumnMajor
    None_: falcor.falcor_ext.SlangCompilerFlags # value = SlangCompilerFlags.None_
    TreatWarningsAsErrors: falcor.falcor_ext.SlangCompilerFlags # value = SlangCompilerFlags.TreatWarningsAsErrors
    __members__: dict # value = {'None_': SlangCompilerFlags.None_, 'TreatWarningsAsErrors': SlangCompilerFlags.TreatWarningsAsErrors, 'DumpIntermediates': SlangCompilerFlags.DumpIntermediates, 'FloatingPointModeFast': SlangCompilerFlags.FloatingPointModeFast, 'FloatingPointModePrecise': SlangCompilerFlags.FloatingPointModePrecise, 'GenerateDebugInfo': SlangCompilerFlags.GenerateDebugInfo, 'MatrixLayoutColumnMajor': SlangCompilerFlags.MatrixLayoutColumnMajor}
    pass
class SphereLight(AnalyticAreaLight, Light, Animatable):
    def __init__(self, name: str = '') -> None: ...
    pass
class StandardMaterial(BasicMaterial, IMaterial):
    def __init__(self, name: str = '', model: ShadingModel = ShadingModel.MetalRough) -> None: ...
    @property
    def emissiveColor(self) -> float3:
        """
        :type: float3
        """
    @emissiveColor.setter
    def emissiveColor(self, arg1: float3) -> None:
        pass
    @property
    def emissiveFactor(self) -> float:
        """
        :type: float
        """
    @emissiveFactor.setter
    def emissiveFactor(self, arg1: float) -> None:
        pass
    @property
    def entryPointVolumeProperties(self) -> bool:
        """
        :type: bool
        """
    @entryPointVolumeProperties.setter
    def entryPointVolumeProperties(self, arg1: bool) -> None:
        pass
    @property
    def metallic(self) -> float:
        """
        :type: float
        """
    @metallic.setter
    def metallic(self, arg1: float) -> None:
        pass
    @property
    def roughness(self) -> float:
        """
        :type: float
        """
    @roughness.setter
    def roughness(self, arg1: float) -> None:
        pass
    @property
    def shadingModel(self) -> ShadingModel:
        """
        :type: ShadingModel
        """
    pass
class SwapPass(RenderPass):
    @property
    def gsCullNum(self) -> int:
        """
        :type: int
        """
    @gsCullNum.setter
    def gsCullNum(self, arg1: int) -> None:
        pass
    @property
    def gsNum(self) -> int:
        """
        :type: int
        """
    @gsNum.setter
    def gsNum(self, arg1: int) -> None:
        pass
    @property
    def normalDepthBuffer(self) -> Buffer:
        """
        :type: Buffer
        """
    @normalDepthBuffer.setter
    def normalDepthBuffer(self, arg1: Buffer) -> None:
        pass
    @property
    def stop(self) -> bool:
        """
        :type: bool
        """
    @property
    def stopAt(self) -> int:
        """
        :type: int
        """
    pass
class TAA(RenderPass):
    @property
    def alpha(self) -> float:
        """
        :type: float
        """
    @alpha.setter
    def alpha(self, arg1: float) -> None:
        pass
    @property
    def antiFlicker(self) -> bool:
        """
        :type: bool
        """
    @antiFlicker.setter
    def antiFlicker(self, arg1: bool) -> None:
        pass
    @property
    def sigma(self) -> float:
        """
        :type: float
        """
    @sigma.setter
    def sigma(self, arg1: float) -> None:
        pass
    pass
class TestPyTorchPass(RenderPass):
    def generateData(self, arg0: uint3, arg1: int) -> torch.Tensor: ...
    def verifyData(self, arg0: uint3, arg1: int, arg2: torch.Tensor) -> bool: ...
    pass
class TestRtProgram(RenderPass):
    def addCustomPrimitive(self) -> None: ...
    def moveCustomPrimitive(self) -> None: ...
    def removeCustomPrimitive(self, arg0: int) -> None: ...
    pass
class Testbed():
    def __init__(self, width: int = 1920, height: int = 1080, create_window: bool = False, device_type: DeviceType = DeviceType.Default, gpu: int = 0, enable_debug_layers: bool = False, enable_aftermath: bool = False, title: str = 'Falcor Sample', show_fps: bool = True, device: Device = None) -> None: ...
    def capture_output(self, path: os.PathLike, output_index: int = 0) -> None: ...
    def create_render_graph(self, name: str = '') -> RenderGraph: ...
    def frame(self) -> None: ...
    def get_import_dicts(self) -> typing.List[dict]: ...
    def get_import_paths(self) -> typing.List[str]: ...
    def load_render_graph(self, path: os.PathLike) -> RenderGraph: ...
    def load_scene(self, path: os.PathLike, build_flags: SceneBuilderFlags = SceneBuilderFlags.Default) -> None: ...
    def load_scene_from_string(self, scene: str, extension: str = 'pyscene', build_flags: SceneBuilderFlags = SceneBuilderFlags.Default) -> None: ...
    def resize_frame_buffer(self, width: int, height: int) -> None: ...
    def run(self) -> None: ...
    @property
    def clock(self) -> Clock:
        """
        :type: Clock
        """
    @property
    def device(self) -> Device:
        """
        :type: Device
        """
    @property
    def keyboard_event_callback(self) -> typing.Callable[[KeyboardEvent], bool]:
        """
        :type: typing.Callable[[KeyboardEvent], bool]
        """
    @keyboard_event_callback.setter
    def keyboard_event_callback(self, arg1: typing.Callable[[KeyboardEvent], bool]) -> None:
        pass
    @property
    def mouse_event_callback(self) -> typing.Callable[[MouseEvent], bool]:
        """
        :type: typing.Callable[[MouseEvent], bool]
        """
    @mouse_event_callback.setter
    def mouse_event_callback(self, arg1: typing.Callable[[MouseEvent], bool]) -> None:
        pass
    @property
    def profiler(self) -> Profiler:
        """
        :type: Profiler
        """
    @property
    def render_graph(self) -> RenderGraph:
        """
        :type: RenderGraph
        """
    @render_graph.setter
    def render_graph(self, arg1: RenderGraph) -> None:
        pass
    @property
    def render_texture(self) -> Texture:
        """
        :type: Texture
        """
    @render_texture.setter
    def render_texture(self, arg1: Texture) -> None:
        pass
    @property
    def scene(self) -> Scene:
        """
        :type: Scene
        """
    @property
    def screen(self) -> ui.Screen:
        """
        :type: ui.Screen
        """
    @property
    def should_close(self) -> bool:
        """
        :type: bool
        """
    @property
    def show_ui(self) -> bool:
        """
        :type: bool
        """
    @show_ui.setter
    def show_ui(self, arg1: bool) -> None:
        pass
    @property
    def window(self) -> Falcor::Window:
        """
        :type: Falcor::Window
        """
    @property
    def window_size_change_callback(self) -> typing.Callable[[int, int], None]:
        """
        :type: typing.Callable[[int, int], None]
        """
    @window_size_change_callback.setter
    def window_size_change_callback(self, arg1: typing.Callable[[int, int], None]) -> None:
        pass
    pass
class Texture(Resource):
    def from_numpy(self, data: numpy.ndarray, mip_level: int = 0, array_slice: int = 0) -> None: ...
    def to_numpy(self, mip_level: int = 0, array_slice: int = 0) -> numpy.ndarray: ...
    @property
    def array_size(self) -> int:
        """
        :type: int
        """
    @property
    def depth(self) -> int:
        """
        :type: int
        """
    @property
    def format(self) -> ResourceFormat:
        """
        :type: ResourceFormat
        """
    @property
    def height(self) -> int:
        """
        :type: int
        """
    @property
    def mip_count(self) -> int:
        """
        :type: int
        """
    @property
    def sample_count(self) -> int:
        """
        :type: int
        """
    @property
    def width(self) -> int:
        """
        :type: int
        """
    pass
class TextureAddressingMode():
    """
    Members:

      Wrap

      Mirror

      Clamp

      Border

      MirrorOnce
    """
    def __eq__(self, other: object) -> bool: ...
    def __getstate__(self) -> int: ...
    def __hash__(self) -> int: ...
    def __index__(self) -> int: ...
    def __init__(self, value: int) -> None: ...
    def __int__(self) -> int: ...
    def __ne__(self, other: object) -> bool: ...
    def __repr__(self) -> str: ...
    def __setstate__(self, state: int) -> None: ...
    @property
    def name(self) -> str:
        """
        :type: str
        """
    @property
    def value(self) -> int:
        """
        :type: int
        """
    Border: falcor.falcor_ext.TextureAddressingMode # value = TextureAddressingMode.Border
    Clamp: falcor.falcor_ext.TextureAddressingMode # value = TextureAddressingMode.Clamp
    Mirror: falcor.falcor_ext.TextureAddressingMode # value = TextureAddressingMode.Mirror
    MirrorOnce: falcor.falcor_ext.TextureAddressingMode # value = TextureAddressingMode.MirrorOnce
    Wrap: falcor.falcor_ext.TextureAddressingMode # value = TextureAddressingMode.Wrap
    __members__: dict # value = {'Wrap': TextureAddressingMode.Wrap, 'Mirror': TextureAddressingMode.Mirror, 'Clamp': TextureAddressingMode.Clamp, 'Border': TextureAddressingMode.Border, 'MirrorOnce': TextureAddressingMode.MirrorOnce}
    pass
class TextureChannelFlags():
    """
    Members:

      None_

      Red

      Green

      Blue

      Alpha

      RGB

      RGBA
    """
    def __eq__(self, other: object) -> bool: ...
    def __getstate__(self) -> int: ...
    def __hash__(self) -> int: ...
    def __index__(self) -> int: ...
    def __init__(self, value: int) -> None: ...
    def __int__(self) -> int: ...
    def __ne__(self, other: object) -> bool: ...
    def __repr__(self) -> str: ...
    def __setstate__(self, state: int) -> None: ...
    @property
    def name(self) -> str:
        """
        :type: str
        """
    @property
    def value(self) -> int:
        """
        :type: int
        """
    Alpha: falcor.falcor_ext.TextureChannelFlags # value = TextureChannelFlags.Alpha
    Blue: falcor.falcor_ext.TextureChannelFlags # value = TextureChannelFlags.Blue
    Green: falcor.falcor_ext.TextureChannelFlags # value = TextureChannelFlags.Green
    None_: falcor.falcor_ext.TextureChannelFlags # value = TextureChannelFlags.None_
    RGB: falcor.falcor_ext.TextureChannelFlags # value = TextureChannelFlags.RGB
    RGBA: falcor.falcor_ext.TextureChannelFlags # value = TextureChannelFlags.RGBA
    Red: falcor.falcor_ext.TextureChannelFlags # value = TextureChannelFlags.Red
    __members__: dict # value = {'None_': TextureChannelFlags.None_, 'Red': TextureChannelFlags.Red, 'Green': TextureChannelFlags.Green, 'Blue': TextureChannelFlags.Blue, 'Alpha': TextureChannelFlags.Alpha, 'RGB': TextureChannelFlags.RGB, 'RGBA': TextureChannelFlags.RGBA}
    pass
class TextureFilteringMode():
    """
    Members:

      Point

      Linear
    """
    def __eq__(self, other: object) -> bool: ...
    def __getstate__(self) -> int: ...
    def __hash__(self) -> int: ...
    def __index__(self) -> int: ...
    def __init__(self, value: int) -> None: ...
    def __int__(self) -> int: ...
    def __ne__(self, other: object) -> bool: ...
    def __repr__(self) -> str: ...
    def __setstate__(self, state: int) -> None: ...
    @property
    def name(self) -> str:
        """
        :type: str
        """
    @property
    def value(self) -> int:
        """
        :type: int
        """
    Linear: falcor.falcor_ext.TextureFilteringMode # value = TextureFilteringMode.Linear
    Point: falcor.falcor_ext.TextureFilteringMode # value = TextureFilteringMode.Point
    __members__: dict # value = {'Point': TextureFilteringMode.Point, 'Linear': TextureFilteringMode.Linear}
    pass
class TextureReductionMode():
    """
    Members:

      Standard

      Comparison

      Min

      Max
    """
    def __eq__(self, other: object) -> bool: ...
    def __getstate__(self) -> int: ...
    def __hash__(self) -> int: ...
    def __index__(self) -> int: ...
    def __init__(self, value: int) -> None: ...
    def __int__(self) -> int: ...
    def __ne__(self, other: object) -> bool: ...
    def __repr__(self) -> str: ...
    def __setstate__(self, state: int) -> None: ...
    @property
    def name(self) -> str:
        """
        :type: str
        """
    @property
    def value(self) -> int:
        """
        :type: int
        """
    Comparison: falcor.falcor_ext.TextureReductionMode # value = TextureReductionMode.Comparison
    Max: falcor.falcor_ext.TextureReductionMode # value = TextureReductionMode.Max
    Min: falcor.falcor_ext.TextureReductionMode # value = TextureReductionMode.Min
    Standard: falcor.falcor_ext.TextureReductionMode # value = TextureReductionMode.Standard
    __members__: dict # value = {'Standard': TextureReductionMode.Standard, 'Comparison': TextureReductionMode.Comparison, 'Min': TextureReductionMode.Min, 'Max': TextureReductionMode.Max}
    pass
class ThicknessPass(RenderPass):
    @property
    def camera(self) -> Camera:
        """
        :type: Camera
        """
    @camera.setter
    def camera(self, arg1: Camera) -> None:
        pass
    @property
    def fluidParticle(self) -> Buffer:
        """
        :type: Buffer
        """
    @fluidParticle.setter
    def fluidParticle(self, arg1: Buffer) -> None:
        pass
    @property
    def fluidParticleNum(self) -> int:
        """
        :type: int
        """
    @fluidParticleNum.setter
    def fluidParticleNum(self, arg1: int) -> None:
        pass
    @property
    def fluidParticleRadius(self) -> float:
        """
        :type: float
        """
    @fluidParticleRadius.setter
    def fluidParticleRadius(self, arg1: float) -> None:
        pass
    pass
class ToneMapper(RenderPass):
    @property
    def autoExposure(self) -> bool:
        """
        :type: bool
        """
    @autoExposure.setter
    def autoExposure(self, arg1: bool) -> None:
        pass
    @property
    def clamp(self) -> bool:
        """
        :type: bool
        """
    @clamp.setter
    def clamp(self, arg1: bool) -> None:
        pass
    @property
    def exposureCompensation(self) -> float:
        """
        :type: float
        """
    @exposureCompensation.setter
    def exposureCompensation(self, arg1: float) -> None:
        pass
    @property
    def exposureMode(self) -> str:
        """
        :type: str
        """
    @exposureMode.setter
    def exposureMode(self, arg1: str) -> None:
        pass
    @property
    def exposureValue(self) -> float:
        """
        :type: float
        """
    @exposureValue.setter
    def exposureValue(self, arg1: float) -> None:
        pass
    @property
    def fNumber(self) -> float:
        """
        :type: float
        """
    @fNumber.setter
    def fNumber(self, arg1: float) -> None:
        pass
    @property
    def filmSpeed(self) -> float:
        """
        :type: float
        """
    @filmSpeed.setter
    def filmSpeed(self, arg1: float) -> None:
        pass
    @property
    def operator(self) -> str:
        """
        :type: str
        """
    @operator.setter
    def operator(self, arg1: str) -> None:
        pass
    @property
    def shutter(self) -> float:
        """
        :type: float
        """
    @shutter.setter
    def shutter(self, arg1: float) -> None:
        pass
    @property
    def whiteBalance(self) -> bool:
        """
        :type: bool
        """
    @whiteBalance.setter
    def whiteBalance(self, arg1: bool) -> None:
        pass
    @property
    def whiteMaxLuminance(self) -> float:
        """
        :type: float
        """
    @whiteMaxLuminance.setter
    def whiteMaxLuminance(self, arg1: float) -> None:
        pass
    @property
    def whitePoint(self) -> float:
        """
        :type: float
        """
    @whitePoint.setter
    def whitePoint(self, arg1: float) -> None:
        pass
    @property
    def whiteScale(self) -> float:
        """
        :type: float
        """
    @whiteScale.setter
    def whiteScale(self, arg1: float) -> None:
        pass
    pass
class TrainGTBuffer(RenderPass):
    @property
    def allFoamBuffer(self) -> Buffer:
        """
        :type: Buffer
        """
    @allFoamBuffer.setter
    def allFoamBuffer(self, arg1: Buffer) -> None:
        pass
    @property
    def allFoamNum(self) -> int:
        """
        :type: int
        """
    @allFoamNum.setter
    def allFoamNum(self, arg1: int) -> None:
        pass
    @property
    def gtBuffer(self) -> Buffer:
        """
        :type: Buffer
        """
    @gtBuffer.setter
    def gtBuffer(self, arg1: Buffer) -> None:
        pass
    @property
    def meshPath(self) -> str:
        """
        :type: str
        """
    @meshPath.setter
    def meshPath(self, arg1: str) -> None:
        pass
    @property
    def newFoamBuffer(self) -> Buffer:
        """
        :type: Buffer
        """
    @newFoamBuffer.setter
    def newFoamBuffer(self, arg1: Buffer) -> None:
        pass
    @property
    def newFoamNum(self) -> int:
        """
        :type: int
        """
    @newFoamNum.setter
    def newFoamNum(self, arg1: int) -> None:
        pass
    @property
    def nextAllFoamBuffer(self) -> Buffer:
        """
        :type: Buffer
        """
    @nextAllFoamBuffer.setter
    def nextAllFoamBuffer(self, arg1: Buffer) -> None:
        pass
    @property
    def nextAllFoamNum(self) -> int:
        """
        :type: int
        """
    @nextAllFoamNum.setter
    def nextAllFoamNum(self, arg1: int) -> None:
        pass
    @property
    def nextGtMeshPath(self) -> str:
        """
        :type: str
        """
    @nextGtMeshPath.setter
    def nextGtMeshPath(self, arg1: str) -> None:
        pass
    @property
    def nextXYZBuffer(self) -> Buffer:
        """
        :type: Buffer
        """
    @nextXYZBuffer.setter
    def nextXYZBuffer(self, arg1: Buffer) -> None:
        pass
    @property
    def surfaceAllFoamBuffer(self) -> Buffer:
        """
        :type: Buffer
        """
    @surfaceAllFoamBuffer.setter
    def surfaceAllFoamBuffer(self, arg1: Buffer) -> None:
        pass
    @property
    def surfaceAllFoamNum(self) -> int:
        """
        :type: int
        """
    @surfaceAllFoamNum.setter
    def surfaceAllFoamNum(self, arg1: int) -> None:
        pass
    @property
    def surfaceNewFoamBuffer(self) -> Buffer:
        """
        :type: Buffer
        """
    @surfaceNewFoamBuffer.setter
    def surfaceNewFoamBuffer(self, arg1: Buffer) -> None:
        pass
    @property
    def surfaceNewFoamNum(self) -> int:
        """
        :type: int
        """
    @surfaceNewFoamNum.setter
    def surfaceNewFoamNum(self, arg1: int) -> None:
        pass
    @property
    def surfaceNextAllFoamBuffer(self) -> Buffer:
        """
        :type: Buffer
        """
    @surfaceNextAllFoamBuffer.setter
    def surfaceNextAllFoamBuffer(self, arg1: Buffer) -> None:
        pass
    @property
    def surfaceNextAllFoamNum(self) -> int:
        """
        :type: int
        """
    @surfaceNextAllFoamNum.setter
    def surfaceNextAllFoamNum(self, arg1: int) -> None:
        pass
    pass
class Transform():
    def __init__(self, **kwargs) -> None: ...
    def __repr__(self) -> str: ...
    def lookAt(self, position: float3, target: float3, up: float3) -> None: ...
    @property
    def matrix(self) -> float4x4:
        """
        :type: float4x4
        """
    @property
    def order(self) -> CompositionOrder:
        """
        :type: CompositionOrder
        """
    @order.setter
    def order(self, arg1: CompositionOrder) -> None:
        pass
    @property
    def rotationEuler(self) -> float3:
        """
        :type: float3
        """
    @rotationEuler.setter
    def rotationEuler(self, arg1: float3) -> None:
        pass
    @property
    def rotationEulerDeg(self) -> float3:
        """
        :type: float3
        """
    @rotationEulerDeg.setter
    def rotationEulerDeg(self, arg1: float3) -> None:
        pass
    @property
    def scaling(self) -> float3:
        """
        :type: float3
        """
    @scaling.setter
    def scaling(self, arg1: float3) -> None:
        pass
    @property
    def translation(self) -> float3:
        """
        :type: float3
        """
    @translation.setter
    def translation(self, arg1: float3) -> None:
        pass
    pass
class TriangleMesh():
    class Vertex():
        @property
        def normal(self) -> float3:
            """
            :type: float3
            """
        @normal.setter
        def normal(self, arg0: float3) -> None:
            pass
        @property
        def position(self) -> float3:
            """
            :type: float3
            """
        @position.setter
        def position(self, arg0: float3) -> None:
            pass
        @property
        def texCoord(self) -> float2:
            """
            :type: float2
            """
        @texCoord.setter
        def texCoord(self, arg0: float2) -> None:
            pass
        pass
    def __init__(self) -> None: ...
    def addTriangle(self, i0: int, i1: int, i2: int) -> None: ...
    def addVertex(self, position: float3, normal: float3, texCoord: float2) -> int: ...
    @staticmethod
    def createCube(size: float3 = float3(1.000000, 1.000000, 1.000000)) -> TriangleMesh: ...
    @staticmethod
    def createDisk(radius: float = 1.0, segments: int = 32) -> TriangleMesh: ...
    @staticmethod
    @typing.overload
    def createFromFile(path: os.PathLike, importFlags: TriangleMeshImportFlags) -> TriangleMesh: ...
    @staticmethod
    @typing.overload
    def createFromFile(path: os.PathLike, smoothNormals: bool = False) -> TriangleMesh: ...
    @staticmethod
    def createQuad(size: float2 = float2(1.000000, 1.000000)) -> TriangleMesh: ...
    @staticmethod
    def createSphere(radius: float = 1.0, segmentsU: int = 32, segmentsV: int = 32) -> TriangleMesh: ...
    @property
    def frontFaceCW(self) -> bool:
        """
        :type: bool
        """
    @frontFaceCW.setter
    def frontFaceCW(self, arg1: bool) -> None:
        pass
    @property
    def indices(self) -> typing.List[int]:
        """
        :type: typing.List[int]
        """
    @property
    def name(self) -> str:
        """
        :type: str
        """
    @name.setter
    def name(self, arg1: str) -> None:
        pass
    @property
    def vertices(self) -> typing.List[TriangleMesh.Vertex]:
        """
        :type: typing.List[TriangleMesh.Vertex]
        """
    pass
class TriangleMeshImportFlags():
    """
    Members:

      Default

      GenSmoothNormals

      JoinIdenticalVertices
    """
    def __and__(self, arg0: TriangleMeshImportFlags) -> TriangleMeshImportFlags: ...
    def __eq__(self, other: object) -> bool: ...
    def __getstate__(self) -> int: ...
    def __hash__(self) -> int: ...
    def __index__(self) -> int: ...
    def __init__(self, value: int) -> None: ...
    def __int__(self) -> int: ...
    def __ne__(self, other: object) -> bool: ...
    def __or__(self, arg0: TriangleMeshImportFlags) -> TriangleMeshImportFlags: ...
    def __repr__(self) -> str: ...
    def __setstate__(self, state: int) -> None: ...
    @property
    def name(self) -> str:
        """
        :type: str
        """
    @property
    def value(self) -> int:
        """
        :type: int
        """
    Default: falcor.falcor_ext.TriangleMeshImportFlags # value = TriangleMeshImportFlags.Default
    GenSmoothNormals: falcor.falcor_ext.TriangleMeshImportFlags # value = TriangleMeshImportFlags.GenSmoothNormals
    JoinIdenticalVertices: falcor.falcor_ext.TriangleMeshImportFlags # value = TriangleMeshImportFlags.JoinIdenticalVertices
    __members__: dict # value = {'Default': TriangleMeshImportFlags.Default, 'GenSmoothNormals': TriangleMeshImportFlags.GenSmoothNormals, 'JoinIdenticalVertices': TriangleMeshImportFlags.JoinIdenticalVertices}
    pass
class UnorderedAccessView():
    pass
class Vao():
    pass
class VertexLayout():
    pass
class WARDiffPathTracer(RenderPass):
    def set_mesh_to_optimize(self, arg0: int) -> None: ...
    @property
    def dL_dI(self) -> Buffer:
        """
        :type: Buffer
        """
    @dL_dI.setter
    def dL_dI(self, arg1: Buffer) -> None:
        pass
    @property
    def run_backward(self) -> int:
        """
        :type: int
        """
    @run_backward.setter
    def run_backward(self, arg1: int) -> None:
        pass
    @property
    def scene_gradients(self) -> SceneGradients:
        """
        :type: SceneGradients
        """
    @scene_gradients.setter
    def scene_gradients(self, arg1: SceneGradients) -> None:
        pass
    pass
class WaterFoamShading(RenderPass):
    @property
    def normalDepthBuffer(self) -> Buffer:
        """
        :type: Buffer
        """
    @normalDepthBuffer.setter
    def normalDepthBuffer(self, arg1: Buffer) -> None:
        pass
    @property
    def thicknessBuffer(self) -> Buffer:
        """
        :type: Buffer
        """
    @thicknessBuffer.setter
    def thicknessBuffer(self, arg1: Buffer) -> None:
        pass
    pass
class WaterParticleProcess(RenderPass):
    @property
    def T0(self) -> float:
        """
        :type: float
        """
    @T0.setter
    def T0(self, arg1: float) -> None:
        pass
    @property
    def T1(self) -> float:
        """
        :type: float
        """
    @T1.setter
    def T1(self, arg1: float) -> None:
        pass
    @property
    def T2(self) -> float:
        """
        :type: float
        """
    @T2.setter
    def T2(self, arg1: float) -> None:
        pass
    @property
    def countBuffer(self) -> Buffer:
        """
        :type: Buffer
        """
    @countBuffer.setter
    def countBuffer(self, arg1: Buffer) -> None:
        pass
    @property
    def currentParticleNum(self) -> int:
        """
        :type: int
        """
    @currentParticleNum.setter
    def currentParticleNum(self, arg1: int) -> None:
        pass
    @property
    def edgeNum(self) -> int:
        """
        :type: int
        """
    @edgeNum.setter
    def edgeNum(self, arg1: int) -> None:
        pass
    @property
    def epoch(self) -> int:
        """
        :type: int
        """
    @epoch.setter
    def epoch(self, arg1: int) -> None:
        pass
    @property
    def fluidRadius(self) -> float:
        """
        :type: float
        """
    @fluidRadius.setter
    def fluidRadius(self, arg1: float) -> None:
        pass
    @property
    def focuseFoam(self) -> bool:
        """
        :type: bool
        """
    @focuseFoam.setter
    def focuseFoam(self, arg1: bool) -> None:
        pass
    @property
    def graphDstId(self) -> Buffer:
        """
        :type: Buffer
        """
    @graphDstId.setter
    def graphDstId(self, arg1: Buffer) -> None:
        pass
    @property
    def graphSrcId(self) -> Buffer:
        """
        :type: Buffer
        """
    @graphSrcId.setter
    def graphSrcId(self, arg1: Buffer) -> None:
        pass
    @property
    def isFoamView(self) -> bool:
        """
        :type: bool
        """
    @property
    def kernelRadius(self) -> float:
        """
        :type: float
        """
    @kernelRadius.setter
    def kernelRadius(self, arg1: float) -> None:
        pass
    @property
    def maxGridPos(self) -> float3:
        """
        :type: float3
        """
    @maxGridPos.setter
    def maxGridPos(self, arg1: float3) -> None:
        pass
    @property
    def maxNeighborNum(self) -> int:
        """
        :type: int
        """
    @maxNeighborNum.setter
    def maxNeighborNum(self, arg1: int) -> None:
        pass
    @property
    def minGridPos(self) -> float3:
        """
        :type: float3
        """
    @minGridPos.setter
    def minGridPos(self, arg1: float3) -> None:
        pass
    @property
    def randomView(self) -> bool:
        """
        :type: bool
        """
    @randomView.setter
    def randomView(self, arg1: bool) -> None:
        pass
    @property
    def sceneDebug(self) -> bool:
        """
        :type: bool
        """
    @sceneDebug.setter
    def sceneDebug(self, arg1: bool) -> None:
        pass
    @property
    def stop(self) -> bool:
        """
        :type: bool
        """
    @property
    def stopAt(self) -> int:
        """
        :type: int
        """
    @stopAt.setter
    def stopAt(self, arg1: int) -> None:
        pass
    @property
    def surfaceParticels(self) -> Buffer:
        """
        :type: Buffer
        """
    @surfaceParticels.setter
    def surfaceParticels(self, arg1: Buffer) -> None:
        pass
    @property
    def surfaceParticleNum(self) -> int:
        """
        :type: int
        """
    @surfaceParticleNum.setter
    def surfaceParticleNum(self, arg1: int) -> None:
        pass
    @property
    def surfaceVel(self) -> Buffer:
        """
        :type: Buffer
        """
    @surfaceVel.setter
    def surfaceVel(self, arg1: Buffer) -> None:
        pass
    @property
    def thicknessTex(self) -> Buffer:
        """
        :type: Buffer
        """
    @thicknessTex.setter
    def thicknessTex(self, arg1: Buffer) -> None:
        pass
    @property
    def waterParticles(self) -> Buffer:
        """
        :type: Buffer
        """
    @waterParticles.setter
    def waterParticles(self, arg1: Buffer) -> None:
        pass
    @property
    def waterVel(self) -> Buffer:
        """
        :type: Buffer
        """
    @waterVel.setter
    def waterVel(self, arg1: Buffer) -> None:
        pass
    pass
class WaterShadingPass(RenderPass):
    @property
    def currentParticleNum(self) -> int:
        """
        :type: int
        """
    @currentParticleNum.setter
    def currentParticleNum(self, arg1: int) -> None:
        pass
    @property
    def foamParticlesPosR(self) -> Buffer:
        """
        :type: Buffer
        """
    @foamParticlesPosR.setter
    def foamParticlesPosR(self, arg1: Buffer) -> None:
        pass
    pass
class WhittedRayTracer(RenderPass):
    pass
class Window():
    def setWindowPos(self, arg0: int, arg1: int) -> None: ...
    def set_window_pos(self, arg0: int, arg1: int) -> None: ...
    pass
class WindowMode():
    """
    Members:

      Normal

      Fullscreen

      Minimized
    """
    def __eq__(self, other: object) -> bool: ...
    def __getstate__(self) -> int: ...
    def __hash__(self) -> int: ...
    def __index__(self) -> int: ...
    def __init__(self, value: int) -> None: ...
    def __int__(self) -> int: ...
    def __ne__(self, other: object) -> bool: ...
    def __repr__(self) -> str: ...
    def __setstate__(self, state: int) -> None: ...
    @property
    def name(self) -> str:
        """
        :type: str
        """
    @property
    def value(self) -> int:
        """
        :type: int
        """
    Fullscreen: falcor.falcor_ext.WindowMode # value = WindowMode.Fullscreen
    Minimized: falcor.falcor_ext.WindowMode # value = WindowMode.Minimized
    Normal: falcor.falcor_ext.WindowMode # value = WindowMode.Normal
    __members__: dict # value = {'Normal': WindowMode.Normal, 'Fullscreen': WindowMode.Fullscreen, 'Minimized': WindowMode.Minimized}
    pass
class bool2():
    def __getstate__(self) -> tuple: ...
    @typing.overload
    def __init__(self) -> None: ...
    @typing.overload
    def __init__(self, arg0: typing.List[bool[2]]) -> None: ...
    @typing.overload
    def __init__(self, c: bool) -> None: ...
    @typing.overload
    def __init__(self, x: bool, y: bool) -> None: ...
    def __repr__(self) -> str: ...
    def __setstate__(self, arg0: tuple) -> None: ...
    def __str__(self) -> str: ...
    @property
    def x(self) -> bool:
        """
        :type: bool
        """
    @x.setter
    def x(self, arg0: bool) -> None:
        pass
    @property
    def y(self) -> bool:
        """
        :type: bool
        """
    @y.setter
    def y(self, arg0: bool) -> None:
        pass
    pass
class bool3():
    def __getstate__(self) -> tuple: ...
    @typing.overload
    def __init__(self) -> None: ...
    @typing.overload
    def __init__(self, arg0: typing.List[bool[3]]) -> None: ...
    @typing.overload
    def __init__(self, c: bool) -> None: ...
    @typing.overload
    def __init__(self, x: bool, y: bool, z: bool) -> None: ...
    def __repr__(self) -> str: ...
    def __setstate__(self, arg0: tuple) -> None: ...
    def __str__(self) -> str: ...
    @property
    def x(self) -> bool:
        """
        :type: bool
        """
    @x.setter
    def x(self, arg0: bool) -> None:
        pass
    @property
    def y(self) -> bool:
        """
        :type: bool
        """
    @y.setter
    def y(self, arg0: bool) -> None:
        pass
    @property
    def z(self) -> bool:
        """
        :type: bool
        """
    @z.setter
    def z(self, arg0: bool) -> None:
        pass
    pass
class bool4():
    def __getstate__(self) -> tuple: ...
    @typing.overload
    def __init__(self) -> None: ...
    @typing.overload
    def __init__(self, arg0: typing.List[bool[4]]) -> None: ...
    @typing.overload
    def __init__(self, c: bool) -> None: ...
    @typing.overload
    def __init__(self, x: bool, y: bool, z: bool, w: bool) -> None: ...
    def __repr__(self) -> str: ...
    def __setstate__(self, arg0: tuple) -> None: ...
    def __str__(self) -> str: ...
    @property
    def w(self) -> bool:
        """
        :type: bool
        """
    @w.setter
    def w(self, arg0: bool) -> None:
        pass
    @property
    def x(self) -> bool:
        """
        :type: bool
        """
    @x.setter
    def x(self, arg0: bool) -> None:
        pass
    @property
    def y(self) -> bool:
        """
        :type: bool
        """
    @y.setter
    def y(self, arg0: bool) -> None:
        pass
    @property
    def z(self) -> bool:
        """
        :type: bool
        """
    @z.setter
    def z(self, arg0: bool) -> None:
        pass
    pass
class float16_t():
    pass
class float16_t2():
    def __getstate__(self) -> tuple: ...
    @typing.overload
    def __init__(self) -> None: ...
    @typing.overload
    def __init__(self, arg0: typing.List[float16_t[2]]) -> None: ...
    @typing.overload
    def __init__(self, c: float16_t) -> None: ...
    @typing.overload
    def __init__(self, v: float2) -> None: ...
    @typing.overload
    def __init__(self, x: float16_t, y: float16_t) -> None: ...
    def __repr__(self) -> str: ...
    def __setstate__(self, arg0: tuple) -> None: ...
    def __str__(self) -> str: ...
    @property
    def x(self) -> float16_t:
        """
        :type: float16_t
        """
    @x.setter
    def x(self, arg0: float16_t) -> None:
        pass
    @property
    def y(self) -> float16_t:
        """
        :type: float16_t
        """
    @y.setter
    def y(self, arg0: float16_t) -> None:
        pass
    pass
class float16_t3():
    def __getstate__(self) -> tuple: ...
    @typing.overload
    def __init__(self) -> None: ...
    @typing.overload
    def __init__(self, arg0: typing.List[float16_t[3]]) -> None: ...
    @typing.overload
    def __init__(self, c: float16_t) -> None: ...
    @typing.overload
    def __init__(self, v: float3) -> None: ...
    @typing.overload
    def __init__(self, x: float16_t, y: float16_t, z: float16_t) -> None: ...
    def __repr__(self) -> str: ...
    def __setstate__(self, arg0: tuple) -> None: ...
    def __str__(self) -> str: ...
    @property
    def x(self) -> float16_t:
        """
        :type: float16_t
        """
    @x.setter
    def x(self, arg0: float16_t) -> None:
        pass
    @property
    def y(self) -> float16_t:
        """
        :type: float16_t
        """
    @y.setter
    def y(self, arg0: float16_t) -> None:
        pass
    @property
    def z(self) -> float16_t:
        """
        :type: float16_t
        """
    @z.setter
    def z(self, arg0: float16_t) -> None:
        pass
    pass
class float16_t4():
    def __getstate__(self) -> tuple: ...
    @typing.overload
    def __init__(self) -> None: ...
    @typing.overload
    def __init__(self, arg0: typing.List[float16_t[4]]) -> None: ...
    @typing.overload
    def __init__(self, c: float16_t) -> None: ...
    @typing.overload
    def __init__(self, v: float4) -> None: ...
    @typing.overload
    def __init__(self, x: float16_t, y: float16_t, z: float16_t, w: float16_t) -> None: ...
    def __repr__(self) -> str: ...
    def __setstate__(self, arg0: tuple) -> None: ...
    def __str__(self) -> str: ...
    @property
    def w(self) -> float16_t:
        """
        :type: float16_t
        """
    @w.setter
    def w(self, arg0: float16_t) -> None:
        pass
    @property
    def x(self) -> float16_t:
        """
        :type: float16_t
        """
    @x.setter
    def x(self, arg0: float16_t) -> None:
        pass
    @property
    def y(self) -> float16_t:
        """
        :type: float16_t
        """
    @y.setter
    def y(self, arg0: float16_t) -> None:
        pass
    @property
    def z(self) -> float16_t:
        """
        :type: float16_t
        """
    @z.setter
    def z(self, arg0: float16_t) -> None:
        pass
    pass
class float2():
    @typing.overload
    def __add__(self, arg0: float) -> float2: ...
    @typing.overload
    def __add__(self, arg0: float2) -> float2: ...
    def __getstate__(self) -> tuple: ...
    @typing.overload
    def __iadd__(self, arg0: float) -> float2: ...
    @typing.overload
    def __iadd__(self, arg0: float2) -> float2: ...
    @typing.overload
    def __imul__(self, arg0: float) -> float2: ...
    @typing.overload
    def __imul__(self, arg0: float2) -> float2: ...
    @typing.overload
    def __init__(self) -> None: ...
    @typing.overload
    def __init__(self, arg0: typing.List[float[2]]) -> None: ...
    @typing.overload
    def __init__(self, arg0: typing.List[int[2]]) -> None: ...
    @typing.overload
    def __init__(self, c: float) -> None: ...
    @typing.overload
    def __init__(self, v: float16_t2) -> None: ...
    @typing.overload
    def __init__(self, x: float, y: float) -> None: ...
    @typing.overload
    def __isub__(self, arg0: float) -> float2: ...
    @typing.overload
    def __isub__(self, arg0: float2) -> float2: ...
    @typing.overload
    def __itruediv__(self, arg0: float) -> float2: ...
    @typing.overload
    def __itruediv__(self, arg0: float2) -> float2: ...
    @typing.overload
    def __mul__(self, arg0: float) -> float2: ...
    @typing.overload
    def __mul__(self, arg0: float2) -> float2: ...
    def __repr__(self) -> str: ...
    def __setstate__(self, arg0: tuple) -> None: ...
    def __str__(self) -> str: ...
    @typing.overload
    def __sub__(self, arg0: float) -> float2: ...
    @typing.overload
    def __sub__(self, arg0: float2) -> float2: ...
    @typing.overload
    def __truediv__(self, arg0: float) -> float2: ...
    @typing.overload
    def __truediv__(self, arg0: float2) -> float2: ...
    @property
    def x(self) -> float:
        """
        :type: float
        """
    @x.setter
    def x(self, arg0: float) -> None:
        pass
    @property
    def y(self) -> float:
        """
        :type: float
        """
    @y.setter
    def y(self, arg0: float) -> None:
        pass
    pass
class float3():
    @typing.overload
    def __add__(self, arg0: float) -> float3: ...
    @typing.overload
    def __add__(self, arg0: float3) -> float3: ...
    def __getstate__(self) -> tuple: ...
    @typing.overload
    def __iadd__(self, arg0: float) -> float3: ...
    @typing.overload
    def __iadd__(self, arg0: float3) -> float3: ...
    @typing.overload
    def __imul__(self, arg0: float) -> float3: ...
    @typing.overload
    def __imul__(self, arg0: float3) -> float3: ...
    @typing.overload
    def __init__(self) -> None: ...
    @typing.overload
    def __init__(self, arg0: typing.List[float[3]]) -> None: ...
    @typing.overload
    def __init__(self, arg0: typing.List[int[3]]) -> None: ...
    @typing.overload
    def __init__(self, c: float) -> None: ...
    @typing.overload
    def __init__(self, v: float16_t3) -> None: ...
    @typing.overload
    def __init__(self, x: float, y: float, z: float) -> None: ...
    @typing.overload
    def __isub__(self, arg0: float) -> float3: ...
    @typing.overload
    def __isub__(self, arg0: float3) -> float3: ...
    @typing.overload
    def __itruediv__(self, arg0: float) -> float3: ...
    @typing.overload
    def __itruediv__(self, arg0: float3) -> float3: ...
    @typing.overload
    def __mul__(self, arg0: float) -> float3: ...
    @typing.overload
    def __mul__(self, arg0: float3) -> float3: ...
    def __repr__(self) -> str: ...
    def __setstate__(self, arg0: tuple) -> None: ...
    def __str__(self) -> str: ...
    @typing.overload
    def __sub__(self, arg0: float) -> float3: ...
    @typing.overload
    def __sub__(self, arg0: float3) -> float3: ...
    @typing.overload
    def __truediv__(self, arg0: float) -> float3: ...
    @typing.overload
    def __truediv__(self, arg0: float3) -> float3: ...
    @property
    def x(self) -> float:
        """
        :type: float
        """
    @x.setter
    def x(self, arg0: float) -> None:
        pass
    @property
    def y(self) -> float:
        """
        :type: float
        """
    @y.setter
    def y(self, arg0: float) -> None:
        pass
    @property
    def z(self) -> float:
        """
        :type: float
        """
    @z.setter
    def z(self, arg0: float) -> None:
        pass
    pass
class float3x3():
    pass
class float3x4():
    pass
class float4():
    @typing.overload
    def __add__(self, arg0: float) -> float4: ...
    @typing.overload
    def __add__(self, arg0: float4) -> float4: ...
    def __getstate__(self) -> tuple: ...
    @typing.overload
    def __iadd__(self, arg0: float) -> float4: ...
    @typing.overload
    def __iadd__(self, arg0: float4) -> float4: ...
    @typing.overload
    def __imul__(self, arg0: float) -> float4: ...
    @typing.overload
    def __imul__(self, arg0: float4) -> float4: ...
    @typing.overload
    def __init__(self) -> None: ...
    @typing.overload
    def __init__(self, arg0: typing.List[float[4]]) -> None: ...
    @typing.overload
    def __init__(self, arg0: typing.List[int[4]]) -> None: ...
    @typing.overload
    def __init__(self, c: float) -> None: ...
    @typing.overload
    def __init__(self, v: float16_t4) -> None: ...
    @typing.overload
    def __init__(self, x: float, y: float, z: float, w: float) -> None: ...
    @typing.overload
    def __isub__(self, arg0: float) -> float4: ...
    @typing.overload
    def __isub__(self, arg0: float4) -> float4: ...
    @typing.overload
    def __itruediv__(self, arg0: float) -> float4: ...
    @typing.overload
    def __itruediv__(self, arg0: float4) -> float4: ...
    @typing.overload
    def __mul__(self, arg0: float) -> float4: ...
    @typing.overload
    def __mul__(self, arg0: float4) -> float4: ...
    def __repr__(self) -> str: ...
    def __setstate__(self, arg0: tuple) -> None: ...
    def __str__(self) -> str: ...
    @typing.overload
    def __sub__(self, arg0: float) -> float4: ...
    @typing.overload
    def __sub__(self, arg0: float4) -> float4: ...
    @typing.overload
    def __truediv__(self, arg0: float) -> float4: ...
    @typing.overload
    def __truediv__(self, arg0: float4) -> float4: ...
    @property
    def w(self) -> float:
        """
        :type: float
        """
    @w.setter
    def w(self, arg0: float) -> None:
        pass
    @property
    def x(self) -> float:
        """
        :type: float
        """
    @x.setter
    def x(self, arg0: float) -> None:
        pass
    @property
    def y(self) -> float:
        """
        :type: float
        """
    @y.setter
    def y(self, arg0: float) -> None:
        pass
    @property
    def z(self) -> float:
        """
        :type: float
        """
    @z.setter
    def z(self, arg0: float) -> None:
        pass
    pass
class float4x4():
    pass
class int2():
    @typing.overload
    def __add__(self, arg0: int) -> int2: ...
    @typing.overload
    def __add__(self, arg0: int2) -> int2: ...
    def __getstate__(self) -> tuple: ...
    @typing.overload
    def __iadd__(self, arg0: int) -> int2: ...
    @typing.overload
    def __iadd__(self, arg0: int2) -> int2: ...
    @typing.overload
    def __imul__(self, arg0: int) -> int2: ...
    @typing.overload
    def __imul__(self, arg0: int2) -> int2: ...
    @typing.overload
    def __init__(self) -> None: ...
    @typing.overload
    def __init__(self, arg0: typing.List[int[2]]) -> None: ...
    @typing.overload
    def __init__(self, c: int) -> None: ...
    @typing.overload
    def __init__(self, x: int, y: int) -> None: ...
    @typing.overload
    def __isub__(self, arg0: int) -> int2: ...
    @typing.overload
    def __isub__(self, arg0: int2) -> int2: ...
    @typing.overload
    def __itruediv__(self, arg0: int) -> int2: ...
    @typing.overload
    def __itruediv__(self, arg0: int2) -> int2: ...
    @typing.overload
    def __mul__(self, arg0: int) -> int2: ...
    @typing.overload
    def __mul__(self, arg0: int2) -> int2: ...
    def __repr__(self) -> str: ...
    def __setstate__(self, arg0: tuple) -> None: ...
    def __str__(self) -> str: ...
    @typing.overload
    def __sub__(self, arg0: int) -> int2: ...
    @typing.overload
    def __sub__(self, arg0: int2) -> int2: ...
    @typing.overload
    def __truediv__(self, arg0: int) -> int2: ...
    @typing.overload
    def __truediv__(self, arg0: int2) -> int2: ...
    @property
    def x(self) -> int:
        """
        :type: int
        """
    @x.setter
    def x(self, arg0: int) -> None:
        pass
    @property
    def y(self) -> int:
        """
        :type: int
        """
    @y.setter
    def y(self, arg0: int) -> None:
        pass
    pass
class int3():
    @typing.overload
    def __add__(self, arg0: int) -> int3: ...
    @typing.overload
    def __add__(self, arg0: int3) -> int3: ...
    def __getstate__(self) -> tuple: ...
    @typing.overload
    def __iadd__(self, arg0: int) -> int3: ...
    @typing.overload
    def __iadd__(self, arg0: int3) -> int3: ...
    @typing.overload
    def __imul__(self, arg0: int) -> int3: ...
    @typing.overload
    def __imul__(self, arg0: int3) -> int3: ...
    @typing.overload
    def __init__(self) -> None: ...
    @typing.overload
    def __init__(self, arg0: typing.List[int[3]]) -> None: ...
    @typing.overload
    def __init__(self, c: int) -> None: ...
    @typing.overload
    def __init__(self, x: int, y: int, z: int) -> None: ...
    @typing.overload
    def __isub__(self, arg0: int) -> int3: ...
    @typing.overload
    def __isub__(self, arg0: int3) -> int3: ...
    @typing.overload
    def __itruediv__(self, arg0: int) -> int3: ...
    @typing.overload
    def __itruediv__(self, arg0: int3) -> int3: ...
    @typing.overload
    def __mul__(self, arg0: int) -> int3: ...
    @typing.overload
    def __mul__(self, arg0: int3) -> int3: ...
    def __repr__(self) -> str: ...
    def __setstate__(self, arg0: tuple) -> None: ...
    def __str__(self) -> str: ...
    @typing.overload
    def __sub__(self, arg0: int) -> int3: ...
    @typing.overload
    def __sub__(self, arg0: int3) -> int3: ...
    @typing.overload
    def __truediv__(self, arg0: int) -> int3: ...
    @typing.overload
    def __truediv__(self, arg0: int3) -> int3: ...
    @property
    def x(self) -> int:
        """
        :type: int
        """
    @x.setter
    def x(self, arg0: int) -> None:
        pass
    @property
    def y(self) -> int:
        """
        :type: int
        """
    @y.setter
    def y(self, arg0: int) -> None:
        pass
    @property
    def z(self) -> int:
        """
        :type: int
        """
    @z.setter
    def z(self, arg0: int) -> None:
        pass
    pass
class int4():
    @typing.overload
    def __add__(self, arg0: int) -> int4: ...
    @typing.overload
    def __add__(self, arg0: int4) -> int4: ...
    def __getstate__(self) -> tuple: ...
    @typing.overload
    def __iadd__(self, arg0: int) -> int4: ...
    @typing.overload
    def __iadd__(self, arg0: int4) -> int4: ...
    @typing.overload
    def __imul__(self, arg0: int) -> int4: ...
    @typing.overload
    def __imul__(self, arg0: int4) -> int4: ...
    @typing.overload
    def __init__(self) -> None: ...
    @typing.overload
    def __init__(self, arg0: typing.List[int[4]]) -> None: ...
    @typing.overload
    def __init__(self, c: int) -> None: ...
    @typing.overload
    def __init__(self, x: int, y: int, z: int, w: int) -> None: ...
    @typing.overload
    def __isub__(self, arg0: int) -> int4: ...
    @typing.overload
    def __isub__(self, arg0: int4) -> int4: ...
    @typing.overload
    def __itruediv__(self, arg0: int) -> int4: ...
    @typing.overload
    def __itruediv__(self, arg0: int4) -> int4: ...
    @typing.overload
    def __mul__(self, arg0: int) -> int4: ...
    @typing.overload
    def __mul__(self, arg0: int4) -> int4: ...
    def __repr__(self) -> str: ...
    def __setstate__(self, arg0: tuple) -> None: ...
    def __str__(self) -> str: ...
    @typing.overload
    def __sub__(self, arg0: int) -> int4: ...
    @typing.overload
    def __sub__(self, arg0: int4) -> int4: ...
    @typing.overload
    def __truediv__(self, arg0: int) -> int4: ...
    @typing.overload
    def __truediv__(self, arg0: int4) -> int4: ...
    @property
    def w(self) -> int:
        """
        :type: int
        """
    @w.setter
    def w(self, arg0: int) -> None:
        pass
    @property
    def x(self) -> int:
        """
        :type: int
        """
    @x.setter
    def x(self, arg0: int) -> None:
        pass
    @property
    def y(self) -> int:
        """
        :type: int
        """
    @y.setter
    def y(self, arg0: int) -> None:
        pass
    @property
    def z(self) -> int:
        """
        :type: int
        """
    @z.setter
    def z(self, arg0: int) -> None:
        pass
    pass
class uint2():
    @typing.overload
    def __add__(self, arg0: int) -> uint2: ...
    @typing.overload
    def __add__(self, arg0: uint2) -> uint2: ...
    def __getstate__(self) -> tuple: ...
    @typing.overload
    def __iadd__(self, arg0: int) -> uint2: ...
    @typing.overload
    def __iadd__(self, arg0: uint2) -> uint2: ...
    @typing.overload
    def __imul__(self, arg0: int) -> uint2: ...
    @typing.overload
    def __imul__(self, arg0: uint2) -> uint2: ...
    @typing.overload
    def __init__(self) -> None: ...
    @typing.overload
    def __init__(self, arg0: typing.List[int[2]]) -> None: ...
    @typing.overload
    def __init__(self, c: int) -> None: ...
    @typing.overload
    def __init__(self, x: int, y: int) -> None: ...
    @typing.overload
    def __isub__(self, arg0: int) -> uint2: ...
    @typing.overload
    def __isub__(self, arg0: uint2) -> uint2: ...
    @typing.overload
    def __itruediv__(self, arg0: int) -> uint2: ...
    @typing.overload
    def __itruediv__(self, arg0: uint2) -> uint2: ...
    @typing.overload
    def __mul__(self, arg0: int) -> uint2: ...
    @typing.overload
    def __mul__(self, arg0: uint2) -> uint2: ...
    def __repr__(self) -> str: ...
    def __setstate__(self, arg0: tuple) -> None: ...
    def __str__(self) -> str: ...
    @typing.overload
    def __sub__(self, arg0: int) -> uint2: ...
    @typing.overload
    def __sub__(self, arg0: uint2) -> uint2: ...
    @typing.overload
    def __truediv__(self, arg0: int) -> uint2: ...
    @typing.overload
    def __truediv__(self, arg0: uint2) -> uint2: ...
    @property
    def x(self) -> int:
        """
        :type: int
        """
    @x.setter
    def x(self, arg0: int) -> None:
        pass
    @property
    def y(self) -> int:
        """
        :type: int
        """
    @y.setter
    def y(self, arg0: int) -> None:
        pass
    pass
class uint3():
    @typing.overload
    def __add__(self, arg0: int) -> uint3: ...
    @typing.overload
    def __add__(self, arg0: uint3) -> uint3: ...
    def __getstate__(self) -> tuple: ...
    @typing.overload
    def __iadd__(self, arg0: int) -> uint3: ...
    @typing.overload
    def __iadd__(self, arg0: uint3) -> uint3: ...
    @typing.overload
    def __imul__(self, arg0: int) -> uint3: ...
    @typing.overload
    def __imul__(self, arg0: uint3) -> uint3: ...
    @typing.overload
    def __init__(self) -> None: ...
    @typing.overload
    def __init__(self, arg0: typing.List[int[3]]) -> None: ...
    @typing.overload
    def __init__(self, c: int) -> None: ...
    @typing.overload
    def __init__(self, x: int, y: int, z: int) -> None: ...
    @typing.overload
    def __isub__(self, arg0: int) -> uint3: ...
    @typing.overload
    def __isub__(self, arg0: uint3) -> uint3: ...
    @typing.overload
    def __itruediv__(self, arg0: int) -> uint3: ...
    @typing.overload
    def __itruediv__(self, arg0: uint3) -> uint3: ...
    @typing.overload
    def __mul__(self, arg0: int) -> uint3: ...
    @typing.overload
    def __mul__(self, arg0: uint3) -> uint3: ...
    def __repr__(self) -> str: ...
    def __setstate__(self, arg0: tuple) -> None: ...
    def __str__(self) -> str: ...
    @typing.overload
    def __sub__(self, arg0: int) -> uint3: ...
    @typing.overload
    def __sub__(self, arg0: uint3) -> uint3: ...
    @typing.overload
    def __truediv__(self, arg0: int) -> uint3: ...
    @typing.overload
    def __truediv__(self, arg0: uint3) -> uint3: ...
    @property
    def x(self) -> int:
        """
        :type: int
        """
    @x.setter
    def x(self, arg0: int) -> None:
        pass
    @property
    def y(self) -> int:
        """
        :type: int
        """
    @y.setter
    def y(self, arg0: int) -> None:
        pass
    @property
    def z(self) -> int:
        """
        :type: int
        """
    @z.setter
    def z(self, arg0: int) -> None:
        pass
    pass
class uint4():
    @typing.overload
    def __add__(self, arg0: int) -> uint4: ...
    @typing.overload
    def __add__(self, arg0: uint4) -> uint4: ...
    def __getstate__(self) -> tuple: ...
    @typing.overload
    def __iadd__(self, arg0: int) -> uint4: ...
    @typing.overload
    def __iadd__(self, arg0: uint4) -> uint4: ...
    @typing.overload
    def __imul__(self, arg0: int) -> uint4: ...
    @typing.overload
    def __imul__(self, arg0: uint4) -> uint4: ...
    @typing.overload
    def __init__(self) -> None: ...
    @typing.overload
    def __init__(self, arg0: typing.List[int[4]]) -> None: ...
    @typing.overload
    def __init__(self, c: int) -> None: ...
    @typing.overload
    def __init__(self, x: int, y: int, z: int, w: int) -> None: ...
    @typing.overload
    def __isub__(self, arg0: int) -> uint4: ...
    @typing.overload
    def __isub__(self, arg0: uint4) -> uint4: ...
    @typing.overload
    def __itruediv__(self, arg0: int) -> uint4: ...
    @typing.overload
    def __itruediv__(self, arg0: uint4) -> uint4: ...
    @typing.overload
    def __mul__(self, arg0: int) -> uint4: ...
    @typing.overload
    def __mul__(self, arg0: uint4) -> uint4: ...
    def __repr__(self) -> str: ...
    def __setstate__(self, arg0: tuple) -> None: ...
    def __str__(self) -> str: ...
    @typing.overload
    def __sub__(self, arg0: int) -> uint4: ...
    @typing.overload
    def __sub__(self, arg0: uint4) -> uint4: ...
    @typing.overload
    def __truediv__(self, arg0: int) -> uint4: ...
    @typing.overload
    def __truediv__(self, arg0: uint4) -> uint4: ...
    @property
    def w(self) -> int:
        """
        :type: int
        """
    @w.setter
    def w(self, arg0: int) -> None:
        pass
    @property
    def x(self) -> int:
        """
        :type: int
        """
    @x.setter
    def x(self, arg0: int) -> None:
        pass
    @property
    def y(self) -> int:
        """
        :type: int
        """
    @y.setter
    def y(self, arg0: int) -> None:
        pass
    @property
    def z(self) -> int:
        """
        :type: int
        """
    @z.setter
    def z(self, arg0: int) -> None:
        pass
    pass
def createPass(type: str, dict: dict = {}) -> RenderPass:
    pass
def get_material_param_layout(type: MaterialType) -> dict:
    pass
def inspect_ndarray(arg0: ndarray) -> None:
    pass
def loadPlugin(name: str) -> None:
    pass
def load_plugin(name: str) -> None:
    pass
Alt: falcor.falcor_ext.ModifierFlags # value = ModifierFlags.Alt
Ctrl: falcor.falcor_ext.ModifierFlags # value = ModifierFlags.Ctrl
MATERIAL_PARAM_LAYOUTS = {'Unknown': {}, 'Standard': {'base_color': {'offset': 0, 'size': 3}, 'metallic': {'offset': 3, 'size': 1}, 'roughness': {'offset': 4, 'size': 1}, 'ior': {'offset': 5, 'size': 1}, 'transmission_color': {'offset': 6, 'size': 3}, 'diffuse_transmission': {'offset': 9, 'size': 1}, 'specular_transmission': {'offset': 10, 'size': 1}, 'emissive_color': {'offset': 11, 'size': 3}, 'emissive_factor': {'offset': 14, 'size': 1}}, 'Cloth': {}, 'Hair': {}, 'MERL': {}, 'MERLMix': {}, 'PBRTDiffuse': {'diffuse': {'offset': 0, 'size': 3}}, 'PBRTDiffuseTransmission': {}, 'PBRTConductor': {'eta': {'offset': 0, 'size': 3}, 'k': {'offset': 3, 'size': 3}, 'roughness': {'offset': 6, 'size': 2}}, 'PBRTDielectric': {}, 'PBRTCoatedConductor': {}, 'PBRTCoatedDiffuse': {}, 'RGL': {}}
None: falcor.falcor_ext.ModifierFlags # value = ModifierFlags.None
Shift: falcor.falcor_ext.ModifierFlags # value = ModifierFlags.Shift
float16: falcor.falcor_ext.DataType # value = DataType.float16
float32: falcor.falcor_ext.DataType # value = DataType.float32
float64: falcor.falcor_ext.DataType # value = DataType.float64
int16: falcor.falcor_ext.DataType # value = DataType.int16
int32: falcor.falcor_ext.DataType # value = DataType.int32
int64: falcor.falcor_ext.DataType # value = DataType.int64
int8: falcor.falcor_ext.DataType # value = DataType.int8
uint16: falcor.falcor_ext.DataType # value = DataType.uint16
uint32: falcor.falcor_ext.DataType # value = DataType.uint32
uint64: falcor.falcor_ext.DataType # value = DataType.uint64
uint8: falcor.falcor_ext.DataType # value = DataType.uint8
Material = falcor.falcor_ext.StandardMaterial
Volume = falcor.falcor_ext.GridVolume
