import { useState, useRef } from "react";
import axios from "axios";

const EXAMPLES = [
  "What is the total revenue?",
  "Which category has the highest average?",
  "How many rows have missing values?",
  "What is the min and max of each column?",
];

function InfoIcon() {
  return (
    <svg viewBox="0 0 24 24" aria-hidden="true">
      <circle cx="12" cy="12" r="10" />
      <line x1="12" y1="8" x2="12" y2="12" />
      <line x1="12" y1="16" x2="12.01" y2="16" />
    </svg>
  );
}

export default function QuestionPanel({ dataset, onResult, analyzing, setAnalyzing }) {
  const [question, setQuestion] = useState("");
  const [error, setError] = useState(null);
  const textareaRef = useRef();

  const handleAnalyze = async () => {
    const q = question.trim();
    if (!q || !dataset || analyzing) return;
    setError(null);
    setAnalyzing(true);
    onResult(null);

    const form = new FormData();
    form.append("question", q);
    // Send the original File object — backend reads it with pandas directly
    form.append("file", dataset.fileObject);

    try {
      const res = await axios.post("/api/analyze", form);
      onResult(res.data);
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

  return (
    <div className="card" role="region" aria-label="Question input">
      <p className="card-label">Question</p>

      <div className="question-wrap">
        {/* Main input field */}
        <div className="question-field">
          <textarea
            ref={textareaRef}
            className="question-input"
            placeholder="Ask a question about your data…"
            value={question}
            onChange={(e) => setQuestion(e.target.value)}
            onKeyDown={handleKey}
            rows={1}
            disabled={!dataset || analyzing}
            aria-label="Data question"
            aria-describedby={!dataset ? "no-file-hint" : undefined}
          />
          <button
            className="analyze-btn"
            onClick={handleAnalyze}
            disabled={!dataset || !question.trim() || analyzing}
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
            Upload a CSV file to get started
          </div>
        )}

        {/* Error */}
        {error && (
          <p className="inline-error" role="alert">{error}</p>
        )}

        {/* Example chips — only when file is loaded */}
        {dataset && !analyzing && (
          <div className="examples-row">
            <span className="examples-prefix">Try:</span>
            {EXAMPLES.map((q) => (
              <button
                key={q}
                className="chip"
                onClick={() => setChip(q)}
                aria-label={`Use example: ${q}`}
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
