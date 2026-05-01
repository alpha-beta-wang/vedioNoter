import { useState, useEffect, useCallback } from "react";
import { Routes, Route, useNavigate } from "react-router-dom";
import { listVideos, uploadVideo, deleteVideo, startTranscribe, startSummarize, pollTask, getTranscript, getNote } from "./api";
import Layout from "./components/Layout";
import UploadZone from "./components/UploadZone";

/* ================================================================
   Shared state hook
   ================================================================ */
function useVideos() {
  const [videos, setVideos] = useState([]);
  const [loading, setLoading] = useState(true);

  const refresh = useCallback(async () => {
    setLoading(true);
    try {
      const data = await listVideos();
      setVideos(data);
    } catch (e) {
      console.error(e);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => { refresh(); }, [refresh]);

  return { videos, loading, refresh };
}

/* ================================================================
   Dashboard
   ================================================================ */
function Dashboard({ videos, loading, refresh }) {
  const navigate = useNavigate();
  const [uploading, setUploading] = useState(false);
  const [tasks, setTasks] = useState({});
  const [language, setLanguage] = useState("zh");
  const [sumStyle, setSumStyle] = useState("general");

  const handleUpload = async (file) => {
    setUploading(true);
    try {
      await uploadVideo(file);
      await refresh();
    } finally {
      setUploading(false);
    }
  };

  const handleDelete = async (name) => {
    if (!confirm(`确认删除「${name}」及所有相关文件？`)) return;
    await deleteVideo(name);
    refresh();
  };

  const handleTranscribe = async (video) => {
    try {
      const { task_id } = await startTranscribe(video.name, "small", language);
      setTasks((prev) => ({ ...prev, [task_id]: { ...video, type: "transcribe", status: "running", progress: 0, error: null } }));
      pollLoop(task_id);
    } catch (e) {
      const tid = "err-" + Math.random().toString(36).slice(2, 8);
      setTasks((prev) => ({ ...prev, [tid]: { ...video, type: "transcribe", status: "failed", progress: 0, error: "无法连接到后端服务，请确认已启动 python web/backend/server.py" } }));
      setTimeout(() => setTasks((prev) => { const n = { ...prev }; delete n[tid]; return n; }), 6000);
    }
  };

  const handleSummarize = async (video) => {
    try {
      const { task_id } = await startSummarize(video.name, sumStyle);
      setTasks((prev) => ({ ...prev, [task_id]: { ...video, type: "summarize", status: "running", progress: 0, error: null } }));
      pollLoop(task_id);
    } catch (e) {
      const tid = "err-" + Math.random().toString(36).slice(2, 8);
      setTasks((prev) => ({ ...prev, [tid]: { ...video, type: "summarize", status: "failed", progress: 0, error: "无法连接到后端服务，请确认已启动 python web/backend/server.py" } }));
      setTimeout(() => setTasks((prev) => { const n = { ...prev }; delete n[tid]; return n; }), 6000);
    }
  };

  const pollLoop = async (taskId) => {
    const poll = async () => {
      try {
        const t = await pollTask(taskId);
        setTasks((prev) => ({ ...prev, [taskId]: t }));
        if (t.status === "completed" || t.status === "failed") {
          refresh();
          setTimeout(() => setTasks((prev) => { const n = { ...prev }; delete n[taskId]; return n; }), t.status === "completed" ? 4000 : 8000);
          return;
        }
      } catch (e) { /* ignore */ }
      setTimeout(poll, 800);
    };
    poll();
  };

  return (
    <div className="animate-fade-in">
      {/* Upload area */}
      <UploadZone onUpload={handleUpload} uploading={uploading} />

      {/* Active tasks */}
      {Object.entries(tasks).length > 0 && (
        <div className="mt-3 space-y-3">
          {Object.entries(tasks).map(([id, t]) => (
            <TaskCard key={id} task={t} />
          ))}
        </div>
      )}

      {/* Video list */}
      <div className="mt-8">
        <div className="flex items-center justify-between mb-5">
          <h2 className="text-lg font-semibold tracking-tight">
            视频列表
            <span className="ml-2 text-sm font-normal text-[var(--text-muted)]">
              {videos.length} 个视频
            </span>
          </h2>
          <div className="flex items-center gap-2">
            {/* Language selector */}
            <span className="text-xs text-[var(--text-muted)]">转录</span>
            <div className="flex rounded-lg border border-[var(--border)] overflow-hidden">
              {[
                { value: "zh", label: "中文" },
                { value: "en", label: "EN" },
                { value: "auto", label: "自动" },
              ].map((opt) => (
                <button
                  key={opt.value}
                  onClick={() => setLanguage(opt.value)}
                  className={`px-2.5 py-1.5 text-xs font-medium transition-colors ${
                    language === opt.value
                      ? "bg-indigo-500 text-white"
                      : "text-[var(--text-muted)] hover:text-[var(--text)] hover:bg-[var(--border)]"
                  }`}
                >
                  {opt.label}
                </button>
              ))}
            </div>
            {/* Style selector */}
            <span className="text-xs text-[var(--text-muted)] ml-2">笔记</span>
            <div className="flex rounded-lg border border-[var(--border)] overflow-hidden">
              {[
                { value: "general", label: "通用" },
                { value: "stem", label: "理工科" },
              ].map((opt) => (
                <button
                  key={opt.value}
                  onClick={() => setSumStyle(opt.value)}
                  className={`px-2.5 py-1.5 text-xs font-medium transition-colors ${
                    sumStyle === opt.value
                      ? "bg-violet-500 text-white"
                      : "text-[var(--text-muted)] hover:text-[var(--text)] hover:bg-[var(--border)]"
                  }`}
                >
                  {opt.label}
                </button>
              ))}
            </div>
            <button
              onClick={refresh}
              className="px-3 py-1.5 text-xs font-medium rounded-lg border border-[var(--border)] hover:bg-[var(--border)] transition-colors"
            >
              刷新
            </button>
          </div>
        </div>

        {loading ? (
          <div className="grid gap-3">
            {[1, 2, 3].map((i) => (
              <div key={i} className="skeleton h-20 rounded-xl" />
            ))}
          </div>
        ) : videos.length === 0 ? (
          <EmptyState />
        ) : (
          <div className="grid gap-3">
            {videos.map((v) => (
              <VideoCard
                key={v.name}
                video={v}
                onTranscribe={() => handleTranscribe(v)}
                onSummarize={() => handleSummarize(v)}
                onDelete={() => handleDelete(v)}
                onViewTranscript={() => navigate(`/transcript/${encodeURIComponent(v.name)}`)}
                onViewNote={() => navigate(`/note/${encodeURIComponent(v.name)}`)}
              />
            ))}
          </div>
        )}
      </div>
    </div>
  );
}

/* ================================================================
   Video Card
   ================================================================ */
function VideoCard({ video, onTranscribe, onSummarize, onDelete, onViewTranscript, onViewNote }) {
  return (
    <div className="group flex items-center gap-3 p-4 rounded-xl bg-[var(--surface)] border border-[var(--border)] hover:border-[var(--accent)]/30 transition-all duration-200 animate-slide-in overflow-hidden">
      {/* Icon */}
      <div className="flex-shrink-0 w-9 h-9 rounded-lg bg-indigo-500/10 flex items-center justify-center">
        <svg className="w-4.5 h-4.5 text-indigo-500" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.5}>
          <path strokeLinecap="round" strokeLinejoin="round" d="M15.75 10.5l4.72-4.72a.75.75 0 011.28.53v11.38a.75.75 0 01-1.28.53l-4.72-4.72M4.5 18.75h9a2.25 2.25 0 002.25-2.25v-9a2.25 2.25 0 00-2.25-2.25h-9A2.25 2.25 0 002.25 7.5v9a2.25 2.25 0 002.25 2.25z" />
        </svg>
      </div>

      {/* Info */}
      <div className="flex-1 min-w-0">
        <div className="font-medium truncate text-sm">{video.name.replace(".mp4", "")}</div>
        <div className="flex items-center gap-2 mt-1 text-xs text-[var(--text-muted)]">
          <span className="flex-shrink-0">{video.size_mb} MB</span>
          {video.has_transcript && (
            <span className="flex items-center gap-1 text-emerald-500 flex-shrink-0">
              <span className="w-1.5 h-1.5 rounded-full bg-emerald-500" /> 已转码
            </span>
          )}
          {video.has_note && (
            <span className="flex items-center gap-1 text-violet-500 flex-shrink-0">
              <span className="w-1.5 h-1.5 rounded-full bg-violet-500" /> 已整理
            </span>
          )}
        </div>
      </div>

      {/* Actions */}
      <div className="flex items-center gap-1 flex-shrink-0 opacity-0 group-hover:opacity-100 transition-opacity">
        {video.has_transcript && (
          <Btn onClick={onViewTranscript} title="查看转录">
            <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.5}>
              <path strokeLinecap="round" strokeLinejoin="round" d="M2.036 12.322a1.012 1.012 0 010-.639C3.423 7.51 7.36 4.5 12 4.5c4.638 0 8.573 3.007 9.963 7.178.07.207.07.431 0 .639C20.577 16.49 16.64 19.5 12 19.5c-4.638 0-8.573-3.007-9.963-7.178z" />
              <path strokeLinecap="round" strokeLinejoin="round" d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
            </svg>
          </Btn>
        )}
        {video.has_note && (
          <Btn onClick={onViewNote} title="查看笔记">
            <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.5}>
              <path strokeLinecap="round" strokeLinejoin="round" d="M19.5 14.25v-2.625a3.375 3.375 0 00-3.375-3.375h-1.5A1.125 1.125 0 0113.5 7.125v-1.5a3.375 3.375 0 00-3.375-3.375H8.25m0 12.75h7.5m-7.5 3H12M10.5 2.25H5.625c-.621 0-1.125.504-1.125 1.125v17.25c0 .621.504 1.125 1.125 1.125h12.75c.621 0 1.125-.504 1.125-1.125V11.25a9 9 0 00-9-9z" />
            </svg>
          </Btn>
        )}
        <Btn onClick={onTranscribe} title="语音转码" accent>
          <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.5}>
            <path strokeLinecap="round" strokeLinejoin="round" d="M19.114 5.636a9 9 0 010 12.728M16.463 8.288a5.25 5.25 0 010 7.424M6.75 8.25l4.72-4.72a.75.75 0 011.28.53v15.88a.75.75 0 01-1.28.53l-4.72-4.72H4.51c-.88 0-1.704-.507-1.938-1.354A9.01 9.01 0 012.25 12c0-.83.112-1.633.322-2.396C2.806 8.756 3.63 8.25 4.51 8.25H6.75z" />
          </svg>
        </Btn>
        {video.has_transcript && !video.has_note && (
          <Btn onClick={onSummarize} title="AI 整理笔记" accent>
            <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.5}>
              <path strokeLinecap="round" strokeLinejoin="round" d="M9.813 15.904L9 18.75l-.813-2.846a4.5 4.5 0 00-3.09-3.09L2.25 12l2.846-.813a4.5 4.5 0 003.09-3.09L9 5.25l.813 2.846a4.5 4.5 0 003.09 3.09L15.75 12l-2.846.813a4.5 4.5 0 00-3.09 3.09zM18.259 8.715L18 9.75l-.259-1.035a3.375 3.375 0 00-2.455-2.456L14.25 6l1.036-.259a3.375 3.375 0 002.455-2.456L18 2.25l.259 1.035a3.375 3.375 0 002.455 2.456L21.75 6l-1.036.259a3.375 3.375 0 00-2.455 2.456zM16.894 20.567L16.5 21.75l-.394-1.183a2.25 2.25 0 00-1.423-1.423L13.5 18.75l1.183-.394a2.25 2.25 0 001.423-1.423l.394-1.183.394 1.183a2.25 2.25 0 001.423 1.423l1.183.394-1.183.394a2.25 2.25 0 00-1.423 1.423z" />
            </svg>
          </Btn>
        )}
        <Btn onClick={onDelete} title="删除" danger>
          <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.5}>
            <path strokeLinecap="round" strokeLinejoin="round" d="M14.74 9l-.346 9m-4.788 0L9.26 9m9.968-3.21c.342.052.682.107 1.022.166m-1.022-.165L18.16 19.673a2.25 2.25 0 01-2.244 2.077H8.084a2.25 2.25 0 01-2.244-2.077L4.772 5.79m14.456 0a48.108 48.108 0 00-3.478-.397m-12 .562c.34-.059.68-.114 1.022-.165m0 0a48.11 48.11 0 013.478-.397m7.5 0v-.916c0-1.18-.91-2.164-2.09-2.201a51.964 51.964 0 00-3.32 0c-1.18.037-2.09 1.022-2.09 2.201v.916m7.5 0a48.667 48.667 0 00-7.5 0" />
          </svg>
        </Btn>
      </div>
    </div>
  );
}

