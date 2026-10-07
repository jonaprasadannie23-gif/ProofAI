import { useState, useEffect } from "react";

export default function FullDatasetViewer({ dataset, onClose }) {
  const [currentPage, setCurrentPage] = useState(1);
  const [pageSize, setPageSize] = useState(50);

  // Keyboard shortcut: close on Escape
  useEffect(() => {
    const handleKeyDown = (e) => {
      if (e.key === "Escape") {
        onClose();
      }
    };
    window.addEventListener("keydown", handleKeyDown);
    return () => window.removeEventListener("keydown", handleKeyDown);
  }, [onClose]);

  if (!dataset) return null;

  const columns    = dataset.columns || [];
  const rows       = dataset.preview || [];
  const missing    = dataset.missing_values || {};
  const dtypes     = dataset.dtypes || {};
  const totalRows  = rows.length;

  const totalPages = Math.max(1, Math.ceil(totalRows / pageSize));

  // Compute pagination slice
  const validPage = Math.min(Math.max(1, currentPage), totalPages);
  const startIdx = (validPage - 1) * pageSize;
  const endIdx = Math.min(startIdx + pageSize, totalRows);
  const currentRows = rows.slice(startIdx, endIdx);

  const handlePrev = () => {
    if (validPage > 1) {
      setCurrentPage((p) => p - 1);
    }
  };

  const handleNext = () => {
    if (validPage < totalPages) {
      setCurrentPage((p) => p + 1);
    }
  };

  const handlePageSizeChange = (e) => {
    const newSize = Number(e.target.value);
    setPageSize(newSize);
    setCurrentPage(1);
  };

  return (
    <div
      className="modal-backdrop"
      onClick={onClose}
      role="dialog"
      aria-modal="true"
      aria-labelledby="full-dataset-title"
    >
      <div
        className="modal-card full-dataset-modal"
        onClick={(e) => e.stopPropagation()}
      >
        {/* Header */}
        <div className="modal-header">
          <div className="modal-title-group">
            <h2 id="full-dataset-title" className="modal-title">
              Full Dataset
            </h2>
            <span className="modal-filename">{dataset.filename}</span>
            <div className="badge-row">
              <span className="badge">{columns.length} cols</span>
              <span className="badge">{totalRows.toLocaleString()} rows</span>
            </div>
          </div>
          <button
            className="modal-close-btn"
            onClick={onClose}
            aria-label="Close dataset viewer"
          >
            Close ✕
          </button>
        </div>

        {/* Body (Scrollable Table Area) */}
        <div className="modal-body full-dataset-body">
          <div className="table-wrap full-dataset-table-wrap">
            <table className="data-table full-dataset-table">
              <thead>
                <tr>
                  <th className="row-num-col">#</th>
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
                {currentRows.map((row, relativeIdx) => {
                  const absoluteRowNumber = startIdx + relativeIdx + 1;
                  return (
                    <tr key={relativeIdx}>
                      <td className="row-num-cell">{absoluteRowNumber}</td>
                      {columns.map((col) => (
                        <td
                          key={col}
                          title={row[col] != null ? String(row[col]) : "null"}
                        >
                          {row[col] == null ? (
                            <span className="td-null">—</span>
                          ) : (
                            String(row[col])
                          )}
                        </td>
                      ))}
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        </div>

        {/* Footer (Pagination & Controls) */}
        <div className="modal-footer full-dataset-footer">
          <div className="pagination-info">
            <span>
              Showing {totalRows > 0 ? startIdx + 1 : 0} – {endIdx} of{" "}
              {totalRows.toLocaleString()} rows
            </span>
            <div className="page-size-selector">
              <label htmlFor="rows-per-page">Rows per page:</label>
              <select
                id="rows-per-page"
                value={pageSize}
                onChange={handlePageSizeChange}
                className="page-size-select"
              >
                <option value={25}>25</option>
                <option value={50}>50</option>
                <option value={100}>100</option>
              </select>
            </div>
          </div>

          <div className="pagination-controls">
            <button
              className="pagination-btn"
              onClick={handlePrev}
              disabled={validPage <= 1}
              aria-label="Previous page"
            >
              ← Previous
            </button>
            <span className="page-counter">
              Page {validPage} of {totalPages}
            </span>
            <button
              className="pagination-btn"
              onClick={handleNext}
              disabled={validPage >= totalPages}
              aria-label="Next page"
            >
              Next →
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}
