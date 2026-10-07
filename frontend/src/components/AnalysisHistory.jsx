/* AnalysisHistory.jsx — conversation session history view */

function formatTime(iso) {
  if (!iso) return "";
  const d = new Date(iso);
  const now = new Date();
  const diffMs = now - d;
  const diffMin = Math.floor(diffMs / 60000);
  if (diffMin < 60) return "Today";
  const diffH = Math.floor(diffMin / 60);
  if (diffH < 24) return "Today";
  const diffDays = Math.floor(diffH / 24);
  if (diffDays === 1) return "Yesterday";
  if (diffDays < 7) return `${diffDays} days ago`;
  return d.toLocaleDateString();
}

function formatTimeDetailed(iso) {
  if (!iso) return "";
  const d = new Date(iso);
  return d.toLocaleString([], { 
    month: 'short',
    day: 'numeric',
    hour: '2-digit',
    minute: '2-digit'
  });
}

export default function AnalysisHistory({ sessions, onOpen }) {
  return (
    <div className="view-panel">
      <div className="view-header">
        <h2 className="view-title">Analysis History</h2>
        <p className="view-subtitle">
          Previous conversation sessions ({sessions.length} total)
        </p>
      </div>

      {sessions.length === 0 ? (
        <div className="ah-empty">
          <p>No conversation sessions yet.</p>
          <p>Start analyzing data to create a session.</p>
        </div>
      ) : (
        <div className="session-list">
          {[...sessions].reverse().map((session) => {
            const questionCount = session.questions.length;
            const datasets = session.datasets.join(', ');
            return (
              <button
                key={session.id}
                className="session-item"
                onClick={() => onOpen(session)}
                aria-label={`Open session: ${session.title}`}
              >
                <div className="session-header">
                  <h3 className="session-title">{session.title}</h3>
                  <span className="session-meta">
                    {questionCount} question{questionCount !== 1 ? 's' : ''} · {formatTime(session.lastUpdated)}
                  </span>
                </div>
                <div className="session-datasets">
                  📊 {datasets}
                </div>
                <div className="session-footer">
                  <span className="session-time">{formatTimeDetailed(session.lastUpdated)}</span>
                  <span className="session-action">Open →</span>
                </div>
              </button>
            );
          })}
        </div>
      )}
    </div>
  );
}
