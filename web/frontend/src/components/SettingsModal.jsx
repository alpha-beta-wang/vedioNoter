import { useState, useEffect } from "react";
import { getConfig, updateConfig, getSystemInfo } from "../api";

export default function SettingsModal({ isOpen, onClose }) {
  const [config, setConfig] = useState(null);
  const [sysInfo, setSysInfo] = useState(null);
  const [saving, setSaving] = useState(false);
  const [savedMsg, setSavedMsg] = useState("");
  const [showKey, setShowKey] = useState(false);

  useEffect(() => {
    if (isOpen) {
      getConfig().then(setConfig).catch(console.error);
      getSystemInfo().then(setSysInfo).catch(console.error);
      setSavedMsg("");
    }
  }, [isOpen]);

  if (!isOpen || !config) return null;

  const handleSave = async (e) => {
    e.preventDefault();
    setSaving(true);
    setSavedMsg("");
    try {
      await updateConfig(config);
      setSavedMsg("配置已保存并生效！");
      setTimeout(() => setSavedMsg(""), 3000);
    } catch (err) {
      alert("保存失败: " + err.message);
    } finally {
      setSaving(false);
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 backdrop-blur-sm p-4 animate-fade-in">
      <div className="bg-[var(--surface)] border border-[var(--border)] rounded-2xl w-full max-w-xl shadow-2xl overflow-hidden flex flex-col max-h-[90vh]">
        <div className="flex items-center justify-between px-6 py-4 border-b border-[var(--border)]">
          <div className="flex items-center gap-2">
            <span className="text-lg">⚙️</span>
            <h3 className="font-semibold text-base text-[var(--text)]">应用设置 (Settings)</h3>
          </div>
          <button
            onClick={onClose}
            className="w-8 h-8 rounded-lg flex items-center justify-center text-[var(--text-muted)] hover:bg-[var(--border)] hover:text-[var(--text)] transition-colors"
          >
            ✕
          </button>
        </div>

        <form onSubmit={handleSave} className="p-6 overflow-y-auto space-y-5 text-xs md:text-sm">
          <div className="space-y-3">
            <h4 className="font-medium text-xs tracking-wider uppercase text-indigo-400">DeepSeek LLM 配置</h4>
            <div>
              <label className="block text-[var(--text-muted)] mb-1 text-xs">DeepSeek API Key</label>
              <div className="relative">
                <input
                  type={showKey ? "text" : "password"}
                  value={config.deepseek?.api_key || ""}
                  onChange={(e) =>
                    setConfig({
                      ...config,
                      deepseek: { ...config.deepseek, api_key: e.target.value },
                    })
                  }
                  placeholder="sk-..."
                  className="w-full px-3 py-2 pr-16 rounded-lg bg-[var(--bg)] border border-[var(--border)] text-[var(--text)] focus:outline-none focus:border-indigo-500 font-mono text-xs"
                />
                <button
                  type="button"
                  onClick={() => setShowKey(!showKey)}
                  className="absolute right-2 top-1/2 -translate-y-1/2 px-2 py-1 text-xs text-[var(--text-muted)] hover:text-[var(--text)]"
                >
                  {showKey ? "隐藏" : "显示"}
                </button>
              </div>
            </div>

            <div className="grid grid-cols-2 gap-3">
              <div>
                <label className="block text-[var(--text-muted)] mb-1 text-xs">API Base URL</label>
                <input
                  type="text"
                  value={config.deepseek?.base_url || ""}
                  onChange={(e) =>
                    setConfig({
                      ...config,
                      deepseek: { ...config.deepseek, base_url: e.target.value },
                    })
                  }
                  className="w-full px-3 py-2 rounded-lg bg-[var(--bg)] border border-[var(--border)] text-[var(--text)] focus:outline-none focus:border-indigo-500 font-mono text-xs"
                />
              </div>
              <div>
                <label className="block text-[var(--text-muted)] mb-1 text-xs">整理模型 (LLM Model)</label>
                <input
                  type="text"
                  value={config.deepseek?.model || ""}
                  onChange={(e) =>
                    setConfig({
                      ...config,
                      deepseek: { ...config.deepseek, model: e.target.value },
                    })
                  }
                  placeholder="deepseek-v4-pro / deepseek-chat"
                  className="w-full px-3 py-2 rounded-lg bg-[var(--bg)] border border-[var(--border)] text-[var(--text)] focus:outline-none focus:border-indigo-500 font-mono text-xs"
                />
              </div>
            </div>
          </div>

          <div className="border-t border-[var(--border)] pt-4 space-y-3">
            <h4 className="font-medium text-xs tracking-wider uppercase text-indigo-400">Whisper 语音转写配置</h4>
            <div>
              <label className="block text-[var(--text-muted)] mb-1 text-xs">默认 Whisper 模型</label>
              <select
                value={config.whisper?.model || "small"}
                onChange={(e) =>
                  setConfig({
                    ...config,
                    whisper: { ...config.whisper, model: e.target.value },
                  })
                }
                className="w-full px-3 py-2 rounded-lg bg-[var(--bg)] border border-[var(--border)] text-[var(--text)] focus:outline-none focus:border-indigo-500"
              >
                {(config.whisper?.available_models || ["tiny", "base", "small", "medium", "large-v3-turbo"]).map((m) => (
                  <option key={m} value={m}>
                    {m} {m === "small" ? "(推荐，平衡速度与精准度)" : ""}
                  </option>
                ))}
              </select>
            </div>
          </div>

          {sysInfo && (
            <div className="border-t border-[var(--border)] pt-4">
              <div className="p-3 rounded-xl bg-[var(--bg)]/70 border border-[var(--border)] text-xs text-[var(--text-muted)] space-y-1">
                <div className="flex justify-between">
                  <span>操作系统:</span>
                  <span className="text-[var(--text)] font-medium">{sysInfo.os} ({sysInfo.arch})</span>
                </div>
                <div className="flex justify-between">
                  <span>CPU 核心数:</span>
                  <span className="text-[var(--text)] font-medium">{sysInfo.cpu_count} 线程</span>
                </div>
                <div className="flex justify-between">
                  <span>引擎状态:</span>
                  <span className={sysInfo.whisper_ready ? "text-emerald-400" : "text-amber-400"}>
                    {sysInfo.whisper_ready ? "✓ whisper.cpp 就绪" : "! whisper-cli 未检测到"}
                  </span>
                </div>
              </div>
            </div>
          )}

          {savedMsg && (
            <div className="p-2.5 rounded-lg bg-emerald-500/10 border border-emerald-500/30 text-emerald-400 text-xs text-center">
              {savedMsg}
            </div>
          )}

          <div className="flex items-center justify-end gap-2 pt-2 border-t border-[var(--border)]">
            <button
              type="button"
              onClick={onClose}
              className="px-4 py-2 rounded-lg text-xs font-medium text-[var(--text-muted)] hover:bg-[var(--border)] transition-colors"
            >
              取消
            </button>
            <button
              type="submit"
              disabled={saving}
              className="px-5 py-2 rounded-lg text-xs font-medium bg-indigo-600 hover:bg-indigo-500 text-white shadow-sm transition-colors disabled:opacity-50"
            >
              {saving ? "保存中..." : "保存设置"}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}
