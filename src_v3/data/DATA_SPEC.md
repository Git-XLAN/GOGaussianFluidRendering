# 数据集说明

`sample = ds[i]` 读入的一帧数据包含以下条目及用法。

## 读入的数据包含哪些

**流体（顶层）：**

| 条目 | 类型 | 含义 |
|------|------|------|
| `input_particles` | [N, 4] | 流体粒子 x,y,z,radius，直接给渲染/训练用 |
| `positions` | [N, 3] | 流体位置 = input_particles[:, :3] |
| `radii` | [N, 1] | 半径列 = input_particles[:, 3:4] |
| `vel` | [N, 3] 或 None | 流体速度 |
| `maxPos` / `minPos` | [3] | 包围盒 |
| `num_particles` | int | 流体粒子数 N |
| `radius` | float | 统一半径标量 |
| `gt_mesh_path` | str 或 None | 本帧 GT mesh 的 OBJ 路径 |
| `meta_scene` / `meta_frame_id` | str, int | 场景名、帧号 |
| `camera` | dict | 由粒子位置生成的相机（与 GT 渲染/高斯投影共用），见下 |

**相机 `camera`：**

由 `camera_from_particles(positions, mode=...)` 在加载时生成，格式与 GTGenerator / GaussianProjector 一致：

| 键 | 类型 | 含义 |
|------|------|------|
| `origin` | [x,y,z] | 相机位置 |
| `target` | [x,y,z] | 看向目标（如粒子包围盒中心） |
| `up` | [x,y,z] | 相机上方向 |
| `fov` | float | 垂直 fov（度） |

**泡沫（两个子字典，可能为 None）：**

| 条目 | 含义 |
|------|------|
| `foam` | 本帧全部泡沫，子键：`positions` [M,4], `vel`, `lifetime`, `id`, `radius`, `num_particles`, `born` |
| `newfoam` | 本帧新生泡沫，子键同上 |

## 相机生成模式（mode）

构造数据集时可指定 `camera_mode` 等，控制每帧 `camera` 的生成方式：

| 参数 | 默认 | 说明 |
|------|------|------|
| `camera_mode` | `"bbox"` | 策略：`bbox` = 看向粒子包围盒中心，相机在盒外 |
| `camera_fov` | 60 | 垂直 fov（度） |
| `camera_distance_scale` | 1.5 | bbox 模式下相机到中心的距离 = 最大边长 × 该倍数（>0.5 即在盒外） |
| `camera_axis` | `"z"` | bbox 模式下相机所在轴：`"x"` / `"y"` / `"z"` |

后续可扩展更多 mode（如固定机位、轨迹、多视角等）。

## 怎么用

```python
# 构造时可选相机参数（与 GT/投影一致）
ds = FluidDataset(root, camera_mode="bbox", camera_fov=60)

sample = ds[0]

# 流体：给模型/光栅化
particles = sample["input_particles"]   # [N, 4]
vel       = sample["vel"]
n         = sample["num_particles"]

# 相机：给 GT 渲染与高斯投影（trainer 中 _get_gt_camera(sample) 会用到）
camera = sample["camera"]   # {"origin", "target", "up", "fov"}

# GT mesh
mesh_path = sample["gt_mesh_path"]     # 渲染 normal/depth 用

# 泡沫：先判空
if sample.get("foam"):
    foam_pos = sample["foam"]["positions"]   # [M, 4]
    foam_vel = sample["foam"]["vel"]
if sample.get("newfoam"):
    newfoam_pos = sample["newfoam"]["positions"]
```
