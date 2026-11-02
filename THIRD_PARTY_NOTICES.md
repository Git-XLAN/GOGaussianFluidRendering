Third-Party Notices
===================

This document lists the third-party software bundled in this repository and the
terms under which each component is redistributed. Full license texts are stored
in the `licenses/` folder.

This software contains source code provided by NVIDIA Corporation.


1. Inria / MPII — `diff-gaussian-rasterization`
-----------------------------------------------
- Files:
  - `diff_gaussian_rasterization/` (including `_C.cp310-win_amd64.pyd`)
  - `Dependency/diff-gaussian-rasterization/`
- License: **Gaussian-Splatting License** (Inria and Max Planck Institut für
  Informatik), plus MIT License for bundled `third_party/glm`.
- Terms: Granted for **non-commercial research and/or evaluation purposes only**.
  Redistribution is permitted in source or compiled form provided the complete
  license and copyright notices are retained (Sections 3, 4.1, 4.4).
- License files:
  - `licenses/diff-gaussian-rasterization-LICENSE.md`
  - `diff_gaussian_rasterization/LICENSE.md`
  - `Dependency/diff-gaussian-rasterization/LICENSE.md`
  - `Dependency/diff-gaussian-rasterization/third_party/glm/copying.txt`


2. cuNSearch — `src_v3/cunnsearch.cp310-win_amd64.pyd`
------------------------------------------------------
- File: `src_v3/cunnsearch.cp310-win_amd64.pyd`
- License: **MIT License** (Copyright (c) 2019-present, cuNSearch contributors;
  upstream: https://github.com/InteractiveComputerGraphics/cuNSearch), linked
  against PyTorch (**BSD 3-Clause**) and pybind11 (**BSD-style**).
- License files:
  - `licenses/cuNSearch-LICENSE.txt`
  - `licenses/pybind11-LICENSE.txt`


3. NVIDIA Falcor (Modified Runtime) — `Falcor/`
-----------------------------------------------
- Files: `Falcor/Falcor.dll`, `Falcor/python/falcor/`, `Falcor/plugins/`,
  `Falcor/shaders/`, `Falcor/data/`, `Falcor/scripts/`
- License: **BSD 3-Clause License** (Copyright (c) 2020, NVIDIA CORPORATION).
- Note on removed proprietary SDKs: The upstream Falcor `LICENSE.md` notes that
  Falcor may link to DLSS, RTXGI, RTXDI, and NRD. Those optional proprietary
  RTX SDK components (`nvngx_dlss.dll`, `NRD.dll`, `DLSSPass.dll`,
  `NRDPass.dll`, `RTXDIPass.dll`, and their shader folders) are not used by
  GOGaussianFluid and have been **removed** from this binary distribution.
- License files:
  - `Falcor/LICENSE.md`
  - `licenses/Falcor-LICENSE.md`


4. Shader Slang — `Falcor/slang*.dll`, `Falcor/gfx.dll`
-------------------------------------------------------
- Files: `Falcor/slang.dll`, `Falcor/slang-glslang.dll`,
  `Falcor/slang-llvm.dll`, `Falcor/slang-rt.dll`, `Falcor/gfx.dll`
- License: **MIT License** (Copyright (c) 2016, Carnegie Mellon University and
  NVIDIA Corporation) and LLVM/Khronos permissive components.
- License file: `licenses/Slang-LICENSE.txt`


5. NVIDIA Texture Tools SDK & CUDA Runtime — `Falcor/nvtt30106.dll`, `Falcor/cudart64_110.dll`
----------------------------------------------------------------------------------------------
- Files: `Falcor/nvtt30106.dll`, `Falcor/cudart64_110.dll`
- License: **NVIDIA Texture Tools SDK License** / **NVIDIA CUDA Toolkit EULA**
  (redistributable runtime).
- Required Notice: *"This software contains source code provided by NVIDIA
  Corporation."*
- Restrictions: Distributed in object code form as part of this application
  only. You may not reverse engineer, decompile, disassemble, or redistribute
  these DLLs as a stand-alone product, nor subject them to any open-source
  software license (Section 4(b), 4(d)).
- License files:
  - `licenses/NVIDIA-Texture-Tools-LICENSE.txt`
  - `licenses/NVIDIA-Texture-Tools-third-party.txt`


6. Microsoft DirectX 12 Agility SDK & DXC & PIX Runtime
-------------------------------------------------------
- Files:
  - `Falcor/D3D12/D3D12Core.dll`, `Falcor/D3D12/d3d12SDKLayers.dll`
    (listed as distributable in the Agility SDK `distributable files.txt`)
  - `Falcor/dxcompiler.dll`, `Falcor/dxil.dll`
  - `Falcor/WinPixEventRuntime.dll`
- License: **Microsoft Software License Terms — Microsoft DirectX / PIX**.
- Restrictions: Distributed in object code form as part of this Windows
  application only. May not be distributed as a stand-alone offering or
  subjected to any license requiring source disclosure.
- License files:
  - `licenses/Microsoft-DirectX-Agility-SDK-LICENSE.txt`
  - `licenses/WinPixEventRuntime-ThirdPartyNotices.txt`


7. FreeImage — `Falcor/FreeImage.dll`, `Falcor/FreeImagePlus.dll`
-----------------------------------------------------------------
- Files: `Falcor/FreeImage.dll`, `Falcor/FreeImagePlus.dll`
- License: Dual-licensed under GPL or the **FreeImage Public License (FIPL)
  Version 1.0**. For this distribution, the binaries are distributed under
  **FIPL Version 1.0**.
- Source Code Availability Notice (FIPL Section 3.6): These DLLs are unmodified
  builds of FreeImage 3.18.0 (from vcpkg). The Original Code of FreeImage is
  available under FIPL v1.0 at https://freeimage.sourceforge.io/ and via the
  Microsoft vcpkg port repository (https://github.com/microsoft/vcpkg). Any
  terms in `LICENSE` that differ from FIPL v1.0 are offered by the repository
  authors alone and not by the Initial Developer or Contributors of FreeImage.
- License file: `licenses/FreeImage-FIPL-1.0.txt`


8. OpenVDB — `Falcor/openvdb.dll`
---------------------------------
- File: `Falcor/openvdb.dll`
- License: **Mozilla Public License 2.0 (MPL-2.0)**.
- Source Code Notice (MPL-2.0 Section 3.2(a)): This DLL is an unmodified build
  of OpenVDB 9.0.0. The corresponding MPL-2.0 source code is available at
  https://github.com/AcademySoftwareFoundation/openvdb/releases/tag/v9.0.0.
- License file: `licenses/OpenVDB-LICENSE.txt`


9. Other Open-Source Libraries in `Falcor/`
-------------------------------------------
All remaining DLLs and embedded libraries in `Falcor/` are under permissive
open-source licenses that permit binary redistribution with copyright and
disclaimer retention:

- **Assimp** (`Falcor/assimp-vc143-mt.dll`, `Falcor/plugins/AssimpImporter.dll`)
  — BSD 3-Clause (`licenses/Assimp-LICENSE.txt`)
- **OpenEXR & Imath** (`Falcor/OpenEXR*.dll`, `Falcor/Iex*.dll`,
  `Falcor/Ilm*.dll`, `Falcor/Imath*.dll`, `Falcor/Half*.dll`)
  — BSD 3-Clause (`licenses/OpenEXR-LICENSE.txt`, `licenses/Imath-LICENSE.txt`)
- **C-Blosc** (`Falcor/blosc.dll`) — BSD 3-Clause (`licenses/Blosc-LICENSE.txt`)
- **Intel oneTBB** (`Falcor/tbb*.dll`) — Apache License 2.0 (`licenses/TBB-LICENSE.txt`)
- **Boost** (`Falcor/boost_*.dll`) — Boost Software License 1.0 (`licenses/Boost-LICENSE.txt`)
- **HDF5** (`Falcor/hdf5*.dll`) — BSD-style HDF5 License (`licenses/HDF5-LICENSE.txt`)
- **CPython** (`Falcor/python3.dll`, `Falcor/python310.dll`) — PSF License v2
  (https://docs.python.org/3.10/license.html)
- **GLFW / Dear ImGui / pybind11** (statically linked into `Falcor.dll` /
  `falcor_ext.cp310-win_amd64.pyd`) — zlib / MIT / BSD-style
  (`licenses/GLFW-LICENSE.md`, `licenses/ImGui-LICENSE.txt`,
  `licenses/pybind11-LICENSE.txt`)


10. External Python Packages (Installed by User, Not Bundled)
-------------------------------------------------------------
Packages listed in `requirements.txt` (`torch`, `numpy`, `scipy`, `vtk`,
`pyexr`, optional `pysplishsplash`) are not redistributed in this repository;
they are downloaded from PyPI/PyTorch by the user under their own permissive
licenses (BSD / MIT / LGPL-3.0).
