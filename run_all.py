#!/usr/bin/env python3
"""
一键全流程：视频转码 → 笔记整理

依次执行:
  1. transcribe.py  —— 视频 → 语音转录 .md
  2. summarize.py   —— 转录 .md → 结构化学习笔记 .note.md

用法:
    uv run python run_all.py --language zh
    uv run python run_all.py --language zh --model medium --skip-existing
"""

import argparse
import os
import subprocess
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

PROJECT_DIR = Path(__file__).resolve().parent
PYTHON = sys.executable  # 使用同一个 Python 解释器


def run_step(name: str, args: list[str]) -> bool:
    """运行一个子脚本，返回是否成功。"""
    print(f"\n{'#'*60}")
    print(f"#  {name}")
    print(f"{'#'*60}\n")
    cmd = [PYTHON, *args]
    result = subprocess.run(cmd, cwd=str(PROJECT_DIR))
    return result.returncode == 0


def main():
    parser = argparse.ArgumentParser(
        description="视频转文字 + 笔记整理 全流程"
    )
    # 转码参数
    parser.add_argument("--language", default=None,
                        help="语言代码 (zh/en/ja...)")
    parser.add_argument("--model", default="small",
                        help="Whisper 模型大小 (默认 small)")
    parser.add_argument("--threads", default=None, type=int,
                        help="CPU 线程数")
    # 笔记整理参数
    parser.add_argument("--api-key", default=None,
                        help="DeepSeek API key")
    parser.add_argument("--llm-model", default="deepseek-v4-pro",
                        help="LLM 模型名称")
    parser.add_argument("--style", default="general", choices=["general", "stem"],
                        help="笔记风格: general (通用) / stem (理工科) (默认: general)")
    parser.add_argument("--skip-existing", action="store_true",
                        help="跳过已处理的文件")
    parser.add_argument("--skip-summarize", action="store_true",
                        help="只转码，不整理笔记")
    args = parser.parse_args()

    # ---- Step 1: 视频转码 ----
    transcribe_args = [
        str(PROJECT_DIR / "transcribe.py"),
    ]
    if args.language:
        transcribe_args += ["--language", args.language]
    if args.model:
        transcribe_args += ["--model", args.model]
    if args.threads:
        transcribe_args += ["--threads", str(args.threads)]
    if args.skip_existing:
        transcribe_args.append("--skip-existing")

    ok = run_step("Step 1/2: 视频转码 → 语音转录", transcribe_args)
    if not ok:
        print("\n[X] 转码步骤失败，终止流程。")
        sys.exit(1)

    # ---- Step 2: 笔记整理 ----
    if args.skip_summarize:
        print("\n[OK] 仅转码模式，流程结束。")
        return

    summarize_args = [
        str(PROJECT_DIR / "summarize.py"),
        str(PROJECT_DIR / "output"),
    ]
    if args.api_key:
        summarize_args += ["--api-key", args.api_key]
    if args.llm_model:
        summarize_args += ["--model", args.llm_model]
    if args.skip_existing:
        summarize_args.append("--skip-existing")
    if args.style:
        summarize_args += ["--style", args.style]

    ok = run_step("Step 2/2: 转录整理 → 学习笔记", summarize_args)
    if not ok:
        print("\n[X] 笔记整理步骤失败。")
        sys.exit(1)

    print(f"\n{'='*60}")
    print("  全流程完成！")
    print(f"  转录原文: {PROJECT_DIR / 'output'}/*.md")
    print(f"  学习笔记: {PROJECT_DIR / 'output'}/*.note.md")
    print(f"{'='*60}")


if __name__ == "__main__":
    main()
