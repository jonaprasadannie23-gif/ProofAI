/* FileManager.jsx — My Data view: lists all uploaded files */
import { useState, useRef } from "react";
import axios from "axios";

const ACCEPTED_EXTENSIONS = ".csv,.xlsx,.xls,.json,.html,.htm,.txt,.pdf";

function FileIcon({ type }) {
  const colors = {
    csv:   "var(--green)",
    excel: "#22C55E",
    json:  "#F59E0B",
    html:  "#F97316",
    txt:   "var(--text-muted)",
    pdf:   "#EF4444",
    default: "var(--accent)",
  };
  const color = colors[type] || colors.default;
  return (
    <svg viewBox="0 0 24 24" aria-hidden="true" style={{ color }}>
      <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z" />
      <polyline points="14 2 14 8 20 8" />
    </svg>
  );
}

function XIcon() {
  return (
    <svg viewBox="0 0 24 24" aria-hidden="true">
      <line x1="18" y1="6" x2="6" y2="18" />
      <line x1="6" y1="6" x2="18" y2="18" />
    </svg>
  );
}

function UploadIcon() {
  return (
    <svg viewBox="0 0 24 24" aria-hidden="true">
      <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4" />
      <polyline points="17 8 12 3 7 8" />
      <line x1="12" y1="3" x2="12" y2="15" />
    </svg>
  );
}

function formatSize(bytes) {
  if (!bytes) return "—";
  if (bytes < 1024) return `${bytes} B`;
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
  return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
}

export default function FileManager({ files, onSelectFile, onFilesChange, activeFileId }) {
  const [uploading, setUploading] = useState(false);
  const [error, setError] = useState(null);
  const inputRef = useRef();

  const handleFiles = async (fileList) => {
    const arr = Array.from(fileList);
    if (!arr.length) return;
    setError(null);
    setUploading(true);

    const newFiles = [];
    const errors = [];

    for (const file of arr) {
      const form = new FormData();
      form.append("file", file);
      try {
        const res = await axios.post("/api/upload", form);
        newFiles.push({
          id: `${Date.now()}-${Math.random()}`,
          fileObject: file,
          uploadDate: new Date().toISOString(),
          size: file.size,
          ...res.data,
        });
      } catch (e) {
        const detail = e.response?.data?.detail || `Failed to upload ${file.name}`;
        errors.push(detail);
      }
    }

    if (errors.length) setError(errors.join(" | "));
    if (newFiles.length) onFilesChange([...files, ...newFiles]);
    setUploading(false);
  };

  const handleDrop = (e) => {
    e.preventDefault();
    handleFiles(e.dataTransfer.files);
  };

  const removeFile = (id) => {
    onFilesChange(files.filter((f) => f.id !== id));
  };

  return (
    <div className="view-panel">
      <div className="view-header">
        <h2 className="view-title">My Data</h2>
        <p className="view-subtitle">Uploaded datasets available for analysis</p>
      </div>

      {/* Upload drop area */}
      <div
        className="fm-dropzone"
        onDragOver={(e) => e.preventDefault()}
        onDrop={handleDrop}
        onClick={() => !uploading && inputRef.current.click()}
        role="button"
        tabIndex={0}
        aria-label="Upload files"
        onKeyDown={(e) => e.key === "Enter" && inputRef.current.click()}
      >
        <input
          ref={inputRef}
          type="file"
          accept={ACCEPTED_EXTENSIONS}
          multiple
          style={{ display: "none" }}
          onChange={(e) => handleFiles(e.target.files)}
        />
        {uploading ? (
          <span className="fm-uploading">
            <span className="upload-spinner" aria-hidden="true" />
            Uploading…
          </span>
        ) : (
          <>
            <span className="fm-drop-icon"><UploadIcon /></span>
            <span className="fm-drop-text">
              Drop files here or <span>click to browse</span>
            </span>
            <span className="fm-drop-hint">
              CSV · Excel · JSON · HTML · TXT · PDF
            </span>
          </>
        )}
      </div>

      {error && <p className="inline-error" role="alert">{error}</p>}

      {/* File list */}
      {files.length === 0 ? (
        <div className="fm-empty">
          <p>No files uploaded yet.</p>
          <p>Upload a file above to get started.</p>
        </div>
      ) : (
        <div className="fm-list">
          {files.map((f) => (
            <div
              key={f.id}
              className={`fm-card${activeFileId === f.id ? " selected" : ""}`}
              onClick={() => onSelectFile(f)}
              role="button"
              tabIndex={0}
              aria-pressed={activeFileId === f.id}
              onKeyDown={(e) => e.key === "Enter" && onSelectFile(f)}
            >
              <div className="fm-card-icon">
                <FileIcon type={f.file_type || "default"} />
              </div>
              <div className="fm-card-info">
                <div className="fm-card-name">{f.filename}</div>
                <div className="fm-card-meta">
                  <span className="fm-badge">{(f.file_type || "file").toUpperCase()}</span>
                  {f.is_tabular && (
                    <>
                      <span>{(f.row_count || 0).toLocaleString()} rows</span>
                      <span>·</span>
                      <span>{(f.col_count || 0)} cols</span>
                    </>
                  )}
                  {f.size && <span>· {formatSize(f.size)}</span>}
                  {f.uploadDate && (
                    <span>· {new Date(f.uploadDate).toLocaleDateString()}</span>
                  )}
                </div>
                {!f.is_tabular && f.parse_error && (
                  <div className="fm-card-warn">{f.parse_error}</div>
                )}
              </div>
              <button
                className="fm-card-remove"
                onClick={(e) => { e.stopPropagation(); removeFile(f.id); }}
                aria-label={`Remove ${f.filename}`}
              >
                <XIcon />
              </button>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
