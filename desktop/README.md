# Video Extract 桌面端应用 (Windows & macOS)

Video Extract 桌面客户端专为高效、沉浸式视频转录与智能笔记整理打造，全面深度适配 **Windows 10/11** 和 **macOS (Intel & Apple Silicon)**。

---

## 启动方式

### 方式一：Windows 直接双击可执行文件 (`.exe`)
在 `release/VideoExtract-win-x64/` 目录下，直接双击运行：
👉 **`VideoExtract.exe`**

或者在根目录下直接双击运行：
👉 **`start_desktop.bat`**

### 方式二：macOS / Linux 一键启动
在终端进入项目根目录运行：
```bash
./start_desktop.sh
```

### 方式三：通过 Node.js 源码启动
```bash
cd desktop
npm start
```

### 方式四：Python 原生独立窗口启动 (无需 Node.js)
```bash
python desktop_app.py
```

---

## 重新生成 Windows 原生 exe 程序
如果修改了前端或客户端逻辑，可以在根目录或 `desktop/` 执行：
```bash
npm run build:exe
# 或进入 desktop 运行: node build.cjs
```
即可将最新的代码与 Electron 引擎打包到 `release/VideoExtract-win-x64/VideoExtract.exe`。
