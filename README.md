Inference / real-time rendering only. No training code.

Requirements: Win10/11 x64, NVIDIA GPU, Python 3.10, torch 2.3.0+cu121. Other Python versions won't work, the bundled pyd files are cp310.

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

Falcor, the Gaussian rasterizer and cunnsearch are bundled, nothing to build. PYTHONPATH has to point at the repo root or the imports fail.

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

Frame id is the first number in the file name. `sample_data` only has a couple of frames, it's just for checking the setup.

Full scenes (Boat, DoubleDamBreak, DownWater, WaterFall; particle data only) are on the [data-v1 release](https://github.com/Git-XLAN/GOGaussianFluid-Public/releases/tag/data-v1). Each scene is split into several independent zips. Download all parts of a scene and extract them into the same `<data>` folder:

```
Expand-Archive Boat_particle_part01.zip -DestinationPath <data>
Expand-Archive Boat_particle_part02.zip -DestinationPath <data>
...
```

You get `<data>/Boat/particle/*.vtk`, then use `--scene Boat`. Unpacked sizes: Boat 12 GB, DoubleDamBreak 4.5 GB, DownWater 2.6 GB, WaterFall 14 GB.

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

Output goes to `<out>/infer/<scene>/`. If cunnsearch breaks, drop `--search_optimized`, it'll use CPU scipy, a bit slower.

Real-time (Falcor window):

```
python -m src_v3.demo.RealTimeWater --mode scene --data_path <data> --scene <scene> --model weights/latest.pth --device cuda:0 --search_optimized --decoder_layers 256,512 --gs_num 24 --decoder_variant direct --surface_neighbor_threshold 0 --width 1920 --height 1080 --factor 4.0 --foam_density_log_alpha 200
```

Change the EnvMap in `src_v3/baseRender.pyscene` to an hdr on your machine, the scene won't load with a bad path. A `baseRender.pyscene` inside the scene folder takes priority if present.

Minimal window (10 particles, Falcor sanity check):

```
python -m src_v3.testbed_minimal_water
```

`--search_optimized` needs CUDA tensors. Falcor is D3D12, Windows only. If python and Falcor are on different drives you may get an Agility SDK warning, usually still works.

License: non-commercial research/evaluation only (includes Inria `diff-gaussian-rasterization` and redistributable Falcor/NVIDIA/Microsoft runtime binaries). This software contains source code provided by NVIDIA Corporation. See `LICENSE`, `THIRD_PARTY_NOTICES.md`, and `licenses/`.
