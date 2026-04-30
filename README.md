# Video to Markdown —— 视频转文字笔记

将 MP4 视频批量转录为带时间戳的 Markdown 笔记。引擎基于 [whisper.cpp](https://github.com/ggml-org/whisper.cpp)（本地运行，无需联网，无需 GPU），配合 ffmpeg 进行音频预处理。

## 功能

- 自动提取视频中的音频（16kHz 单声道 WAV）
- 使用 Whisper 模型进行语音识别（支持中/英/日等 99 种语言）
- 生成结构化的 Markdown 笔记：
  - **转录全文**：连续段落，便于通读
  - **带时间戳的转录**：每段标注时间码，便于定位回看
- 音频缓存：同一视频的音频只提取一次，重复运行跳过提取步骤
- 已生成笔记跳过：`--skip-existing` 参数避免重复转录

## 文件夹架构

```
vedio_extract/
├── setup.sh                 # 一键环境配置脚本
├── transcribe.py            # 主转码脚本
├── requirements.txt         # Python 依赖（当前仅需标准库）
├── README.md                # 本文件
├── vedio/                   # [用户] 放入待转录的 .mp4 视频
├── output/                  # [输出] 转录结果 .md 笔记
├── audio_temp/              # [缓存] 提取的中间音频文件（WAV）
├── tools/
│   ├── whisper-cpp/Release/ # whisper.cpp 预编译二进制
│   │   └── whisper-cli.exe
│   ├── ffmpeg/              # ffmpeg 静态构建
│   │   └── ffmpeg.exe
│   └── ggml-small.bin       # Whisper 模型文件
└── .venv/                   # Python 虚拟环境（uv 管理）
```

## 环境依赖

### 运行时

| 组件 | 用途 | 来源 |
|---|---|---|
| **Python 3.11+** | 脚本运行环境 | uv 自动管理 |
| **whisper.cpp** | 语音识别引擎 | setup.sh 自动下载 |
| **ffmpeg** | 视频音频提取 | setup.sh 自动下载 |
| **ggml-*.bin** | Whisper 模型权重 | setup.sh 自动下载 |

### Python 依赖

当前版本仅使用 Python 标准库（`argparse`, `csv`, `subprocess`, `pathlib` 等），无需额外 pip 包。`requirements.txt` 保留供未来扩展。

## 快速开始

### 1. 一键配置环境

```bash
# 使用默认 small 模型（推荐，466MB，中英文均表现良好）
bash setup.sh

# 或指定其他模型
bash setup.sh medium       # 更大更准 (1.5GB)
bash setup.sh base         # 更小更快 (148MB)
bash setup.sh large-v3-turbo  # 最强 (1.6GB)
```

`setup.sh` 会自动完成：
- 安装 [uv](https://docs.astral.sh/uv/)（Python 包管理器）
- 创建 Python 3.11 虚拟环境
- 下载 whisper.cpp 预编译二进制（匹配当前操作系统）
- 下载 Whisper 模型文件
- 下载 ffmpeg 静态构建

### 2. 放入视频

将待转录的 `.mp4` 文件放入 `vedio/` 文件夹。

### 3. 运行转录

```bash
# 中文视频（指定语言可提升准确率）
uv run python transcribe.py --language zh

# 自动检测语言
uv run python transcribe.py

# 使用更大模型（更准但更慢）
uv run python transcribe.py --model medium --language zh

# 跳过已有笔记，增量处理
uv run python transcribe.py --language zh --skip-existing
```

### 4. 查看结果

转录笔记输出在 `output/` 目录，文件名与视频同名（`.mp4` → `.md`）。

## 使用说明

```
用法: transcribe.py [选项]

选项:
  --model MODEL      Whisper 模型大小 (默认: small)
                     可选: tiny, base, small, medium, large-v3, large-v3-turbo
                     英文优化版: tiny.en, base.en, small.en, medium.en
  --language LANG    语言代码 (zh/en/ja...)，不指定则自动检测
  --threads N        线程数 (默认: CPU 核心数)
  --skip-existing    跳过 output/ 中已有同名 md 的视频
```

### 模型选择指南

| 模型 | 大小 | 速度 | 准确率 | 适用场景 |
|---|---|---|---|---|
| `tiny` | 78 MB | 极快 | 一般 | 快速预览，短片段 |
| `base` | 148 MB | 快 | 尚可 | 简单对话 |
| `small` | 466 MB | 适中 | 良好 | **推荐默认**，技术内容可用 |
| `medium` | 1.5 GB | 较慢 | 很好 | 需要高准确率的技术讲座 |
| `large-v3-turbo` | 1.6 GB | 慢 | 最佳 | 重要内容归档，专业术语多 |
| `large-v3` | 3.1 GB | 很慢 | 最好 | 极致准确率要求 |

## 代码逻辑

`transcribe.py` 对每个视频执行三步流水线：

### 第 1 步：音频提取 (`extract_audio`)

```python
ffmpeg -i video.mp4 -vn -acodec pcm_s16le -ar 16000 -ac 1 -y audio.wav
```

- 丢弃视频流 (`-vn`)
- 编码为 16-bit PCM
- 重采样到 16kHz（Whisper 要求的采样率）
- 合并为单声道
- 输出 WAV 缓存到 `audio_temp/`

### 第 2 步：语音识别 (`transcribe_with_whisper_cpp`)

```
whisper-cli -m model.bin -f audio.wav -ocsv -of output_prefix
```

- 调用 whisper.cpp 的 CLI 二进制
- 以 CSV 格式输出（`start_ms, end_ms, text`）
- 实时回显进度行
- 解析 CSV，构建 segment 列表（含 `start`, `end`, `text` 字段）

### 第 3 步：生成笔记 (`build_markdown`)

- **转录全文**：将所有 segment 的 `text` 拼接为连续段落
- **带时间戳的转录**：逐行输出 `- [MM:SS] text`
- 写入 `output/<视频名>.md`

### 异常处理

- 音频提取失败 → 打印错误，跳过该视频继续下一个
- 转录失败（whisper-cli 非零退出码）→ 打印错误，跳过
- 无语音内容（空 segments）→ 生成空笔记占位

## 手动配置（不使用 setup.sh）

如果需要手动搭建环境：

```bash
# 1. 创建虚拟环境
uv venv --python 3.11
# 或: python -m venv .venv

# 2. 创建工具目录
mkdir -p tools/whisper-cpp tools/ffmpeg

# 3. 下载 whisper.cpp
# https://github.com/ggml-org/whisper.cpp/releases
# 解压 whisper-cli 到 tools/whisper-cpp/Release/

# 4. 下载模型
# https://huggingface.co/ggerganov/whisper.cpp
# 将 ggml-small.bin 放入 tools/

# 5. 下载 ffmpeg
# Windows: https://www.gyan.dev/ffmpeg/builds/
# 将 ffmpeg.exe 放入 tools/ffmpeg/

# 6. 运行
uv run python transcribe.py --language zh
```
