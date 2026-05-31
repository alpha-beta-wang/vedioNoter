# Video to Markdown —— 视频转文字笔记

将 MP4 视频批量转录为 Markdown 笔记，并通过大模型整理为结构化学习笔记。

**本地引擎**：基于 [whisper.cpp](https://github.com/ggml-org/whisper.cpp) 进行语音识别（无需联网、无需 GPU），配合 ffmpeg 进行音频预处理。

**智能整理**：调用 DeepSeek API 将原始转录整理为结构清晰的学习笔记。

## 功能

### 语音转录 (`transcribe.py`)
- 自动提取视频中的音频（16kHz 单声道 WAV）
- 使用 Whisper 模型进行语音识别（支持中/英/日等 99 种语言）
- 生成带时间戳的原始转录 Markdown
- 可选提取关键帧（场景检测），按时间戳嵌入笔记作为图示

### 笔记整理 (`summarize.py` / `summarizer/` 包)
- 调用 DeepSeek v4 Pro API，将转录全文整理为结构化学习笔记
- 两套提示词风格：
  - **通用**：适合一般技术内容，修正错字、提炼要点、去除冗余
  - **理工科**：适合数理课程，保留推导过程、直觉解释、公式、类比和作者风格
- 自动修正同音错字、去除口语冗余、提炼核心要点
- 按逻辑重新分段，添加标题层级
- 保留全部技术术语和专业内容
- 末尾附「核心要点」总结
- 自动处理超长文本（分块 + 合并）

### 全流程脚本 (`run_all.py`)
- 一键执行「转码 → 整理」两个步骤
- 适合批量处理多个视频

### Web 前端 (`web/`)
- 现代化 React SPA 界面，拖拽上传视频
- 转录语言可选：中文 / English / 自动检测
- 笔记风格可选：通用 / 理工科
- 实时进度条追踪转录 / 整理任务
- 转录全文阅读 & 时间戳视图切换
- 结构化学习笔记 Markdown 渲染
- 暗色模式自适应

### 通用特性
- 音频缓存：同一视频音频只提取一次
- 增量处理：`--skip-existing` 跳过已处理文件
- 关键帧提取（可选）：ffmpeg 场景检测，按时间戳嵌入笔记
- uv 一键配置环境

## 文件夹架构

```
vedio_extract/
├── setup.sh                       # 一键环境配置脚本 (uv + tools)
├── run_all.py                     # 全流程脚本 (转码 → 整理)
├── transcribe.py                  # 视频转码脚本
├── summarize.py                   # 笔记整理脚本
├── summarizer/                    # 笔记整理 Python 包
│   ├── __init__.py                # 包入口
│   ├── api.py                     # DeepSeek API 客户端
│   ├── prompts.py                 # 提示词模板
│   ├── processor.py               # 核心处理逻辑
│   └── io.py                      # 文件读写
├── requirements.txt               # Python 依赖
├── README.md                      # 本文件
├── vedio/                         # [用户] 放入待转录的 .mp4 视频
├── output/                        # [输出] 转录 .md 和笔记 .note.md
├── audio_temp/                    # [缓存] 提取的中间音频文件 (WAV)
├── tools/
│   ├── whisper-cpp/Release/       # whisper.cpp 预编译二进制
│   ├── ffmpeg/                    # ffmpeg 静态构建
│   └── ggml-small.bin            # Whisper 模型文件
├── web/                           # Web 应用
│   ├── backend/
│   │   ├── server.py              # Flask API 服务器
│   │   └── tasks.py               # 异步任务管理（线程池）
│   └── frontend/
│       ├── src/
│       │   ├── App.jsx            # React SPA 主组件
│       │   ├── api.js             # API 请求封装
│       │   └── components/
│       │       ├── Layout.jsx     # 页面布局（导航栏/页脚）
│       │       └── UploadZone.jsx # 拖拽上传组件
│       ├── dist/                  # 前端构建产物
│       └── vite.config.js         # Vite 配置（含代理）
└── .venv/                         # Python 虚拟环境 (uv 管理)
```

## 环境依赖

### 运行时

| 组件 | 用途 | 来源 |
|---|---|---|
| **Python 3.11+** | 脚本运行环境 | uv 自动管理 |
| **whisper.cpp** | 语音识别引擎 | setup.sh 自动下载 |
| **ffmpeg** | 视频音频提取 | setup.sh 自动下载 |
| **ggml-*.bin** | Whisper 模型权重 | setup.sh 自动下载 |
| **requests** | DeepSeek API 调用 (HTTP) | setup.sh 自动安装 |
| **flask** | Web API 服务器 | setup.sh 自动安装 |
| **flask-cors** | 跨域支持 | setup.sh 自动安装 |
| **Node.js / npm** | 前端构建 (可选) | 手动安装 |

### Python 依赖

```
requests>=2.25.0
flask>=3.0.0
flask-cors>=4.0.0
imageio-ffmpeg>=0.5.0
```

`transcribe.py` 仅使用标准库，无需额外 pip 包。`summarizer/api.py` 使用 `requests` 直调 DeepSeek API（HTTP 请求），避免 C 扩展依赖。`flask` 用于 Web API 服务器。

### 前端依赖

| 组件 | 用途 |
|---|---|
| **React 19** | UI 框架 |
| **React Router 7** | 客户端路由 |
| **Tailwind CSS v4** | 原子化 CSS 框架 |
| **Vite 8** | 前端构建工具 |
| **lucide-react** | 图标库（预留） |

## 快速开始

### 1. 一键配置环境

```bash
# 使用默认 small 模型（推荐，466MB，中英文均表现良好）
bash setup.sh

# 或指定其他模型
bash setup.sh medium           # 更大更准 (1.5GB)
bash setup.sh base             # 更小更快 (148MB)
bash setup.sh large-v3-turbo   # 最强 (1.6GB)
```

`setup.sh` 会自动完成：
- 安装 [uv](https://docs.astral.sh/uv/)（Python 包管理器）
- 创建 Python 3.11 虚拟环境
- 安装 pip 依赖（flask, requests 等）
- 下载 whisper.cpp 预编译二进制
- 下载 Whisper 模型文件
- 下载 ffmpeg 静态构建

### 2. 放入视频

将待转录的 `.mp4` 文件放入 `vedio/` 文件夹。

### 3. 运行

```bash
# --- 方式一：全流程一键运行（推荐）---
uv run python run_all.py --language zh

# --- 方式二：分步运行 ---
# Step 1: 视频转码
uv run python transcribe.py --language zh

# Step 2: 整理为学习笔记
uv run python summarize.py output/

# --- 方式三：仅转码 ---
uv run python run_all.py --language zh --skip-summarize
```

### 4. 查看结果

| 输出文件 | 说明 |
|---|---|
| `output/<视频名>.md` | 原始转录（全文 + 时间戳） |
| `output/<视频名>.note.md` | 结构化学习笔记 |

### 5. (可选) 启动 Web 界面

```bash
# 构建前端（首次或前端代码修改后需要）
cd web/frontend && npm install && npm run build && cd ../..

# 启动后端服务器
uv run python web/backend/server.py

# 浏览器访问 http://localhost:8765
```

Web 界面功能：
- **拖拽上传** .mp4 视频
- **一键转码**：启动语音识别任务，实时进度条，可选择转录语言
- **一键整理**：启动 AI 笔记整理任务，可选择「通用」或「理工科」风格
- **在线查看**：转录全文 / 时间戳视图切换
- **笔记阅读**：结构化学习笔记 Markdown 渲染

## 使用说明

### transcribe.py —— 视频转码

```
用法: uv run python transcribe.py [选项]

选项:
  --model MODEL       Whisper 模型 (默认: small)
                      可选: tiny, base, small, medium, large-v3, large-v3-turbo
  --language LANG     语言代码 (zh/en/ja...)，不指定则自动检测
  --threads N         线程数 (默认: CPU 核心数)
  --skip-existing     跳过 output/ 中已有同名 .md 的视频
  --extract-frames    提取关键帧并嵌入笔记（场景检测，默认不提取）
```

### summarize.py —— 笔记整理

```
用法: uv run python summarize.py <文件或目录> [选项]

参数:
  target              转录 .md 文件或 output/ 目录

选项:
  --api-key KEY       DeepSeek API key (默认读取 DEEPSEEK_API_KEY)
  --model MODEL       LLM 模型 (默认: deepseek-v4-pro)
  --style STYLE       笔记风格: general (通用) / stem (理工科) (默认: general)
  --skip-existing     跳过已有 .note.md 的文件
  --output-dir DIR    笔记输出目录 (默认与转录文件同目录)
```

### run_all.py —— 全流程

```
用法: uv run python run_all.py [选项]

选项:
  --language LANG     语言代码 (zh/en/ja...)
  --model MODEL       Whisper 模型 (默认: small)
  --api-key KEY       DeepSeek API key
  --llm-model MODEL   LLM 模型 (默认: deepseek-v4-pro)
  --style STYLE       笔记风格: general (通用) / stem (理工科) (默认: general)
  --skip-existing     跳过已处理的文件
  --skip-summarize    仅转码，不整理笔记
  --extract-frames    提取关键帧并嵌入笔记
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

### transcribe.py —— 三步流水线

**第 1 步：音频提取** (`extract_audio`)
```bash
ffmpeg -i video.mp4 -vn -acodec pcm_s16le -ar 16000 -ac 1 -y audio.wav
```
丢弃视频流，编码为 16-bit PCM 单声道 16kHz WAV，缓存到 `audio_temp/`。

**第 2 步：语音识别** (`transcribe_with_whisper_cpp`)
```bash
whisper-cli -m model.bin -f audio.wav -ocsv -of output_prefix
```
调用 whisper.cpp CLI 输出 CSV（`start_ms, end_ms, text`），实时回显进度，解析为 segment 列表。

**第 3 步：生成笔记** (`build_markdown`)
- 拼接所有 segment 为连续全文
- 逐段输出带时间戳文本
- 若启用关键帧提取，按时间戳将帧图片嵌入对应段落
- 末尾追加「关键图示」章节列出全部帧
- 写入 `output/<视频名>.md`

**可选：关键帧提取** (`extract_keyframes`)
```bash
ffmpeg -i video.mp4 -vf "select='gt(scene,0.3)',showinfo" -vsync vfr -f null NUL
# 解析场景变化时间戳 → 选取 top 20 代表性时刻 → 逐帧提取 JPEG
```
- 第一遍：场景检测，获取变化点时间戳列表
- 第二遍：逐时刻 `-ss` seek 提取帧，输出到 `output/frames/<视频名>/`
- 通过 `--extract-frames` 启用，前端通过「帧」开关控制

### summarizer/ 包 —— 模块架构

```
summarizer/
├── api.py        # DeepSeek API 客户端（requests 直调 DeepSeek API）
├── prompts.py    # 提示词模板（通用 SYSTEM_PROMPT / 理工科 STEM_SYSTEM_PROMPT + build_user_prompt）
├── processor.py  # 核心逻辑：文本分块 → API 调用 → 结果合并，支持 style 参数切换提示词
└── io.py         # 文件 IO：reads transcript from .md, writes .note.md
```

**调用流程**：

```
process_file(md_path)
  │
  ├─ io.read_transcript_text()          # 从 .md 提取「转录全文」
  ├─ io.read_metadata()                 # 读取标题、时长
  │
  └─ summarize_transcript(text, title)
       │
       ├─ _split_text()                 # 超长文本按段落分块
       │
       ├─ for each chunk:
       │     api.chat(client, prompt)   # 调用 DeepSeek API
       │
       └─ _merge_chunk_results()        # 多块结果二次合并整理
             │
             └─ io.write_note()         # 写入 .note.md
```

**提示词设计思路**：
- 两套 System prompt，通过 `--style` 或前端开关切换：
  - **通用 (general)**：角色为学术笔记整理专家，六项职责（修正错误、结构化、提炼要点、保留术语、去冗余、加小结）
  - **理工科 (stem)**：角色为数理工科视频笔记整理专家，重点保留推导过程、直觉解释、公式、类比、作者风格，不压缩结论，推荐章节结构与通用不同
- User prompt 传入视频标题和转录全文
- 使用 `reasoning_effort="high"` 和 `thinking: enabled` 提升整理质量

## 手动配置（不使用 setup.sh）

```bash
# 1. 创建虚拟环境并安装依赖
uv venv --python 3.11
uv pip install -r requirements.txt

# 2. 创建工具目录
mkdir -p tools/whisper-cpp/Release tools/ffmpeg

# 3. 下载 whisper.cpp
# https://github.com/ggml-org/whisper.cpp/releases
# 解压 whisper-cli 到 tools/whisper-cpp/Release/

# 4. 下载模型
# https://huggingface.co/ggerganov/whisper.cpp
# 将 ggml-small.bin 放入 tools/

# 5. 下载 ffmpeg
# https://www.gyan.dev/ffmpeg/builds/ (Windows)
# 将 ffmpeg 放入 tools/ffmpeg/

# 6. 设置 API key
export DEEPSEEK_API_KEY="sk-xxx"

# 7. 运行
uv run python run_all.py --language zh
```
