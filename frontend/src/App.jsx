import { useState } from "react";
import Header from "./components/Header";
import UploadPanel from "./components/UploadPanel";
import DatasetPreview from "./components/DatasetPreview";
import QuestionPanel from "./components/QuestionPanel";
import ResultPanel, { IdleResult, AnalyzingResult } from "./components/ResultPanel";

export default function App() {
  const [dataset, setDataset] = useState(null);
  const [result, setResult] = useState(null);
  const [analyzing, setAnalyzing] = useState(false);

  const handleClear = () => {
    setDataset(null);
    setResult(null);
  };

  return (
    <>
      <Header />

      <div className="page">
        {/* ── Top workspace row ── */}
        <div className="workspace">
          {/* Left: upload + preview stacked */}
          <div style={{ display: "flex", flexDirection: "column", gap: "20px" }}>
            <UploadPanel
              dataset={dataset}
              onUpload={setDataset}
              onClear={handleClear}
            />
            {dataset && <DatasetPreview dataset={dataset} />}
          </div>

          {/* Right: question */}
          <QuestionPanel
            dataset={dataset}
            onResult={setResult}
            analyzing={analyzing}
            setAnalyzing={setAnalyzing}
          />
        </div>

        {/* ── Results — full width below ── */}
        {analyzing ? (
          <AnalyzingResult />
        ) : result ? (
          <ResultPanel result={result} />
        ) : (
          <IdleResult />
        )}
      </div>
    </>
  );
}
