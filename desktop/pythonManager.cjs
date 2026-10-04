const { spawn } = require("child_process");
const http = require("http");
const path = require("path");
const fs = require("fs");

class PythonManager {
  constructor(projectDir, port = 8765) {
    this.projectDir = projectDir;
    this.port = port;
    this.process = null;
    this.isQuitting = false;
  }

  findPython() {
    const isWin = process.platform === "win32";
    const candidates = isWin
      ? [
          path.join(this.projectDir, ".venv", "bin", "python.exe"),
          path.join(this.projectDir, ".venv", "Scripts", "python.exe"),
          "python.exe",
          "python",
          "py",
        ]
      : [
          path.join(this.projectDir, ".venv", "bin", "python"),
          path.join(this.projectDir, ".venv", "bin", "python3"),
          "/opt/homebrew/bin/python3",
          "/usr/local/bin/python3",
          "python3",
          "python",
        ];

    for (const c of candidates) {
      if (c.includes(path.sep)) {
        if (fs.existsSync(c)) return c;
      } else {
        return c;
      }
    }
    return isWin ? "python" : "python3";
  }

  async checkHealth() {
    return new Promise((resolve) => {
      const req = http.get(`http://127.0.0.1:${this.port}/api/health`, (res) => {
        resolve(res.statusCode === 200);
      });
      req.on("error", () => resolve(false));
      req.setTimeout(800, () => {
        req.destroy();
        resolve(false);
      });
    });
  }

  async startBackend() {
    const isRunning = await this.checkHealth();
    if (isRunning) {
      console.log(`[PythonManager] 后端服务已在端口 ${this.port} 运行`);
      return true;
    }

    const pythonPath = this.findPython();
    const serverScript = path.join(this.projectDir, "web", "backend", "server.py");
    console.log(`[PythonManager] 启动服务: ${pythonPath} "${serverScript}"`);

    const env = {
      ...process.env,
      PYTHONUNBUFFERED: "1",
      PYTHONIOENCODING: "utf-8",
      FLASK_PORT: String(this.port),
      FLASK_HOST: "127.0.0.1",
    };

    this.process = spawn(pythonPath, [serverScript], {
      cwd: this.projectDir,
      env,
      stdio: ["pipe", "pipe", "pipe"],
    });

    this.process.stdout.on("data", (data) => {
      const line = data.toString().trim();
      if (line) console.log(`[Flask] ${line}`);
    });

    this.process.stderr.on("data", (data) => {
      const line = data.toString().trim();
      if (line) console.log(`[Flask] ${line}`);
    });

    for (let i = 0; i < 30; i++) {
      await new Promise((r) => setTimeout(r, 500));
      if (await this.checkHealth()) {
        console.log(`[PythonManager] 后端就绪！`);
        return true;
      }
    }
    return false;
  }

  stopBackend() {
    if (!this.process) return;
    this.isQuitting = true;
    const pid = this.process.pid;
    console.log(`[PythonManager] 正在关闭后端 (PID: ${pid})...`);
    if (process.platform === "win32") {
      try {
        spawn("taskkill", ["/pid", pid.toString(), "/f", "/t"]);
      } catch (e) {}
    } else {
      try {
        process.kill(-pid, "SIGTERM");
      } catch (e) {
        try { this.process.kill("SIGTERM"); } catch (_) {}
      }
    }
    this.process = null;
  }
}

module.exports = PythonManager;
