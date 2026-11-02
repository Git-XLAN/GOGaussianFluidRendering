from __future__ import annotations
import falcor
import typing
from falcor.falcor_ext import AABB
from falcor.falcor_ext import AccumulatePass
from falcor.falcor_ext import AdapterInfo
from falcor.falcor_ext import AlphaMode
from falcor.falcor_ext import AnalyticAreaLight
from falcor.falcor_ext import Animatable
from falcor.falcor_ext import Animation
from falcor.falcor_ext import AssertionError
from falcor.falcor_ext import AssetCategory
from falcor.falcor_ext import AssetResolver
from falcor.falcor_ext import BSDFOptimizer
from falcor.falcor_ext import BackGroundPass
from falcor.falcor_ext import BaseLinePass
from falcor.falcor_ext import BasicMaterial
from falcor.falcor_ext import BgPass
from falcor.falcor_ext import BlendState
from falcor.falcor_ext import BlitPass
from falcor.falcor_ext import Buffer
from falcor.falcor_ext import Camera
from falcor.falcor_ext import Clock
from falcor.falcor_ext import ClothMaterial
from falcor.falcor_ext import ComparePass
from falcor.falcor_ext import CompareSwapPass
from falcor.falcor_ext import ComparisonFunc
from falcor.falcor_ext import CompositionOrder
from falcor.falcor_ext import ComputeContext
from falcor.falcor_ext import ComputePass
from falcor.falcor_ext import ComputeState
from falcor.falcor_ext import CopyContext
from falcor.falcor_ext import DLSSPass
from falcor.falcor_ext import DataType
from falcor.falcor_ext import DepthStencilState
from falcor.falcor_ext import DepthStencilView
from falcor.falcor_ext import Device
from falcor.falcor_ext import DeviceType
from falcor.falcor_ext import DiffMode
from falcor.falcor_ext import DirectionalLight
from falcor.falcor_ext import DiscLight
from falcor.falcor_ext import DistantLight
from falcor.falcor_ext import EnvMap
from falcor.falcor_ext import Fbo
from falcor.falcor_ext import FoamParticleProcess
from falcor.falcor_ext import FoamPass
from falcor.falcor_ext import FoamShadingPass
from falcor.falcor_ext import GTPass
from falcor.falcor_ext import GTRenderingPass
from falcor.falcor_ext import GaussianBlur
from falcor.falcor_ext import GpuTimer
from falcor.falcor_ext import GradConfig
from falcor.falcor_ext import GradientType
from falcor.falcor_ext import GraphicsState
from falcor.falcor_ext import Grid
from falcor.falcor_ext import GridVolume
from falcor.falcor_ext import HairMaterial
from falcor.falcor_ext import IMaterial
from falcor.falcor_ext import ImporterError
from falcor.falcor_ext import Key
from falcor.falcor_ext import KeyboardEvent
from falcor.falcor_ext import Light
from falcor.falcor_ext import Logger
from falcor.falcor_ext import MERLMaterial
from falcor.falcor_ext import MERLMixMaterial
from falcor.falcor_ext import MaterialTextureSlot
from falcor.falcor_ext import MaterialType
from falcor.falcor_ext import MemoryType
from falcor.falcor_ext import MeshDesc
from falcor.falcor_ext import ModifierFlags
from falcor.falcor_ext import MouseButton
from falcor.falcor_ext import MouseEvent
from falcor.falcor_ext import ObjectID
from falcor.falcor_ext import PBRTCoatedConductorMaterial
from falcor.falcor_ext import PBRTCoatedDiffuseMaterial
from falcor.falcor_ext import PBRTConductorMaterial
from falcor.falcor_ext import PBRTDielectricMaterial
from falcor.falcor_ext import PBRTDiffuseMaterial
from falcor.falcor_ext import PBRTDiffuseTransmissionMaterial
from falcor.falcor_ext import ParameterBlockReflection
from falcor.falcor_ext import ParticleFilterPass
from falcor.falcor_ext import PathTracer
from falcor.falcor_ext import PixelStats
from falcor.falcor_ext import PointLight
from falcor.falcor_ext import Profiler
from falcor.falcor_ext import ProfilerEvent
from falcor.falcor_ext import Program
from falcor.falcor_ext import ProgramDesc
from falcor.falcor_ext import ProgramReflection
from falcor.falcor_ext import RGLMaterial
from falcor.falcor_ext import RasterizerState
from falcor.falcor_ext import RectLight
from falcor.falcor_ext import Rectangle
from falcor.falcor_ext import ReflectionArrayType
from falcor.falcor_ext import ReflectionBasicType
from falcor.falcor_ext import ReflectionInterfaceType
from falcor.falcor_ext import ReflectionResourceType
from falcor.falcor_ext import ReflectionStructType
from falcor.falcor_ext import ReflectionType
from falcor.falcor_ext import ReflectionVar
from falcor.falcor_ext import RenderContext
from falcor.falcor_ext import RenderGraph
from falcor.falcor_ext import RenderPass
from falcor.falcor_ext import RenderTargetView
from falcor.falcor_ext import Resource
from falcor.falcor_ext import ResourceBindFlags
from falcor.falcor_ext import ResourceFormat
from falcor.falcor_ext import RuntimeError
from falcor.falcor_ext import SDFGrid
from falcor.falcor_ext import SSFR
from falcor.falcor_ext import SSRShading
from falcor.falcor_ext import Sampler
from falcor.falcor_ext import Scene
from falcor.falcor_ext import SceneBuilder
from falcor.falcor_ext import SceneBuilderFlags
from falcor.falcor_ext import SceneDebugger
from falcor.falcor_ext import SceneGradients
from falcor.falcor_ext import SceneRenderSettings
from falcor.falcor_ext import SearchPathPriority
from falcor.falcor_ext import Settings
from falcor.falcor_ext import ShaderModel
from falcor.falcor_ext import ShaderResourceView
from falcor.falcor_ext import ShaderVar
from falcor.falcor_ext import ShadingModel
from falcor.falcor_ext import ShadingPass
from falcor.falcor_ext import SimplePostFX
from falcor.falcor_ext import SlangCompilerFlags
from falcor.falcor_ext import SphereLight
from falcor.falcor_ext import StandardMaterial
from falcor.falcor_ext import SwapPass
from falcor.falcor_ext import TAA
from falcor.falcor_ext import TestPyTorchPass
from falcor.falcor_ext import TestRtProgram
from falcor.falcor_ext import Testbed
from falcor.falcor_ext import Texture
from falcor.falcor_ext import TextureAddressingMode
from falcor.falcor_ext import TextureChannelFlags
from falcor.falcor_ext import TextureFilteringMode
from falcor.falcor_ext import TextureReductionMode
from falcor.falcor_ext import ThicknessPass
from falcor.falcor_ext import ToneMapper
from falcor.falcor_ext import TrainGTBuffer
from falcor.falcor_ext import Transform
from falcor.falcor_ext import TriangleMesh
from falcor.falcor_ext import TriangleMeshImportFlags
from falcor.falcor_ext import UnorderedAccessView
from falcor.falcor_ext import Vao
from falcor.falcor_ext import VertexLayout
from falcor.falcor_ext import WARDiffPathTracer
from falcor.falcor_ext import WaterFoamShading
from falcor.falcor_ext import WaterParticleProcess
from falcor.falcor_ext import WaterShadingPass
from falcor.falcor_ext import WhittedRayTracer
from falcor.falcor_ext import Window
from falcor.falcor_ext import WindowMode
from falcor.falcor_ext import bool2
from falcor.falcor_ext import bool3
from falcor.falcor_ext import bool4
from falcor.falcor_ext import float16_t
from falcor.falcor_ext import float16_t2
from falcor.falcor_ext import float16_t3
from falcor.falcor_ext import float16_t4
from falcor.falcor_ext import float2
from falcor.falcor_ext import float3
from falcor.falcor_ext import float3x3
from falcor.falcor_ext import float3x4
from falcor.falcor_ext import float4
from falcor.falcor_ext import float4x4
from falcor.falcor_ext import int2
from falcor.falcor_ext import int3
from falcor.falcor_ext import int4
from falcor.falcor_ext import uint2
from falcor.falcor_ext import uint3
from falcor.falcor_ext import uint4
import falcor.falcor_ext
import falcor.falcor_ext.ui

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
    "falcor_ext",
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


def createPass(type: str, dict: dict = {}) -> falcor_ext.RenderPass:
    pass
def get_material_param_layout(type: falcor_ext.MaterialType) -> dict:
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
ui = falcor.falcor_ext.ui
