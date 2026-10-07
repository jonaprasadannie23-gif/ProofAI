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
  const [dataset, setDataset]           = useState(null);   // current active dataset
  const [files, setFiles]               = useState([]);     // all uploaded files (FileManager + UploadPanel)
  const [activeFileId, setActiveFileId] = useState(null);

  // ── Analysis / Conversation state ──────────────────────────────
  const [conversation, setConversation] = useState([]); // array of result objects for current session
  const [analyzing, setAnalyzing]       = useState(false);

  // ── History state ─────────────────────────────────────────────
  const [history, setHistory]       = useState([]);

  // ── Follow-up state ───────────────────────────────────────────
  const [isFollowUp, setIsFollowUp] = useState(false);
  const [followUpContext, setFollowUpContext] = useState([]); // {question, answer}[]

  // ── Settings ──────────────────────────────────────────────────
  const [settings, setSettings]     = useState(DEFAULT_SETTINGS);

  // ── Handlers ──────────────────────────────────────────────────

  const handleResult = (newResult) => {
    if (!newResult) return;
    setConversation((prev) => [...prev, newResult]);
    setIsFollowUp(true);
  };

  const handleUpload = (uploadedDataset) => {
    const fileId = uploadedDataset.id || `${Date.now()}-${Math.random()}`;
    const fileEntry = {
      ...uploadedDataset,
      id: fileId,
    };
    setFiles((prev) => {
      const idx = prev.findIndex((f) => f.filename === fileEntry.filename);
      if (idx >= 0) {
        const copy = [...prev];
        copy[idx] = fileEntry;
        return copy;
      }
      return [...prev, fileEntry];
    });
    setDataset(fileEntry);
    setActiveFileId(fileId);
    setConversation([]);
    setIsFollowUp(false);
    setFollowUpContext([]);
  };

  const handleRemoveFile = (fileId) => {
    setFiles((prevFiles) => {
      const updated = prevFiles.filter((f) => f.id !== fileId && f.filename !== fileId);
      if (activeFileId === fileId || dataset?.id === fileId) {
        if (updated.length > 0) {
          const nextActive = updated[updated.length - 1];
          setDataset(nextActive);
          setActiveFileId(nextActive.id);
        } else {
          setDataset(null);
          setActiveFileId(null);
          setConversation([]);
          setIsFollowUp(false);
          setFollowUpContext([]);
        }
      }
      return updated;
    });
  };

  const handleClear = () => {
    setDataset(null);
    setFiles([]);
    setActiveFileId(null);
    setConversation([]);
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
    const restoredResult = item.result
      ? { ...item.result, question: item.question }
      : { question: item.question, answer: item.answer };
    setConversation([restoredResult]);
    setIsFollowUp(true);
    setActiveView("new");
    // Re-load the dataset that was used if we can find it by filename
    const matchingFile = files.find((f) => f.filename === item.filename);
    if (matchingFile) {
      setDataset(matchingFile);
      setActiveFileId(matchingFile.id);
    }
  };

  const handleSelectFile = (file) => {
    setDataset(file);
    setActiveFileId(file.id);
    setConversation([]);
    setIsFollowUp(false);
    setFollowUpContext([]);
    setActiveView("new");
  };

  const handleFilesChange = (updatedFiles) => {
    setFiles(updatedFiles);
    // If current dataset was removed, clear it
    if (dataset && !updatedFiles.find((f) => f.id === activeFileId || f.filename === dataset.filename)) {
      if (updatedFiles.length > 0) {
        setDataset(updatedFiles[updatedFiles.length - 1]);
        setActiveFileId(updatedFiles[updatedFiles.length - 1].id);
      } else {
        setDataset(null);
        setActiveFileId(null);
        setConversation([]);
      }
    }
  };

  const handleFollowUp = () => {
    setIsFollowUp(true);
    // Keep conversation and followUpContext intact
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
                  files={files}
                  dataset={dataset}
                  activeFileId={activeFileId}
                  onUpload={handleUpload}
                  onSelectFile={handleSelectFile}
                  onRemoveFile={handleRemoveFile}
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
                onResult={handleResult}
                analyzing={analyzing}
                setAnalyzing={setAnalyzing}
                contextHistory={followUpContext}
                onAddToHistory={handleAddToHistory}
                isFollowUp={isFollowUp}
              />
            </div>

            {/* Results — full width below */}
            {conversation.length === 0 && analyzing ? (
              <AnalyzingResult />
            ) : conversation.length > 0 ? (
              <>
                <ResultPanel
                  results={conversation}
                  settings={settings}
                  onFollowUp={handleFollowUp}
                />
                {analyzing && <AnalyzingResult />}
              </>
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
