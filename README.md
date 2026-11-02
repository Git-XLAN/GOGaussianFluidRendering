# GOGaussianFluidRendering

Inference / real-time rendering only. No training code.

Requirements: Win10/11 x64, NVIDIA GPU with a recent [driver](https://www.nvidia.com/Download/index.aspx) (CUDA 12.1 capable), [Miniconda](https://docs.conda.io/en/latest/miniconda.html), Python 3.10, [PyTorch](https://pytorch.org/get-started/previous-versions/#v230) 2.3.0+cu121. Other Python versions won't work, the bundled pyd files are cp310.

```
conda create -n falcor-pytorch python=3.10 -y
conda activate falcor-pytorch
pip install torch==2.3.0+cu121 torchvision==0.18.0+cu121 --index-url https://download.pytorch.org/whl/cu121
pip install -r requirements.txt
```

Before each run, from the repo root:

```
conda activate falcor-pytorch
$env:PYTHONPATH = (Get-Location).Path
```

Bundled prebuilt, nothing to build: a modified [Falcor](https://github.com/NVIDIAGameWorks/Falcor) runtime (`Falcor/`), Inria's [diff-gaussian-rasterization](https://github.com/graphdeco-inria/diff-gaussian-rasterization) (`diff_gaussian_rasterization/`), and a [cuNSearch](https://github.com/InteractiveComputerGraphics/cuNSearch) based neighbor search (`src_v3/cunnsearch.cp310-win_amd64.pyd`). PYTHONPATH has to point at the repo root or the imports fail.

Neighbor search: with `--search_optimized` it uses `src_v3/cunnsearch.cp310-win_amd64.pyd` (CUDA, only depends on torch). Without it, falls back to scipy cKDTree.

Data layout:

```
<data>/
  <scene>/
    particle/   *.vtk     required
    foam/       *.vtk     optional
    Newfoam/    *.vtk     optional
    mesh/       *.obj     optional, not needed for infer
    baseRender.pyscene    optional, overrides the default scene
```

Placeholders used below: `<data>` is the data root folder (e.g. `sample_data`, or wherever you unzip the release data), `<scene>` is a subfolder name in it (`WaterFall`, `Boat`, `DoubleDamBreak`, `DownWater`), `<out>` is any output folder (e.g. `output`).

Frame id is the first number in the file name. `sample_data` only has a couple of frames of `WaterFall`, it's just for checking the setup.

Full scenes (Boat, DoubleDamBreak, DownWater, WaterFall; particle data only) are on the [data-v1 release](https://github.com/Git-XLAN/GOGaussianFluidRendering/releases/tag/data-v1). Each scene is split into several independent zips (not a split archive, every part opens on its own):

| Scene | Frames | Files | Unpacked |
|---|---|---|---|
| Boat | 300 | `Boat_particle_part01..06.zip` | 12 GB |
| DoubleDamBreak | 300 | `DoubleDamBreak_particle_part01..02.zip` | 4.5 GB |
| DownWater | 300 | `DownWater_particle_part01..02.zip` | 2.6 GB |
| WaterFall | 400 | `WaterFall_particle_part01..04.zip` | 14 GB |

Download all parts of a scene and extract them into the same `<data>` folder, e.g. for Boat:

```
Get-ChildItem Boat_particle_part*.zip | ForEach-Object { Expand-Archive $_ -DestinationPath <data> -Force }
```

You get `<data>/Boat/particle/*.vtk`, then use `--scene Boat`.

`SceneDes/` holds the render setup for these scenes: `SceneDes/<scene>/baseRender.pyscene` (camera, env map) plus the background meshes and textures in `SceneDes/<scene>/mesh/bg/`. It's picked up automatically from the scene name. DoubleDamBreak has no background and uses the default `src_v3/baseRender.pyscene`. The env map shared by all scenes is `SceneDes/envmap/20050806-03_4k.hdr`.

Weights: `weights/latest.pth` (same architecture as `direct.pth`). These args must match:

```
--decoder_variant direct
--decoder_layers 256,512
--gs_num 24
--foam_density_log_alpha 200
-f 4.0
```

Otherwise loading fails with a shape mismatch.

Offline infer (no window):

```
python -m src_v3.main -d <data> -o <out> -D cuda:0 -f 4.0 --search_optimized infer -m weights/latest.pth --scene <scene> --decoder_variant direct --decoder_layers 256,512 --gs_num 24 --foam_density_log_alpha 200 --width 256 --height 256 --surface_neighbor_threshold 0
```

With the bundled sample: `-d sample_data -o output --scene WaterFall`. Output goes to `<out>/infer/<scene>/`. If cunnsearch breaks, drop `--search_optimized`, it'll use CPU scipy, a bit slower.

Real-time (Falcor window):

```
python -m src_v3.demo.RealTimeWater --mode scene --data_path <data> --scene <scene> --model weights/latest.pth --device cuda:0 --search_optimized --decoder_layers 256,512 --gs_num 24 --decoder_variant direct --surface_neighbor_threshold 0 --width 1920 --height 1080 --factor 4.0 --foam_density_log_alpha 200
```

With the bundled sample: `--data_path sample_data --scene WaterFall`.

Pyscene lookup order: `<data>/<scene>/baseRender.pyscene`, then `SceneDes/<scene>/baseRender.pyscene`, then `src_v3/baseRender.pyscene`. Relative paths inside a pyscene are best built from `__file__` (see the ones in `SceneDes`). The env map is required, Falcor crashes without one.

Minimal window (10 particles, Falcor sanity check):

```
python -m src_v3.testbed_minimal_water
```

`--search_optimized` needs CUDA tensors. Falcor is D3D12, Windows only. If python and Falcor are on different drives you may get an Agility SDK warning, usually still works.

## License

Non-commercial research and evaluation use only, see [LICENSE](LICENSE). This is mainly because the bundled [diff-gaussian-rasterization](https://github.com/graphdeco-inria/diff-gaussian-rasterization) is under Inria's non-commercial license.

Other bundled components (Falcor, Slang, cuNSearch, NVIDIA and Microsoft runtime DLLs, etc.) keep their own licenses. They are listed in [THIRD_PARTY_NOTICES.md](THIRD_PARTY_NOTICES.md), with full texts in [licenses/](licenses/).
