# -*- coding: utf-8 -*-
"""
训练配置

Searching 相关参数与 search() 对应关系：
  search_factor    -> radius = search_factor * 粒子半径
  search_workers   -> workers
  search_timing    -> timing
  search_optimized -> use_optimized
  search_cov_method-> cov_method
  search_exclude_self   -> exclude_self（半径图是否排除自身）
  search_splash_threshold -> splash_threshold（邻居数低于此则协方差用单位矩阵）
  pos_scale 在 trainer 中取 radius，如需单独配置可在此增加 search_pos_scale_factor 等

设备：device 统一控制「模型 + 送入模型的数据」所在设备；Searching 当前为 CPU（numpy/scipy），
  结果会传到 device 上再跑网络。若后续 backend_optimized 支持 GPU，可在同一 device 上执行。
"""

from dataclasses import dataclass, field
from typing import Optional, List


@dataclass
class TrainConfig:
    """训练器配置"""
    output_dir: str = "Output"
    # 实验名/运行ID：用于同一套代码下对比不同超参的训练结果（会作为输出子目录名）
    run_name: Optional[str] = None
    # 运行设备：cpu / cuda / cuda:0 等；模型与输入数据均放在此设备
    device: str = "cpu"
    epochs: int = 50
    batch_size: int = 32
    lr: float = 1e-3
    weight_decay: float = 0.0
    final_lr_ratio: float = 0.0001
    warmup_ratio: float = 0.01
    checkpoint_interval: int = 5000
    log_interval: int = 64
    # 每多少个 epoch 保存一次网络（仅模型），>0 时在对应 epoch 结束后保存；0 表示不按 epoch 保存
    save_epoch_interval: int = 50
    resume: Optional[str] = None
    # True=每步从 [0,n-1] 随机抽一个 idx（可重复）；False=每轮打乱顺序后逐条取（每帧每轮恰好一次）
    random_sample: bool = True

    # ---------- 表面粒子剔除（网络运行前，与 src_v2 detect_surface_particles 一致） ----------
    # surface_neighbor_threshold ≤ 0：不剔除；>0：启用基于「位置协方差特征值扁平度 + 飞溅邻居数」的筛选
    surface_neighbor_threshold: int = 64
    # λ_min/λ_max < flatness_threshold → 几何表面；与 v2 GraphBuilder.surface_threshold 同量级
    surface_flatness_threshold: float = 0.45
    # 邻居数 < 此值视为飞溅粒子（始终作为表面保留）；与 v2 splash_threshold 对应，独立于 search_splash_threshold
    surface_splash_neighbor: int = 6

    # ---------- Searching（与 src_v3.core.Searching.search 参数对应） ----------
    search_factor: float = 3.3          # 搜索半径 = search_factor * 粒子半径
    search_workers: int = -1            # cKDTree 并行数，-1 表示全部
    search_timing: bool = True          # 是否打印 search 各阶段耗时
    search_optimized: bool = False      # True=优先用 backend_optimized，未实现则回退默认
    search_cov_method: int = 0          # 协方差计算方法，见 covariance 模块顶部注释（0=默认，1/2=预留）
    search_exclude_self: bool = True   # 半径图中是否排除自身
    search_splash_threshold: int = 2   # 邻居数低于此的粒子协方差用单位矩阵（与 SPLASH_NEIGHBOR_THRESHOLD 一致）
    # Searching 结果缓存：同一 sample + 同一搜索参数时直接读缓存，避免重复计算
    search_cache: bool = True          # 是否启用 Searching 结果缓存
    search_cache_dir: Optional[str] = None  # 缓存目录，None 时使用 output_dir / "search_cache"

    # ---------- 解码网络（NetConfig，动态控制每层维度） ----------
    # 解码时 scale/offset 使用与位置归一化一致的尺度：kernel_size = radius = search_factor * 粒子半径
    net_gs_num: int = 36                # 每粒子高斯数（对应 v2 GdLayer.maxGSNum）
    net_decoder_variant: str = "split"   # "split"=scale/rotation 在 Split 中计算；"direct"=由 MLP 直接输出
    net_decoder_layers: List[int] = field(default_factory=lambda: [])  # 解码 MLP 隐藏层维度,这里的值无意义
    net_activation: str = "LeakyReLU"
    net_alpha: float = 0.01
    net_dropout: float = 0.0
    net_use_layer_norm: bool = True

    # ---------- GT 生成（normal+depth 渲染）与高斯投影共用相机 ----------
    # GT 后端：mitsuba（当前实现）/ falcor（TODO 占位）
    gt_backend: str = "falcor"
    gt_width: int = 256                 # GT 渲染宽度
    gt_height: int = 256                # GT 渲染高度
    # 相机描述（与 GTGenerator / GaussianProjector 共用）。None 表示使用内置默认
    gt_camera_origin: Optional[List[float]] = None   # [x,y,z]，默认 [0,0,5]
    gt_camera_target: Optional[List[float]] = None   # [x,y,z]，默认 [0,0,0]
    gt_camera_up: Optional[List[float]] = None       # [x,y,z]，默认 [0,1,0]
    gt_camera_fov: Optional[float] = None             # 垂直 fov 度数，默认 60
    single_view: bool = False                         # True 时训练中固定样本初始相机，不做自由更新

    # ---------- 损失权重（总 loss = geometry_weight * 几何损失 + foam_weight * 泡沫损失） ----------
    loss_geometry_weight: float = 1.0   # 几何损失权重
    loss_foam_weight: float = 1.0       # 泡沫损失权重；样本 sph==1（无 pscale）时训练步内会置为 0
    loss_foam_l1_weight: float = 1.0    # 泡沫：全点 L1(pred, GT_y) 的系数（GT_y 为三线性采样密度再 log 映射）
    loss_foam_local_weight: float = 1.0 # 泡沫：GT_y>0 子集上 MSE(L2) 的系数
    # 几何损失内部权重（与 src_v2 LossConfig 一致）
    loss_mask_weight: float = 1.0
    loss_normal_weight: float = 1.0
    loss_depth_weight: float = 1.0
    loss_edge_weight: float = 0.0       # 可选边缘损失，0 表示关闭
    loss_use_blur_loss: bool = True     # mask 用 BCE，否则 L1
    loss_hit_threshold: float = 0.5
    loss_max_depth: float = 50.0

    # newFoamDensity GT：compute_Foam_Density 中 log 映射的 α 与 d_ref（与 foam_density 一致）
    foam_density_log_alpha: float = 1.0
    foam_density_log_d_max: float = 1.0
    # 泡沫监督：True=用 GaussianProjector 内 scale 剔除后的 *_culled；False=用网络输出的全量 foam_prob/foam_prob_raw/gs_pos
    foam_loss_use_culled_gaussians: bool = True


