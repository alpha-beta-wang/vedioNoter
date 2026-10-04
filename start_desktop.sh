#!/usr/bin/env bash
# ============================================================
# Video Extract 桌面客户端一键启动脚本 (macOS & Linux)
# ============================================================
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$SCRIPT_DIR"

echo "======================================================"
echo "   Video Extract 视频文案提取与笔记整理 - 桌面客户端"
echo "======================================================"
echo ""

# 1. 优先启动 Electron 桌面客户端
if [ -d "desktop/node_modules/electron" ]; then
    echo "[启动] 正在以 Electron 原生客户端启动..."
    cd desktop
    npm start
    exit 0
fi

# 2. 备选启动：使用 Python 原生独立窗口启动
echo "[启动] 正在以 Python 原生独立窗口模式启动..."
if [ -f ".venv/bin/python" ]; then
    .venv/bin/python desktop_app.py
elif [ -f ".venv/bin/python3" ]; then
    .venv/bin/python3 desktop_app.py
elif command -v python3 &>/dev/null; then
    python3 desktop_app.py
else
    python desktop_app.py
fi
