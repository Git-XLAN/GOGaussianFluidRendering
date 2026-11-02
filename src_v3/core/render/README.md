# 高斯投影与 Falcor 合成

本发行包不含训练用 GT Generator（Mitsuba / nvdiffrast）。运行时依赖：

- **PyTorch + CUDA**
- **diff_gaussian_rasterization**（`GaussianProjector`）
- **Falcor** Python 绑定（`falcor_manager.py`，通过环境变量 `FALCOR_DIR` 定位）

## 高斯投影器（GaussianProjector）

将网络输出的高斯参数投影为 normal / depth / hit。

```python
from src_v3.core.render import GaussianProjector

projector = GaussianProjector(width=256, height=256)
normal, depth, hit, vel, foam_prob_culled, gs_pos_culled, foam_prob_raw_culled, gs_vel_culled = projector.project(
    camera,
    gs_pos, gs_scale, gs_rotation,
    gs_normal=target_n,
    gs_opacity=foam_prob,
)
```

相机字典格式：`origin` / `target` / `up` / `fov`。

## 文件

| 文件 | 说明 |
|------|------|
| `camera_utils.py` | 相机：dict/对象 → view、proj、cam_pos、tanfov |
| `gaussian_projector.py` | 高斯投影：网络输出 → normal/depth/hit |
| `falcor_manager.py` | Falcor 粒子过滤与实时水合成 |
