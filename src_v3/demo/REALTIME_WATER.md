# RealTimeWater 说明文档

`RealTimeWater.py` 提供实时流体 + 高斯泡沫演示的主循环，根据**命令行是否带 `--timing`** 分为两种**运行模式**（与数据源 `scene` / `simulation` 正交）。本文说明这两种模式的差异、数据流、退出条件与产出文件。

---

## 1. 如何区分两种模式

入口在 `main()`：

- **`--timing` 未传**（默认）：`runner.infer_cfg.search_timing` 为 `false` → 调用 **`run_loop_realtime`** → **Realtime 模式**（交互演示向）。
- **`--timing` 已传**：`search_timing` 为 `true` → 调用 **`run_loop_timing`** → **Timing 模式**（基准测试 / 统计向）。

两种模式共用同一套 `DemoConfig`、`RealTimeWaterRunner`、模型与 Falcor，区别主要在**主循环函数**、**每帧处理函数**以及 **Timing 模式下的统计与落盘**。

---

## 2. 数据源：`--mode`（与 Timing/Realtime 独立）

| `mode` | 说明 |
|--------|------|
| **`scene`**（默认） | 使用 `SceneSampleProvider`，从 `--data_path` + `--scene` 读取 `SceneDataset` 帧（与训练数据布局一致，可含 `foam` / `newfoam` 等）。 |
| **`simulation`** | 使用 `SimulationSampleProvider` 占位随机粒子，用于接口调试，**无真实 GT 泡沫**。 |

两种运行模式均可搭配 `scene` 或 `simulation`；**泡沫密度 MAE、CSV 等**依赖 `scene` 数据里的 GT。

---

## 3. Realtime 模式（未使用 `--timing`）

### 3.1 用途

窗口内连续播放、Falcor 暂停由 **`runner.falcorRender.getPause()`** 每帧刷新；适合**交互预览**，不做会话级 timing 汇总文件。

### 3.2 每帧处理

调用 **`process_frame_realtime`**，内部等价路径：

1. `_prepare_inputs` / `prepare_sample`
2. **`_run_search_cull_model_splat`**：Falcor 表面裁剪 → `search` → `CovDecoderModel` → `GaussianProjector.project`
3. `getFoamDensity()` → `_sample_new_foam`（Bernoulli 采样 newFoam）
4. **`render_real_time_water`**（含可选 GT 全泡沫 `gt_foam_positions` 等）

### 3.3 帧计数与退出

- **`frame_count`**：仅在 **`not cfg.pause`** 时自增（暂停时不推进“逻辑帧号”）。
- **退出**（与 Timing 共用 `frames` / `loop` / `save_result` 语义）：
  - **`--save_result`**：写出 `frames` 张 EXR 后退出；
  - **未 `save_result`**：`--no_loop` 时 `frame_count >= frames` 退出（`frame_count` 仅在非暂停时递增）；**默认 loop** 时 `frame_count` 到 `frames` 后**归零循环**，可能长时间运行。

### 3.4 输出

- 可选：`--save_result` → **`--output_dir`** 目录下 `frame_XXXX.exr`
- **无** `RealTimeWater_timing_summary.json`、**无** `foam_density_metrics.csv` 会话统计（每帧仍可有控制台日志）。

---

## 4. Timing 模式（使用 `--timing`）

### 4.1 用途

对 **Culling / 邻域搜索 / 网络 / Splatting** 分段计时，并可选计算 **newFoam 与 GT newFoam 的体素密度 MAE**；结束时写入 **JSON 汇总** 与可选 **CSV**。

### 4.2 每帧处理

调用 **`process_frame_timing`**（与 Realtime **不共用** `_run_search_cull_model_splat`，逻辑与之对齐）：在同一函数内对 cull、search、model、splat、Falcor 渲染分段 `perf_counter`，写入 **`timing_info`**。

### 4.3 `search` 与 `--timing` 的关系

- 命令行 **`--timing`** 控制的是**主循环**（Timing / Realtime），并设置 **`search_timing`**。
- **`search(..., timing=cfg.search_timing)`**：为 **Searching** 模块是否输出/使用内部计时；与主循环是否 Timing **同源**，一般与 `--timing` 一致。

### 4.4 累积规则（统计与 CSV）

仅在 **`not cfg.pause`** 时累积：

- **`timing_runs`** 及各阶段毫秒列表（cull / search / model / splat）；
- **泡沫 MAE 列表 `foam_mae_vals`** 与 **foam CSV 行**：额外要求本帧存在 **GT newFoam**（`sample["newfoam"]["positions"]` 至少 1 个点），且 MAE 为**有限数** 才计入平均与写 CSV。

暂停帧仍会跑 `process_frame_timing`（渲染可继续），但**不计入**上述统计，与 **`frame_count`** 行为一致。

