/* DataQualityPanel.jsx — shows detected data quality issues */
import { useState } from "react";

const SEVERITY_META = {
  error:   { label: "Error",   cls: "dq-error"   },
  warning: { label: "Warning", cls: "dq-warning"  },
  info:    { label: "Info",    cls: "dq-info"     },
};

const TYPE_LABELS = {
  missing_values:  "Missing Values",
  duplicate_rows:  "Duplicate Rows",
  duplicate_ids:   "Duplicate IDs",
  empty_column:    "Empty Column",
  constant_column: "Constant Column",
  mixed_types:     "Mixed Types",
};

export default function DataQualityPanel({ dataQuality }) {
  const [open, setOpen] = useState(true);

  if (!dataQuality) return null;

  const { issues = [], total_issues = 0 } = dataQuality;

  if (total_issues === 0) {
    return (
      <div className="card dq-card" role="region" aria-label="Data quality">
        <div className="dq-clean">
          <span className="dq-clean-icon" aria-hidden="true">✓</span>
          <span className="dq-clean-text">No data quality issues detected</span>
        </div>
      </div>
    );
  }

  return (
    <div className="card dq-card" role="region" aria-label="Data quality">
      <button
        className="section-toggle"
        style={{ padding: "0 0 0 0" }}
        onClick={() => setOpen(!open)}
        aria-expanded={open}
        aria-controls="dq-issues"
      >
        <span className="section-toggle-left">
          <span className="dq-header-icon" aria-hidden="true">⚠</span>
          <span className="card-label" style={{ margin: 0 }}>Data Quality</span>
          <span className="dq-count-badge">{total_issues}</span>
        </span>
        <span className="toggle-chevron" aria-hidden="true">
          {open ? "▲" : "▼"}
        </span>
      </button>

      {open && (
        <div className="dq-issues" id="dq-issues">
          {issues.map((issue, i) => {
            const sev = SEVERITY_META[issue.severity] || SEVERITY_META.info;
            const typeLabel = TYPE_LABELS[issue.type] || issue.type;
            return (
              <div key={i} className={`dq-issue ${sev.cls}`}>
                <div className="dq-issue-type">{typeLabel}</div>
                <div className="dq-issue-desc">{issue.description}</div>
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
}
