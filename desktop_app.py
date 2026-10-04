#!/usr/bin/env python3
"""
Video Extract 桌面端应用启动器 (跨平台 Windows & macOS)
无需额外复杂安装，直接以原生独立应用窗口形式启动系统。
"""

import os
import platform
import shutil
import subprocess
import sys
import threading
import time
import urllib.request
from pathlib import Path

PROJECT_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(PROJECT_DIR))

from config import get_server_port


def check_server(port: int, host: str = "127.0.0.1") -> bool:
    try:
        url = f"http://{host}:{port}/api/health"
        with urllib.request.urlopen(url, timeout=1) as resp:
            return resp.status == 200
    except Exception:
        return False


def start_flask_thread(host: str, port: int):
    from web.backend.server import app
    import logging
    log = logging.getLogger("werkzeug")
    log.setLevel(logging.ERROR)
    app.run(host=host, port=port, debug=False, use_reloader=False)


def launch_desktop_window(url: str, title: str = "Video Extract"):
    system = platform.system()
    print(f"[Desktop] 正在创建跨平台独立桌面窗口 ({system})...")

    if system == "Windows":
        edge_paths = [
            os.path.expandvars(r"%ProgramFiles(x86)%\Microsoft\Edge\Application\msedge.exe"),
            os.path.expandvars(r"%ProgramFiles%\Microsoft\Edge\Application\msedge.exe"),
            os.path.expandvars(r"%LocalAppData%\Microsoft\Edge\Application\msedge.exe"),
        ]
        chrome_paths = [
            os.path.expandvars(r"%ProgramFiles%\Google\Chrome\Application\chrome.exe"),
            os.path.expandvars(r"%ProgramFiles(x86)%\Google\Chrome\Application\chrome.exe"),
            os.path.expandvars(r"%LocalAppData%\Google\Chrome\Application\chrome.exe"),
        ]
        
        browser_exe = None
        for p in edge_paths + chrome_paths:
            if os.path.exists(p):
                browser_exe = p
                break

        if browser_exe:
            cmd = [
                browser_exe,
                f"--app={url}",
                "--window-size=1280,860",
                f"--app-id=com.videoextract.desktop",
            ]
            return subprocess.Popen(cmd)

    elif system == "Darwin":
        chrome_app = "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"
        edge_app = "/Applications/Microsoft Edge.app/Contents/MacOS/Microsoft Edge"
        
        for browser in [chrome_app, edge_app]:
            if os.path.exists(browser):
                cmd = [
                    browser,
                    f"--app={url}",
                    "--window-size=1280,860",
                ]
                return subprocess.Popen(cmd)
        
        return subprocess.Popen(["open", url])

    else:
        for cli in ["google-chrome", "chromium-browser", "chromium", "microsoft-edge", "xdg-open"]:
            path = shutil.which(cli)
            if path:
                if "open" in cli:
                    return subprocess.Popen([path, url])
                else:
                    return subprocess.Popen([path, f"--app={url}", "--window-size=1280,860"])

    import webbrowser
    webbrowser.open(url)
    return None


def main():
    host = "127.0.0.1"
    port = get_server_port()
    url = f"http://{host}:{port}"

    print("=" * 60)
    print("  Video Extract 视频文案提取与笔记整理 —— 桌面客户端")
    print("=" * 60)

    dist_dir = PROJECT_DIR / "web" / "frontend" / "dist"
    if not dist_dir.exists():
        print("[!] 检测到前端尚未构建，正在自动构建中...")
        frontend_dir = PROJECT_DIR / "web" / "frontend"
        try:
            subprocess.run(["npm", "run", "build"], cwd=str(frontend_dir), check=True)
            print("[OK] 前端构建完成！")
        except Exception as e:
            print(f"[!] 自动构建前端失败: {e}")

    if not check_server(port, host):
        print(f"[1/2] 正在启动后台服务: {url} ...")
        server_thread = threading.Thread(
            target=start_flask_thread,
            args=(host, port),
            daemon=True,
        )
        server_thread.start()

        for _ in range(30):
            time.sleep(0.3)
            if check_server(port, host):
                break
        else:
            print("[X] 后台服务启动超时")
            sys.exit(1)
        print("[OK] 后台服务就绪！")
    else:
        print(f"[1/2] 检测到已有后台服务正在运行: {url}")

    print(f"[2/2] 正在打开桌面独立窗口...")
    proc = launch_desktop_window(url)

    print("\n" + "-" * 60)
    print(f"桌面应用已启动！访问地址: {url}")
    print("提示：关闭应用窗口后，可在终端按 Ctrl+C 退出程序。")
    print("-" * 60 + "\n")

    try:
        if proc:
            proc.wait()
        else:
            while True:
                time.sleep(1)
    except KeyboardInterrupt:
        print("\n[Desktop] 正在退出应用...")
        sys.exit(0)


if __name__ == "__main__":
    main()
