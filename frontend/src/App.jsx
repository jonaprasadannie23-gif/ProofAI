import { useState } from "react";
import Sidebar from "./components/Sidebar";
import UploadPanel from "./components/UploadPanel";
import DatasetPreview from "./components/DatasetPreview";
import QuestionPanel from "./components/QuestionPanel";
import ResultPanel, { IdleResult, AnalyzingResult } from "./components/ResultPanel";
import FileManager from "./components/FileManager";
import AnalysisHistory from "./components/AnalysisHistory";
import RecentQuestions from "./components/RecentQuestions";
import Settings from "./components/Settings";

const DEFAULT_SETTINGS = {
  showDataQuality: true,
  showVerificationPanel: true,
  showGeneratedCode: true,
  maxPreviewRows: 10,
  confirmClearHistory: true,
};

export default function App() {
  // ── Navigation ────────────────────────────────────────────────
  const [activeView, setActiveView] = useState("new");

  // ── Dataset / upload state ────────────────────────────────────
  const [dataset, setDataset]       = useState(null);   // current active dataset
  const [files, setFiles]           = useState([]);     // all uploaded files (FileManager)
  const [activeFileId, setActiveFileId] = useState(null);

  // ── Analysis state ────────────────────────────────────────────
  const [result, setResult]         = useState(null);
  const [analyzing, setAnalyzing]   = useState(false);

  // ── History state ─────────────────────────────────────────────
  const [history, setHistory]       = useState([]);

  // ── Follow-up state ───────────────────────────────────────────
  const [isFollowUp, setIsFollowUp] = useState(false);
  const [followUpContext, setFollowUpContext] = useState([]); // {question, answer}[]

  // ── Settings ──────────────────────────────────────────────────
  const [settings, setSettings]     = useState(DEFAULT_SETTINGS);

  // ── Handlers ──────────────────────────────────────────────────

  const handleUpload = (uploadedDataset) => {
    setDataset(uploadedDataset);
    setResult(null);
    setIsFollowUp(false);
    setFollowUpContext([]);
  };

  const handleClear = () => {
    setDataset(null);
    setResult(null);
    setIsFollowUp(false);
    setFollowUpContext([]);
  };

  const handleAddToHistory = (item) => {
    setHistory((prev) => [...prev, item]);
    // Build follow-up context
    setFollowUpContext((prev) => [
      ...prev,
      { question: item.question, answer: item.answer || "" },
    ]);
  };

  const handleOpenHistoryItem = (item) => {
    // Restore result from history and switch to analysis view
    setResult(item.result);
    setActiveView("new");
    // Re-load the dataset that was used if we can find it by filename
    const matchingFile = files.find((f) => f.filename === item.filename);
    if (matchingFile) {
      setDataset(matchingFile);
    }
  };

  const handleSelectFile = (file) => {
    setDataset(file);
    setActiveFileId(file.id);
    setResult(null);
    setIsFollowUp(false);
    setFollowUpContext([]);
    setActiveView("new");
  };

  const handleFilesChange = (updatedFiles) => {
    setFiles(updatedFiles);
    // If current dataset was removed, clear it
    if (dataset && !updatedFiles.find((f) => f.id === activeFileId)) {
      setDataset(null);
      setActiveFileId(null);
      setResult(null);
    }
  };

  const handleFollowUp = () => {
    setIsFollowUp(true);
    setResult(null);
    // Keep dataset and followUpContext intact
  };

  const handleNavigate = (view) => {
    setActiveView(view);
  };

  const handleClearHistory = () => {
    setHistory([]);
  };

  // ── Render ────────────────────────────────────────────────────

  return (
    <div className="app-shell">
      <Sidebar activeView={activeView} onNavigate={handleNavigate} />

      <div className="app-main">

        {/* ══ NEW ANALYSIS view ══ */}
        {activeView === "new" && (
          <div className="page">
            {/* Top workspace row */}
            <div className="workspace">
              {/* Left: upload + preview stacked */}
              <div style={{ display: "flex", flexDirection: "column", gap: "20px" }}>
                <UploadPanel
                  dataset={dataset}
                  onUpload={handleUpload}
                  onClear={handleClear}
                />
                {dataset && (
                  <DatasetPreview
                    dataset={dataset}
                    maxRows={settings.maxPreviewRows}
                  />
                )}
              </div>

              {/* Right: question */}
              <QuestionPanel
                dataset={dataset}
                onResult={setResult}
                analyzing={analyzing}
                setAnalyzing={setAnalyzing}
                contextHistory={followUpContext}
                onAddToHistory={handleAddToHistory}
                isFollowUp={isFollowUp}
              />
            </div>

            {/* Results — full width below */}
            {analyzing ? (
              <AnalyzingResult />
            ) : result ? (
              <ResultPanel
                result={result}
                settings={settings}
                onFollowUp={handleFollowUp}
              />
            ) : (
              <IdleResult />
            )}
          </div>
        )}

        {/* ══ RECENT QUESTIONS view ══ */}
        {activeView === "recent" && (
          <div className="page">
            <RecentQuestions
              history={history}
              onOpen={handleOpenHistoryItem}
            />
          </div>
        )}

        {/* ══ MY DATA view ══ */}
        {activeView === "data" && (
          <div className="page">
            <FileManager
              files={files}
              onSelectFile={handleSelectFile}
              onFilesChange={handleFilesChange}
              activeFileId={activeFileId}
            />
          </div>
        )}

        {/* ══ ANALYSIS HISTORY view ══ */}
        {activeView === "history" && (
          <div className="page">
            <AnalysisHistory
              history={history}
              onOpen={handleOpenHistoryItem}
            />
          </div>
        )}

        {/* ══ SETTINGS view ══ */}
        {activeView === "settings" && (
          <div className="page">
            <Settings
              settings={settings}
              onUpdate={setSettings}
              onClearHistory={handleClearHistory}
              historyCount={history.length}
            />
          </div>
        )}
      </div>
    </div>
  );
}
