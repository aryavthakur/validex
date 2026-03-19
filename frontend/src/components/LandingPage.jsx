import { useRef, useState } from "react";

// ── REUSABLE MEDIA COMPONENTS ────────────────────────────────────────────────

function FeatureVideo({ src, poster, fallback }) {
  const videoRef = useRef(null);
  const [playing, setPlaying] = useState(true);

  const toggle = () => {
    if (!videoRef.current) return;
    if (videoRef.current.paused) { videoRef.current.play(); setPlaying(true); }
    else { videoRef.current.pause(); setPlaying(false); }
  };

  return (
    <div className="feature-panel" style={{ overflow: "hidden" }}>
      <div className="feature-panel-chrome">
        <div className="feature-panel-dot" />
        <div className="feature-panel-dot" />
        <div className="feature-panel-dot" />
      </div>
      <div style={{ position: "relative", width: "100%", aspectRatio: "4/3", background: "var(--bg)", overflow: "hidden" }}>
        <video
          ref={videoRef}
          src={src}
          poster={poster}
          autoPlay
          muted
          loop
          playsInline
          preload="metadata"
          style={{ width: "100%", height: "100%", objectFit: "cover", display: "block" }}
          onError={e => { e.target.style.display = "none"; e.target.nextSibling.style.display = "flex"; }}
        />
        {/* Fallback shown if video fails to load */}
        <div style={{ display: "none", position: "absolute", inset: 0, alignItems: "center", justifyContent: "center", background: "var(--bg-panel)" }}>
          {fallback}
        </div>
        <div
          onClick={toggle}
          style={{ position: "absolute", inset: 0, display: "flex", alignItems: "center", justifyContent: "center", background: "rgba(0,0,0,0.25)", opacity: 0, transition: "opacity 0.2s", cursor: "pointer" }}
          onMouseEnter={e => e.currentTarget.style.opacity = 1}
          onMouseLeave={e => e.currentTarget.style.opacity = 0}
        >
          <div style={{ width: 48, height: 48, borderRadius: "50%", background: "rgba(240,237,232,0.1)", border: "1px solid rgba(240,237,232,0.2)", backdropFilter: "blur(8px)", display: "flex", alignItems: "center", justifyContent: "center", fontSize: 16 }}>
            {playing ? "⏸" : "▶"}
          </div>
        </div>
      </div>
    </div>
  );
}

function FeatureScreenshot({ src, alt, fallback }) {
  const [failed, setFailed] = useState(false);

  if (failed) {
    return (
      <div className="feature-panel">
        <div className="feature-panel-chrome">
          <div className="feature-panel-dot" /><div className="feature-panel-dot" /><div className="feature-panel-dot" />
        </div>
        <div className="feature-panel-body">{fallback}</div>
      </div>
    );
  }

  return (
    <div className="feature-panel" style={{ overflow: "hidden" }}>
      <div className="feature-panel-chrome">
        <div className="feature-panel-dot" /><div className="feature-panel-dot" /><div className="feature-panel-dot" />
      </div>
      <img
        src={src}
        alt={alt}
        onError={() => setFailed(true)}
        style={{ width: "100%", display: "block", objectFit: "cover" }}
      />
    </div>
  );
}

// ── HERO VIDEO ───────────────────────────────────────────────────────────────

