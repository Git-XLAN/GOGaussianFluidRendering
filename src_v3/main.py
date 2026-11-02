# -*- coding: utf-8 -*-
"""
src_v3 推理入口（本发行包不含训练）。

Searching 参数（factor、workers、timing）与 infer 共用。
加 --timing 时，调用 Searching 会打印耗时。

默认权重结构：decoder_variant=direct, decoder_layers=256,512, gs_num=24。
"""

import os
import sys
import argparse
import statistics
from collections import defaultdict
from typing import Dict
from pathlib import Path
import numpy as np

project_root = Path(__file__).resolve().parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))


def _parse_grid_dim_arg(value: str):
    text = str(value).strip()
    if not text:
        raise argparse.ArgumentTypeError("GridDim 不能为空")
    for sep in ("x", "X", ";"):
        text = text.replace(sep, ",")
    try:
        values = [int(v.strip()) for v in text.split(",") if v.strip()]
    except ValueError as exc:
        raise argparse.ArgumentTypeError("GridDim 必须是整数，如 100,100,100") from exc
    if len(values) == 1:
        values = values * 3
    if len(values) != 3 or any(v <= 0 for v in values):
        raise argparse.ArgumentTypeError("GridDim 必须为 1 个或 3 个正整数，如 100 或 100,100,100")
    return tuple(values)


def parse_args():
    p = argparse.ArgumentParser(description="GOGaussianFluid v3 推理")
    p.add_argument(
        "--data_path",
        "-d",
        type=str,
        default=str(project_root / "sample_data"),
        help="数据集根目录",
    )
    p.add_argument(
        "--output_dir",
        "-o",
        type=str,
        default=str(project_root / "output"),
        help="输出目录",
    )
    p.add_argument("--factor", "-f", type=float, default=4.0, help="搜索半径 = factor * 粒子半径")
    p.add_argument("--workers", type=int, default=-1, help="Searching 并行数，-1 全部")
    p.add_argument("--timing", action="store_true", help="调用 Searching 时输出耗时")
    p.add_argument("--search_optimized", action="store_true", help="优先使用 Searching 优化后端；未实现则回退默认")
    p.add_argument("--cov_method", type=int, default=0, help="协方差计算方法，见 covariance 模块注释（0=默认，1/2=预留）")
    p.add_argument("--search_exclude_self", type=int, default=1, choices=(0, 1), help="半径图是否排除自身，1=是 0=否")
    p.add_argument("--search_splash_threshold", type=int, default=2, help="邻居数低于此的粒子协方差用单位矩阵")
    p.add_argument("--device", "-D", type=str, default="cuda:0", help="运行设备: cpu 或 cuda 或 cuda:0")
    p.add_argument("--search_cache", action="store_true", default=True, help="启用 Searching 结果缓存（默认开启）")
    p.add_argument("--no_search_cache", action="store_false", dest="search_cache", help="禁用 Searching 结果缓存")
    p.add_argument("--search_cache_dir", type=str, default=None, help="Searching 缓存目录，默认 output_dir/search_cache")
    sub = p.add_subparsers(dest="mode", required=True, help="infer")

    infer_p = sub.add_parser("infer", help="推理")
    infer_p.add_argument("--model", "-m", type=str, required=True, help="模型检查点路径")
    infer_p.add_argument("--scene", type=str, default=None, help="单场景名，不指定则用全部")
    infer_p.add_argument("--gs_num", type=int, default=24, help="每粒子高斯数（须与 checkpoint 一致）")
    infer_p.add_argument(
        "--decoder_variant",
        type=str,
        default="direct",
        choices=["split", "direct"],
        help="解码器变体，须与 checkpoint 一致",
    )
    infer_p.add_argument("--decoder_layers", type=str, default="256,512", help="解码 MLP 隐藏层维度，逗号分隔")
    infer_p.add_argument("--width", type=int, default=256, help="渲染宽度")
    infer_p.add_argument("--height", type=int, default=256, help="渲染高度")
    infer_p.add_argument(
        "--require_mesh",
        action="store_true",
        help="仅索引「同时有 particle 与 mesh」的帧；默认关闭：无 mesh 也可只读粒子帧",
    )
    infer_p.add_argument(
        "--camera_random",
        action="store_true",
        help="随机相机轴/距离；默认关闭，使用固定 bbox 视角",
    )
    infer_p.add_argument("--foam_density_log_alpha", type=float, default=200.0, help="foam log 映射 α")
    infer_p.add_argument("--foam_density_log_d_max", type=float, default=1.0, help="foam log 映射 d_ref")
    infer_p.add_argument(
        "--foam_density_grid_mode",
        type=str,
        default="adaptive",
        choices=["adaptive", "fixed"],
        help="newFoamDensity GridDim 模式",
    )
    infer_p.add_argument(
        "--foam_density_grid_dim",
        type=_parse_grid_dim_arg,
        default=None,
        help="fixed 模式下的固定 GridDim，如 100 或 100,100,100",
    )
    infer_p.add_argument("--foam_sample_factor", type=float, default=1.0, help="泡沫采样 p 乘以该系数")
    infer_p.add_argument(
        "--foam_loss_unculled",
        action="store_true",
        help="泡沫采样用 scale 剔除前的网络输出；默认用 *_culled",
    )
    infer_p.add_argument(
        "--infer_timing_passes",
        type=int,
        default=10,
        help="仅单帧场景有效：整场景重复遍数（第 0 遍写盘，后续遍只统计耗时）",
    )
    infer_p.add_argument("--surface_neighbor_threshold", type=int, default=64, help="≤0 不剔除；>0 启用协方差表面筛选")
    infer_p.add_argument("--surface_flatness_threshold", type=float, default=0.45, help="λ_min/λ_max 阈值")
    infer_p.add_argument("--surface_splash_neighbor", type=int, default=6, help="邻居数 < 此值视为飞溅（表面）")

    return p.parse_args()


