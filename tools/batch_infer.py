import argparse
import os
import sys
import time
from pathlib import Path

import torch

from core.engine import InferenceEngine


DEFAULT_MODEL = "DCNet"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Batch inference tool")
    parser.add_argument("--model", default=DEFAULT_MODEL, help="Model name")
    parser.add_argument("--input_dir", required=True, help="Input image directory")
    parser.add_argument("--output_dir", required=True, help="Output directory")
    parser.add_argument(
        "--device",
        default="auto",
        choices=["cpu", "cuda", "auto"],
        help="Device to use: cpu, cuda, or auto",
    )
    parser.add_argument("--weights", default=None, help="Weights path (optional)")
    return parser.parse_args()


def resolve_device(device_arg: str) -> str:
    if device_arg == "auto":
        return "cuda" if torch.cuda.is_available() else "cpu"
    if device_arg == "cuda":
        if not torch.cuda.is_available():
            print("? CUDA 不可用，请使用 --device cpu 或 --device auto")
            sys.exit(1)
        return "cuda"
    return "cpu"


def count_images(input_dir: str, extensions: set) -> int:
    image_files = []
    for ext in extensions:
        image_files.extend(Path(input_dir).glob(f"*{ext}"))
        image_files.extend(Path(input_dir).glob(f"*{ext.upper()}"))
    return len(set(image_files))


def extract_stats(stats: object, fallback_total: int, elapsed_ms: float) -> tuple:
    total_count = fallback_total
    total_time_ms = None
    avg_time_ms = None

    if isinstance(stats, dict):
        if "total_count" in stats:
            total_count = stats.get("total_count")
        elif "total_images" in stats:
            total_count = stats.get("total_images")
        elif "total" in stats:
            total_count = stats.get("total")

        if "total_time_ms" in stats:
            total_time_ms = stats.get("total_time_ms")
        elif "total_time" in stats:
            total_time_ms = stats.get("total_time") * 1000
        elif "total_time_sec" in stats:
            total_time_ms = stats.get("total_time_sec") * 1000

        if "avg_time_ms" in stats:
            avg_time_ms = stats.get("avg_time_ms")
        elif "avg_ms" in stats:
            avg_time_ms = stats.get("avg_ms")
        elif "avg_time" in stats:
            avg_time_ms = stats.get("avg_time") * 1000

    if total_time_ms is None:
        total_time_ms = elapsed_ms
    if avg_time_ms is None:
        avg_time_ms = total_time_ms / total_count if total_count else 0.0

    return total_count, total_time_ms, avg_time_ms


def main() -> int:
    args = parse_args()

    if not os.path.isdir(args.input_dir):
        print(f"? 输入目录不存在: {args.input_dir}")
        return 1

    os.makedirs(args.output_dir, exist_ok=True)
    device = resolve_device(args.device)

    try:
        engine = InferenceEngine(model_name=args.model, device=device)
        engine.load(weights_path=args.weights)

        fallback_total = count_images(args.input_dir, engine.SUPPORTED_EXTENSIONS)

        start = time.perf_counter()
        stats = engine.predict_batch(
            input_dir=args.input_dir,
            output_dir=args.output_dir,
        )
        elapsed_ms = (time.perf_counter() - start) * 1000

        total_count, total_time_ms, avg_time_ms = extract_stats(
            stats, fallback_total, elapsed_ms
        )

        print("=== 批量推理完成 ===")
        print(f"模型名: {args.model}")
        print(f"设备: {device}")
        print(f"输入目录: {args.input_dir}")
        print(f"输出目录: {args.output_dir}")
        print(f"处理图片总张数: {int(total_count)}")
        print(f"总耗时(秒): {total_time_ms / 1000:.3f}")
        print(f"平均单张耗时(毫秒): {avg_time_ms:.3f}")
        print(
            "输出结构: <output_dir>/mask 下是 *_mask.png，<output_dir>/overlay 下是 *_overlay.png"
        )
        return 0
    except Exception as error:
        print(f"? 批量推理失败: {error}")
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
