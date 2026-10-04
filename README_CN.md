# Video to Markdown —— 视频转文字与 AI 结构化学习笔记

[English](README.md) | [简体中文](README_CN.md)

将 MP4 视频批量转录为 Markdown 笔记，并通过大模型整理为深度、结构化的学术学习笔记。支持命令行 CLI、Web 前端界面以及 **Windows & macOS 原生桌面客户端**。

* **本地离线引擎**：基于 [whisper.cpp](https://github.com/ggml-org/whisper.cpp) 进行语音识别（无需联网、无需高端 GPU），配合 ffmpeg 自动进行高质量音频预处理。
* **智能深度整理**：调用 DeepSeek LLM 将原始口语转录重构为结构清晰、保留公式推导与图表的专业笔记。
* **全平台原生桌面支持**：提供 Windows 独立 `.exe` 安装运行包，macOS 独立运行环境，支持全局热配置。

---

## 🌟 核心功能

### 1. 语音转录 (`transcribe.py`)
- 自动提取视频中的音频（转换为 16kHz 16-bit 单声道 WAV）
- 使用 Whisper 模型进行语音识别（支持中文、英文、日语等 99 种语言）
- 生成带精准时间戳的原始转录 Markdown
- **关键帧提取**（可选）：基于 ffmpeg 场景变动检测，将视频关键帧按时间戳自动嵌入笔记对应段落

### 2. AI 笔记深度整理 (`summarize.py` / `summarizer/` 包)
- 调用 DeepSeek LLM，将口语化转录整理为结构化学术笔记
- **三套专业提示词模板**：
  - **理论推导型（STEM）**：保留数学物理推导过程、变量物理意义、几何直觉、ASCII 框图、完整例题，绝不跳步压缩
  - **机制架构型**：系统痛点剖析、拓扑流程图、算法细节、参数调优与避坑指南
  - **通用型**：修正错音别字、提炼核心要点、按逻辑分段分层
- 自动分块处理超长文本并智能合并

### 3. 跨平台桌面客户端 (`desktop/` / `release/`)
- **Windows 原生可执行程序**：预构建好的独立程序 `release/VideoExtract-win-x64/VideoExtract.exe`，无需配置复杂的终端环境，双击秒开
- **macOS 原生适配**：一键运行脚本 `./start_desktop.sh`，支持原生无边框红绿灯交通灯按键
- **可视化设置面板**：无需编辑配置文件，在界面中直接填入 DeepSeek API Key、修改 LLM 模型名称与 Whisper 模型大小
- **本地目录一键直达**：支持在界面中直接打开 `output/` 输出目录与文件管理

### 4. Web 前端界面 (`web/`)
- 现代化 React 19 + Tailwind CSS SPA 界面
- 拖拽上传视频、实时进度条轮询追踪
- 双栏对照阅读：转录原文（全文/时间戳视图）与结构化 Markdown 笔记双向对照

---

## 📂 项目架构

```
vedio_extract/
├── start_desktop.bat              # Windows 桌面客户端一键启动
├── start_desktop.sh               # macOS / Linux 桌面客户端一键启动
├── desktop_app.py                 # Python 原生独立窗口备用启动器
├── setup.sh                       # 一键开发环境配置脚本 (uv + tools)
├── run_all.py                     # 全流程命令行工具 (转码 → 整理)
├── transcribe.py                  # 视频转录核心脚本
├── summarize.py                   # 笔记整理脚本
├── summarizer/                    # 笔记整理核心模块
│   ├── __init__.py
│   ├── api.py                     # DeepSeek API 交互客户端
│   ├── prompts.py                 # 结构化系统提示词 (通用 / 理工科 / 架构型)
│   ├── processor.py               # 文本长分块切分与合并
│   └── io.py                      # 转录解析与输出读写
├── desktop/                       # Electron 原生桌面客户端源码
│   ├── main.cjs                   # 桌面主进程 (窗口管理、原生文件对话框)
│   ├── preload.cjs                # 安全 IPC 通信桥
│   ├── pythonManager.cjs          # Python 后端生命周期管理
│   ├── build.cjs                  # Windows .exe 打包组装工具
│   └── package.json
├── release/                       # [构建产物] 打包好的独立桌面客户端
│   └── VideoExtract-win-x64/      # Windows 原生程序 (含 VideoExtract.exe)
├── web/                           # Web 应用
│   ├── backend/
│   │   ├── server.py              # Flask API 后端服务器
│   │   └── tasks.py               # 线程池异步任务控制
│   └── frontend/                  # React 19 SPA 前端
│       ├── src/
│       │   ├── App.jsx            # 核心业务界面
│       │   ├── api.js             # API 与桌面桥通信
│       │   └── components/
│       │       ├── Layout.jsx     # 全局布局 (含导航栏/输出目录)
│       │       ├── SettingsModal.jsx # 可视化配置面板
│       │       └── UploadZone.jsx # 拖拽上传
│       └── dist/                  # 前端静态构建资产
├── config.yaml                    # 本地私有配置文件 (API Key、模型参数)
├── config.example.yaml            # 配置文件模板
├── config.py                      # 统一配置加载器
├── requirements.txt               # Python 依赖清单
├── README.md                      # 英文说明文档
└── README_CN.md                   # 中文说明文档 (本文件)
```

---

## 🚀 快速上手

### 选项 A：使用原生桌面客户端（最便捷）

#### Windows
直接双击运行：
```text
release/VideoExtract-win-x64/VideoExtract.exe
```
或者双击项目根目录下的 [`start_desktop.bat`](start_desktop.bat)。

#### macOS / Linux
赋予执行权限后运行启动脚本：
```bash
chmod +x start_desktop.sh
./start_desktop.sh
```

#### 极简模式（无需 Node.js）
直接运行 Python 独立窗口模式：
```bash
python desktop_app.py
```

---

### 选项 B：使用命令行 CLI

#### 1. 初始化环境与依赖
```bash
# 使用默认 small 模型（推荐，466MB，中英双语精准平衡）
bash setup.sh

# 或指定更大模型
bash setup.sh medium           # 1.5GB
bash setup.sh large-v3-turbo   # 1.6GB
```

#### 2. 配置 API Key
复制配置模板并填入您的 DeepSeek API Key：
```bash
cp config.example.yaml config.yaml
```
或直接通过环境变量配置：
```bash
export DEEPSEEK_API_KEY="sk-your-key-here"
```

#### 3. 运行处理
将待处理的 `.mp4` 文件放入 `vedio/` 目录，然后执行：
```bash
# 一键运行完整流水线 (转录 + 整理)
uv run python run_all.py --language zh

# 分步执行：
# 步骤 1: 语音转录
uv run python transcribe.py --language zh

# 步骤 2: 整理为结构化笔记 (可指定 --style general 或 stem)
uv run python summarize.py output/ --style stem
```

---

### 选项 C：本地 Web 服务

```bash
# 启动 Flask 后台服务
uv run python web/backend/server.py

# 浏览器访问
http://localhost:8765
```

---

## ⚙️ 配置文件说明 (`config.yaml`)

项目配置采用层次化结构，运行时优先读取环境变量，其次读取 `config.yaml`：

```yaml
deepseek:
  api_key: ""                         # 留空则自动读取环境变量 DEEPSEEK_API_KEY
  base_url: "https://api.deepseek.com"
  model: "deepseek-v4-pro"
  max_chars_per_chunk: 30000

whisper:
  model: "small"                      # 默认 Whisper 语音识别模型

keyframe:
  scene_threshold: 0.3                # 场景变化阈值 (0.0 ~ 1.0)
  max_frames: 20                      # 笔记中最大嵌入帧数

server:
  host: "0.0.0.0"
  port: 8765
```

---

## 📊 Whisper 模型性能参考

| 模型 | 大小 | 转录速度 | 识别精度 | 推荐使用场景 |
|:---|:---|:---|:---|:---|
| `tiny` | 78 MB | 极快 | 基础 | 快速预览、粗略校对 |
| `base` | 148 MB | 很快 | 良好 | 语速平稳的标准对话 |
| `small` | 466 MB | 适中 | 优秀 | **推荐默认**，兼顾技术术语与性能 |
| `medium` | 1.5 GB | 较慢 | 极佳 | 复杂背景音、高难度学术讲座 |
| `large-v3-turbo` | 1.6 GB | 适中 | 卓越 | 追求高精度、多语言混合场景 |
| `large-v3` | 3.1 GB | 较慢 | 最高 | 极限精度要求 |

---

## 📄 开源许可证

本项目基于 [MIT License](LICENSE) 开源。
