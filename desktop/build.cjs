const fs = require("fs");
const path = require("path");

const DESKTOP_DIR = __dirname;
const ROOT_DIR = path.resolve(__dirname, "..");
const ELECTRON_DIST = path.join(DESKTOP_DIR, "node_modules", "electron", "dist");
const OUT_DIR = path.join(ROOT_DIR, "release", "VideoExtract-win-x64");
const APP_DIR = path.join(OUT_DIR, "resources", "app");

console.log("=== 开始构建 Windows 原生独立可执行文件 (VideoExtract.exe) ===");

if (!fs.existsSync(ELECTRON_DIST)) {
  console.error("[X] 未找到 Electron 运行时: " + ELECTRON_DIST);
  process.exit(1);
}

// 1. 创建输出目录
fs.mkdirSync(APP_DIR, { recursive: true });

// 2. 复制 Electron 运行时
console.log("[1/3] 复制 Electron 引擎二进制文件...");
fs.cpSync(ELECTRON_DIST, OUT_DIR, { recursive: true });

// 3. 将 electron.exe 重命名为 VideoExtract.exe
const origExe = path.join(OUT_DIR, "electron.exe");
const targetExe = path.join(OUT_DIR, "VideoExtract.exe");
if (fs.existsSync(origExe)) {
  if (fs.existsSync(targetExe)) fs.unlinkSync(targetExe);
  fs.renameSync(origExe, targetExe);
  console.log("[2/3] 已生成原生可执行文件: " + targetExe);
}

// 4. 将应用脚本放置到 resources/app
console.log("[3/3] 组装应用代码资源 (resources/app)...");
const filesToCopy = ["main.cjs", "preload.cjs", "pythonManager.cjs", "package.json"];
for (const file of filesToCopy) {
  fs.copyFileSync(path.join(DESKTOP_DIR, file), path.join(APP_DIR, file));
}
if (fs.existsSync(path.join(DESKTOP_DIR, "icons"))) {
  fs.cpSync(path.join(DESKTOP_DIR, "icons"), path.join(APP_DIR, "icons"), { recursive: true });
}

console.log("\n======================================================");
console.log("  构建成功！");
console.log("  Windows 原生独立程序已生成: " + targetExe);
console.log("======================================================\n");
