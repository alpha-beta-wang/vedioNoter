"""异步任务管理：转录 & 笔记整理，支持进度轮询。"""

import threading
import time
import uuid
from pathlib import Path

# ============================================================
# task store
# ============================================================

tasks: dict[str, dict] = {}
_tasks_lock = threading.Lock()


def _update(task_id: str, **kwargs):
    with _tasks_lock:
        tasks[task_id].update(kwargs)


def get_task(task_id: str) -> dict | None:
    with _tasks_lock:
        return tasks.get(task_id)


# ============================================================
# transcription task
# ============================================================

def start_transcription(
    video_path: Path,
    project_dir: Path,
    model: str = "small",
    language: str | None = None,
) -> str:
    """启动转录任务，返回 task_id。"""
    task_id = str(uuid.uuid4())
    with _tasks_lock:
        tasks[task_id] = {
            "id": task_id,
            "type": "transcribe",
            "video": video_path.name,
            "status": "pending",
            "progress": 0,
            "message": "",
            "output_file": None,
            "error": None,
        }

    thread = threading.Thread(
        target=_run_transcription,
        args=(task_id, video_path, project_dir, model, language),
        daemon=True,
    )
    thread.start()
    return task_id


def _run_transcription(
    task_id: str,
    video_path: Path,
    project_dir: Path,
    model: str,
    language: str | None,
):
    try:
        _update(task_id, status="running", progress=5, message="提取音频...")

        import imageio_ffmpeg
        ffmpeg_path = project_dir / "tools" / "ffmpeg" / "ffmpeg.exe"
        if not ffmpeg_path.exists():
            ffmpeg_path = imageio_ffmpeg.get_ffmpeg_exe()

        from transcribe import extract_audio
        audio_dir = project_dir / "audio_temp"
        audio_dir.mkdir(exist_ok=True)
        audio_path = audio_dir / f"{video_path.stem}.wav"

        if not audio_path.exists():
            extract_audio(video_path, audio_path, ffmpeg_path)

        _update(task_id, progress=25, message="语音识别中...")

        # whisper-cli
        from transcribe import transcribe_with_whisper_cpp

        whisper_exe = project_dir / "tools" / "whisper-cpp" / "Release" / "whisper-cli.exe"
        model_path = project_dir / "tools" / f"ggml-{model}.bin"
        output_dir = project_dir / "output"
        output_dir.mkdir(exist_ok=True)

        def progress_callback(percent: int):
            mapped = 25 + int(percent * 0.65)  # 25 → 90
            _update(task_id, progress=mapped)

        segments = transcribe_with_whisper_cpp(
            audio_path, model_path, whisper_exe, language, output_dir,
            progress_callback=progress_callback,
        )

        _update(task_id, progress=90, message="生成笔记...")

        # build markdown
        from transcribe import build_markdown
        md_content = build_markdown(video_path, segments)
        output_path = output_dir / f"{video_path.stem}.md"
        output_path.write_text(md_content, encoding="utf-8")

        _update(
            task_id,
            status="completed",
            progress=100,
            message="转录完成",
            output_file=str(output_path.name),
        )

    except Exception as e:
        _update(task_id, status="failed", error=str(e), message=f"错误: {e}")


# ============================================================
# summarization task
# ============================================================

def start_summarization(
    md_path: Path,
    project_dir: Path,
    api_key: str,
    style: str = "general",
) -> str:
    """启动笔记整理任务，返回 task_id。"""
    task_id = str(uuid.uuid4())
    with _tasks_lock:
        tasks[task_id] = {
            "id": task_id,
            "type": "summarize",
            "video": md_path.name,
            "status": "pending",
            "progress": 0,
            "message": "",
            "output_file": None,
            "error": None,
        }

    thread = threading.Thread(
        target=_run_summarization,
        args=(task_id, md_path, project_dir, api_key, style),
        daemon=True,
    )
    thread.start()
    return task_id


def _run_summarization(task_id: str, md_path: Path, project_dir: Path, api_key: str, style: str = "general"):
    try:
        _update(task_id, status="running", progress=10, message="读取转录...")

        from summarizer.io import read_transcript_text, read_metadata
        from summarizer.api import create_client, chat
        from summarizer.prompts import get_system_prompt, build_user_prompt

        transcript = read_transcript_text(md_path)
        if not transcript:
            raise ValueError("无法提取转录文本")

        meta = read_metadata(md_path)
        title = meta.get("title", md_path.stem)

        _update(task_id, progress=30, message="调用 AI 整理...")

        client = create_client(api_key)
        user_msg = build_user_prompt(transcript, title)
        note = chat(client, get_system_prompt(style), user_msg)

        _update(task_id, progress=90, message="保存笔记...")

        note_path = md_path.with_suffix(".note.md")
        note_path.write_text(note, encoding="utf-8")

        _update(
            task_id,
            status="completed",
            progress=100,
            message="笔记整理完成",
            output_file=str(note_path.name),
        )

    except Exception as e:
        _update(task_id, status="failed", error=str(e), message=f"错误: {e}")
