import { useState } from "react";

/* ── Helper icons ─────────────────────────────────────────────── */
function CodeIcon() {
  return (
    <svg viewBox="0 0 24 24" width="16" height="16" fill="none" stroke="currentColor" strokeWidth="2">
      <polyline points="16 18 22 12 16 6" />
      <polyline points="8 6 2 12 8 18" />
    </svg>
  );
}

function DbIcon() {
  return (
    <svg viewBox="0 0 24 24" width="16" height="16" fill="none" stroke="currentColor" strokeWidth="2">
      <ellipse cx="12" cy="5" rx="9" ry="3" />
      <path d="M21 12c0 1.66-4 3-9 3s-9-1.34-9-3" />
      <path d="M3 5v14c0 1.66 4 3 9 3s9-1.34 9-3V5" />
    </svg>
  );
}

const BADGE = {
  success: { cls: "verified", label: "Verified" },
  refused: { cls: "refused", label: "Unable to Answer" },
  error: { cls: "failed", label: "Failed" },
};

/* ── Main AnalysisResult Component ─────────────────────────────── */
export default function AnalysisResult({ result, onConvertCurrency }) {
  const [codeOpen, setCodeOpen] = useState(true);
  const [evidenceOpen, setEvidenceOpen] = useState(false);
  const [proofOpen, setProofOpen] = useState(false);
  const [verificationOpen, setVerificationOpen] = useState(true);
  const [copied, setCopied] = useState(false);
  const [proofCopied, setProofCopied] = useState(false);

  if (!result) return null;

  const badge = BADGE[result.status] ?? BADGE.error;

  const copyCode = () => {
    if (!result.generated_code) return;
    navigator.clipboard.writeText(result.generated_code).then(() => {
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    });
  };

  const copyProof = () => {
    if (!result.reproducible_proof) return;
    navigator.clipboard.writeText(result.reproducible_proof).then(() => {
      setProofCopied(true);
      setTimeout(() => setProofCopied(false), 2000);
    });
  };

  const ds = result.dataset_summary;

  return (
    <div className="analysis-result">
      {/* ── Answer section ── */}
      <div className="result-answer-section">
        <div className="result-answer-header">
          <span className="result-answer-label">AI Answer</span>
          <span className={`result-badge ${badge.cls}`}>
            {badge.label}
          </span>
        </div>
        <div className="result-answer-text">
          {result.answer || result.verification_detail || "No answer available"}
        </div>
        {result.verification_detail && result.answer && (
          <div className="result-answer-detail">{result.verification_detail}</div>
        )}
      </div>

      {/* ── Currency Conversion UI ── */}
      {result.status === "refused" && (result.currency_conversion_options?.available || (result.verification_detail && result.verification_detail.includes("INR") && result.verification_detail.includes("USD"))) && (
        <div className="currency-conversion-card" style={{ marginTop: "12px", marginBottom: "16px", padding: "16px", background: "#1e293b", borderRadius: "8px", border: "1px solid #334155" }}>
          <div style={{ display: "flex", alignItems: "center", gap: "8px", color: "#f59e0b", fontWeight: 600, marginBottom: "8px" }}>
            <span style={{ fontSize: "1.2rem" }}>⚠️</span> Currency Conversion Required
          </div>
          <p style={{ margin: "0 0 16px 0", color: "#94a3b8", fontSize: "0.95rem" }}>
            "Your data contains INR and USD. They cannot be safely combined without conversion."
          </p>
          <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "16px" }}>
            <div style={{ border: "1px solid #334155", borderRadius: "8px", padding: "14px", background: "#0f172a" }}>
              <h4 style={{ margin: "0 0 6px 0", fontSize: "1rem", color: "#f8fafc" }}>Convert to INR</h4>
              <p style={{ fontSize: "0.85rem", color: "#94a3b8", margin: "0 0 12px 0" }}>1 USD = ₹83.50</p>
              <button
                className="result-copy-btn"
                style={{ width: "100%", padding: "8px 12px", background: "#2563eb", color: "#ffffff", borderRadius: "6px", fontWeight: 600, border: "none", cursor: "pointer" }}
                onClick={() => onConvertCurrency && onConvertCurrency("INR")}
              >
                Convert &amp; Calculate
              </button>
            </div>
            <div style={{ border: "1px solid #334155", borderRadius: "8px", padding: "14px", background: "#0f172a" }}>
              <h4 style={{ margin: "0 0 6px 0", fontSize: "1rem", color: "#f8fafc" }}>Convert to USD</h4>
              <p style={{ fontSize: "0.85rem", color: "#94a3b8", margin: "0 0 12px 0" }}>1 USD = ₹83.50</p>
              <button
                className="result-copy-btn"
                style={{ width: "100%", padding: "8px 12px", background: "#2563eb", color: "#ffffff", borderRadius: "6px", fontWeight: 600, border: "none", cursor: "pointer" }}
                onClick={() => onConvertCurrency && onConvertCurrency("USD")}
              >
                Convert &amp; Calculate
              </button>
            </div>
          </div>
        </div>
      )}

      {/* ── Warnings ── */}
      {result.warnings && result.warnings.length > 0 && (
        <div className="result-warnings">
          {result.warnings.map((w, i) => (
            <div key={i} className="result-warning-item">
              <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                <path d="M10.29 3.86L1.82 18a2 2 0 0 0 1.71 3h16.94a2 2 0 0 0 1.71-3L13.71 3.86a2 2 0 0 0-3.42 0z" />
                <line x1="12" y1="9" x2="12" y2="13" />
                <line x1="12" y1="17" x2="12.01" y2="17" />
              </svg>
              {w}
            </div>
          ))}
        </div>
      )}

      {/* ── Generated Python Code ── */}
      {result.generated_code && (
        <div className="result-section">
          <button
            className="result-section-toggle"
            onClick={() => setCodeOpen(!codeOpen)}
          >
            <span className="result-section-title">
              <CodeIcon />
              Generated Python Code
            </span>
            <span className="result-toggle-icon">{codeOpen ? "▲" : "▼"}</span>
          </button>

          {codeOpen && (
            <div className="result-code-body">
              <div className="result-code-toolbar">
                <span className="result-code-lang">python</span>
                <button
                  className={`result-copy-btn${copied ? " copied" : ""}`}
                  onClick={copyCode}
                >
                  {copied ? "Copied ✓" : "Copy"}
                </button>
              </div>
              <pre className="result-code-pre">{result.generated_code}</pre>
            </div>
          )}
        </div>
      )}

      {/* ── Dataset Evidence ── */}
      {ds && (
        <div className="result-section">
          <button
            className="result-section-toggle"
            onClick={() => setEvidenceOpen(!evidenceOpen)}
          >
            <span className="result-section-title">
              <DbIcon />
              Dataset Evidence
            </span>
            <span className="result-toggle-icon">{evidenceOpen ? "▲" : "▼"}</span>
          </button>

          {evidenceOpen && (
            <div className="result-evidence-body">
              <div className="result-evidence-grid">
                <div className="result-evidence-item">
                  <div className="result-evidence-key">File</div>
                  <div className="result-evidence-val">{ds.filename}</div>
                </div>
                <div className="result-evidence-item">
                  <div className="result-evidence-key">Shape</div>
                  <div className="result-evidence-val">
                    {ds.rows?.toLocaleString()} rows × {ds.columns?.length} cols
                  </div>
                </div>
                <div className="result-evidence-item full-width">
                  <div className="result-evidence-key">Columns</div>
                  <div className="result-evidence-val">{ds.columns?.join(", ")}</div>
                </div>
              </div>
            </div>
          )}
        </div>
      )}

      {/* ── Reproducible Proof ── */}
      {result.reproducible_proof && (
        <div className="result-section">
          <button
            className="result-section-toggle"
            onClick={() => setProofOpen(!proofOpen)}
          >
            <span className="result-section-title">
              <CodeIcon />
              Reproducible Proof
            </span>
            <span className="result-toggle-icon">{proofOpen ? "▲" : "▼"}</span>
          </button>

          {proofOpen && (
            <div className="result-code-body">
              <div className="result-proof-desc">
                Run this complete Python script with the uploaded dataset to reproduce the result independently.
              </div>
              <div className="result-code-toolbar">
                <span className="result-code-lang">python</span>
                <button
                  className={`result-copy-btn${proofCopied ? " copied" : ""}`}
                  onClick={copyProof}
                >
                  {proofCopied ? "Copied ✓" : "Copy Code"}
                </button>
              </div>
              <pre className="result-code-pre">{result.reproducible_proof}</pre>
            </div>
          )}
        </div>
      )}

      {/* ── Verification ── */}
      {result.verification && (
        <div className="result-section">
          <button
            className="result-section-toggle"
            onClick={() => setVerificationOpen(!verificationOpen)}
          >
            <span className="result-section-title">
              <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                <polyline points="20 6 9 17 4 12" />
              </svg>
              Verification
            </span>
            <span className="result-toggle-icon">{verificationOpen ? "▲" : "▼"}</span>
          </button>

          {verificationOpen && (
            <div className="result-verification-body">
              <div className={`verification-status ${result.verification.toLowerCase()}`}>
                {result.verification === "VERIFIED" && (
                  <>
                    <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                      <polyline points="20 6 9 17 4 12" />
                    </svg>
                    Verified
                  </>
                )}
                {result.verification === "REFUSED" && (
                  <>
                    <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                      <circle cx="12" cy="12" r="10" />
                      <line x1="15" y1="9" x2="9" y2="15" />
                      <line x1="9" y1="9" x2="15" y2="15" />
                    </svg>
                    Refused
                  </>
                )}
                {result.verification === "ERROR" && (
                  <>
                    <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                      <circle cx="12" cy="12" r="10" />
                      <line x1="12" y1="8" x2="12" y2="12" />
                      <line x1="12" y1="16" x2="12.01" y2="16" />
                    </svg>
                    Error
                  </>
                )}
              </div>

              {result.ai_answer !== undefined && result.code_result !== undefined && (
                <div className="verification-comparison">
                  <div className="verification-item">
                    <div className="verification-label">AI ANSWER:</div>
                    <div className="verification-value">{String(result.ai_answer)}</div>
                  </div>
                  <div className="verification-item">
                    <div className="verification-label">CODE RESULT:</div>
                    <div className="verification-value">{String(result.code_result)}</div>
                  </div>
                  {result.match !== undefined && (
                    <div className="verification-item">
                      <div className="verification-label">MATCH:</div>
                      <div className={`verification-match ${result.match ? "yes" : "no"}`}>
                        {result.match ? "✓" : "✗"}
                      </div>
                    </div>
                  )}
                </div>
              )}
            </div>
          )}
        </div>
      )}

      {/* ── Data Quality ── */}
      {result.data_quality && result.data_quality.issues && result.data_quality.issues.length > 0 && (
        <div className="result-section">
          <div className="result-data-quality">
            <div className="data-quality-header">
              Data Quality Issues ({result.data_quality.total_issues})
            </div>
            <div className="data-quality-issues">
              {result.data_quality.issues.map((issue, idx) => (
                <div key={idx} className={`data-quality-issue ${issue.severity}`}>
                  <span className="issue-type">{issue.type}</span>
                  <span className="issue-desc">{issue.description}</span>
                </div>
              ))}
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
