# Searching — 邻域搜索与位置/速度协方差

- **输入**：FluidDataset 的 `positions` [N, 3]、可选 `vel` [N, 3]，以及 `radius`（搜索半径）。可选 `pos_scale` 用于位置协方差归一化（如取 `radius`）。
- **输出**：
  - 边连接 `(src, dst)`：每条边表示 `src[i]` 与 `dst[i]` 在半径内相邻。
  - `cov_pos` [N, 9]：位置协方差（3×3 行优先展平）；计算时可用 `pos_scale` 对相对位置做归一化。
  - `cov_vel` [N, 9]：速度协方差（3×3 行优先展平）；未提供 `vel` 时为零。飞溅粒子（邻居数低于 `splash_threshold`）协方差用单位矩阵（3×3 展平为 9）。

## 协方差计算公式

对每个粒子 $i$，设其邻域为 $\mathcal{N}(i) = \{ j : (i,j) \in \text{edges} \}$，$|\mathcal{N}(i)| = n_i$。

1. **质心**（邻域位置均值）：
   $$
   \boldsymbol{\mu}_i = \frac{1}{n_i} \sum_{j \in \mathcal{N}(i)} \boldsymbol{p}_j
   $$

2. **位置协方差**（3×3，展平为 9 通道）：令 $\boldsymbol{d}_p = \boldsymbol{p}_j - \boldsymbol{\mu}_i$，若提供 `pos_scale` 则 $\boldsymbol{d}_p \gets \boldsymbol{d}_p / \texttt{pos\_scale}$，再计算：
   $$
   \mathbf{C}^{\mathrm{pos}}_i = \frac{1}{n_i} \sum_{j \in \mathcal{N}(i)} \boldsymbol{d}_p \boldsymbol{d}_p^\top
   $$
   输出 `cov_pos` 为 $\mathbf{C}^{\mathrm{pos}}_i$ 行优先展成 9 维。**速度协方差** $\mathbf{C}^{\mathrm{vel}}_i$ 同理，用速度质心与相对速度，输出 `cov_vel` [N, 9]；未提供速度时 `cov_vel` 为零。

3. **飞溅粒子**：若 $n_i < \texttt{splash\_threshold}$，令 $\mathbf{C}_i = \mathbf{I}$，保证数值稳定。

4. **正则化**：最终输出为 $\mathbf{C}_i + \varepsilon \mathbf{I}$（$\varepsilon$ 默认 1e-6），避免奇异。

## 用法

```python
from src_v3.core.Searching import search

# positions [N, 3]，可选 vel [N, 3]
src, dst, cov_pos, cov_vel = search(positions, radius=0.05, vel=vel, pos_scale=0.05)
# src, dst: [E]；cov_pos, cov_vel: [N, 9]
```

单独用半径图或协方差（可指定 `method`）：

```python
from src_v3.core.Searching import radius_graph, covariance_matrices, COV_METHOD_DEFAULT

src, dst = radius_graph(positions, radius)
cov_pos, cov_vel = covariance_matrices(positions, src, dst, vel=vel, pos_scale=radius, method=COV_METHOD_DEFAULT)
```

## 协方差计算方法（cov_method / method）

协方差计算方式可通过整数 `method` 选择，在 `search(..., cov_method=...)` 或全局参数 `--cov_method` 中指定。常量与含义见 **covariance.py 模块顶部注释**：

- **0**（默认）：质心 + 相对向量外积，位置可选 `pos_scale` 归一化。
- **1、2**：预留自定义实现（TODO），在 `covariance.py` 中实现 `_covariance_custom_1` / `_covariance_custom_2` 并注册即可。

## 依赖

- `scipy`（用于 `scipy.spatial.cKDTree` 半径搜索）
