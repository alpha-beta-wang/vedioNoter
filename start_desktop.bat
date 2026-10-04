@echo off
chcp 65001 >nul
title Video Extract 桌面客户端

echo ======================================================
echo    Video Extract 视频文案提取与笔记整理 - 桌面客户端
echo ======================================================
echo.

cd /d "%~dp0"

:: 1. 优先启动原生打包好的 exe 独立程序
if exist "release\VideoExtract-win-x64\VideoExtract.exe" (
    echo [启动方式 1/3] 正在启动原生可执行程序 VideoExtract.exe ...
    start "" "release\VideoExtract-win-x64\VideoExtract.exe"
    exit /b 0
)

:: 2. 检查是否安装了 Electron 开发依赖
if exist "desktop\node_modules\electron" (
    echo [启动方式 2/3] 正在启动 Electron 原生桌面客户端...
    cd desktop
    call npm start
    exit /b 0
)

:: 3. 备选启动：使用 Python 原生独立窗口启动
echo [启动方式 3/3] 正在通过 Python 原生独立窗口启动...
if exist ".venv\bin\python.exe" (
    ".venv\bin\python.exe" desktop_app.py
) else if exist ".venv\Scripts\python.exe" (
    ".venv\Scripts\python.exe" desktop_app.py
) else (
    python desktop_app.py
)

pause
