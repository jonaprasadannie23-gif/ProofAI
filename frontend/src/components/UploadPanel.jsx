import { useState, useRef } from "react";
import axios from "axios";

const ACCEPTED_EXTENSIONS = ".csv,.xlsx,.xls,.json,.html,.htm,.txt,.pdf";

/* ── SVG icons ──────────────────────────────────────────────── */
function UploadIcon() {
  return (
    <svg viewBox="0 0 24 24" aria-hidden="true">
      <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4" />
      <polyline points="17 8 12 3 7 8" />
      <line x1="12" y1="3" x2="12" y2="15" />
    </svg>
  );
}

function FileIcon() {
  return (
    <svg viewBox="0 0 24 24" aria-hidden="true">
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

/* ── Component ──────────────────────────────────────────────── */
export default function UploadPanel({
  files = [],
  dataset,
  activeFileId,
  onUpload,
  onSelectFile,
  onRemoveFile,
  onClear,
}) {
  const [dragging, setDragging] = useState(false);
  const [loading, setLoading]   = useState(false);
  const [error, setError]       = useState(null);
  const inputRef = useRef();

  const uploadFile = async (file) => {
    if (!file) return;
    setError(null);
    setLoading(true);
    const form = new FormData();
    form.append("file", file);
    try {
      const res = await axios.post("/api/upload", form);
      onUpload({
        ...res.data,
        fileObject: file,
        size: file.size,
        uploadDate: new Date().toISOString(),
      });
    } catch (e) {
      setError(e.response?.data?.detail || "Upload failed. Is the backend running?");
    } finally {
      setLoading(false);
    }
  };

  const handleDrop = (e) => {
    e.preventDefault();
    setDragging(false);
    if (e.dataTransfer.files && e.dataTransfer.files.length > 0) {
      uploadFile(e.dataTransfer.files[0]);
    }
  };

  // Fallback files list if only single dataset prop passed
  const displayFiles = files.length > 0
    ? files
    : (dataset ? [dataset] : []);

  const activeId = activeFileId || dataset?.id || dataset?.filename;

  return (
    <div className="card" role="region" aria-label="Dataset upload">
      {/* Hidden file input */}
      <input
        ref={inputRef}
        type="file"
        accept={ACCEPTED_EXTENSIONS}
        style={{ display: "none" }}
        onChange={(e) => uploadFile(e.target.files[0])}
      />

      <div className="card-label-row">
        <p className="card-label" style={{ marginBottom: 0 }}>
          {displayFiles.length > 0 ? `Datasets (${displayFiles.length})` : "Dataset"}
        </p>
        {displayFiles.length > 0 && (
          <button
            className="add-files-btn"
            onClick={() => !loading && inputRef.current.click()}
            disabled={loading}
          >
            + Add files
          </button>
        )}
      </div>

      {loading && (
        <div className="dropzone-loading" style={{ padding: "12px 0" }}>
          <div className="upload-spinner" aria-hidden="true" />
          <p className="dropzone-secondary">Parsing dataset…</p>
        </div>
      )}

      {/* ── Dropzone (no files uploaded yet) ── */}
      {displayFiles.length === 0 && !loading && (
        <>
          <div
            className={`dropzone${dragging ? " dragging" : ""}`}
            onClick={() => !loading && inputRef.current.click()}
            onDragOver={(e) => { e.preventDefault(); setDragging(true); }}
            onDragLeave={() => setDragging(false)}
            onDrop={handleDrop}
            role="button"
            tabIndex={0}
            aria-label="Upload a data file"
            onKeyDown={(e) => e.key === "Enter" && inputRef.current.click()}
          >
            <div className="dropzone-upload-icon">
              <UploadIcon />
            </div>
            <p className="dropzone-primary">Drop your file here</p>
            <p className="dropzone-secondary">
              or <span>click to browse</span>
            </p>
            <p className="dropzone-formats">
              CSV · Excel · JSON · HTML · TXT · PDF
            </p>
          </div>

          {error && (
            <p className="inline-error" role="alert">
              {error}
            </p>
          )}
        </>
      )}

      {/* ── Multiple uploaded files list ── */}
      {displayFiles.length > 0 && (
        <>
          <div
            className="file-list"
            onDragOver={(e) => { e.preventDefault(); setDragging(true); }}
            onDragLeave={() => setDragging(false)}
            onDrop={handleDrop}
          >
            {displayFiles.map((file) => {
              const fileKey = file.id || file.filename;
              const isActive = activeId === fileKey || activeId === file.id || (dataset && dataset.filename === file.filename);
              const rows = file.row_count ?? file.rows ?? 0;
              const cols = file.col_count ?? file.columns?.length ?? 0;
              const fileType = file.file_type ?? "file";

              return (
                <div
                  key={fileKey}
                  className={`file-pill-item${isActive ? " active" : ""}`}
                  onClick={() => onSelectFile && onSelectFile(file)}
                  role="button"
                  tabIndex={0}
                  aria-label={`Select ${file.filename}`}
                >
                  <div className="file-pill-left">
                    <div className="file-pill-icon" aria-hidden="true">
                      <FileIcon />
                    </div>
                    <div className="file-pill-info">
                      <div className="file-pill-name-row">
                        <span className="file-pill-name">{file.filename}</span>
                        {isActive && <span className="active-badge">Active</span>}
                      </div>
                      <div className="file-pill-meta">
                        {file.is_tabular === false ? (
                          <span className="file-pill-type">{fileType.toUpperCase()} · Non-tabular</span>
                        ) : (
                          <span className="file-pill-type">
                            {fileType.toUpperCase()} · {rows.toLocaleString()} rows · {cols} cols
                          </span>
                        )}
                      </div>
                    </div>
                  </div>
                  <button
                    className="file-pill-remove"
                    onClick={(e) => {
                      e.stopPropagation();
                      if (onRemoveFile && file.id) {
                        onRemoveFile(file.id);
                      } else if (onClear) {
                        onClear();
                      }
                    }}
                    aria-label={`Remove ${file.filename}`}
                    title="Remove dataset"
                  >
                    <XIcon />
                  </button>
                </div>
              );
            })}
          </div>

          {error && (
            <p className="inline-error" role="alert">
              {error}
            </p>
          )}

          {/* Active dataset non-tabular warning */}
          {dataset?.is_tabular === false && dataset?.parse_error && (
            <p className="inline-warn" role="note">
              {dataset.parse_error}
            </p>
          )}
        </>
      )}
    </div>
  );
}