@dataclass
class InferConfig:
    """推理配置（与训练流程类似，但不包含优化器/损失相关参数）"""
    output_dir: str = "OutputInfer"
    device: str = "cpu"

    # Searching 参数
    search_factor: float = 3.3
    search_workers: int = -1
    search_timing: bool = False
    search_optimized: bool = False
    search_cov_method: int = 0
    search_exclude_self: bool = True
    search_splash_threshold: int = 2
    search_cache: bool = True
    search_cache_dir: Optional[str] = None

    # 解码网络（由 NetConfig 使用）
    net_gs_num: int = 36
    net_decoder_variant: str = "split"  # "split" | "direct"
    net_decoder_layers: List[int] = field(default_factory=lambda: [256, 512, 512])
    net_activation: str = "LeakyReLU"
    net_alpha: float = 0.01
    net_dropout: float = 0.0
    net_use_layer_norm: bool = True

    # GS 投影分辨率（与训练中的 gt_width/gt_height 复用）
    width: int = 256
    height: int = 256

    # 视角与表面剔除（逻辑见 TrainConfig 与 src_v3.core.surface_particles）
    views_per_frame: int = 1
    surface_neighbor_threshold: int = 64
    surface_flatness_threshold: float = 0.45
    surface_splash_neighbor: int = 6

    # 与训练 GT 一致：RealTimeWater / 后处理中 foam 逆映射用
    foam_density_log_alpha: float = 1.0
    foam_density_log_d_max: float = 1.0
    # 与 RealTimeWater._sample_new_foam(..., factor) 一致，调大可提高采样率
    foam_sample_factor: float = 1.0
    # 与 TrainConfig 一致：泡沫采样 / 导出的 prob_raw 用 culled 还是网络全量输出
    foam_loss_use_culled_gaussians: bool = True

    # TensorRT 相关（预留）
    use_tensorrt: bool = False
    tensorrt_engine_path: Optional[str] = None

    def to_net_config(self):
        """从 InferConfig 构建 models.NetConfig，供推理时创建模型。"""
        from src_v3.models.config import NetConfig
        layers = getattr(self, "net_decoder_layers", None)
        if layers is None:
            layers = [256, 512, 512]
        return NetConfig(
            decoder_layers=list(layers),
            gs_num=int(getattr(self, "net_gs_num", 36)),
            decoder_variant=str(getattr(self, "net_decoder_variant", "split")),
            activation=str(getattr(self, "net_activation", "LeakyReLU")),
            alpha=float(getattr(self, "net_alpha", 0.01)),
            dropout=float(getattr(self, "net_dropout", 0.0)),
            use_layer_norm=bool(getattr(self, "net_use_layer_norm", True)),
        )
