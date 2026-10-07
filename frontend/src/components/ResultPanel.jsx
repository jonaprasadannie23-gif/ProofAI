import { useState, useEffect, useRef } from "react";
import VerificationPanel from "./VerificationPanel";
import DataQualityPanel from "./DataQualityPanel";

/* ── Helpers ─────────────────────────────────────────────────── */
function CodeIcon() {
  return (
    <svg viewBox="0 0 24 24" aria-hidden="true">
      <polyline points="16 18 22 12 16 6" />
      <polyline points="8 6 2 12 8 18" />
    </svg>
  );
}

function DbIcon() {
  return (
    <svg viewBox="0 0 24 24" aria-hidden="true">
      <ellipse cx="12" cy="5" rx="9" ry="3" />
      <path d="M21 12c0 1.66-4 3-9 3s-9-1.34-9-3" />
      <path d="M3 5v14c0 1.66 4 3 9 3s9-1.34 9-3V5" />
    </svg>
  );
}

const BADGE = {
  success: { cls: "verified", label: "Verified",            dot: true },
  refused: { cls: "refused",  label: "Unable to Answer",    dot: true },
  error:   { cls: "failed",   label: "Failed",              dot: true },
};

/* ── Idle / analyzing states ─────────────────────────────────── */
export function IdleResult() {
  return (
    <div className="card result-card">
      <div className="idle-state" aria-live="polite">
        <div className="idle-icon">
          <svg viewBox="0 0 24 24" fill="none" aria-hidden="true">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="1.5"
              d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2" />
          </svg>
        </div>
        <p className="idle-title">No results yet</p>
        <p className="idle-desc">Upload a dataset and ask a question to see your analysis here.</p>
      </div>
    </div>
  );
}

export function AnalyzingResult() {
  return (
    <div className="card result-card">
      <div className="analyzing-state" aria-live="polite" aria-busy="true">
        <div className="analyzing-spinner" aria-hidden="true" />
        <p className="analyzing-label">Analyzing your data…</p>
        <p className="analyzing-sub">Generating and executing Python code</p>
      </div>
    </div>
  );
}