function Btn({ onClick, children, title, accent, danger }) {
  const base = "p-2 rounded-lg transition-colors";
  const colors = danger
    ? "text-rose-400 hover:bg-rose-500/10 hover:text-rose-300"
    : accent
      ? "text-[var(--accent)] hover:bg-indigo-500/10"
      : "text-[var(--text-muted)] hover:text-[var(--text)] hover:bg-[var(--border)]";
  return (
    <button onClick={onClick} className={`${base} ${colors}`} title={title}>
      {children}
    </button>
  );
}

/* ================================================================
   Task Card (progress bar)
   ================================================================ */
function TaskCard({ task }) {
  const isFailed = task.status === "failed";
  const isCompleted = task.status === "completed";

  const icon = isFailed ? "❌" : isCompleted ? "✅" : task.type === "summarize" ? "✨" : "🎙️";
  const label = isFailed
    ? (task.error ? "任务失败" : "任务失败")
    : isCompleted
      ? (task.type === "summarize" ? "整理完成" : "转录完成")
      : task.type === "summarize"
        ? "AI 整理中"
        : "语音识别中";

  const barColor = isFailed ? "bg-rose-500" : isCompleted ? "bg-emerald-500" : "bg-indigo-500";
  const borderColor = isFailed ? "border-rose-500/20" : isCompleted ? "border-emerald-500/20" : "border-indigo-500/20";

  return (
    <div className={`p-4 rounded-xl bg-[var(--surface)] border ${borderColor} animate-slide-in`}>
      <div className="flex items-center gap-2 mb-2 text-sm">
        <span>{icon}</span>
        <span className="font-medium">{label}</span>
        <span className="text-[var(--text-muted)] text-xs ml-1 truncate">{task.video?.name || task.video}</span>
        <span className="ml-auto text-xs text-[var(--text-muted)] flex-shrink-0">{task.progress}%</span>
      </div>
      <div className="h-1.5 rounded-full bg-[var(--border)] overflow-hidden">
        <div
          className={`h-full rounded-full transition-all duration-500 ${barColor}`}
          style={{ width: `${isFailed ? 100 : task.progress}%` }}
        />
      </div>
      {task.error && (
        <p className="mt-2 text-xs text-rose-400">{task.error}</p>
      )}
      {isCompleted && task.output_file && (
        <p className="mt-2 text-xs text-[var(--text-muted)]">已保存: {task.output_file}</p>
      )}
    </div>
  );
}

