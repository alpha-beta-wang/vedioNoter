const BASE = "/api";

async function request(url, opts = {}) {
  const res = await fetch(`${BASE}${url}`, opts);
  if (!res.ok) {
    const err = await res.json().catch(() => ({}));
    throw new Error(err.error || `HTTP ${res.status}`);
  }
  return res.json();
}

export function listVideos()       { return request("/videos"); }
export function uploadVideo(file)  { const fd = new FormData(); fd.append("file", file); return request("/upload", { method: "POST", body: fd }); }
export function deleteVideo(name)  { return request(`/videos/${encodeURIComponent(name)}`, { method: "DELETE" }); }
export function startTranscribe(name, model = "small", language = "", extractFrames = false) {
  return request(`/transcribe/${encodeURIComponent(name)}`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ model, language, extract_frames: extractFrames }),
  });
}
export function startSummarize(name, style = "general") {
  return request(`/summarize/${encodeURIComponent(name)}`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ style }),
  });
}
export function pollTask(taskId)   { return request(`/tasks/${taskId}`); }
export function getTranscript(name){ return request(`/transcript/${encodeURIComponent(name)}`); }
export function getNote(name)      { return request(`/note/${encodeURIComponent(name)}`); }

// 桌面端专属接口
export function getConfig()         { return request("/config"); }
export function updateConfig(data)  { return request("/config", { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify(data) }); }
export function openFolder(type, name) { return request("/open-folder", { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ type, name }) }); }
export function importFile(path)    { return request("/import-file", { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ path }) }); }
export function getSystemInfo()     { return request("/system-info"); }

