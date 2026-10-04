# Video to Markdown —— Video Speech Transcription & AI Note Generator

[English](README.md) | [简体中文](README_CN.md)

Batch transcribe MP4 videos into high-precision Markdown documents, and transform raw transcripts into comprehensive, structured academic study notes using Large Language Models. Supports CLI workflow, Web interface, and **native desktop applications for Windows & macOS**.

* **Local Offline Engine**: Powered by [whisper.cpp](https://github.com/ggml-org/whisper.cpp) for fast, offline speech recognition (no GPU or internet required), coupled with `ffmpeg` for automatic audio extraction and normalization.
* **Deep AI Note Synthesis**: Integrates DeepSeek LLM to restructure spoken transcriptions into structured study notes while preserving technical derivations, intuition, and illustrations.
* **Native Desktop Client**: Includes a standalone `.exe` for Windows and one-click launcher for macOS, complete with in-app settings management.

---

## 🌟 Key Features

### 1. High-Precision Speech Transcription (`transcribe.py`)
- Automatically extracts 16kHz 16-bit mono WAV audio from MP4 videos.
- Transcribes speech using Whisper models supporting 99+ languages (Chinese, English, Japanese, etc.).
- Generates raw transcripts with accurate segment timestamps.
- **Optional Keyframe Extraction**: Utilizes `ffmpeg` scene detection to extract representative frames and embed them directly into the Markdown notes.

### 2. Deep Academic Note Synthesis (`summarize.py` / `summarizer/` package)
- Formats unstructured transcripts into coherent academic notes using DeepSeek LLM.
- **Multiple Note Styles**:
  - **STEM / Theoretical Derivations**: Preserves mathematical and physical derivations step-by-step, intuitive physical analogies, LaTeX formulas, and ASCII diagrams without skipping steps or omitting examples.
  - **Mechanisms & Architecture**: Focuses on system bottlenecks, topological flowcharts, algorithms, and practical debugging guides.
  - **General**: Fixes homophone typos, cleans spoken redundancies, and organizes content into hierarchical sections with key summaries.
- Handles ultra-long video transcripts via chunking and intelligent hierarchical merging.

### 3. Cross-Platform Desktop Client (`desktop/` / `release/`)
- **Windows Standalone Executable**: Pre-assembled at `release/VideoExtract-win-x64/VideoExtract.exe`. Instant startup by double-clicking—no terminal or Node.js environment required.
- **macOS Native Integration**: Run via `./start_desktop.sh` with native frameless traffic light window buttons.
- **GUI Settings Panel**: Configure DeepSeek API keys, LLM models, and Whisper models directly in the UI without editing configuration files.
- **One-Click Directory Navigation**: Open the `output/` folder and explore generated notes with a single click.

### 4. Interactive Web Interface (`web/`)
- Built with React 19 and Tailwind CSS.
- Drag-and-drop video upload with real-time task progress tracking.
- Split-screen comparison view: read raw transcripts (with timestamp view) side-by-side with rendered Markdown notes.

---

## 📂 Project Architecture

```
vedio_extract/
├── start_desktop.bat              # Windows desktop client one-click launcher
├── start_desktop.sh               # macOS / Linux desktop client one-click launcher
├── desktop_app.py                 # Standalone Python App-Mode fallback launcher
├── setup.sh                       # One-click environment installer (uv + binaries)
├── run_all.py                     # Full end-to-end CLI pipeline (transcribe -> summarize)
├── transcribe.py                  # Video transcription CLI script
├── summarize.py                   # Note summarization CLI script
├── summarizer/                    # Note summarization Python package
│   ├── __init__.py
│   ├── api.py                     # DeepSeek API client (via requests)
│   ├── prompts.py                 # Structured system prompts (General / STEM / Architecture)
│   ├── processor.py               # Text chunking, API orchestration, and merging
│   └── io.py                      # Markdown reading and note writing
├── desktop/                       # Electron desktop client source code
│   ├── main.cjs                   # Main process (window management, native dialogs)
│   ├── preload.cjs                # Context bridge IPC
│   ├── pythonManager.cjs          # Python backend lifecycle manager
│   ├── build.cjs                  # Windows standalone .exe packager
│   └── package.json
├── release/                       # [Build Artifacts] Packaged standalone desktop app
│   └── VideoExtract-win-x64/      # Standalone Windows executable package
├── web/                           # Web application
│   ├── backend/
│   │   ├── server.py              # Flask API server
│   │   └── tasks.py               # Thread pool asynchronous task runner
│   └── frontend/                  # React 19 SPA frontend
│       ├── src/
│       │   ├── App.jsx            # Main application UI
│       │   ├── api.js             # API client & desktop bridge calls
│       │   └── components/
│       │       ├── Layout.jsx     # Header navigation & folder shortcut
│       │       ├── SettingsModal.jsx # Visual configuration modal
│       │       └── UploadZone.jsx # Drag-and-drop upload component
│       └── dist/                  # Static frontend build artifacts
├── config.yaml                    # Local configuration file (API keys, models, server)
├── config.example.yaml            # Configuration template
├── config.py                      # Centralized configuration loader
├── requirements.txt               # Python package dependencies
├── README.md                      # English documentation (This file)
└── README_CN.md                   # Chinese documentation
```

---

## 🚀 Quick Start

### Option A: Native Desktop App (Recommended)

#### Windows
Simply double-click the pre-built binary:
```text
release/VideoExtract-win-x64/VideoExtract.exe
```
Or run [`start_desktop.bat`](start_desktop.bat).

#### macOS / Linux
Grant execution permission and run:
```bash
chmod +x start_desktop.sh
./start_desktop.sh
```

#### Standalone Python App Mode (Zero Node.js dependency)
Launch the native window directly via Python:
```bash
python desktop_app.py
```

---

### Option B: Command Line Interface (CLI)

#### 1. Setup Environment
```bash
# Using the default 'small' model (recommended, 466MB, balanced speed & accuracy)
bash setup.sh

# Or specify a different model size:
bash setup.sh medium           # 1.5GB, higher accuracy
bash setup.sh large-v3-turbo   # 1.6GB, best performance
```

`setup.sh` automatically installs [uv](https://docs.astral.sh/uv/), sets up Python 3.11 virtual environment, downloads pre-compiled `whisper.cpp` binaries, `ffmpeg`, and the specified model weights.

#### 2. Set DeepSeek API Key
Copy the configuration template and add your API key:
```bash
cp config.example.yaml config.yaml
```
Alternatively, set the environment variable:
```bash
export DEEPSEEK_API_KEY="sk-your-key-here"
```

#### 3. Run Pipeline
Place your `.mp4` video files into the `vedio/` directory, then run:

```bash
# Run full pipeline: transcription + note generation
uv run python run_all.py --language zh

# Or step-by-step:
# Step 1: Transcribe video
uv run python transcribe.py --language zh

# Step 2: Generate notes (choose style: general / stem)
uv run python summarize.py output/ --style stem
```

Output files:
- `output/<video_name>.md`: Raw speech transcript with timestamps.
- `output/<video_name>.note.md`: Structured AI study note.

---

### Option C: Web Interface

```bash
# Build frontend (if modified)
cd web/frontend && npm install && npm run build && cd ../..

# Start backend server
uv run python web/backend/server.py

# Open your browser at
http://localhost:8765
```

---

## ⚙️ Configuration (`config.yaml`)

All runtime options are centralized in `config.yaml`. Environment variables override file settings:

```yaml
deepseek:
  api_key: ""                         # Falls back to DEEPSEEK_API_KEY environment variable
  base_url: "https://api.deepseek.com"
  model: "deepseek-v4-pro"
  max_chars_per_chunk: 30000

whisper:
  model: "small"                      # Default Whisper model

keyframe:
  scene_threshold: 0.3                # Scene detection sensitivity (0.0 - 1.0)
  max_frames: 20                      # Maximum extracted keyframes per video

server:
  host: "0.0.0.0"
  port: 8765
```

---

## 📊 Whisper Model Comparison

| Model | Disk Size | Transcription Speed | Accuracy | Recommended Use Case |
|:---|:---|:---|:---|:---|
| `tiny` | 78 MB | Extremely Fast | Basic | Quick drafts, short testing clips |
| `base` | 148 MB | Very Fast | Good | Casual conversations |
| `small` | 466 MB | Moderate | Great | **Default Choice**, optimal balance for lectures |
| `medium` | 1.5 GB | Slower | Excellent | Noisy audio, specialized domain vocabulary |
| `large-v3-turbo` | 1.6 GB | Moderate | Superior | Complex multilingual videos |
| `large-v3` | 3.1 GB | Slow | Maximum | Highest fidelity transcription |

---

## 📄 License

This project is licensed under the [MIT License](LICENSE).
