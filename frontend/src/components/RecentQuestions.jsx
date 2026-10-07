/* RecentQuestions.jsx — shows recently asked questions */

const STATUS_META = {
  success: { label: "Verified",  cls: "verified" },
  refused: { label: "Refused",   cls: "refused"  },
  error:   { label: "Failed",    cls: "failed"   },
};

function formatTime(iso) {
  if (!iso) return "";
  const d = new Date(iso);
  const now = new Date();
  const diffMs = now - d;
  const diffMin = Math.floor(diffMs / 60000);
  if (diffMin < 1) return "just now";
  if (diffMin < 60) return `${diffMin}m ago`;
  const diffH = Math.floor(diffMin / 60);
  if (diffH < 24) return `${diffH}h ago`;
  return d.toLocaleDateString();
}

export default function RecentQuestions({ history, onOpen }) {
  // Show only unique recent questions (last 20)
  const recent = [...history].reverse().slice(0, 20);

  return (
    <div className="view-panel">
      <div className="view-header">
        <h2 className="view-title">Recent Questions</h2>
        <p className="view-subtitle">Click any question to view its result</p>
      </div>

      {recent.length === 0 ? (
        <div className="ah-empty">
          <p>No recent questions.</p>
          <p>Ask a question to see it here.</p>
        </div>
      ) : (
        <div className="rq-list">
          {recent.map((item) => {
            const meta = STATUS_META[item.status] || STATUS_META.error;
            return (
              <button
                key={item.id}
                className="rq-item"
                onClick={() => onOpen(item)}
                aria-label={`Reopen: ${item.question}`}
              >
                <div className="rq-item-inner">
                  <p className="rq-question">{item.question}</p>
                  <div className="rq-meta">
                    <span className={`rq-badge ${meta.cls}`}>{meta.label}</span>
                    <span className="rq-filename">{item.filename}</span>
                    <span className="rq-time">{formatTime(item.timestamp)}</span>
                  </div>
                </div>
                <span className="rq-arrow" aria-hidden="true">›</span>
              </button>
            );
          })}
        </div>
      )}
    </div>
  );
}
