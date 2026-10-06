/* Settings.jsx — basic application settings */
import { useState } from "react";

const DEFAULT_SETTINGS = {
  showDataQuality: true,
  showVerificationPanel: true,
  showGeneratedCode: true,
  maxPreviewRows: 10,
  confirmClearHistory: true,
};

export default function Settings({ settings, onUpdate, onClearHistory, historyCount }) {
  const [localSettings, setLocalSettings] = useState(settings || DEFAULT_SETTINGS);
  const [saved, setSaved] = useState(false);

  const update = (key, value) => {
    setLocalSettings((prev) => ({ ...prev, [key]: value }));
    setSaved(false);
  };

  const save = () => {
    onUpdate(localSettings);
    setSaved(true);
    setTimeout(() => setSaved(false), 2000);
  };

  return (
    <div className="view-panel">
      <div className="view-header">
        <h2 className="view-title">Settings</h2>
        <p className="view-subtitle">Application preferences for this session</p>
      </div>

      <div className="settings-sections">

        {/* Display settings */}
        <section className="settings-section">
          <h3 className="settings-section-title">Display</h3>

          <label className="settings-toggle-row">
            <span className="settings-toggle-label">
              <span className="settings-label-main">Show Data Quality Panel</span>
              <span className="settings-label-sub">Display data quality issues after upload</span>
            </span>
            <input
              type="checkbox"
              className="settings-checkbox"
              checked={localSettings.showDataQuality}
              onChange={(e) => update("showDataQuality", e.target.checked)}
            />
          </label>

          <label className="settings-toggle-row">
            <span className="settings-toggle-label">
              <span className="settings-label-main">Show Verification Panel</span>
              <span className="settings-label-sub">Show the proof verification section in results</span>
            </span>
            <input
              type="checkbox"
              className="settings-checkbox"
              checked={localSettings.showVerificationPanel}
              onChange={(e) => update("showVerificationPanel", e.target.checked)}
            />
          </label>

          <label className="settings-toggle-row">
            <span className="settings-toggle-label">
              <span className="settings-label-main">Show Generated Code</span>
              <span className="settings-label-sub">Show the Python code that was executed</span>
            </span>
            <input
              type="checkbox"
              className="settings-checkbox"
              checked={localSettings.showGeneratedCode}
              onChange={(e) => update("showGeneratedCode", e.target.checked)}
            />
          </label>

          <div className="settings-select-row">
            <span className="settings-label-main">Preview Rows</span>
            <span className="settings-label-sub">Number of rows shown in dataset preview</span>
            <select
              className="settings-select"
              value={localSettings.maxPreviewRows}
              onChange={(e) => update("maxPreviewRows", Number(e.target.value))}
            >
              <option value={5}>5 rows</option>
              <option value={10}>10 rows</option>
              <option value={20}>20 rows</option>
            </select>
          </div>
        </section>

        {/* Session data */}
        <section className="settings-section">
          <h3 className="settings-section-title">Session Data</h3>
          <div className="settings-danger-row">
            <div>
              <p className="settings-label-main">Clear Analysis History</p>
              <p className="settings-label-sub">
                Removes all {historyCount} stored analyses from this session
              </p>
            </div>
            <button
              className="settings-clear-btn"
              onClick={onClearHistory}
              disabled={historyCount === 0}
            >
              Clear History
            </button>
          </div>
        </section>

        {/* About */}
        <section className="settings-section">
          <h3 className="settings-section-title">About</h3>
          <div className="settings-about">
            <div className="settings-about-row">
              <span className="settings-about-key">Product</span>
              <span className="settings-about-val">ProofAI</span>
            </div>
            <div className="settings-about-row">
              <span className="settings-about-key">Version</span>
              <span className="settings-about-val">2.0.0</span>
            </div>
            <div className="settings-about-row">
              <span className="settings-about-key">Description</span>
              <span className="settings-about-val">Proof-Carrying AI Data Analyst</span>
            </div>
            <div className="settings-about-row">
              <span className="settings-about-key">Supported Formats</span>
              <span className="settings-about-val">CSV · Excel · JSON · HTML · TXT · PDF</span>
            </div>
          </div>
        </section>

      </div>

      <div className="settings-actions">
        <button className="settings-save-btn" onClick={save}>
          {saved ? "Saved ✓" : "Save Settings"}
        </button>
      </div>
    </div>
  );
}
