#!/usr/bin/env python3
"""
视频转文字笔记
使用 whisper.cpp 将 vedio/ 下的 .mp4 视频转录为 Markdown 笔记，输出到 output/ 文件夹。
"""

import argparse
import csv
import subprocess
import sys
from datetime import datetime
from pathlib import Path

# 强制 UTF-8 输出，避免 Windows GBK 终端编码问题
sys.stdout.reconfigure(encoding="utf-8", errors="replace")


# ============================================================
# helpers
# ============================================================

def format_timestamp(seconds: float) -> str:
    """秒数 -> HH:MM:SS 或 MM:SS"""
    h = int(seconds // 3600)
    m = int((seconds % 3600) // 60)
    s = int(seconds % 60)
    if h > 0:
        return f"{h:02d}:{m:02d}:{s:02d}"
    return f"{m:02d}:{s:02d}"


def find_video_files(video_dir: Path) -> list[Path]:
    files = sorted(video_dir.rglob("*.mp4"))
    return [f for f in files if not f.name.startswith(".")]


# ============================================================
# pipeline steps
# ============================================================

def extract_audio(video_path: Path, audio_path: Path, ffmpeg_path: Path) -> None:
    """用 ffmpeg 从视频提取 16kHz 单声道 WAV 音频。"""
    subprocess.run([
        str(ffmpeg_path),
        "-i", str(video_path),
        "-vn",                   # 不要视频流
        "-acodec", "pcm_s16le",  # 16-bit PCM
        "-ar", "16000",          # 16kHz
        "-ac", "1",              # 单声道
        "-y",                    # 覆盖已有文件
        str(audio_path),
    ], check=True, capture_output=True)


def transcribe_with_whisper_cpp(
    audio_path: Path,
    model_path: Path,
    whisper_exe: Path,
    language: "str | None",
    output_dir: Path,
    progress_callback: "callable | None" = None,
) -> "list[dict]":
    """调用 whisper-cli.exe 转录，返回 segment 列表。

    Args:
        progress_callback: 可选，接收 0-100 整数进度百分比
    """
    csv_prefix = output_dir / "temp_whisper"

    cmd = [
        str(whisper_exe),
        "-m", str(model_path),
        "-f", str(audio_path),
        "-ocsv",
        "-of", str(csv_prefix),
        "-pp",
    ]
    if language:
        cmd += ["-l", language]

    proc = subprocess.Popen(
        cmd,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        encoding="utf-8",
        errors="replace",
    )

    import re
    last_progress = ""
    for line in proc.stdout:
        line_stripped = line.strip()
        # 解析 whisper.cpp 的进度百分比行
        m = re.search(r"progress\s*=\s*(\d+)%", line_stripped)
        if m:
            pct = int(m.group(1))
            if progress_callback:
                progress_callback(pct)
        elif line_stripped and ("[" in line_stripped or "ms" in line_stripped):
            # 控制台回显转录片段
            if line_stripped != last_progress:
                print(f"\r  {line_stripped[:80]}", end="", flush=True)
                last_progress = line_stripped
    proc.wait()
    print()

    if proc.returncode != 0:
        raise RuntimeError(f"whisper-cli 退出码 {proc.returncode}")

    # 解析 CSV 输出
    csv_file = Path(f"{csv_prefix}.csv")
    if not csv_file.exists():
        raise FileNotFoundError(f"未找到输出文件: {csv_file}")

    segments = []
    with open(csv_file, "r", encoding="utf-8") as f:
        reader = csv.reader(f)
        _ = next(reader, None)  # 跳过标题行
        for row in reader:
            if len(row) >= 3:
                try:
                    start_ms = int(row[0].strip())
                    end_ms = int(row[1].strip())
                    text = row[2].strip()
                    if text:
                        segments.append({
                            "start": start_ms / 1000.0,
                            "end": end_ms / 1000.0,
                            "text": text,
                        })
                except (ValueError, IndexError):
                    continue

    # 清理临时文件
    csv_file.unlink(missing_ok=True)

    return segments



def build_markdown(video_path: Path, segments: list[dict]) -> str:
    """根据转录 segments 生成 Markdown。"""
    if not segments:
        return f"# {video_path.stem}\n\n*(未识别到语音内容)*\n"

    title = video_path.stem
    duration = segments[-1]["end"]

    md = f"# {title}\n\n"
    md += f"**时长**: {format_timestamp(duration)}\n"
    md += f"**片段数**: {len(segments)}\n"
    md += f"**转码时间**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"
    md += "\n---\n\n"

    # 连续全文
    md += "## 转录全文\n\n"
    full_text = " ".join(seg["text"] for seg in segments)
    md += f"{full_text}\n\n"

    # 带时间戳
    md += "## 带时间戳的转录\n\n"
    for seg in segments:
        ts = format_timestamp(seg["start"])
        md += f"- [{ts}] {seg['text']}\n"

    return md


# ============================================================
# main
# ============================================================

def main():
    parser = argparse.ArgumentParser(description="视频转文字笔记 —— whisper.cpp 引擎")
    parser.add_argument("--model", default="small",
                        choices=["tiny", "tiny.en", "base", "base.en",
                                 "small", "small.en", "medium", "medium.en",
                                 "large-v1", "large-v2", "large-v3", "large-v3-turbo"],
                        help="Whisper 模型（默认 small）")
    parser.add_argument("--language", default=None,
                        help="语言代码 (zh/en/ja...)，不指定则自动检测")
    parser.add_argument("--threads", default=None, type=int,
                        help="线程数（默认 CPU 核心数）")
    parser.add_argument("--skip-existing", action="store_true",
                        help="跳过已有对应 md 的视频")
    args = parser.parse_args()

    base_dir = Path(__file__).resolve().parent
    video_dir = base_dir / "vedio"
    output_dir = base_dir / "output"
    audio_dir = base_dir / "audio_temp"
    tools_dir = base_dir / "tools"

    whisper_exe = tools_dir / "whisper-cpp" / "Release" / "whisper-cli.exe"
    model_path = tools_dir / f"ggml-{args.model}.bin"
    ffmpeg_path = tools_dir / "ffmpeg" / "ffmpeg.exe"

    # 校验依赖
    if not whisper_exe.exists():
        print(f"[X] 未找到 whisper-cli.exe: {whisper_exe}")
        print("  请先将 whisper.cpp 放入 tools/whisper-cpp/")
        return
    if not model_path.exists():
        print(f"[X] 未找到模型文件: {model_path}")
        print("  请先将 ggml 模型下载到 tools/ 目录")
        return
    if not ffmpeg_path.exists():
        print(f"[X] 未找到 ffmpeg.exe: {ffmpeg_path}")
        print("  请先将 ffmpeg.exe 放入 tools/ffmpeg/")
        return

    output_dir.mkdir(exist_ok=True)
    audio_dir.mkdir(exist_ok=True)

    video_files = find_video_files(video_dir)
    if not video_files:
        print("vedio/ 文件夹下未找到 .mp4 文件。")
        return

    print(f"引擎: whisper.cpp  模型: {args.model}")
    print(f"找到 {len(video_files)} 个视频\n")

    for i, video_path in enumerate(video_files, 1):
        stem = video_path.stem
        output_path = output_dir / f"{stem}.md"

        if args.skip_existing and output_path.exists():
            print(f"[{i}/{len(video_files)}] 跳过（已存在）: {video_path.name}")
            continue

        print(f"{'-'*55}")
        print(f"[{i}/{len(video_files)}] {video_path.name}")
        print(f"{'-'*55}")

        # 1. 提取音频
        audio_path = audio_dir / f"{stem}.wav"
        if audio_path.exists():
            print("  [1/3] 使用缓存音频 ...")
        else:
            print("  [1/3] 提取音频 ...")
            try:
                extract_audio(video_path, audio_path, ffmpeg_path)
            except Exception as e:
                print(f"  [X] 音频提取失败: {e}")
                continue

        # 2. 语音识别
        print("  [2/3] 语音识别 ...")
        try:
            segments = transcribe_with_whisper_cpp(
                audio_path, model_path, whisper_exe,
                args.language, output_dir
            )
        except Exception as e:
            print(f"  [X] 转录失败: {e}")
            continue

        if not segments:
            print("  [!] 未识别到语音内容")
            continue

        print(f"  [OK] 识别到 {len(segments)} 个片段，总时长 {format_timestamp(segments[-1]['end'])}")

        # 3. 生成 Markdown
        print("  [3/3] 生成笔记 ...")
        try:
            md_content = build_markdown(video_path, segments)
            output_path.write_text(md_content, encoding="utf-8")
        except Exception as e:
            print(f"  [X] 笔记生成失败: {e}")
            continue

        print(f"  [OK] 已保存: output/{output_path.name}")

    print(f"\n{'='*55}")
    print(f"完成 —— 共处理 {len(video_files)} 个视频，输出: {output_dir}")


if __name__ == "__main__":
    main()
