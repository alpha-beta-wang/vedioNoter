#!/usr/bin/env bash
# ============================================================
# 视频转文字笔记 —— 一键环境配置脚本
# 使用 uv 管理 Python 虚拟环境，自动下载 whisper.cpp / ffmpeg / 模型
# ============================================================
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$SCRIPT_DIR"

# ---------- 颜色输出 ----------
RED='\033[0;31m'; GREEN='\033[0;32m'; CYAN='\033[0;36m'; NC='\033[0m'
info()  { echo -e "${CYAN}[INFO]${NC}  $*"; }
ok()    { echo -e "${GREEN}[OK]${NC}   $*"; }
err()   { echo -e "${RED}[ERR]${NC}  $*"; exit 1; }

# ---------- 平台检测 ----------
case "$(uname -s)" in
    Linux*)   OS=linux;;
    Darwin*)  OS=macos;;
    MINGW*|MSYS*|CYGWIN*) OS=windows;;
    *)        err "不支持的操作系统: $(uname -s)";;
esac
info "检测到平台: $OS"

# ---------- 可配置参数 ----------
MODEL="${1:-small}"                         # 默认模型: small
WHISPER_VERSION="v1.8.4"                    # whisper.cpp 版本
WHISPER_URL_BASE="https://github.com/ggml-org/whisper.cpp/releases/download/${WHISPER_VERSION}"
MODEL_URL_BASE="https://huggingface.co/ggerganov/whisper.cpp/resolve/main"

# ============================================================
# Step 1: 安装 uv
# ============================================================
info "Step 1/5: 检查 uv ..."
if command -v uv &>/dev/null; then
    ok "uv 已安装: $(uv --version 2>&1)"
else
    info "正在安装 uv ..."
    if [ "$OS" = "windows" ]; then
        powershell -Command "irm https://astral.sh/uv/install.ps1 | iex" 2>/dev/null || \
            err "uv 安装失败，请手动安装: https://docs.astral.sh/uv/getting-started/installation/"
    else
        curl -LsSf https://astral.sh/uv/install.sh | sh 2>/dev/null || \
            err "uv 安装失败，请手动安装: https://docs.astral.sh/uv/getting-started/installation/"
    fi
    # 刷新 PATH
    export PATH="$HOME/.local/bin:$HOME/.cargo/bin:$PATH"
    ok "uv 安装完成: $(uv --version 2>&1)"
fi

# ============================================================
# Step 2: 创建 Python 虚拟环境
# ============================================================
info "Step 2/5: 创建 Python 虚拟环境 ..."
uv venv --python 3.11 2>/dev/null || uv venv 2>/dev/null || \
    err "创建虚拟环境失败"
ok ".venv 已就绪"

# 安装 Python 依赖（当前版本仅需标准库，预留扩展）
if [ -f requirements.txt ] && grep -q '[a-zA-Z]' requirements.txt 2>/dev/null; then
    uv pip install -r requirements.txt
fi
ok "Python 依赖安装完成"

# ============================================================
# Step 3: 下载 whisper.cpp
# ============================================================
info "Step 3/5: 下载 whisper.cpp (${WHISPER_VERSION}) ..."
WHISPER_DIR="$SCRIPT_DIR/tools/whisper-cpp"
WHISPER_EXE="$WHISPER_DIR/Release/whisper-cli"

if [ "$OS" = "windows" ]; then
    WHISPER_EXE="${WHISPER_EXE}.exe"
    WHISPER_ZIP="whisper-bin-x64.zip"
else
    WHISPER_ZIP="whisper-bin-x64"  # Linux/macOS 使用不同的包名
fi

if [ -f "$WHISPER_EXE" ]; then
    ok "whisper.cpp 已存在，跳过下载"
else
    mkdir -p "$WHISPER_DIR"
    WHISPER_URL="${WHISPER_URL_BASE}/${WHISPER_ZIP}"

    # 对 macOS 做特殊处理
    if [ "$OS" = "macos" ]; then
        WHISPER_URL="${WHISPER_URL_BASE}/whisper-bin-arm64.zip"
    fi

    info "下载 $WHISPER_URL ..."
    curl -L -o "$SCRIPT_DIR/tools/whisper-cpp.zip" "$WHISPER_URL" || \
        err "whisper.cpp 下载失败"

    unzip -o "$SCRIPT_DIR/tools/whisper-cpp.zip" -d "$WHISPER_DIR" 2>/dev/null || \
        tar -xzf "$SCRIPT_DIR/tools/whisper-cpp.zip" -C "$WHISPER_DIR" 2>/dev/null || \
        err "解压 whisper.cpp 失败"

    rm -f "$SCRIPT_DIR/tools/whisper-cpp.zip"

    # 确保可执行
    chmod +x "$WHISPER_EXE" 2>/dev/null || true
    ok "whisper.cpp 下载完成"
fi

# ============================================================
# Step 4: 下载 Whisper 模型
# ============================================================
info "Step 4/5: 下载 Whisper 模型 (ggml-${MODEL}.bin) ..."
MODEL_PATH="$SCRIPT_DIR/tools/ggml-${MODEL}.bin"