/* ================================================================
   Empty State
   ================================================================ */
function EmptyState() {
  return (
    <div className="text-center py-16 text-[var(--text-muted)]">
      <svg className="w-12 h-12 mx-auto mb-4 opacity-40" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1}>
        <path strokeLinecap="round" strokeLinejoin="round" d="M15.75 10.5l4.72-4.72a.75.75 0 011.28.53v11.38a.75.75 0 01-1.28.53l-4.72-4.72M4.5 18.75h9a2.25 2.25 0 002.25-2.25v-9a2.25 2.25 0 00-2.25-2.25h-9A2.25 2.25 0 002.25 7.5v9a2.25 2.25 0 002.25 2.25z" />
      </svg>
      <p className="text-sm">还没有视频，拖拽上传一个 .mp4 试试</p>
    </div>
  );
}

/* ================================================================
   Transcript Page
   ================================================================ */
function TranscriptPage() {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const name = decodeURIComponent(window.location.pathname.split("/transcript/")[1]);

  useEffect(() => {
    getTranscript(name)
      .then(setData)
      .catch(console.error)
      .finally(() => setLoading(false));
  }, [name]);

  if (loading) return <div className="animate-fade-in p-8 text-center text-[var(--text-muted)]">加载中...</div>;
  if (!data) return <div className="animate-fade-in p-8 text-center text-rose-400">转录不存在</div>;

  // Parse timestamped lines
  const tsLines = [];
  const tsSection = data.timestamped || "";
  const lines = tsSection.split("\n");
  for (const line of lines) {
    const m = line.match(/^- \[(\d{2}:\d{2}(?::\d{2})?)\]\s+(.+)/);
    if (m) tsLines.push({ time: m[1], text: m[2] });
  }

  // Parse full text (remove markdown headers for display)
  const fullText = (data.full_text || "")
    .replace(/^# .+$/gm, "")
    .replace(/^\*\*.+\*\*$/gm, "")
    .replace(/^---$/gm, "")
    .replace(/^## .+$/gm, "")
    .trim();

  return (
    <div className="animate-fade-in max-w-4xl mx-auto">
      <div className="mb-6">
        <a href="/" className="text-sm text-[var(--accent)] hover:underline">← 返回列表</a>
        <h1 className="text-xl font-bold mt-3 mb-1">{name.replace(".md", "").replace(".mp4", "")}</h1>
      </div>

      {/* Tabs */}
      <Tabs labels={["全文阅读", "时间戳视图"]}>
        {/* Tab 1: Full text */}
        <div className="bg-[var(--surface)] rounded-xl border border-[var(--border)] p-6 md:p-8 leading-loose text-[0.95rem] whitespace-pre-line">
          {fullText}
        </div>

        {/* Tab 2: Timestamped */}
        <div className="bg-[var(--surface)] rounded-xl border border-[var(--border)] p-4 md:p-6">
          {tsLines.map((line, i) => (
            <div key={i} className="ts-line">
              <span className="ts">{line.time}</span>
              {line.text}
            </div>
          ))}
        </div>
      </Tabs>
    </div>
  );
}

/* ================================================================
   Note Page
   ================================================================ */
function NotePage() {
  const [content, setContent] = useState("");
  const [loading, setLoading] = useState(true);
  const name = decodeURIComponent(window.location.pathname.split("/note/")[1]);

  useEffect(() => {
    getNote(name)
      .then((d) => setContent(d.content))
      .catch(console.error)
      .finally(() => setLoading(false));
  }, [name]);

  if (loading) return <div className="animate-fade-in p-8 text-center text-[var(--text-muted)]">加载中...</div>;
  if (!content) return <div className="animate-fade-in p-8 text-center text-rose-400">笔记不存在</div>;

  return (
    <div className="animate-fade-in max-w-3xl mx-auto">
      <div className="mb-6">
        <a href="/" className="text-sm text-[var(--accent)] hover:underline">← 返回列表</a>
      </div>
      <div className="bg-[var(--surface)] rounded-xl border border-[var(--border)] p-6 md:p-10 note-content"
        dangerouslySetInnerHTML={{ __html: mdToHtml(content) }}
      />
    </div>
  );
}

/* ================================================================
   Helpers
   ================================================================ */
function Tabs({ labels, children }) {
  const [active, setActive] = useState(0);
  return (
    <div>
      <div className="flex gap-1 mb-4 bg-[var(--surface)] rounded-lg border border-[var(--border)] p-1 w-fit">
        {labels.map((l, i) => (
          <button
            key={i}
            onClick={() => setActive(i)}
            className={`px-4 py-1.5 text-sm rounded-md transition-colors ${
              active === i
                ? "bg-indigo-500 text-white shadow-sm"
                : "text-[var(--text-muted)] hover:text-[var(--text)]"
            }`}
          >
            {l}
          </button>
        ))}
      </div>
      {Array.isArray(children) ? children[active] : children}
    </div>
  );
}

function mdToHtml(md) {
  let html = md
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;");
  html = html.replace(/^#### (.+)$/gm, "<h4>$1</h4>");
  html = html.replace(/^### (.+)$/gm, "<h3>$1</h3>");
  html = html.replace(/^## (.+)$/gm, "<h2>$1</h2>");
  html = html.replace(/^# (.+)$/gm, "<h1>$1</h1>");
  html = html.replace(/\*\*(.+?)\*\*/g, "<strong>$1</strong>");
  html = html.replace(/\*(.+?)\*/g, "<em>$1</em>");
  html = html.replace(/`([^`]+)`/g, "<code>$1</code>");
  html = html.replace(/^---$/gm, "<hr>");
  html = html.replace(/^- (.+)$/gm, "<li>$1</li>");
  html = html.replace(/(<li>.*<\/li>)/s, "<ul>$1</ul>");
  html = html.replace(/<\/li>\n<li>/g, "</li><li>");
  html = html.replace(/^> (.+)$/gm, "<blockquote>$1</blockquote>");
  html = html.replace(/\n\n/g, "</p><p>");
  html = "<p>" + html + "</p>";
  html = html.replace(/<p><h([1-6])>/g, "<h$1>");
  html = html.replace(/<\/h([1-6])><\/p>/g, "</h$1>");
  html = html.replace(/<p><hr><\/p>/g, "<hr>");
  html = html.replace(/<p><ul>/g, "<ul>");
  html = html.replace(/<\/ul><\/p>/g, "</ul>");
  html = html.replace(/<p><blockquote>/g, "<blockquote>");
  html = html.replace(/<\/blockquote><\/p>/g, "</blockquote>");
  html = html.replace(/<p>\s*<\/p>/g, "");
  return html;
}

/* ================================================================
   App
   ================================================================ */
export default function App() {
  const { videos, loading, refresh } = useVideos();
  return (
    <Layout>
      <Routes>
        <Route path="/" element={<Dashboard videos={videos} loading={loading} refresh={refresh} />} />
        <Route path="/transcript/:name" element={<TranscriptPage />} />
        <Route path="/note/:name" element={<NotePage />} />
      </Routes>
    </Layout>
  );
}
