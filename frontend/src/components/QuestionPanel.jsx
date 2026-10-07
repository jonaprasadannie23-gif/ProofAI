import { useState, useRef, useEffect } from "react";
import axios from "axios";

function InfoIcon() {
  return (
    <svg viewBox="0 0 24 24" aria-hidden="true">
      <circle cx="12" cy="12" r="10" />
      <line x1="12" y1="8" x2="12" y2="12" />
      <line x1="12" y1="16" x2="12.01" y2="16" />
    </svg>
  );
}

function FollowUpIcon() {
  return (
    <svg viewBox="0 0 24 24" aria-hidden="true">
      <polyline points="9 14 4 9 9 4" />
      <path d="M20 20v-7a4 4 0 0 0-4-4H4" />
    </svg>
  );
}

export default function QuestionPanel({
  dataset,
  onResult,
  analyzing,
  setAnalyzing,
  contextHistory,
  onAddToHistory,
  isFollowUp,
}) {
  const [question, setQuestion]     = useState("");
  const [error, setError]           = useState(null);
  const [suggestions, setSuggestions] = useState([]);
  const textareaRef = useRef();

  // Load suggestions from the dataset upload response
  useEffect(() => {
    if (dataset?.suggestions?.length) {
      setSuggestions(dataset.suggestions);
    } else {
      setSuggestions([]);
    }
  }, [dataset]);

  const handleAnalyze = async () => {
    const q = question.trim();
    if (!q || !dataset || analyzing) return;
    setError(null);
    setAnalyzing(true);
    onResult(null);

    const form = new FormData();
    form.append("question", q);
    form.append("file", dataset.fileObject);
    // Pass context history for follow-up support
    form.append("context_history", JSON.stringify(
      (contextHistory || []).map(({ question, answer }) => ({ question, answer }))
    ));

    try {
      const res = await axios.post("/api/analyze", form);
      const result = { ...res.data, question: q };
      onResult(result);

      // Add to history
      if (onAddToHistory) {
        onAddToHistory({
          id: `${Date.now()}-${Math.random()}`,
          question: q,
          filename: dataset.filename,
          answer: result.answer,
          status: result.status,
          result,
          timestamp: new Date().toISOString(),
        });
      }

      setQuestion("");
    } catch (e) {
      const detail = e.response?.data?.detail;
      setError(detail || "Analysis failed. Is the backend running?");
    } finally {
      setAnalyzing(false);
    }
  };

  const handleKey = (e) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      handleAnalyze();
    }
  };

  const setChip = (q) => {
    setQuestion(q);
    textareaRef.current?.focus();
  };

  const disabled = !dataset || analyzing;

  return (
    <div className="card" role="region" aria-label="Question input">
      <div className="qp-header">
        <p className="card-label" style={{ marginBottom: 0 }}>
          {isFollowUp ? "Follow-up Question" : "Question"}
        </p>
        {isFollowUp && (
          <span className="qp-followup-badge">
            <FollowUpIcon />
            Follow-up
          </span>
        )}
      </div>

      <div className="question-wrap">
        {/* Main input field */}
        <div className="question-field">
          <textarea
            ref={textareaRef}
            className="question-input"
            placeholder={
              isFollowUp
                ? "Ask a follow-up about the same dataset…"
                : "Ask anything about your data…"
            }
            value={question}
            onChange={(e) => setQuestion(e.target.value)}
            onKeyDown={handleKey}
            rows={1}
            disabled={disabled}
            aria-label="Data question"
            aria-describedby={!dataset ? "no-file-hint" : undefined}
          />
          <button
            className="analyze-btn"
            onClick={handleAnalyze}
            disabled={disabled || !question.trim()}
            aria-busy={analyzing}
          >
            {analyzing ? (
              <>
                <span className="btn-spinner" aria-hidden="true" />
                Analyzing
              </>
            ) : (
              "Analyze →"
            )}
          </button>
        </div>

        {/* No file hint */}
        {!dataset && (
          <div className="no-file-hint" id="no-file-hint" role="note">
            <InfoIcon />
            Upload a file to get started
          </div>
        )}

        {/* Error */}
        {error && (
          <p className="inline-error" role="alert">{error}</p>
        )}

        {/* Smart suggestion chips — from actual dataset schema */}
        {dataset && !analyzing && suggestions.length > 0 && (
          <div className="examples-row">
            <span className="examples-prefix">Try:</span>
            {suggestions.map((q) => (
              <button
                key={q}
                className="chip"
                onClick={() => setChip(q)}
                aria-label={`Use suggestion: ${q}`}
              >
                {q}
              </button>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
