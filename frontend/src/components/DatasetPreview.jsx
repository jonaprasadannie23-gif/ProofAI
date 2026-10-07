import { useState } from "react";

export default function DatasetPreview({ dataset, maxRows = 10 }) {
  const [expanded, setExpanded] = useState(false);

  if (!dataset) return null;

  // Handle non-tabular files (PDF, TXT, HTML without tables)
  if (dataset.is_tabular === false) {
    return (
      <div className="card preview-card" role="region" aria-label="File preview">
        <div className="preview-header">
          <p className="card-label" style={{ marginBottom: 0 }}>Preview</p>
          <span className="badge">
            {(dataset.file_type || "file").toUpperCase()}
          </span>
        </div>
        {dataset.parse_error && (
          <p className="preview-non-tabular-note">{dataset.parse_error}</p>
        )}
        {dataset.text_content ? (
          <pre className="preview-text-content">{dataset.text_content}</pre>
        ) : (
          <p className="preview-non-tabular-note">No preview available.</p>
        )}
      </div>
    );
  }

  // Tabular preview (CSV, Excel, JSON, HTML with table)
  // Support both old API format (columns, preview) and new (columns, preview)
  const columns       = dataset.columns || [];
  const preview       = dataset.preview || [];
  const missing       = dataset.missing_values || {};
  const dtypes        = dataset.dtypes || {};
  const rows_total    = dataset.row_count ?? dataset.rows ?? preview.length;

  const hasNulls = Object.values(missing).some((v) => v > 0);
  const shownRows = expanded ? preview : preview.slice(0, maxRows);

  return (
    <div className="card preview-card" role="region" aria-label="Dataset preview">
      <div className="preview-header">
        <p className="card-label" style={{ marginBottom: 0 }}>Preview</p>
        <div className="badge-row">
          <span className="badge">{columns.length} cols</span>
          <span className="badge">{rows_total.toLocaleString()} rows</span>
          {hasNulls && <span className="badge badge-warn">Missing values</span>}
        </div>
      </div>

      <div className="table-wrap" role="table" aria-label="Data preview table">
        <table className="data-table">
          <thead>
            <tr>
              {columns.map((col) => (
                <th key={col} scope="col">
                  <div className="th-col">{col}</div>
                  {dtypes[col] && <div className="th-type">{dtypes[col]}</div>}
                  {missing[col] > 0 && (
                    <div className="th-null">{missing[col]} null</div>
                  )}
                </th>
              ))}
            </tr>
          </thead>
          <tbody>
            {shownRows.map((row, i) => (
              <tr key={i}>
                {columns.map((col) => (
                  <td key={col} title={row[col] != null ? String(row[col]) : "null"}>
                    {row[col] == null ? (
                      <span className="td-null">—</span>
                    ) : (
                      String(row[col])
                    )}
                  </td>
                ))}
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {preview.length > maxRows && (
        <button className="show-more-btn" onClick={() => setExpanded(!expanded)}>
          {expanded
            ? "Show fewer rows"
            : `Show all ${preview.length} preview rows →`}
        </button>
      )}
    </div>
  );
}
