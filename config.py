"""从 config.yaml 加载项目配置，支持环境变量覆盖。"""

import os
from pathlib import Path

import yaml

_CONFIG_PATH = Path(__file__).resolve().parent / "config.yaml"

with open(_CONFIG_PATH, "r", encoding="utf-8") as _f:
    _cfg = yaml.safe_load(_f)


# -----------------------------------------------------------
# DeepSeek API
# -----------------------------------------------------------

def get_api_key() -> str:
    """返回 DeepSeek API key。优先环境变量，其次 config.yaml。"""
    return os.environ.get("DEEPSEEK_API_KEY") or _cfg["deepseek"]["api_key"] or None


def get_api_base_url() -> str:
    return _cfg["deepseek"]["base_url"]


def get_llm_model() -> str:
    return _cfg["deepseek"]["model"]


def get_max_chars_per_chunk() -> int:
    return _cfg["deepseek"]["max_chars_per_chunk"]


# -----------------------------------------------------------
# Whisper
# -----------------------------------------------------------

def get_whisper_model() -> str:
    return _cfg["whisper"]["model"]


def get_available_whisper_models() -> list[str]:
    return list(_cfg["whisper"]["available_models"])


# -----------------------------------------------------------
# Keyframe extraction
# -----------------------------------------------------------

def get_scene_threshold() -> float:
    return _cfg["keyframe"]["scene_threshold"]


def get_max_keyframes() -> int:
    return _cfg["keyframe"]["max_frames"]


# -----------------------------------------------------------
# Server
# -----------------------------------------------------------

def get_server_host() -> str:
    return os.environ.get("FLASK_HOST") or _cfg["server"]["host"]


def get_server_port() -> int:
    env_port = os.environ.get("FLASK_PORT")
    if env_port:
        return int(env_port)
    return _cfg["server"]["port"]
