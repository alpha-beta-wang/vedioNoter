"""核心处理逻辑：调用 DeepSeek API 将转录文本整理为学习笔记。"""

import logging
from pathlib import Path

from config import get_max_chars_per_chunk
from summarizer.api import create_client, chat
from summarizer.io import read_transcript_text, read_metadata
from summarizer.prompts import get_system_prompt, build_user_prompt

logger = logging.getLogger(__name__)


def _split_text(text: str, max_chars: int | None = None) -> list[str]:
    """按段落边界拆分超长文本，尽量在句号处断开。"""
    if max_chars is None:
        max_chars = get_max_chars_per_chunk()
    if len(text) <= max_chars:
        return [text]

    chunks = []
    paragraphs = text.split("\n")
    current = ""

    for para in paragraphs:
        if len(current) + len(para) + 1 <= max_chars:
            current = (current + "\n" + para).strip()
        else:
            if current:
                chunks.append(current)
            # 如果单个段落就超过上限，按句子拆分
            if len(para) > max_chars:
                sub = _split_by_sentence(para, max_chars)
                chunks.extend(sub)
                current = ""
            else:
                current = para

    if current:
        chunks.append(current)

    return chunks


def _split_by_sentence(text: str, max_chars: int) -> list[str]:
    """按句号/问号/感叹号拆分长文本。"""
    import re

    sentences = re.split(r"(?<=[。！？])", text)
    chunks = []
    current = ""
    for s in sentences:
        if len(current) + len(s) <= max_chars:
            current += s
        else:
            if current:
                chunks.append(current)
            current = s
    if current:
        chunks.append(current)
    return chunks or [text]


def _call_api_for_chunk(
    client, title: str, chunk: str, chunk_idx: int, total: int, style: str = "general",
) -> str:
    """对单个文本块调用 API。"""
    if total > 1:
        user_msg = build_user_prompt(chunk, f"{title}（第{chunk_idx + 1}/{total}部分）")
    else:
        user_msg = build_user_prompt(chunk, title)

    return chat(client, get_system_prompt(style), user_msg)


def _merge_chunk_results(results: list[str], title: str, client, style: str = "general") -> str:
    """将多个分块的结果合并整理为统一笔记。"""
    if len(results) == 1:
        return results[0]

    combined = "\n\n---\n\n".join(
        f"## 第{i + 1}部分\n\n{r}" for i, r in enumerate(results)
    )

    merge_prompt = f"""以下是将一个长视频分块整理的笔记合并结果。请将它们整合为一篇完整连贯的学习笔记，去掉重复内容，统一结构。

视频标题：{title}

{combined}
"""
    return chat(client, get_system_prompt(style), merge_prompt)


def summarize_transcript(
    transcript: str,
    title: str = "未命名",
    api_key: str | None = None,
    base_url: str | None = None,
    model: str | None = None,
    style: str = "general",
) -> str:
    """将转录全文整理为结构化学习笔记。

    Args:
        transcript: 语音转录的原始全文
        title: 视频标题
        api_key: DeepSeek API key（默认读取环境变量 DEEPSEEK_API_KEY）
        base_url: API 地址
        model: 模型名称

    Returns:
        整理后的 Markdown 笔记文本
    """
    import os

    api_key = api_key or os.environ.get("DEEPSEEK_API_KEY")
    if not api_key:
        raise ValueError("请提供 api_key 或设置环境变量 DEEPSEEK_API_KEY")

    client = create_client(api_key, base_url)

    chunks = _split_text(transcript)
    logger.info("转录文本共 %d 字符，分为 %d 块处理", len(transcript), len(chunks))

    results = []
    for i, chunk in enumerate(chunks):
        logger.info("处理第 %d/%d 块 (%d 字符)...", i + 1, len(chunks), len(chunk))
        result = _call_api_for_chunk(client, title, chunk, i, len(chunks), style)
        results.append(result)
        logger.info("第 %d 块完成", i + 1)

    if len(results) > 1:
        logger.info("合并 %d 块结果...", len(results))
        final = _merge_chunk_results(results, title, client, style)
    else:
        final = results[0]

    return final


def process_file(
    md_path: Path,
    api_key: str | None = None,
    base_url: str | None = None,
    model: str | None = None,
    output_dir: Path | None = None,
    style: str = "general",
) -> Path | None:
    """处理单个转录 .md 文件：读取、整理、写出笔记。

    Args:
        md_path: 转录 markdown 文件路径
        api_key: DeepSeek API key
        base_url: API 地址
        model: 模型名称
        output_dir: 输出目录（默认与转录文件同目录）

    Returns:
        输出文件路径；失败返回 None
    """
    transcript = read_transcript_text(md_path)
    if not transcript:
        logger.warning("无法从 %s 中提取转录文本，跳过", md_path.name)
        return None

    meta = read_metadata(md_path)
    title = meta.get("title", md_path.stem)

    logger.info("开始整理: %s (%d 字符)", title, len(transcript))

    try:
        note = summarize_transcript(transcript, title, api_key, base_url, model, style)
    except Exception as e:
        logger.error("API 调用失败: %s", e)
        return None

    # 确定输出路径
    out_dir = output_dir or md_path.parent
    out_path = out_dir / f"{md_path.stem}.note.md"
    out_path.write_text(note, encoding="utf-8")
    logger.info("笔记已保存: %s", out_path.name)
    return out_path
