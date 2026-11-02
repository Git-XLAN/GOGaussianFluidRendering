import sys
from pathlib import Path

# 与 testbed 一致：直接运行本文件时把仓库根加入 path，否则找不到包 src_v3
_REPO_ROOT = Path(__file__).resolve().parents[1]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from src_v3.data.vtk_loader import load_fluid_vtk

data = load_fluid_vtk(
    "E:/Train/RandomFoam_010/particle/ParticleData_Fluid_1.vtk", 0.0
)
print(data)