if [ -f "$MODEL_PATH" ]; then
    ok "模型 ggml-${MODEL}.bin 已存在，跳过下载"
else
    MODEL_URL="${MODEL_URL_BASE}/ggml-${MODEL}.bin"
    info "下载 $MODEL_URL (~500MB-3GB，请耐心等待)..."
    curl -L -o "$MODEL_PATH" "$MODEL_URL" || \
        err "模型下载失败，请检查网络或手动下载到 $MODEL_PATH"

    ok "模型下载完成 ($(du -h "$MODEL_PATH" 2>/dev/null | cut -f1 || echo 'ok'))"
fi

# ============================================================
# Step 5: 下载 ffmpeg
# ============================================================
info "Step 5/5: 下载 ffmpeg ..."
FFMPEG_DIR="$SCRIPT_DIR/tools/ffmpeg"
FFMPEG_EXE="$FFMPEG_DIR/ffmpeg"

if [ "$OS" = "windows" ]; then
    FFMPEG_EXE="${FFMPEG_EXE}.exe"
fi

if [ -f "$FFMPEG_EXE" ]; then
    ok "ffmpeg 已存在，跳过下载"
else
    mkdir -p "$FFMPEG_DIR"

    if [ "$OS" = "windows" ]; then
        FFMPEG_URL="https://www.gyan.dev/ffmpeg/builds/ffmpeg-release-essentials.zip"
        info "下载 $FFMPEG_URL ..."
        curl -L -o "$SCRIPT_DIR/tools/ffmpeg.zip" "$FFMPEG_URL" || \
            err "ffmpeg 下载失败"

        unzip -o "$SCRIPT_DIR/tools/ffmpeg.zip" -d "$SCRIPT_DIR/tools/ffmpeg_tmp" 2>/dev/null || \
            err "解压 ffmpeg 失败"

        # 找到 ffmpeg.exe 并复制
        FFMPEG_SRC=$(find "$SCRIPT_DIR/tools/ffmpeg_tmp" -name "ffmpeg.exe" -type f 2>/dev/null | head -1)
        if [ -z "$FFMPEG_SRC" ]; then
            err "在解压包中未找到 ffmpeg.exe"
        fi
        cp "$FFMPEG_SRC" "$FFMPEG_DIR/"
        rm -rf "$SCRIPT_DIR/tools/ffmpeg_tmp" "$SCRIPT_DIR/tools/ffmpeg.zip"
    elif [ "$OS" = "macos" ]; then
        # macOS 使用 brew 或直接下载静态构建
        if command -v brew &>/dev/null; then
            brew install ffmpeg 2>/dev/null && \
            cp "$(which ffmpeg)" "$FFMPEG_DIR/" || \
            err "ffmpeg 安装失败"
        else
            err "macOS 请先安装 Homebrew，然后重新运行此脚本"
        fi
    else
        # Linux: 从静态构建下载
        FFMPEG_URL="https://johnvansickle.com/ffmpeg/releases/ffmpeg-release-amd64-static.tar.xz"
        info "下载 $FFMPEG_URL ..."
        curl -L -o "$SCRIPT_DIR/tools/ffmpeg.tar.xz" "$FFMPEG_URL" || \
            err "ffmpeg 下载失败"
        tar -xf "$SCRIPT_DIR/tools/ffmpeg.tar.xz" -C "$SCRIPT_DIR/tools/ffmpeg_tmp" 2>/dev/null || \
            err "解压 ffmpeg 失败"
        FFMPEG_SRC=$(find "$SCRIPT_DIR/tools/ffmpeg_tmp" -name "ffmpeg" -type f 2>/dev/null | head -1)
        cp "$FFMPEG_SRC" "$FFMPEG_DIR/"
        rm -rf "$SCRIPT_DIR/tools/ffmpeg_tmp" "$SCRIPT_DIR/tools/ffmpeg.tar.xz"
    fi

    chmod +x "$FFMPEG_EXE" 2>/dev/null || true
    ok "ffmpeg 安装完成"
fi

# ============================================================
# 完成
# ============================================================
echo ""
echo -e "${GREEN}============================================================${NC}"
echo -e "${GREEN}  环境配置完成！${NC}"
echo -e "${GREEN}============================================================${NC}"
echo ""
echo "  目录结构:"
echo "    tools/whisper-cpp/  - whisper.cpp 引擎"
echo "    tools/ggml-${MODEL}.bin - Whisper 模型"
echo "    tools/ffmpeg/       - ffmpeg 音频提取"
echo "    .venv/              - Python 虚拟环境"
echo "    vedio/              - 放入待转录的 .mp4 视频"
echo "    output/             - 转录结果 .md 输出"
echo ""
echo -e "  运行转录:"
echo -e "    ${CYAN}uv run python transcribe.py --language zh${NC}"
echo ""
echo "  更多选项:"
echo "    uv run python transcribe.py --model medium --language zh"
echo "    uv run python transcribe.py --help"
echo ""
