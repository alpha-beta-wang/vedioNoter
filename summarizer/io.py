"""文件读写操作。"""

import re
from pathlib import Path


def read_transcript_text(md_path: Path) -> str | None:
    """从转录 markdown 文件中提取「转录全文」部分的纯文本。

    Args:
        md_path: 转录 .md 文件路径

    Returns:
        转录纯文本；如无法解析则返回 None
    """
    if not md_path.exists():
        return None

    content = md_path.read_text(encoding="utf-8")

    # 提取 "转录全文" 部分（在两段 "---" 之后）
    # 结构: # Title \n **...** \n --- \n ## 转录全文 \n <text> \n ## 带时间戳...
    match = re.search(
        r"##\s*转录全文\s*\n+(.+?)(?=\n##\s*带时间戳)",
        content,
        re.DOTALL,
    )
    if match:
        return match.group(1).strip()

    # 回退：提取第一个 --- 之后的所有文本
    parts = content.split("---", 1)
    if len(parts) > 1:
        text = parts[1].strip()
        # 去掉时间戳部分
        text = re.sub(r"\n##\s*带时间戳的转录.*", "", text, flags=re.DOTALL)
        # 去掉 "转录全文" 标题
        text = re.sub(r"^##\s*转录全文\s*\n*", "", text)
        return text.strip()

    return None


def write_note(md_path: Path, note_content: str) -> Path:
    """将整理后的笔记写入文件（与原始转录文件同目录，文件名加 .note 后缀）。

    Args:
        md_path: 原始转录 .md 文件路径
        note_content: 整理后的笔记内容

    Returns:
        输出文件路径 (.note.md)
    """
    output_path = md_path.with_suffix(".note.md")
    output_path.write_text(note_content, encoding="utf-8")
    return output_path


def read_metadata(md_path: Path) -> dict:
    """从转录 markdown 中读取元数据（时长、片段数等）。

    Returns:
        dict，键如 title, duration, segments
    """
    if not md_path.exists():
        return {}

    content = md_path.read_text(encoding="utf-8")
    meta = {}

    # 标题（第一行 # 开头）
    m = re.match(r"^#\s+(.+)$", content, re.MULTILINE)
    if m:
        meta["title"] = m.group(1).strip()

    # 时长
    m = re.search(r"\*\*时长\*\*:\s*(.+)", content)
    if m:
        meta["duration"] = m.group(1).strip()

    # 片段数
    m = re.search(r"\*\*片段数\*\*:\s*(.+)", content)
    if m:
        meta["segments"] = m.group(1).strip()

    return meta
