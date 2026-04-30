import { useRef, useState, useCallback } from "react";

export default function UploadZone({ onUpload, uploading }) {
  const inputRef = useRef(null);
  const [dragging, setDragging] = useState(false);
  const [dragCounter, setDragCounter] = useState(0);

  const handleDrag = useCallback((e, entering) => {
    e.preventDefault();
    e.stopPropagation();
    setDragCounter((prev) => {
      const next = entering ? prev + 1 : prev - 1;
      setDragging(next > 0);
      return Math.max(0, next);
    });
  }, []);

  const handleDrop = useCallback(
    (e) => {
      e.preventDefault();
      e.stopPropagation();
      setDragging(false);
      setDragCounter(0);
      const file = e.dataTransfer?.files?.[0];
      if (file && (file.name.endsWith(".mp4") || file.type.startsWith("video/"))) {
        onUpload(file);
      }
    },
    [onUpload],
  );

  const handleChange = useCallback(
    (e) => {
      const file = e.target.files?.[0];
      if (file) onUpload(file);
      e.target.value = "";
    },
    [onUpload],
  );

  return (
    <div
      onDragEnter={(e) => handleDrag(e, true)}
      onDragLeave={(e) => handleDrag(e, false)}
      onDragOver={(e) => e.preventDefault()}
      onDrop={handleDrop}
      onClick={() => inputRef.current?.click()}
      className={`
        relative cursor-pointer rounded-2xl border-2 border-dashed p-8 md:p-12 text-center
        transition-all duration-300 select-none
        ${dragging
          ? "border-indigo-400 bg-indigo-500/5 scale-[1.01]"
          : "border-[var(--border)] hover:border-indigo-500/30 hover:bg-[var(--surface)]"
        }
      `}
    >
      <input
        ref={inputRef}
        type="file"
        accept="video/mp4,video/*"
        className="hidden"
        onChange={handleChange}
        disabled={uploading}
      />

      {uploading ? (
        <div className="flex flex-col items-center gap-3">
          <svg className="w-10 h-10 text-indigo-500 animate-spin" fill="none" viewBox="0 0 24 24">
            <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
            <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
          </svg>
          <p className="text-sm font-medium text-[var(--text)]">上传中...</p>
          <p className="text-xs text-[var(--text-muted)]">正在保存视频文件</p>
        </div>
      ) : (
        <div className="flex flex-col items-center gap-3">
          {/* Upload icon */}
          <div className="w-12 h-12 rounded-2xl bg-indigo-500/10 flex items-center justify-center mb-1">
            <svg className="w-6 h-6 text-indigo-500" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.5}>
              <path strokeLinecap="round" strokeLinejoin="round" d="M12 16.5V9.75m0 0l3 3m-3-3l-3 3M6.75 19.5a4.5 4.5 0 01-1.41-8.775 5.25 5.25 0 0110.233-2.33 3 3 0 013.758 3.848A3.752 3.752 0 0118 19.5H6.75z" />
            </svg>
          </div>

          <div>
            <p className="text-sm font-medium text-[var(--text)]">
              拖拽视频到此处，或<span className="text-[var(--accent)]">点击选择</span>
            </p>
            <p className="text-xs text-[var(--text-muted)] mt-1">支持 MP4 格式，最大 2GB</p>
          </div>
        </div>
      )}
    </div>
  );
}
