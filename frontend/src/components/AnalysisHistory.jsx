/* AnalysisHistory.jsx — session analysis history view */

function VerifiedIcon() {
  return (
    <svg viewBox="0 0 24 24" aria-hidden="true" style={{ color: "var(--green)" }}>
      <polyline points="20 6 9 17 4 12" />
    </svg>
  );
}

function RefusedIcon() {
  return (
    <svg viewBox="0 0 24 24" aria-hidden="true" style={{ color: "var(--amber)" }}>
      <circle cx="12" cy="12" r="10" />
      <line x1="12" y1="8" x2="12" y2="12" />
      <line x1="12" y1="16" x2="12.01" y2="16" />
    </svg>
  );
}

function FailedIcon() {
  return (
    <svg viewBox="0 0 24 24" aria-hidden="true" style={{ color: "var(--red)" }}>
      <circle cx="12" cy="12" r="10" />
      <line x1="15" y1="9" x2="9" y2="15" />
      <line x1="9" y1="9" x2="15" y2="15" />
    </svg>
  );
}

const STATUS_META = {
  success: { label: "Verified",      Icon: VerifiedIcon, cls: "verified" },
  refused: { label: "Refused",       Icon: RefusedIcon,  cls: "refused"  },
  error:   { label: "Failed",        Icon: FailedIcon,   cls: "failed"   },
};

function formatTime(iso) {
  if (!iso) return "";
  const d = new Date(iso);
  return d.toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" });
}

export default function AnalysisHistory({ history, onOpen }) {
  return (
    <div className="view-panel">
      <div className="view-header">
        <h2 className="view-title">Analysis History</h2>
        <p className="view-subtitle">
          All analyses from this session ({history.length} total)
        </p>
      </div>

      {history.length === 0 ? (
        <div className="ah-empty">
          <p>No analyses yet.</p>
          <p>Run an analysis to see it here.</p>
        </div>
      ) : (
        <div className="ah-list">
          {[...history].reverse().map((item) => {
            const meta = STATUS_META[item.status] || STATUS_META.error;
            const Icon = meta.Icon;
            return (
              <button
                key={item.id}
                className="ah-item"
                onClick={() => onOpen(item)}
                aria-label={`Open analysis: ${item.question}`}
              >
                <div className="ah-item-header">
                  <span className={`ah-badge ${meta.cls}`}>
                    <span className="ah-badge-icon"><Icon /></span>
                    {meta.label}
                  </span>
                  <span className="ah-time">{formatTime(item.timestamp)}</span>
                </div>
                <p className="ah-question">{item.question}</p>
                <div className="ah-meta">
                  <span className="ah-filename">{item.filename}</span>
                  {item.answer && (
                    <span className="ah-answer-preview">
                      → {String(item.answer).slice(0, 60)}{String(item.answer).length > 60 ? "…" : ""}
                    </span>
                  )}
                </div>
              </button>
            );
          })}
        </div>
      )}
    </div>
  );
}
