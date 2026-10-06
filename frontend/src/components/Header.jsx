export default function Header() {
  return (
    <header className="header">
      <div className="header-inner">
        {/* Logo */}
        <div className="logo">
          <div className="logo-mark" aria-hidden="true">
            <svg viewBox="0 0 16 16" xmlns="http://www.w3.org/2000/svg">
              {/* shield-check icon */}
              <path
                fillRule="evenodd"
                clipRule="evenodd"
                d="M8 1L2 3.5V8c0 3.1 2.4 5.4 6 6.5 3.6-1.1 6-3.4 6-6.5V3.5L8 1zM6.7 9.7L5 8l1-1 1.2 1.2 2.8-2.9 1 1L6.7 9.7z"
              />
            </svg>
          </div>
          <span className="logo-name">ProofAI</span>
        </div>

        <div className="header-sep" aria-hidden="true" />

        <p className="header-tagline">Proof-Carrying AI Data Analyst</p>

        {/* Status */}
        <div className="header-status" role="status" aria-label="System status: ready">
          <span className="status-dot" aria-hidden="true" />
          System Ready
        </div>
      </div>
    </header>
  );
}