def run_infer(args):
    """
    推理入口：构建 SceneDataset 与 InferRunner，遍历所有帧并输出 buffer。
    """
    from src_v3.data import SceneDataset
    from src_v3.training import InferConfig, InferRunner

    if args.scene is None:
        print("infer 模式需要指定 --scene（单场景名）")
        return

    cam_rand = bool(getattr(args, "camera_random", False))
    dataset = SceneDataset(
        root=args.data_path,
        scene=args.scene,
        require_mesh=bool(getattr(args, "require_mesh", False)),
        cache_size=0,
        foam_density_log_alpha=getattr(args, "foam_density_log_alpha", 1.0),
        foam_density_log_d_max=getattr(args, "foam_density_log_d_max", 1.0),
        foam_density_kernel_size=args.factor,
        foam_density_grid_mode=getattr(args, "foam_density_grid_mode", "adaptive"),
        foam_density_grid_dim=getattr(args, "foam_density_grid_dim", None),
        camera_random=cam_rand,
    )
    rm = bool(getattr(args, "require_mesh", False))
    print(
        f"[infer] 使用 SceneDataset, scene={dataset.scene_name}, 帧数={len(dataset)}, "
        f"require_mesh={rm}, camera_random={cam_rand}（默认固定视角；需要随机请加 --camera_random）"
    )

    cfg = InferConfig(
        output_dir=args.output_dir,
        device=args.device,
        search_factor=args.factor,
        search_workers=args.workers,
        search_timing=args.timing,
        search_optimized=args.search_optimized,
        search_cov_method=args.cov_method,
        search_exclude_self=bool(args.search_exclude_self),
        search_splash_threshold=args.search_splash_threshold,
        search_cache=args.search_cache,
        search_cache_dir=args.search_cache_dir,
        net_gs_num=args.gs_num,
        net_decoder_variant=args.decoder_variant,
        net_decoder_layers=[int(x) for x in args.decoder_layers.split(",")],
        width=args.width,
        height=args.height,
        views_per_frame=1,
        surface_neighbor_threshold=args.surface_neighbor_threshold,
        surface_flatness_threshold=args.surface_flatness_threshold,
        surface_splash_neighbor=args.surface_splash_neighbor,
        foam_density_log_alpha=getattr(args, "foam_density_log_alpha", 1.0),
        foam_density_log_d_max=getattr(args, "foam_density_log_d_max", 1.0),
        foam_sample_factor=getattr(args, "foam_sample_factor", 1.0),
        foam_loss_use_culled_gaussians=not bool(getattr(args, "foam_loss_unculled", False)),
    )

    runner = InferRunner(dataset, cfg)
    runner.load_checkpoint(args.model)

    n_frames = len(dataset)
    user_timing_passes = max(1, int(getattr(args, "infer_timing_passes", 10)))
    multi_frame_mode = n_frames > 1
    if multi_frame_mode:
        num_passes = 1
        print(
            f"[infer] 多帧场景 (n={n_frames})：每帧只跑 1 遍，用各帧耗时聚合；"
            f"忽略 --infer_timing_passes={user_timing_passes}"
        )
    else:
        num_passes = user_timing_passes
        print(
            f"[infer] 单帧场景：重复 {num_passes} 遍（第 0 遍写盘，第 1..{num_passes - 1} 遍仅统计耗时）"
        )

    wirtePath = f"{args.output_dir}/infer/{args.scene}"
    os.makedirs(wirtePath, exist_ok=True)

    frame_timings_pass0: Dict[int, Dict[str, float]] = {}
    frame_timings_repeat: Dict[int, list] = defaultdict(list)

    for pass_id in range(num_passes):
        for idx in range(len(dataset)):
            sample = dataset[idx]
            if sample is None:
                continue
            if hasattr(dataset, "update_sample_camera"):
                dataset.update_sample_camera(sample)
            outputs, timing_ms = runner.infer_sample(sample)
            if outputs is None:
                continue

            scene = sample.get("meta_scene", dataset.scene_name)
            frame_id = int(sample.get("meta_frame_id", idx))

            if pass_id == 0:
                frame_timings_pass0[frame_id] = dict(timing_ms)
            else:
                frame_timings_repeat[frame_id].append(dict(timing_ms))

            if pass_id != 0:
                continue

            buf_dir = os.path.join(wirtePath, "buffers")
            os.makedirs(buf_dir, exist_ok=True)

            wx = outputs.get("world_xyz")
            buf_npz = os.path.join(buf_dir, f"frame_{frame_id:05d}.npz")
            normal_np = outputs["normal"].detach().float().cpu().numpy()
            depth_np = outputs["depth"].detach().float().cpu().numpy()
            hit_np = outputs["hit"].detach().float().cpu().numpy()
            vel_np = outputs["vel"].detach().float().cpu().numpy()
            if wx is not None:
                xyz_np = wx.detach().float().cpu().numpy()
                np.savez(buf_npz, normal=normal_np, xyz=xyz_np, hit=hit_np)
            else:
                np.savez(buf_npz, normal=normal_np, hit=hit_np)

            exr_dir = os.path.join(buf_dir, "exr")
            os.makedirs(exr_dir, exist_ok=True)
            exr_base = os.path.join(exr_dir, f"frame_{frame_id:05d}")
            try:
                import pyexr

                pyexr.write(f"{exr_base}_normal.exr", normal_np)
                pyexr.write(f"{exr_base}_depth.exr", depth_np)
                pyexr.write(f"{exr_base}_hit.exr", hit_np)
                pyexr.write(f"{exr_base}_vel.exr", vel_np)
                if wx is not None:
                    pyexr.write(f"{exr_base}_xyz.exr", xyz_np)
            except ImportError:
                print("[infer] 未安装 pyexr，跳过 EXR 写出。安装: pip install pyexr")
            except Exception as e:
                print(f"[infer] 写出 EXR 失败: {e}")

            foam_dir = os.path.join(wirtePath, "foam")
            os.makedirs(foam_dir, exist_ok=True)
            foam_sample = outputs.get("foam_sample")
            if foam_sample is not None and foam_sample.shape[0] > 0:
                foam_pred_path = os.path.join(foam_dir, f"pre_foam_{frame_id:05d}.npz")
                fs = foam_sample.detach().float().cpu().numpy()
                np.savez(foam_pred_path, pos=fs[:, :3], pos_vel=fs)
            else:
                print(f"[infer] frame idx={idx}, scene={scene}, frame_id={frame_id}, foam_sample empty")

            newfoam = sample.get("newfoam") or {}
            gt_newfoam_pos = newfoam.get("positions")
            if gt_newfoam_pos is not None:
                foam_gt_path = os.path.join(foam_dir, f"gt_foam_{frame_id:05d}.npz")
                np.savez(foam_gt_path, pos=np.asarray(gt_newfoam_pos, dtype=np.float32))
            print(
                f"[infer] frame idx={idx}, scene={scene}, frame_id={frame_id}, "
                f"normal_shape={tuple(outputs['normal'].shape)}"
            )

    def _mean(xs):
        return float(sum(xs) / len(xs)) if xs else 0.0

    def _std(xs):
        return float(statistics.stdev(xs)) if len(xs) > 1 else 0.0

    timing_txt = os.path.join(wirtePath, "infer_timings.txt")
    lines = [
        f"scene={args.scene}",
        f"timing_mode={'multi_frame' if multi_frame_mode else 'single_frame_repeats'}",
        f"n_frames_in_dataset={n_frames}",
        f"infer_timing_passes_effective={num_passes}",
        f"infer_timing_passes_requested={user_timing_passes}",
        "units=ms",
    ]

    all_search: list = []
    all_cull: list = []
    all_model: list = []
    all_splat: list = []

    def _cull_ms(tw: Dict) -> float:
        return float(tw.get("cull_ms", 0.0))

    if multi_frame_mode:
        lines.extend(
            [
                "",
                "=== per-frame timings (one pass per frame; aggregated across frames below) ===",
                "frame_id\tsearch_ms\tcull_ms\tmodel_ms\tsplat_ms\tsum_ms",
            ]
        )
        for fid in sorted(frame_timings_pass0.keys()):
            tw = frame_timings_pass0[fid]
            cu = _cull_ms(tw)
            s = tw["search_ms"] + cu + tw["model_ms"] + tw["splat_ms"]
            lines.append(
                f"{fid}\t{tw['search_ms']:.4f}\t{cu:.4f}\t{tw['model_ms']:.4f}\t{tw['splat_ms']:.4f}\t{s:.4f}"
            )
            all_search.append(tw["search_ms"])
            all_cull.append(cu)
            all_model.append(tw["model_ms"])
            all_splat.append(tw["splat_ms"])
        lines.extend(["", "=== aggregate across frames (mean / std over frame samples) ==="])
        if all_search:
            lines.append(f"search_ms_mean={_mean(all_search):.4f}\tsearch_ms_std={_std(all_search):.4f}")
            lines.append(f"cull_ms_mean={_mean(all_cull):.4f}\tcull_ms_std={_std(all_cull):.4f}")
            lines.append(f"model_ms_mean={_mean(all_model):.4f}\tmodel_ms_std={_std(all_model):.4f}")
            lines.append(f"splat_ms_mean={_mean(all_splat):.4f}\tsplat_ms_std={_std(all_splat):.4f}")
            lines.append(
                f"sum_ms_mean={_mean(all_search) + _mean(all_cull) + _mean(all_model) + _mean(all_splat):.4f}"
            )
            lines.append(f"frame_sample_count={len(all_search)}")
        else:
            lines.append("(no timing rows)")
    else:
        lines.extend(
            [
                "",
                "=== warmup (pass 0 only, results saved this pass) ===",
                "frame_id\tsearch_ms\tcull_ms\tmodel_ms\tsplat_ms\tsum_ms",
            ]
        )
        for fid in sorted(frame_timings_pass0.keys()):
            tw = frame_timings_pass0[fid]
            cu = _cull_ms(tw)
            s = tw["search_ms"] + cu + tw["model_ms"] + tw["splat_ms"]
            lines.append(
                f"{fid}\t{tw['search_ms']:.4f}\t{cu:.4f}\t{tw['model_ms']:.4f}\t{tw['splat_ms']:.4f}\t{s:.4f}"
            )

        lines.extend(
            [
                "",
                f"=== aggregate over passes 1..{num_passes - 1} (mean / std per frame); excluded warmup ===",
                "frame_id\tsearch_mean\tsearch_std\tcull_mean\tcull_std\tmodel_mean\tmodel_std\tsplat_mean\tsplat_std\tsum_mean",
            ]
        )
        for fid in sorted(frame_timings_repeat.keys()):
            rows = frame_timings_repeat[fid]
            if not rows:
                continue
            sm = [r["search_ms"] for r in rows]
            cm = [_cull_ms(r) for r in rows]
            mm = [r["model_ms"] for r in rows]
            pm = [r["splat_ms"] for r in rows]
            smean, sstd = _mean(sm), _std(sm)
            cmean, cstd = _mean(cm), _std(cm)
            mmean, mstd = _mean(mm), _std(mm)
            pmean, pstd = _mean(pm), _std(pm)
            sum_mean = smean + cmean + mmean + pmean
            all_search.extend(sm)
            all_cull.extend(cm)
            all_model.extend(mm)
            all_splat.extend(pm)
            lines.append(
                f"{fid}\t{smean:.4f}\t{sstd:.4f}\t{cmean:.4f}\t{cstd:.4f}\t{mmean:.4f}\t{mstd:.4f}\t{pmean:.4f}\t{pstd:.4f}\t{sum_mean:.4f}"
            )

        lines.extend(["", "=== global (single-frame: all post-warmup repeat samples pooled) ==="])
        if all_search:
            g_s = sum(all_search) / len(all_search)
            g_c = sum(all_cull) / len(all_cull) if all_cull else 0.0
            g_m = sum(all_model) / len(all_model)
            g_p = sum(all_splat) / len(all_splat)
            lines.append(f"pooled_sample_count={len(all_search)}")
            lines.append(f"search_ms_mean={g_s:.4f}")
            lines.append(f"cull_ms_mean={g_c:.4f}")
            lines.append(f"model_ms_mean={g_m:.4f}")
            lines.append(f"splat_ms_mean={g_p:.4f}")
            lines.append(f"sum_ms_mean={g_s + g_c + g_m + g_p:.4f}")
        else:
            lines.append("(no post-warmup passes; set --infer_timing_passes >= 2 for repeat statistics)")

    with open(timing_txt, "w", encoding="utf-8") as f:
        f.write("\n".join(lines) + "\n")
    print(f"[infer] timing report written: {timing_txt}")


def main():
    args = parse_args()
    if args.mode == "infer":
        run_infer(args)
    else:
        print("未知 mode:", args.mode)


if __name__ == "__main__":
    main()
