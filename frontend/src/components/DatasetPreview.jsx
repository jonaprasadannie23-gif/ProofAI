import { useState } from "react";

export default function DatasetPreview({ dataset }) {
  const [expanded, setExpanded] = useState(false);
  const { columns, preview, missing_values, dtypes } = dataset;

  const hasNulls = Object.values(missing_values).some((v) => v > 0);
  const rows = expanded ? preview : preview.slice(0, 5);

  return (
    <div className="card preview-card" role="region" aria-label="Dataset preview">
      <div className="preview-header">
        <p className="card-label" style={{ marginBottom: 0 }}>Preview</p>
        <div className="badge-row">
          <span className="badge">{columns.length} cols</span>
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
                  <div className="th-type">{dtypes[col]}</div>
                  {missing_values[col] > 0 && (
                    <div className="th-null">{missing_values[col]} null</div>
                  )}
                </th>
              ))}
            </tr>
          </thead>
          <tbody>
            {rows.map((row, i) => (
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

      {preview.length > 5 && (
        <button className="show-more-btn" onClick={() => setExpanded(!expanded)}>
          {expanded ? "Show fewer rows" : `Show all ${preview.length} preview rows →`}
        </button>
      )}
    </div>
  );
}
