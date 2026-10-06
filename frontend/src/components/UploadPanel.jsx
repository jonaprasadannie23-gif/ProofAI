import { useState, useRef } from "react";
import axios from "axios";

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
export default function UploadPanel({ onUpload, onClear, dataset }) {
  const [dragging, setDragging] = useState(false);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const inputRef = useRef();

  const uploadFile = async (file) => {
    if (!file) return;
    if (!file.name.endsWith(".csv")) {
      setError("Only CSV files are supported.");
      return;
    }
    setError(null);
    setLoading(true);
    const form = new FormData();
    form.append("file", file);
    try {
      const res = await axios.post("/api/upload", form);
      // Store the raw File object alongside server metadata so /analyze can resend it
      onUpload({ ...res.data, fileObject: file });
    } catch (e) {
      setError(e.response?.data?.detail || "Upload failed. Is the backend running?");
    } finally {
      setLoading(false);
    }
  };

  const handleDrop = (e) => {
    e.preventDefault();
    setDragging(false);
    uploadFile(e.dataTransfer.files[0]);
  };

  const handleClear = () => {
    setError(null);
    onClear();
  };

  return (
    <div className="card" role="region" aria-label="Dataset upload">
      <p className="card-label">Dataset</p>

      {/* ── Dropzone (no file yet) ── */}
      {!dataset ? (
        <>
          <div
            className={`dropzone${dragging ? " dragging" : ""}`}
            onClick={() => !loading && inputRef.current.click()}
            onDragOver={(e) => { e.preventDefault(); setDragging(true); }}
            onDragLeave={() => setDragging(false)}
            onDrop={handleDrop}
            role="button"
            tabIndex={0}
            aria-label="Upload CSV file"
            onKeyDown={(e) => e.key === "Enter" && inputRef.current.click()}
          >
            <input
              ref={inputRef}
              type="file"
              accept=".csv"
              style={{ display: "none" }}
              onChange={(e) => uploadFile(e.target.files[0])}
            />

            {loading ? (
              <div className="dropzone-loading">
                <div className="upload-spinner" aria-hidden="true" />
                <p className="dropzone-secondary">Parsing dataset…</p>
              </div>
            ) : (
              <>
                <div className="dropzone-upload-icon">
                  <UploadIcon />
                </div>
                <p className="dropzone-primary">Drop your CSV here</p>
                <p className="dropzone-secondary">
                  or <span>click to browse</span>
                </p>
              </>
            )}
          </div>

          {error && (
            <p className="inline-error" role="alert">
              {error}
            </p>
          )}
        </>
      ) : (
        /* ── File loaded state ── */
        <>
          <div className="file-pill">
            <div className="file-pill-icon" aria-hidden="true">
              <FileIcon />
            </div>
            <div className="file-pill-info">
              <div className="file-pill-name">{dataset.filename}</div>
              <div className="file-pill-meta">
                {dataset.rows.toLocaleString()} rows · {dataset.columns.length} columns
              </div>
            </div>
            <button
              className="file-pill-remove"
              onClick={handleClear}
              aria-label="Remove dataset"
            >
              <XIcon />
            </button>
          </div>

          {/* Stats */}
          <div className="data-stats">
            <div className="stat-item">
              <div className="stat-value">{dataset.rows.toLocaleString()}</div>
              <div className="stat-label">Rows</div>
            </div>
            <div className="stat-item">
              <div className="stat-value">{dataset.columns.length}</div>
              <div className="stat-label">Columns</div>
            </div>
          </div>
        </>
      )}
    </div>
  );
}
