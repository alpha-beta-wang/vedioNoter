"""
summarizer —— 将视频转录文本整理为结构化学习笔记

用法:
    from summarizer import summarize_transcript

    note = summarize_transcript(transcript_text, video_title="...")
    # 或从文件直接处理:
    from summarizer import process_file
    process_file("output/xxx.md", api_key="...")
"""

from summarizer.processor import summarize_transcript, process_file  # noqa: F401

__all__ = ["summarize_transcript", "process_file"]