/* ── Single Result Item Component ─────────────────────────────── */
function ResultItem({ result, settings, isLast, onFollowUp }) {
  const [codeOpen, setCodeOpen]         = useState(true);
  const [evidenceOpen, setEvidenceOpen] = useState(false);
  const [proofOpen, setProofOpen]       = useState(false);
  const [copied, setCopied]             = useState(false);
  const [proofCopied, setProofCopied]   = useState(false);

  const badge = BADGE[result.status] ?? BADGE.error;

  const showVerification = settings?.showVerificationPanel !== false;
  const showCode         = settings?.showGeneratedCode !== false;
  const showQuality      = settings?.showDataQuality !== false;

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
    <div className="result-item-wrap">
      {/* ── Main answer card ── */}
      <div className="card result-card" role="region" aria-label="Analysis result">

        {/* ── Question section ── */}
        {result.question && (
          <div className="question-section">
            <span className="question-heading">Question</span>
            <p className="question-text">"{result.question}"</p>
          </div>
        )}

        {/* ── Answer section ── */}
        <div className="answer-section">
          <div className="answer-top">
            <span className="answer-heading">Answer</span>
            <span className={`v-badge ${badge.cls}`} role="status" aria-label={`Status: ${badge.label}`}>
              {badge.dot && <span className="v-dot" aria-hidden="true" />}
              {badge.label}
            </span>
          </div>

          {result.answer ? (
            <>
              <p className={`answer-text${result.status !== "success" ? " refused" : ""}`}>
                {result.answer}
              </p>
              <p className="answer-detail">{result.verification_detail}</p>
            </>
          ) : (
            <p className="answer-text refused">{result.verification_detail}</p>
          )}
        </div>

        {/* ── Warnings ── */}
        {result.warnings?.length > 0 && (
          <div className="warnings-section" role="alert">
            <p className="warnings-label">⚠ Data warnings</p>
            {result.warnings.map((w, i) => (
              <p key={i} className="warning-item">· {w}</p>
            ))}
          </div>
        )}

        {/* ── Generated code ── */}
        {showCode && result.generated_code && (
          <div className="code-section">
            <button
              className="section-toggle"
              onClick={() => setCodeOpen(!codeOpen)}
              aria-expanded={codeOpen}
            >
              <span className="section-toggle-left">
                <CodeIcon />
                Generated Python Code
              </span>
              <span className="toggle-chevron" aria-hidden="true">
                {codeOpen ? "▲" : "▼"}
              </span>
            </button>

            {codeOpen && (
              <div className="code-body">
                <div className="code-toolbar">
                  <span className="code-lang">python</span>
                  <button
                    className={`copy-btn${copied ? " copied" : ""}`}
                    onClick={copyCode}
                    aria-label="Copy code to clipboard"
                  >
                    {copied ? "Copied ✓" : "Copy"}
                  </button>
                </div>
                <pre className="code-pre" tabIndex={0}>{result.generated_code}</pre>
              </div>
            )}
          </div>
        )}

        {/* ── Dataset evidence ── */}
        {ds && (
          <div className="evidence-section">
            <button
              className="section-toggle"
              style={{ padding: "0 0 12px 0" }}
              onClick={() => setEvidenceOpen(!evidenceOpen)}
              aria-expanded={evidenceOpen}
            >
              <span className="section-toggle-left">
                <DbIcon />
                Dataset Evidence
              </span>
              <span className="toggle-chevron" aria-hidden="true">
                {evidenceOpen ? "▲" : "▼"}
              </span>
            </button>

            {evidenceOpen && (
              <div>
                <div className="evidence-grid">
                  <div className="evidence-item">
                    <p className="evidence-key">File</p>
                    <p className="evidence-val mono">{ds.filename}</p>
                  </div>
                  <div className="evidence-item">
                    <p className="evidence-key">Shape</p>
                    <p className="evidence-val">
                      {ds.rows?.toLocaleString()} rows × {ds.columns?.length} cols
                    </p>
                  </div>
                  <div className="evidence-item" style={{ gridColumn: "1 / -1" }}>
                    <p className="evidence-key">Columns</p>
                    <p className="evidence-val">{ds.columns?.join(", ")}</p>
                  </div>
                  <div className="evidence-item" style={{ gridColumn: "1 / -1" }}>
                    <p className="evidence-key">Types</p>
                    <div className="dtype-tags">
                      {ds.dtypes && Object.entries(ds.dtypes).map(([col, dtype]) => (
                        <span key={col} className="dtype-tag">{col}: {dtype}</span>
                      ))}
                    </div>
                  </div>
                </div>
              </div>
            )}
          </div>
        )}

        {/* ── Reproducible proof ── */}
        {result.reproducible_proof && (
          <div className="code-section">
            <button
              className="section-toggle"
              onClick={() => setProofOpen(!proofOpen)}
              aria-expanded={proofOpen}
            >
              <span className="section-toggle-left">
                <CodeIcon />
                Reproducible Proof
              </span>
              <span className="toggle-chevron" aria-hidden="true">
                {proofOpen ? "▲" : "▼"}
              </span>
            </button>

            {proofOpen && (
              <div className="code-body">
                <p className="proof-desc">
                  Run this complete Python script with the uploaded dataset to reproduce the result independently.
                </p>
                <div className="code-toolbar">
                  <span className="code-lang">python</span>
                  <button
                    className={`copy-btn${proofCopied ? " copied" : ""}`}
                    onClick={copyProof}
                    aria-label="Copy reproducible proof to clipboard"
                  >
                    {proofCopied ? "Copied ✓" : "Copy Code"}
                  </button>
                </div>
                <pre className="code-pre" tabIndex={0}>{result.reproducible_proof}</pre>
              </div>
            )}
          </div>
        )}
      </div>

      {/* ── Verification panel ── */}
      {showVerification && (
        <VerificationPanel result={result} />
      )}

      {/* ── Data quality panel ── */}
      {showQuality && result.data_quality && (
        <DataQualityPanel dataQuality={result.data_quality} />
      )}

      {/* ── Follow-up prompt (on last item only) ── */}
      {isLast && result.status === "success" && onFollowUp && (
        <div className="followup-prompt">
          <span className="followup-label">Have a follow-up question?</span>
          <button className="followup-btn" onClick={onFollowUp}>
            Ask a follow-up →
          </button>
        </div>
      )}
    </div>
  );
}

/* ── Main result container ─────────────────────────────────────── */
export default function ResultPanel({ result, results, settings, onFollowUp }) {
  const endRef = useRef(null);

  const resultList = results && results.length > 0
    ? results
    : (result ? [result] : []);

  useEffect(() => {
    if (resultList.length > 1) {
      endRef.current?.scrollIntoView({ behavior: "smooth", block: "nearest" });
    }
  }, [resultList.length]);

  if (resultList.length === 0) {
    return <IdleResult />;
  }

  return (
    <div className="result-stack conversation-container">
      {resultList.map((res, index) => (
        <ResultItem
          key={res.id || `${index}-${res.question}`}
          result={res}
          settings={settings}
          isLast={index === resultList.length - 1}
          onFollowUp={onFollowUp}
        />
      ))}
      <div ref={endRef} />
    </div>
  );
}