function VideoShowcase() {
  const videoRef = useRef(null);
  const [playing, setPlaying] = useState(true);

  const toggle = () => {
    if (!videoRef.current) return;
    if (videoRef.current.paused) { videoRef.current.play(); setPlaying(true); }
    else { videoRef.current.pause(); setPlaying(false); }
  };

  const HAS_VIDEO = true;

  return (
    <div className="showcase-wrap">
      <div className="showcase-frame">
        <div className="showcase-chrome">
          <div className="chrome-dots">
            <div className="chrome-dot" /><div className="chrome-dot" /><div className="chrome-dot" />
          </div>
          <div className="chrome-title">validex — metabolomics audit</div>
          <div className="chrome-badge">● live</div>
        </div>
        <div className="showcase-video-wrap">
          {HAS_VIDEO ? (
            <>
              <video ref={videoRef} className="showcase-video" src="/demo.mp4" poster="/demo-poster.jpg" autoPlay muted loop playsInline preload="metadata" />
              <div className="showcase-play-overlay" onClick={toggle}>
                <div className="play-btn">{playing ? "⏸" : "▶"}</div>
              </div>
            </>
          ) : (
            <div className="showcase-placeholder">
              <div className="showcase-placeholder-icon">📊</div>
              <div className="showcase-placeholder-text">Drop demo.mp4 into frontend/public/</div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

// ── FALLBACK MOCKUPS (shown when no media file exists) ───────────────────────

function AiScoreFallback() {
  return (
    <div className="confidence-demo">
      <div style={{ display: "flex", gap: 32, marginBottom: 16 }}>
        <div>
          <div style={{ fontFamily: "var(--font-mono)", fontSize: 10, color: "var(--text-dim)", letterSpacing: "0.1em", textTransform: "uppercase", marginBottom: 6 }}>Automated</div>
          <div className="confidence-num" style={{ fontSize: 36 }}>80<span style={{ fontSize: 16, opacity: 0.3 }}>/100</span></div>
        </div>
        <div style={{ display: "flex", alignItems: "center", color: "var(--text-dim)", fontSize: 18 }}>→</div>
        <div>
          <div style={{ fontFamily: "var(--font-mono)", fontSize: 10, color: "var(--accent-warm)", letterSpacing: "0.1em", textTransform: "uppercase", marginBottom: 6 }}>AI-adjusted</div>
          <div className="confidence-num" style={{ fontSize: 36, color: "var(--amber)" }}>62<span style={{ fontSize: 16, opacity: 0.3 }}>/100</span></div>
        </div>
      </div>
      <div style={{ height: 3, background: "var(--border)", borderRadius: 2, overflow: "hidden", marginBottom: 16 }}>
        <div style={{ height: "100%", width: "62%", background: "var(--amber)", borderRadius: 2 }} />
      </div>
      <div style={{ background: "var(--bg-raised)", border: "1px solid var(--border)", borderRadius: 8, padding: "10px 12px", fontSize: 12, color: "var(--text-muted)", lineHeight: 1.6 }}>
        <span style={{ color: "var(--amber)", fontFamily: "var(--font-mono)", fontSize: 11, fontWeight: 500 }}>−18 pts · </span>
        Pilot study with small n reduces confidence. Batch correction absent across 3 instrument runs.
      </div>
      <div className="confidence-flag" style={{ marginTop: 12 }}>
        <div className="flag-dot high" />
        <span style={{ fontSize: 13, color: "var(--text-muted)" }}>No FDR/q-values detected</span>
      </div>
      <div className="confidence-flag">
        <div className="flag-dot med" />
        <span style={{ fontSize: 13, color: "var(--text-muted)" }}>Small sample size flagged in notes</span>
      </div>
    </div>
  );
}

function AiAnalysisFallback() {
  return (
    <>
      <div style={{ fontFamily: "var(--font-mono)", fontSize: 10, color: "var(--text-dim)", letterSpacing: "0.08em", marginBottom: 10, textTransform: "uppercase" }}>
        AI-POWERED ANALYSIS · GROQ
      </div>
      <div style={{ fontSize: 13, color: "var(--text-muted)", lineHeight: 1.8 }}>
        <div style={{ marginBottom: 12 }}>
          <strong style={{ color: "var(--text)", fontWeight: 500 }}>1. Data Quality</strong><br />
          Dataset is well-formed with 0 missing values across 30 samples and 18 metabolites.
        </div>
        <div style={{ marginBottom: 12 }}>
          <strong style={{ color: "var(--text)", fontWeight: 500 }}>2. Key Patterns</strong><br />
          Glucose levels are significantly elevated in the Disease group (avg 9.07 vs 5.30 in Control).
        </div>
        <div>
          <strong style={{ color: "var(--text)", fontWeight: 500 }}>3. Top Biomarkers</strong><br />
          Glucose, Lactate, and Tryptophan show the strongest group separation.
        </div>
      </div>
      <div style={{ marginTop: 14, display: "flex", gap: 8 }}>
        <span style={{ fontFamily: "var(--font-mono)", fontSize: 10, color: "var(--green)", background: "var(--green-subtle)", border: "1px solid rgba(74,222,128,0.15)", padding: "3px 9px", borderRadius: 99 }}>AI ● online</span>
        <span style={{ fontFamily: "var(--font-mono)", fontSize: 10, color: "var(--text-dim)", background: "var(--bg-panel)", border: "1px solid var(--border)", padding: "3px 9px", borderRadius: 99 }}>Groq · free</span>
      </div>
    </>
  );
}

function CleanDataFallback() {
  return (
    <>
      <div style={{ fontFamily: "var(--font-mono)", fontSize: 10, color: "var(--text-dim)", letterSpacing: "0.08em", marginBottom: 14, textTransform: "uppercase" }}>
        Cleaning settings
      </div>
      <div style={{ marginBottom: 14 }}>
        <div style={{ display: "flex", justifyContent: "space-between", fontSize: 11, fontFamily: "var(--font-mono)", color: "var(--text-dim)", marginBottom: 6 }}>
          <span>Missing threshold</span><span style={{ color: "var(--accent-warm)" }}>50%</span>
        </div>
        <div style={{ height: 3, background: "var(--border)", borderRadius: 2 }}>
          <div style={{ height: "100%", width: "50%", background: "var(--accent-warm)", borderRadius: 2 }} />
        </div>
      </div>
      <div style={{ marginBottom: 18 }}>
        <div style={{ display: "flex", justifyContent: "space-between", fontSize: 11, fontFamily: "var(--font-mono)", color: "var(--text-dim)", marginBottom: 6 }}>
          <span>Outlier threshold</span><span style={{ color: "var(--accent-warm)" }}>3σ</span>
        </div>
        <div style={{ height: 3, background: "var(--border)", borderRadius: 2 }}>
          <div style={{ height: "100%", width: "33%", background: "var(--accent-warm)", borderRadius: 2 }} />
        </div>
      </div>
      <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 8 }}>
        {[
          { label: "Original", value: "30 rows" },
          { label: "To remove", value: "6 rows", warn: true },
          { label: "Kept", value: "24 rows" },
          { label: "Columns", value: "20 cols" },
        ].map((m, i) => (
          <div key={i} style={{ background: "var(--bg-raised)", border: `1px solid ${m.warn ? "rgba(245,158,11,0.3)" : "var(--border)"}`, borderRadius: 8, padding: "10px 12px" }}>
            <div style={{ fontFamily: "var(--font-mono)", fontSize: 9, color: "var(--text-dim)", letterSpacing: "0.1em", textTransform: "uppercase", marginBottom: 4 }}>{m.label}</div>
            <div style={{ fontFamily: "var(--font-serif)", fontSize: 20, color: m.warn ? "var(--amber)" : "var(--text)" }}>{m.value}</div>
          </div>
        ))}
      </div>
    </>
  );
}

// ── LANDING PAGE ─────────────────────────────────────────────────────────────

export default function LandingPage({ onLaunch, onDemo }) {
  return (
    <div className="landing">

      {/* HERO */}
      <section className="hero">
        <div className="hero-eyebrow">
          <span className="hero-eyebrow-dot" />
          Metabolomics validity auditing · AI-powered
        </div>
        <h1 className="hero-title">
          From raw data to<br />
          <em>publication-ready</em> in seconds.
        </h1>
        <p className="hero-sub">
          Upload a metabolomics CSV. Validex audits your statistical completeness, flags issues, scores confidence with AI, and returns a cleaned dataset — all in one step.
        </p>
        <div className="hero-cta">
          <button className="btn-primary" onClick={onLaunch}>Run your first audit →</button>
          <button className="btn-secondary" onClick={onDemo}>See an example report</button>
        </div>
        <VideoShowcase />
      </section>

      {/* HOW IT WORKS */}
      <section className="section">
        <div className="section-label">How it works</div>
        <h2 className="section-title">Four steps from upload to clean, scored report.</h2>
        <p className="section-sub">
          No configuration required. Validex adapts to your column naming conventions and study design automatically.
        </p>
        <div className="steps-grid" style={{ gridTemplateColumns: "repeat(4, 1fr)" }}>
          <div className="step-card">
            <div className="step-num">01</div>
            <span className="step-icon">📁</span>
            <div className="step-title">Upload your CSV</div>
            <p className="step-desc">Drag and drop any metabolomics results file. Works with untargeted and targeted exports from common platforms.</p>
          </div>
          <div className="step-card">
            <div className="step-num">02</div>
            <span className="step-icon">⚙️</span>
            <div className="step-title">Set study context</div>
            <p className="step-desc">Specify your design — paired vs independent, batch effects, sample size, and notes. Context shapes what Validex flags.</p>
          </div>
          <div className="step-card">
            <div className="step-num">03</div>
            <span className="step-icon">🤖</span>
            <div className="step-title">Get AI insights</div>
            <p className="step-desc">Ask any question about your data. Groq analyzes patterns, flags outliers, and suggests next steps.</p>
          </div>
          <div className="step-card">
            <div className="step-num">04</div>
            <span className="step-icon">🧹</span>
            <div className="step-title">Download clean data</div>
            <p className="step-desc">Review proposed removals — duplicates, outliers, missing values — then download a cleaned CSV with your approval.</p>
          </div>
        </div>
      </section>

      {/* FEATURE: SCHEMA DETECTION — code mockup, no media */}
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
            <div className="feature-panel-dot" /><div className="feature-panel-dot" /><div className="feature-panel-dot" />
          </div>
          <div className="feature-panel-body">
            {[
              { key: "p_value",     val: "P_Value_ttest", ok: true  },
              { key: "fdr",         val: "adj.p.BH",       ok: true  },
              { key: "fold_change", val: "FC_log2",        ok: true  },
              { key: "feature",     val: "Metabolite_ID",  ok: true  },
              { key: "log2fc",      val: null,             ok: false },
            ].map(r => (
              <div className="schema-row-demo" key={r.key}>
                <span className="schema-key">{r.key}</span>
                <span className="schema-val">{r.val || "—"}</span>
                <span className={r.ok ? "schema-badge-ok" : "schema-badge-miss"}>{r.ok ? "mapped" : "missing"}</span>
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* FEATURE: AI CONFIDENCE SCORING — screenshot (drop demo-ai-score.mp4 into public/) */}
      <div className="feature-split reverse">
        <div className="feature-text">
          <div className="section-label">AI confidence scoring</div>
          <h2 className="section-title">A score that actually reflects your study design.</h2>
          <p className="section-sub">
            Validex starts with an automated score based on statistical completeness. Add notes about your study — sample size, batch effects, validation methods — and AI adjusts the score to reflect the full picture.
          </p>
          <div style={{ marginTop: 24, display: "flex", flexDirection: "column", gap: 10 }}>
            {[
              { note: '"Pilot study, n=6 per group, no batch correction"', delta: "−18 pts", color: "var(--red)" },
              { note: '"Validated by orthogonal LC-MS/MS, n=120"',         delta: "+12 pts", color: "var(--green)" },
            ].map((ex, i) => (
              <div key={i} style={{ display: "flex", alignItems: "center", gap: 12, background: "var(--bg-panel)", border: "1px solid var(--border)", borderRadius: 10, padding: "10px 14px" }}>
                <span style={{ fontFamily: "var(--font-mono)", fontSize: 12, fontWeight: 500, color: ex.color, flexShrink: 0, minWidth: 52 }}>{ex.delta}</span>
                <span style={{ fontSize: 12, color: "var(--text-muted)", fontFamily: "var(--font-mono)" }}>{ex.note}</span>
              </div>
            ))}
          </div>
        </div>
        {/* Screenshot: drop demo-ai-score.mp4 (or .png) into public/ */}
        <FeatureVideo
          src="/demo-ai-score.mp4"
          
          fallback={<AiScoreFallback />}
        />
      </div>

      {/* FEATURE: AI ANALYSIS — video (drop demo-ai-analysis.mp4 into public/) */}
      <div className="feature-split">
        <div className="feature-text">
          <div className="section-label">AI analysis</div>
          <h2 className="section-title">Ask anything about your metabolite data.</h2>
          <p className="section-sub">
            Powered by Groq. Ask about key patterns, biomarker candidates, batch effects, statistical concerns, or next steps. The AI reads your actual data — not a summary.
          </p>
          <div style={{ marginTop: 24, display: "flex", flexDirection: "column", gap: 8 }}>
            {[
              "Which metabolites differ most between groups?",
              "Are there outlier samples I should remove?",
              "What statistical test fits this design?",
              "Identify potential biomarkers by importance",
            ].map((q, i) => (
              <div key={i} style={{ display: "flex", alignItems: "center", gap: 10, padding: "8px 12px", background: "var(--bg-panel)", border: "1px solid var(--border)", borderRadius: 8, fontSize: 13, color: "var(--text-muted)" }}>
                <span style={{ color: "var(--accent-warm)", fontSize: 11 }}>→</span>
                {q}
              </div>
            ))}
          </div>
        </div>
        {/* Video: drop demo-ai-analysis.mp4 into public/ */}
        <FeatureVideo
          src="/demo-ai-analysis.mp4"
          
          fallback={<AiAnalysisFallback />}
        />
      </div>

      {/* FEATURE: CLEAN DATA — video (drop demo-clean-data.mp4 into public/) */}
      <div className="feature-split reverse">
        <div className="feature-text">
          <div className="section-label">Data cleaning</div>
          <h2 className="section-title">Review proposed changes before you download.</h2>
          <p className="section-sub">
            Validex detects duplicates, high-missing rows, and statistical outliers. You see exactly what would be removed and why — then approve and download the cleaned CSV. Nothing is deleted without your sign-off.
          </p>
          <div style={{ marginTop: 24, display: "flex", flexDirection: "column", gap: 10 }}>
            {[
              { sev: "high", label: "Rows with >50% missing values", count: "3 rows" },
              { sev: "med",  label: "Statistical outliers (>3σ)",    count: "2 rows" },
              { sev: "med",  label: "Duplicate rows",                count: "1 row"  },
            ].map((item, i) => (
              <div key={i} style={{ display: "flex", alignItems: "center", gap: 10 }}>
                <span style={{ fontFamily: "var(--font-mono)", fontSize: 9, fontWeight: 500, letterSpacing: "0.1em", textTransform: "uppercase", padding: "2px 7px", borderRadius: 4, flexShrink: 0, ...(item.sev === "high" ? { color: "#fca5a5", background: "var(--red-subtle)", border: "1px solid rgba(248,113,113,0.2)" } : { color: "#fcd34d", background: "var(--amber-subtle)", border: "1px solid rgba(245,158,11,0.2)" }) }}>
                  {item.sev}
                </span>
                <span style={{ fontSize: 13, color: "var(--text-muted)", flex: 1 }}>{item.label}</span>
                <span style={{ fontFamily: "var(--font-mono)", fontSize: 11, color: "var(--text-dim)" }}>{item.count}</span>
              </div>
            ))}
            <div style={{ marginTop: 8, padding: "10px 14px", background: "rgba(74,222,128,0.04)", border: "1px solid rgba(74,222,128,0.15)", borderRadius: 8, fontSize: 13, color: "var(--green)" }}>
              ✓ Reviewed and approved → download_clean.csv
            </div>
          </div>
        </div>
        {/* Video: drop demo-clean-data.mp4 into public/ */}
        <FeatureVideo
          src="/demo-clean-data.mp4"
          poster="/demo-clean-data-poster.jpg"
          fallback={<CleanDataFallback />}
        />
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
