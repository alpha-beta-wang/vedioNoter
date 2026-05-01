"""Flask 后端 —— 视频上传、转码、笔记整理的 Web API。"""

import json
import os
import re
import shutil
import sys
from pathlib import Path

# 将项目根目录加入 sys.path
PROJECT_DIR = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(PROJECT_DIR))

from flask import Flask, request, jsonify, send_from_directory, send_file
from flask_cors import CORS

from web.backend.tasks import (
    get_task,
    start_summarization,
    start_transcription,
    tasks as task_store,
)

app = Flask(__name__, static_folder=None)
CORS(app)

VEDIO_DIR = PROJECT_DIR / "vedio"
OUTPUT_DIR = PROJECT_DIR / "output"
VEDIO_DIR.mkdir(exist_ok=True)
OUTPUT_DIR.mkdir(exist_ok=True)


# ============================================================
# 视频管理
# ============================================================

@app.route("/api/videos", methods=["GET"])
def list_videos():
    """列出所有视频及其状态。"""
    videos = []
    for f in sorted(VEDIO_DIR.glob("*.mp4")):
        if f.name.startswith("."):
            continue
        md = OUTPUT_DIR / f"{f.stem}.md"
        note = OUTPUT_DIR / f"{f.stem}.note.md"
        videos.append({
            "name": f.name,
            "size_mb": round(f.stat().st_size / 1024 / 1024, 1),
            "has_transcript": md.exists(),
            "has_note": note.exists(),
        })
    return jsonify(videos)


@app.route("/api/upload", methods=["POST"])
def upload_video():
    """上传视频文件。"""
    if "file" not in request.files:
        return jsonify({"error": "未选择文件"}), 400

    file = request.files["file"]
    if not file.filename.endswith(".mp4"):
        return jsonify({"error": "仅支持 .mp4 文件"}), 400

    path = VEDIO_DIR / file.filename
    file.save(str(path))
    return jsonify({
        "name": file.filename,
        "size_mb": round(path.stat().st_size / 1024 / 1024, 1),
    })


@app.route("/api/videos/<name>", methods=["DELETE"])
def delete_video(name: str):
    """删除视频及相关文件。"""
    stem = Path(name).stem
    for d in [VEDIO_DIR, OUTPUT_DIR, PROJECT_DIR / "audio_temp"]:
        for ext in [".mp4", ".md", ".note.md", ".wav"]:
            p = d / f"{stem}{ext}"
            if p.exists():
                p.unlink()
    return jsonify({"ok": True})


# ============================================================
# 转码 & 笔记
# ============================================================

@app.route("/api/transcribe/<name>", methods=["POST"])
def start_transcribe(name: str):
    """启动转录任务。"""
    video_path = VEDIO_DIR / name
    if not video_path.exists():
        return jsonify({"error": "视频不存在"}), 404

    data = request.get_json(silent=True) or {}
    model = data.get("model", "small")
    lang = data.get("language") or None
    language = lang if lang and lang != "auto" else None

    task_id = start_transcription(video_path, PROJECT_DIR, model, language or None)
    return jsonify({"task_id": task_id})


@app.route("/api/summarize/<name>", methods=["POST"])
def start_summarize(name: str):
    """启动笔记整理任务。"""
    md_path = OUTPUT_DIR / name
    if not md_path.exists():
        md_path = OUTPUT_DIR / f"{Path(name).stem}.md"
    if not md_path.exists():
        return jsonify({"error": "转录文件不存在，请先转码"}), 404

    data = request.get_json(silent=True) or {}
    api_key = data.get("api_key") or os.environ.get(
        "DEEPSEEK_API_KEY", ""
    )

    task_id = start_summarization(md_path, PROJECT_DIR, api_key)
    return jsonify({"task_id": task_id})


@app.route("/api/tasks/<task_id>", methods=["GET"])
def poll_task(task_id: str):
    """轮询任务状态。"""
    task = get_task(task_id)
    if not task:
        return jsonify({"error": "任务不存在"}), 404
    return jsonify(task)


@app.route("/api/transcript/<name>", methods=["GET"])
def get_transcript(name: str):
    """获取转录文本。"""
    md_path = OUTPUT_DIR / f"{Path(name).stem}.md"
    if not md_path.exists():
        return jsonify({"error": "转录不存在"}), 404

    raw = md_path.read_text(encoding="utf-8")

    # 返回结构化数据：分离全文和时间戳
    full_text = raw
    ts_section = ""

    # 提取时间戳部分
    m = re.search(r"(##\s*带时间戳的转录.*)", raw, re.DOTALL)
    if m:
        ts_section = m.group(1)
        full_text = raw[: m.start()].strip()

    return jsonify({"full_text": full_text, "timestamped": ts_section, "raw": raw})


@app.route("/api/note/<name>", methods=["GET"])
def get_note(name: str):
    """获取整理后的学习笔记。"""
    stem = Path(name).stem
    note_path = OUTPUT_DIR / f"{stem}.note.md"
    if not note_path.exists():
        return jsonify({"error": "笔记不存在"}), 404

    raw = note_path.read_text(encoding="utf-8")
    return jsonify({"content": raw})


# ============================================================
# 静态文件（前端构建产物）
# ============================================================

FRONTEND_DIST = PROJECT_DIR / "web" / "frontend" / "dist"

@app.route("/", defaults={"path": ""})
@app.route("/<path:path>")
def serve_frontend(path: str):
    """Serve React frontend or fallback to index.html."""
    if not FRONTEND_DIST.exists():
        return jsonify({"message": "前端尚未构建，请运行 cd web/frontend && npm run build"}), 200

    file_path = FRONTEND_DIST / path
    if path and file_path.exists() and file_path.is_file():
        return send_file(str(file_path))

    # SPA fallback
    return send_file(str(FRONTEND_DIST / "index.html"))


def main():
    print(f"启动服务: http://localhost:8765")
    print(f"视频目录: {VEDIO_DIR}")
    print(f"输出目录: {OUTPUT_DIR}")
    app.run(host="0.0.0.0", port=8765, debug=True)


if __name__ == "__main__":
    main()
