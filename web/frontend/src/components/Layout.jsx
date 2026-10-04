import { useState } from "react";
import { Link, useLocation } from "react-router-dom";
import SettingsModal from "./SettingsModal";
import { openFolder } from "../api";

export default function Layout({ children }) {
  const { pathname } = useLocation();
  const isHome = pathname === "/";
  const [showSettings, setShowSettings] = useState(false);

  const handleOpenOutput = async () => {
    try {
      if (window.electronAPI?.openPath) {
        await window.electronAPI.openPath("output");
      } else {
        await openFolder("output");
      }
    } catch (e) {
      console.error(e);
    }
  };

  return (
    <div className="min-h-screen">
      {/* Header */}
      <header className="sticky top-0 z-50 backdrop-blur-md bg-[var(--bg)]/80 border-b border-[var(--border)]">
        <div className="max-w-6xl mx-auto px-4 md:px-6 h-14 flex items-center justify-between">
          <Link to="/" className="flex items-center gap-2.5 font-semibold tracking-tight text-[var(--text)] hover:opacity-80 transition-opacity">
            <div className="w-7 h-7 rounded-lg bg-indigo-500 flex items-center justify-center">
              <svg className="w-4 h-4 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                <path strokeLinecap="round" strokeLinejoin="round" d="M15.75 10.5l4.72-4.72a.75.75 0 011.28.53v11.38a.75.75 0 01-1.28.53l-4.72-4.72M4.5 18.75h9a2.25 2.25 0 002.25-2.25v-9a2.25 2.25 0 00-2.25-2.25h-9A2.25 2.25 0 002.25 7.5v9a2.25 2.25 0 002.25 2.25z" />
              </svg>
            </div>
            <span className="text-sm">Video Extract</span>
          </Link>

          <nav className="flex items-center gap-2">
            {!isHome && (
              <Link
                to="/"
                className="px-3 py-1.5 text-xs font-medium rounded-lg text-[var(--text-muted)] hover:text-[var(--text)] hover:bg-[var(--border)] transition-colors"
              >
                首页
              </Link>
            )}
            <button
              onClick={handleOpenOutput}
              title="打开输出文件夹"
              className="px-2.5 py-1.5 text-xs font-medium rounded-lg text-[var(--text-muted)] hover:text-[var(--text)] hover:bg-[var(--border)] transition-colors flex items-center gap-1.5"
            >
              <svg className="w-3.5 h-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                <path strokeLinecap="round" strokeLinejoin="round" d="M3.75 9.776c.112-.017.227-.026.344-.026h15.812c.117 0 .232.009.344.026m-16.5 0a2.25 2.25 0 00-1.883 2.542l.857 6a2.25 2.25 0 002.227 1.932H19.05a2.25 2.25 0 002.227-1.932l.857-6a2.25 2.25 0 00-1.883-2.542m-16.5 0V6A2.25 2.25 0 016 3.75h3.879a1.5 1.5 0 011.06.44l2.122 2.12a1.5 1.5 0 001.06.44H18A2.25 2.25 0 0120.25 9v.776" />
              </svg>
              <span>输出目录</span>
            </button>
            <button
              onClick={() => setShowSettings(true)}
              title="应用设置"
              className="px-2.5 py-1.5 text-xs font-medium rounded-lg text-[var(--text-muted)] hover:text-[var(--text)] hover:bg-[var(--border)] transition-colors flex items-center gap-1.5"
            >
              <svg className="w-3.5 h-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                <path strokeLinecap="round" strokeLinejoin="round" d="M10.325 4.317c.426-1.756 2.924-1.756 3.35 0a1.724 1.724 0 002.573 1.066c1.543-.94 3.31.826 2.37 2.37a1.724 1.724 0 001.065 2.572c1.756.426 1.756 2.924 0 3.35a1.724 1.724 0 00-1.066 2.573c.94 1.543-.826 3.31-2.37 2.37a1.724 1.724 0 00-2.572 1.065c-.426 1.756-2.924 1.756-3.35 0a1.724 1.724 0 00-2.573-1.066c-1.543.94-3.31-.826-2.37-2.37a1.724 1.724 0 00-1.065-2.572c-1.756-.426-1.756-2.924 0-3.35a1.724 1.724 0 001.066-2.573c-.94-1.543.826-3.31 2.37-2.37.996.608 2.296.07 2.572-1.065z" />
                <path strokeLinecap="round" strokeLinejoin="round" d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
              </svg>
              <span>设置</span>
            </button>
          </nav>
        </div>
      </header>

      <SettingsModal isOpen={showSettings} onClose={() => setShowSettings(false)} />

      {/* Main */}
      <main className="max-w-6xl mx-auto px-4 md:px-6 py-6 md:py-10">
        {children}
      </main>

      {/* Footer */}
      <footer className="border-t border-[var(--border)] mt-12">
        <div className="max-w-6xl mx-auto px-4 md:px-6 py-6 text-center text-xs text-[var(--text-muted)]">
          Video Extract — 将视频转为结构化学习笔记
        </div>
      </footer>
    </div>
  );
}