### 4.5 退出条件（重要）

- **`--save_result`**：写出 `frames` 张 EXR 后退出（与 Realtime 相同）。
- **`--no_loop`**：当 **`frame_count >= frames`** 时退出（`frame_count` 仅在非暂停时递增），**不必**等满 `timing_runs` 上限。
- **`--loop`（默认）**：还会在 **`timing_runs >= max_timing_frames`** 时退出；`max_timing_frames = max(1, N)`，其中 **`N = --timing_max_frames`**（若 `>0`），否则 **`N = --frames`**。若窗口**一直处于暂停**，`timing_runs` 不增加，进程可能一直不退出；**建议**需要自动结束时配合取消暂停、使用 **`--no_loop`** / **`--save_result`**，或确认 **`--frames` / `--timing_max_frames`** 合理。

| 参数 | 含义 |
|------|------|
| **`--timing_max_frames N`** | 非暂停下 **`timing_runs`** 达到 `N` 后退出；**`N=0`** 表示用 **`--frames`** 计算 `max_timing_frames`（至少为 1）。 |
| **`--frames`** | 与 `timing_max_frames` 联动；亦为 `save_result` 写出张数、`no_loop` 的 `frame_count` 上限。 |

**产出目录**：命令行 **`--output_dir`** 映射为配置里的 **`save_dir`**（默认 `output/realTime`），JSON / CSV / EXR 均相对该路径解析。

### 4.6 输出文件

| 文件 | 说明 |
|------|------|
| **`{save_dir}/RealTimeWater_timing_summary.json`** | 会话汇总：各阶段 **平均毫秒**（仅非暂停帧）、**泡沫密度 MAE 平均**（仅「有 GT newFoam + 有限 MAE」的帧）、帧数、配置等。可用 **`--timing_summary`** 改路径（`save_dir` 由 **`--output_dir`** 指定）。 |
| **`{save_dir}/foam_density_metrics.csv`** | 当帧存在 **`foam_density_mae`** 且 **GT newFoam** 时追加一行：frame、scene、pred/gt 点数、MAE、union 体素数等。 |
| **`--save_result`** | 同 Realtime：`frame_XXXX.exr` 写入 **`--output_dir`**。 |

### 4.7 泡沫密度 MAE（Timing）

- 与数据集 **`newFoamDensity`** 一致：固定 **[-5,5]³** 体素盒、**`compute_Foam_Density`**、默认 **100³** 网格（**`--foam_metric_grid`**）。
- MAE 定义：pred / GT 两套归一化密度在 **\((d_\mathrm{pred}>0)\vee(d_\mathrm{gt}>0)\)** 体素上的 **\|Δ\|** 平均。
- **会话平均**：只对 **有 GT newFoam** 且 **MAE 有限** 的帧取平均（见上文）。

---

## 5. 常用命令示例

```bash
# Realtime + scene 数据（默认 loop，可能长期运行）
python -m src_v3.demo.RealTimeWater --mode scene --data_path <数据根> --scene <场景名> --model <ckpt.pt>

# Timing：跑满 200 个非暂停统计帧后退出并写 JSON（timing_max_frames 用 frames）
python -m src_v3.demo.RealTimeWater --timing --frames 200 --mode scene --data_path <根> --scene <场景名> --model <ckpt.pt>

# 显式指定最多统计 50 帧后退出
python -m src_v3.demo.RealTimeWater --timing --timing_max_frames 50 ...

# 指定汇总 JSON 路径
python -m src_v3.demo.RealTimeWater --timing --timing_summary D:/out/summary.json ...
```

---

## 6. 参数速查（与模式相关）

| 参数 | Realtime | Timing |
|------|----------|--------|
| `--timing` | 关 | 开 |
| `--timing_max_frames` | 忽略 | 建议设置或与 `--frames` 配合退出 |
| `--timing_summary` | 忽略 | 汇总 JSON 路径 |
| `--foam_metric_grid` | 忽略 | MAE 体素分辨率（默认 100） |
| `--save_result` / `--output_dir` | 可选 EXR | 可选 EXR + 默认 JSON/CSV 在 `--output_dir` |

---

## 7. 与 `DATA_SPEC.md` 的关系

样本字段（`positions`、`vel`、`foam`、`newfoam`、`minPos`/`maxPos` 等）见 **`src_v3/data/DATA_SPEC.md`**。Timing 下泡沫 MAE 依赖 **`newfoam`** GT；全泡沫渲染辅助输入见 **`foam`**（`sample_gt_foam_positions_xyz`）。

---

## 8. 版本与维护

行为以 `src_v3/demo/RealTimeWater.py` 源码为准；若增删参数或退出逻辑，请同步更新本文档。
