#!/usr/bin/env python3
"""
转录文本整理 —— 将 output/ 中的原始转录 MD 整理为结构化学习笔记。

用法:
    # 处理单个文件
    uv run python summarize.py output/xxx.md

    # 处理整个目录（所有 .md 文件，跳过已有 .note.md 的）
    uv run python summarize.py output/

    # 指定 API key
    uv run python summarize.py output/ --api-key sk-xxx

    # 跳过已生成的笔记
    uv run python summarize.py output/ --skip-existing
"""

import argparse
import logging
import os
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

from summarizer import process_file, summarize_transcript

logger = logging.getLogger("summarize")
logger.setLevel(logging.INFO)
handler = logging.StreamHandler()
handler.setFormatter(logging.Formatter("[%(levelname)s] %(message)s"))
logger.addHandler(handler)

# 在这里填入 API_KEY 
DEFAULT_API_KEY = ""


def find_transcript_files(target: Path) -> list[Path]:
    """找到所有需要处理的转录 .md 文件（排除 .note.md）。"""
    if target.is_file():
        return [target] if target.suffix == ".md" else []
    return sorted(
        p for p in target.rglob("*.md")
        if not p.name.endswith(".note.md") and not p.name.startswith(".")
    )


def main():
    parser = argparse.ArgumentParser(
        description="将转录 MD 整理为结构化学习笔记"
    )
    parser.add_argument(
        "target",
        help="转录文件 .md 或包含转录文件的 output/ 目录",
    )
    parser.add_argument(
        "--api-key",
        default=os.environ.get("DEEPSEEK_API_KEY", DEFAULT_API_KEY),
        help="DeepSeek API key（默认读取 DEEPSEEK_API_KEY 环境变量）",
    )
    parser.add_argument(
        "--base-url",
        default="https://api.deepseek.com",
        help="API 地址",
    )
    parser.add_argument(
        "--model",
        default="deepseek-v4-pro",
        help="模型名称",
    )
    parser.add_argument(
        "--style",
        default="general",
        choices=["general", "stem"],
        help="笔记风格: general (通用) / stem (理工科) (默认: general)",
    )
    parser.add_argument(
        "--skip-existing",
        action="store_true",
        help="跳过已有 .note.md 的文件",
    )
    parser.add_argument(
        "--output-dir",
        default=None,
        help="笔记输出目录（默认与转录文件同目录）",
    )
    args = parser.parse_args()

    target = Path(args.target)
    files = find_transcript_files(target)

    if not files:
        print("未找到转录 .md 文件。")
        return

    print(f"找到 {len(files)} 个转录文件\n")

    success = 0
    for i, md_path in enumerate(files, 1):
        note_path = md_path.with_suffix(".note.md")

        if args.skip_existing and note_path.exists():
            print(f"[{i}/{len(files)}] 跳过（已存在）: {md_path.name}")
            continue

        print(f"{'-'*55}")
        print(f"[{i}/{len(files)}] {md_path.name}")
        print(f"{'-'*55}")

        out_dir = Path(args.output_dir) if args.output_dir else None
        result = process_file(
            md_path,
            api_key=args.api_key,
            base_url=args.base_url,
            model=args.model,
            output_dir=out_dir,
            style=args.style,
        )
        if result:
            print(f"  [OK] 笔记已保存: {result.name}")
            success += 1
        else:
            print(f"  [X] 处理失败")

    print(f"\n{'='*55}")
    print(f"完成 —— 成功 {success}/{len(files)}")


if __name__ == "__main__":
    main()
