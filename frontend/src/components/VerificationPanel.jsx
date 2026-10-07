/* VerificationPanel.jsx — proof verification display */

export default function VerificationPanel({ result }) {
  if (!result) return null;

  const isVerified  = result.status === "success" && result.match === true;
  const isRefused   = result.status === "refused";
  const isFailed    = result.status === "error" || result.match === false;

  const statusLabel = isVerified ? "Verified ✓" : isRefused ? "Unable to Answer" : "Verification Failed";
  const statusCls   = isVerified ? "verified"    : isRefused ? "refused"          : "failed";

  return (
    <div className="vp-card card" role="region" aria-label="Verification proof">
      <p className="card-label">Verification</p>

      <div className="vp-status-row">
        <span className={`v-badge ${statusCls}`}>
          <span className="v-dot" aria-hidden="true" />
          {statusLabel}
        </span>
        <span className="vp-description">
          {isVerified
            ? "The answer was produced by executing Python code against your actual data."
            : isRefused
            ? "This question could not be answered reliably with the available data."
            : "Code execution did not produce a matching result."}
        </span>
      </div>

      {/* Comparison table */}
      {(result.ai_answer != null || result.code_result != null) && !isRefused && (
        <div className="vp-comparison">
          <div className="vp-comp-row vp-comp-header">
            <span>AI Answer</span>
            <span>Code Result</span>
            <span>Match</span>
          </div>
          <div className="vp-comp-row vp-comp-data">
            <span className="vp-value">
              {result.ai_answer != null ? String(result.ai_answer) : "—"}
            </span>
            <span className="vp-value">
              {result.code_result != null ? String(result.code_result).slice(0, 200) : "—"}
            </span>
            <span className={`vp-match ${result.match ? "match" : "no-match"}`}>
              {result.match === true  ? "Match ✓"    :
               result.match === false ? "Mismatch ✗" :
               "—"}
            </span>
          </div>
        </div>
      )}

      {/* Refused explanation (only if not currency conversion warning to avoid duplicate text) */}
      {isRefused && !result.currency_conversion_options?.available && !(result.verification_detail && result.verification_detail.includes("INR") && result.verification_detail.includes("USD")) && (
        <div className="vp-refused-box">
          <p className="vp-refused-label">Refusal reason</p>
          <p className="vp-refused-text">{result.verification_detail}</p>
        </div>
      )}
    </div>
  );
}
