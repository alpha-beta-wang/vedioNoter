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

from config import get_api_key, get_server_host, get_server_port
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
    extract_frames = data.get("extract_frames", False)

    task_id = start_transcription(video_path, PROJECT_DIR, model, language or None, extract_frames)
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
    api_key = data.get("api_key") or get_api_key()
    style = data.get("style") or "general"

    task_id = start_summarization(md_path, PROJECT_DIR, api_key, style)
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
# 关键帧图片
# ============================================================

FRAMES_DIR = OUTPUT_DIR / "frames"


@app.route("/api/frames/<path:subpath>")
def serve_frame(subpath: str):
    """提供提取的关键帧图片。"""
    file_path = FRAMES_DIR / subpath
    if not file_path.exists() or not file_path.is_file():
        return jsonify({"error": "图片不存在"}), 404
    return send_file(str(file_path))


# ============================================================
# 桌面与系统管理接口 (Desktop API)
# ============================================================

@app.route("/api/health", methods=["GET"])
def health_check():
    """桌面端探针接口。"""
    return jsonify({"status": "ok", "platform": sys.platform})


@app.route("/api/config", methods=["GET"])
def get_config():
    """获取系统当前配置。"""
    from config import get_raw_config
    return jsonify(get_raw_config())


@app.route("/api/config", methods=["POST"])
def update_config():
    """更新配置并写回 config.yaml。"""
    from config import get_raw_config, save_config
    data = request.get_json(silent=True) or {}
    current = get_raw_config()
    for section in ["deepseek", "whisper", "keyframe", "server"]:
        if section in data and isinstance(data[section], dict):
            current.setdefault(section, {}).update(data[section])
    save_config(current)
    return jsonify({"ok": True, "config": current})


@app.route("/api/open-folder", methods=["POST"])
def open_folder():
    """跨平台在系统文件管理器中打开或定位目录/文件（Win Explorer / macOS Finder）。"""
    import platform
    import subprocess

    data = request.get_json(silent=True) or {}
    target_type = data.get("type", "output")
    file_name = data.get("name")

    if target_type == "output":
        target = OUTPUT_DIR
    elif target_type == "vedio":
        target = VEDIO_DIR
    else:
        target = PROJECT_DIR

    if file_name:
        candidate = target / file_name
        if candidate.exists():
            target = candidate

    try:
        os_name = platform.system()
        if os_name == "Windows":
            if target.is_file():
                subprocess.Popen(["explorer.exe", f"/select,{str(target)}"])
            else:
                subprocess.Popen(["explorer.exe", str(target)])
        elif os_name == "Darwin":  # macOS
            if target.is_file():
                subprocess.Popen(["open", "-R", str(target)])
            else:
                subprocess.Popen(["open", str(target)])
        else:  # Linux
            subprocess.Popen(["xdg-open", str(target.parent if target.is_file() else target)])
        return jsonify({"ok": True})
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/api/import-file", methods=["POST"])
def import_local_file():
    """桌面端直接导入本地视频文件（复制到 vedio 目录）。"""
    data = request.get_json(silent=True) or {}
    file_path = data.get("path")
    if not file_path:
        return jsonify({"error": "缺少文件路径"}), 400

    src = Path(file_path)
    if not src.exists() or not src.is_file():
        return jsonify({"error": "指定的文件不存在"}), 404

    allowed_exts = {".mp4", ".mov", ".mkv", ".flv", ".webm", ".avi"}
    if src.suffix.lower() not in allowed_exts:
        return jsonify({"error": f"不支持的文件格式: {src.suffix}"}), 400

    dest = VEDIO_DIR / src.name
    if not dest.exists():
        shutil.copy2(str(src), str(dest))

    return jsonify({
        "name": dest.name,
        "size_mb": round(dest.stat().st_size / 1024 / 1024, 1),
    })


@app.route("/api/system-info", methods=["GET"])
def system_info():
    """返回操作系统、硬件及底层推理工具状态。"""
    import platform
    whisper_exe = PROJECT_DIR / "tools" / "whisper-cpp" / "Release" / ("whisper-cli.exe" if platform.system() == "Windows" else "whisper-cli")
    ffmpeg_exe = PROJECT_DIR / "tools" / "ffmpeg" / ("ffmpeg.exe" if platform.system() == "Windows" else "ffmpeg")

    return jsonify({
        "os": platform.system(),
        "arch": platform.machine(),
        "cpu_count": os.cpu_count() or 1,
        "whisper_ready": whisper_exe.exists() or bool(shutil.which("whisper-cli")),
        "ffmpeg_ready": ffmpeg_exe.exists() or bool(shutil.which("ffmpeg")),
        "models": [p.stem.replace("ggml-", "") for p in (PROJECT_DIR / "tools").glob("ggml-*.bin")],
    })


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
    host = get_server_host()
    port = get_server_port()
    print(f"启动服务: http://localhost:{port}")
    print(f"视频目录: {VEDIO_DIR}")
    print(f"输出目录: {OUTPUT_DIR}")
    app.run(host=host, port=port, debug=True)


if __name__ == "__main__":
    main()
