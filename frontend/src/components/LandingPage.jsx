import { useRef, useState } from "react";

// ── VIDEO SHOWCASE ──────────────────────────────────────────────────────────
// To add your real video, place it at: frontend/public/demo.mp4
// and optionally frontend/public/demo-poster.jpg
// The component will use it automatically.
// If no video file exists, a polished placeholder is shown instead.

function VideoShowcase() {
  const videoRef = useRef(null);
  const [playing, setPlaying] = useState(true);

  const toggle = () => {
    if (!videoRef.current) return;
    if (videoRef.current.paused) { videoRef.current.play(); setPlaying(true); }
    else { videoRef.current.pause(); setPlaying(false); }
  };

  // Check if video file likely exists (you can hardcode true once you add demo.mp4)
  const HAS_VIDEO = true; // ← set to true once you drop demo.mp4 into public/

  return (
    <div className="showcase-wrap">
      <div className="showcase-frame">
        {/* Chrome bar */}
        <div className="showcase-chrome">
          <div className="chrome-dots">
            <div className="chrome-dot" />
            <div className="chrome-dot" />
            <div className="chrome-dot" />
          </div>
          <div className="chrome-title">validex — metabolomics audit</div>
          <div className="chrome-badge">● live</div>
        </div>

        {/* Video / placeholder */}
        <div className="showcase-video-wrap">
          {HAS_VIDEO ? (
            <>
              <video
                ref={videoRef}
                className="showcase-video"
                src="/demo.mp4"
                poster="/demo-poster.jpg"
                autoPlay
                muted
                loop
                playsInline
                preload="metadata"
              />
              <div className="showcase-play-overlay" onClick={toggle}>
                <div className="play-btn">
                  {playing ? "⏸" : "▶"}
                </div>
              </div>
            </>
          ) : (
            <div className="showcase-placeholder">
              <div className="showcase-placeholder-icon">📊</div>
              <div className="showcase-placeholder-text">
                Drop demo.mp4 into frontend/public/<br />
                to activate the video showcase
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

// ── LANDING PAGE ────────────────────────────────────────────────────────────
export default function LandingPage({ onLaunch, onDemo }) {
  return (
    <div className="landing">

      {/* HERO */}
      <section className="hero">
        <div className="hero-eyebrow">
          <span className="hero-eyebrow-dot" />
          Metabolomics validity auditing
        </div>
        <h1 className="hero-title">
          Make your results<br />
          <em>audit-ready</em> in seconds.
        </h1>
        <p className="hero-sub">
          Upload a metabolomics CSV. Validex detects your statistical schema, checks for p-values, FDR correction, and fold change — then generates a structured validity report.
        </p>
        <div className="hero-cta">
          <button className="btn-primary" onClick={onLaunch}>
            Run your first audit →
          </button>
          <button className="btn-secondary" onClick={onDemo}>
            See an example report
          </button>
        </div>
        <VideoShowcase />
      </section>

      {/* HOW IT WORKS */}
      <section className="section">
        <div className="section-label">How it works</div>
        <h2 className="section-title">From raw output to structured report in three steps.</h2>
        <p className="section-sub">
          No configuration required. Validex adapts to your column naming conventions automatically.
        </p>
        <div className="steps-grid">
          <div className="step-card">
            <div className="step-num">01</div>
            <span className="step-icon">📁</span>
            <div className="step-title">Upload your CSV</div>
            <p className="step-desc">Drag and drop any metabolomics results file. Validex handles untargeted and targeted exports from common platforms.</p>
          </div>
          <div className="step-card">
            <div className="step-num">02</div>
            <span className="step-icon">⚙️</span>
            <div className="step-title">Set study context</div>
            <p className="step-desc">Specify your design — paired vs independent, confirmatory vs exploratory, batch effects, sample size. Context changes what Validex expects.</p>
          </div>
          <div className="step-card">
            <div className="step-num">03</div>
            <span className="step-icon">📋</span>
            <div className="step-title">Export the report</div>
            <p className="step-desc">Get a structured validity report with confidence score, flags, scientific interpretations, and corrective recommendations.</p>
          </div>
        </div>
      </section>

      {/* FEATURE: SCHEMA DETECTION */}
      <div className="feature-split">
        <div className="feature-text">
          <div className="section-label">Schema detection</div>
          <h2 className="section-title">Finds your columns, whatever you call them.</h2>
          <p className="section-sub">
            Validex normalizes hundreds of column naming conventions — pval, p.val, P_Value, adjusted_p — and maps them to canonical statistical fields automatically.
          </p>
        </div>
        <div className="feature-panel">
          <div className="feature-panel-chrome">
            <div className="feature-panel-dot" />
            <div className="feature-panel-dot" />
            <div className="feature-panel-dot" />
          </div>
          <div className="feature-panel-body">
            {[
              { key: "p_value", val: "P_Value_ttest", ok: true },
              { key: "fdr", val: "adj.p.BH", ok: true },
              { key: "fold_change", val: "FC_log2", ok: true },
              { key: "feature", val: "Metabolite_ID", ok: true },
              { key: "log2fc", val: null, ok: false },
            ].map(r => (
              <div className="schema-row-demo" key={r.key}>
                <span className="schema-key">{r.key}</span>
                <span className="schema-val">{r.val || "—"}</span>
                <span className={r.ok ? "schema-badge-ok" : "schema-badge-miss"}>
                  {r.ok ? "mapped" : "missing"}
                </span>
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* FEATURE: CONFIDENCE SCORE */}
      <div className="feature-split reverse">
        <div className="feature-text">
          <div className="section-label">Confidence scoring</div>
          <h2 className="section-title">A single score that captures statistical completeness.</h2>
          <p className="section-sub">
            Validex deducts from a 100-point confidence score based on missing corrections, absent effect sizes, schema ambiguities, and design mismatches.
          </p>
        </div>
        <div className="feature-panel">
          <div className="feature-panel-chrome">
            <div className="feature-panel-dot" />
            <div className="feature-panel-dot" />
            <div className="feature-panel-dot" />
          </div>
          <div className="confidence-demo">
            <div className="confidence-num">72<span style={{ fontSize: 20, opacity: 0.3 }}>/100</span></div>
            <div className="confidence-bar-track">
              <div className="confidence-bar-fill" />
            </div>
            <div className="confidence-flag">
              <div className="flag-dot high" />
              <span style={{ fontSize: 13, color: "var(--text-muted)" }}>No FDR/q-values detected — multiple testing risk</span>
            </div>
            <div className="confidence-flag">
              <div className="flag-dot med" />
              <span style={{ fontSize: 13, color: "var(--text-muted)" }}>Schema ambiguity in fold_change column</span>
            </div>
            <div className="confidence-flag">
              <div className="flag-dot med" />
              <span style={{ fontSize: 13, color: "var(--text-muted)" }}>Small sample size — overclaiming risk elevated</span>
            </div>
          </div>
        </div>
      </div>

      {/* FOOTER */}
      <div style={{ borderTop: "1px solid var(--border)" }}>
        <footer className="footer">
          <div className="footer-logo">Validex</div>
          <div className="footer-copy">© 2026 · Metabolomics Validity Auditor</div>
        </footer>
      </div>

    </div>
  );
}
