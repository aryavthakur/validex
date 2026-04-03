import { useRef, useState, useEffect, useMemo } from "react";
import { motion, AnimatePresence, useInView } from "framer-motion";
import { ShimmerButton } from "./ui/ShimmerButton";
import { Marquee } from "./ui/Marquee";
import { Spotlight } from "./ui/Spotlight";

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
    <div style={{
      background: "var(--bg-panel)", border: "1px solid var(--border-mid)",
      borderRadius: "var(--radius-lg)", overflow: "hidden",
      boxShadow: "0 0 0 1px rgba(255,255,255,0.04) inset, 0 40px 80px rgba(0,0,0,0.5)",
    }}>
      <div style={{
        display: "flex", alignItems: "center", gap: 12,
        padding: "14px 20px", borderBottom: "1px solid var(--border)",
        background: "var(--bg-raised)",
      }}>
        <div style={{ display: "flex", gap: 6 }}>
          {["rgba(248,113,113,0.4)", "rgba(245,158,11,0.4)", "rgba(74,222,128,0.4)"].map((bg, i) => (
            <div key={i} style={{ width: 10, height: 10, borderRadius: "50%", background: bg }} />
          ))}
        </div>
        <div style={{ flex: 1, textAlign: "center", fontFamily: "var(--font-mono)", fontSize: 11, color: "var(--text-dim)", letterSpacing: "0.06em" }}>
          validex — metabolomics audit
        </div>
        <div style={{ fontFamily: "var(--font-mono)", fontSize: 10, color: "var(--green)", background: "var(--green-subtle)", border: "1px solid rgba(74,222,128,0.15)", padding: "2px 8px", borderRadius: 99, letterSpacing: "0.06em" }}>
          ● live
        </div>
      </div>
      <div style={{ position: "relative", width: "100%", aspectRatio: "16/9", background: "var(--bg)", overflow: "hidden" }}>
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
          onError={e => {
            e.target.style.display = "none";
            e.target.nextSibling.style.display = "flex";
          }}
        />
        <div style={{ display: "none", position: "absolute", inset: 0, alignItems: "center", justifyContent: "center", background: "var(--bg-panel)", padding: 32 }}>
          {fallback}
        </div>
        <div
          onClick={toggle}
          style={{ position: "absolute", inset: 0, display: "flex", alignItems: "center", justifyContent: "center", background: "rgba(0,0,0,0.2)", opacity: 0, transition: "opacity 0.2s", cursor: "pointer" }}
          onMouseEnter={e => e.currentTarget.style.opacity = 1}
          onMouseLeave={e => e.currentTarget.style.opacity = 0}
        >
          <div style={{ width: 56, height: 56, borderRadius: "50%", background: "rgba(240,237,232,0.1)", border: "1px solid rgba(240,237,232,0.2)", backdropFilter: "blur(8px)", display: "flex", alignItems: "center", justifyContent: "center", fontSize: 18 }}>
            {playing ? "⏸" : "▶"}
          </div>
        </div>
      </div>
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
          <video ref={videoRef} className="showcase-video" src="/demo.mp4" poster="/demo-poster.jpg" autoPlay muted loop playsInline preload="metadata" />
          <div className="showcase-play-overlay" onClick={toggle}>
            <div className="play-btn">{playing ? "⏸" : "▶"}</div>
          </div>
        </div>
      </div>
    </div>
  );
}

// ── FULL-WIDTH FEATURE SECTION ───────────────────────────────────────────────
// Text on left, video fills right — same max-width as hero, video dominates

function FeatureSection({ label, title, sub, extras, videoSrc, videoPoster, fallback }) {
  return (
    <div style={{
      borderTop: "1px solid var(--border)",
      padding: "100px 32px",
      maxWidth: 1100,
      margin: "0 auto",
    }}>
      {/* Text row — two columns: title left, sub + extras right */}
      <div style={{
        display: "grid",
        gridTemplateColumns: "1fr 1fr",
        gap: 64,
        alignItems: "start",
        marginBottom: 52,
      }}>
        <FadeUp>
          <div>
            <div className="section-label">{label}</div>
            <h2 style={{
              fontFamily: "var(--font-serif)",
              fontSize: "clamp(2rem, 3.5vw, 3rem)",
              fontWeight: 400,
              lineHeight: 1.1,
              letterSpacing: "-0.02em",
              color: "var(--text)",
              margin: 0,
            }}>{title}</h2>
          </div>
        </FadeUp>
        <FadeUp delay={0.1}>
          <div style={{ paddingTop: 8 }}>
            <p style={{ fontSize: 15, color: "var(--text-muted)", lineHeight: 1.75, marginBottom: extras ? 24 : 0 }}>{sub}</p>
            {extras}
          </div>
        </FadeUp>
      </div>
      {/* Full-width video */}
      <FeatureVideo src={videoSrc} poster={videoPoster} fallback={fallback} />
    </div>
  );
}

// ── FALLBACK MOCKUPS ─────────────────────────────────────────────────────────

function AiScoreFallback() {
  return (
    <div style={{ width: "100%", padding: "40px 60px" }}>
      <div style={{ display: "flex", gap: 48, marginBottom: 24, justifyContent: "center" }}>
        <div style={{ textAlign: "right" }}>
          <div style={{ fontFamily: "var(--font-mono)", fontSize: 11, color: "var(--text-dim)", letterSpacing: "0.1em", textTransform: "uppercase", marginBottom: 8 }}>Automated</div>
          <div style={{ fontFamily: "var(--font-serif)", fontSize: 64, color: "var(--green)", lineHeight: 1 }}>80<span style={{ fontSize: 24, opacity: 0.3 }}>/100</span></div>
        </div>
        <div style={{ display: "flex", alignItems: "center", color: "var(--text-dim)", fontSize: 28 }}>→</div>
        <div>
          <div style={{ fontFamily: "var(--font-mono)", fontSize: 11, color: "var(--accent-warm)", letterSpacing: "0.1em", textTransform: "uppercase", marginBottom: 8 }}>AI-adjusted</div>
          <div style={{ fontFamily: "var(--font-serif)", fontSize: 64, color: "var(--amber)", lineHeight: 1 }}>62<span style={{ fontSize: 24, opacity: 0.3 }}>/100</span></div>
        </div>
      </div>
      <div style={{ height: 3, background: "var(--border)", borderRadius: 2, overflow: "hidden", marginBottom: 20, maxWidth: 500, margin: "0 auto 20px" }}>
        <div style={{ height: "100%", width: "62%", background: "var(--amber)", borderRadius: 2 }} />
      </div>
      <div style={{ maxWidth: 520, margin: "0 auto", background: "var(--bg-raised)", border: "1px solid var(--border)", borderRadius: 10, padding: "14px 18px", fontSize: 13, color: "var(--text-muted)", lineHeight: 1.6 }}>
        <span style={{ color: "var(--amber)", fontFamily: "var(--font-mono)", fontSize: 12, fontWeight: 500 }}>−18 pts · </span>
        Pilot study with small n reduces confidence. Batch correction absent across 3 instrument runs.
      </div>
    </div>
  );
}

function AiAnalysisFallback() {
  return (
    <div style={{ width: "100%", padding: "40px 60px" }}>
      <div style={{ fontFamily: "var(--font-mono)", fontSize: 10, color: "var(--text-dim)", letterSpacing: "0.1em", marginBottom: 20, textTransform: "uppercase" }}>
        AI-POWERED ANALYSIS · GROQ
      </div>
      <div style={{ fontSize: 14, color: "var(--text-muted)", lineHeight: 1.9, maxWidth: 600 }}>
        <div style={{ marginBottom: 16 }}>
          <strong style={{ color: "var(--text)", fontWeight: 500 }}>1. Data Quality</strong><br />
          Dataset is well-formed with 0 missing values across 30 samples and 18 metabolites.
        </div>
        <div style={{ marginBottom: 16 }}>
          <strong style={{ color: "var(--text)", fontWeight: 500 }}>2. Key Patterns</strong><br />
          Glucose levels are significantly elevated in the Disease group (avg 9.07 vs 5.30 in Control).
        </div>
        <div>
          <strong style={{ color: "var(--text)", fontWeight: 500 }}>3. Top Biomarkers</strong><br />
          Glucose, Lactate, and Tryptophan show the strongest group separation.
        </div>
      </div>
      <div style={{ marginTop: 20, display: "flex", gap: 8 }}>
        <span style={{ fontFamily: "var(--font-mono)", fontSize: 10, color: "var(--green)", background: "var(--green-subtle)", border: "1px solid rgba(74,222,128,0.15)", padding: "3px 9px", borderRadius: 99 }}>AI ● online</span>
        <span style={{ fontFamily: "var(--font-mono)", fontSize: 10, color: "var(--text-dim)", background: "var(--bg-panel)", border: "1px solid var(--border)", padding: "3px 9px", borderRadius: 99 }}>Groq · free</span>
      </div>
    </div>
  );
}

function CleanDataFallback() {
  return (
    <div style={{ width: "100%", padding: "40px 60px" }}>
      <div style={{ display: "grid", gridTemplateColumns: "repeat(4, 1fr)", gap: 12, marginBottom: 24 }}>
        {[
          { label: "Original", value: "30 rows" },
          { label: "To remove", value: "6 rows", warn: true },
          { label: "Kept", value: "24 rows" },
          { label: "Columns", value: "20 cols" },
        ].map((m, i) => (
          <div key={i} style={{ background: "var(--bg-raised)", border: `1px solid ${m.warn ? "rgba(245,158,11,0.3)" : "var(--border)"}`, borderRadius: 10, padding: "16px" }}>
            <div style={{ fontFamily: "var(--font-mono)", fontSize: 9, color: "var(--text-dim)", letterSpacing: "0.1em", textTransform: "uppercase", marginBottom: 6 }}>{m.label}</div>
            <div style={{ fontFamily: "var(--font-serif)", fontSize: 28, color: m.warn ? "var(--amber)" : "var(--text)" }}>{m.value}</div>
          </div>
        ))}
      </div>
      <div style={{ padding: "12px 16px", background: "rgba(74,222,128,0.04)", border: "1px solid rgba(74,222,128,0.15)", borderRadius: 8, fontSize: 13, color: "var(--green)" }}>
        ✓ Reviewed and approved → dataset_clean.csv
      </div>
    </div>
  );
}

// ── FADE-UP SCROLL REVEAL ────────────────────────────────────────────────────

function FadeUp({ children, delay = 0, style = {} }) {
  const ref = useRef(null);
  const inView = useInView(ref, { once: true, margin: "-60px" });
  return (
    <motion.div
      ref={ref}
      initial={{ opacity: 0, y: 22 }}
      animate={inView ? { opacity: 1, y: 0 } : { opacity: 0, y: 22 }}
      transition={{ type: "spring", stiffness: 100, damping: 20, delay }}
      style={style}
    >
      {children}
    </motion.div>
  );
}

// ── MARQUEE KEYWORDS ─────────────────────────────────────────────────────────

const KEYWORDS = [
  "STATISTICAL INTEGRITY",
  "FDR CONTROL",
  "BATCH CORRECTION",
  "REPRODUCIBLE SCIENCE",
  "AI-SCORED",
  "OUTLIER DETECTION",
  "SCHEMA DETECTION",
  "PUBLICATION-READY",
];

function KeywordMarquee() {
  const item = (text, i) => (
    <span key={i} style={{
      display: "inline-flex",
      alignItems: "center",
      gap: 10,
      fontFamily: "var(--font-mono)",
      fontSize: 10,
      letterSpacing: "0.14em",
      textTransform: "uppercase",
      color: "var(--text-dim)",
      whiteSpace: "nowrap",
      padding: "0 24px",
    }}>
      <span style={{ width: 3, height: 3, borderRadius: "50%", background: "var(--accent-warm)", display: "inline-block", flexShrink: 0 }} />
      {text}
    </span>
  );

  return (
    <div style={{
      width: "100%",
      borderTop: "1px solid var(--border)",
      borderBottom: "1px solid var(--border)",
      padding: "12px 0",
      overflow: "hidden",
      maskImage: "linear-gradient(to right, transparent, black 10%, black 90%, transparent)",
      WebkitMaskImage: "linear-gradient(to right, transparent, black 10%, black 90%, transparent)",
    }}>
      <Marquee duration="30s" gap="0px" repeat={3} pauseOnHover>
        {KEYWORDS.map(item)}
      </Marquee>
    </div>
  );
}

// ── STATS ROW ────────────────────────────────────────────────────────────────

const STATS = [
  { value: "< 3s",  label: "Average audit time"     },
  { value: "18+",   label: "Detection rules"         },
  { value: "Free",  label: "Always, no login needed" },
  { value: "AI",    label: "Groq-powered analysis"   },
];

function StatsRow() {
  return (
    <FadeUp delay={0.1}>
      <div style={{
        display: "grid",
        gridTemplateColumns: "repeat(4, 1fr)",
        gap: 1,
        background: "var(--border)",
        border: "1px solid var(--border)",
        borderRadius: "var(--radius)",
        overflow: "hidden",
        maxWidth: 680,
        margin: "0 auto",
      }}>
        {STATS.map((s, i) => (
          <div key={i} style={{
            background: "var(--bg-panel)",
            padding: "18px 16px",
            textAlign: "center",
          }}>
            <div style={{
              fontFamily: "var(--font-serif)",
              fontSize: 26,
              color: "var(--text)",
              lineHeight: 1,
              marginBottom: 5,
            }}>{s.value}</div>
            <div style={{
              fontFamily: "var(--font-mono)",
              fontSize: 9,
              letterSpacing: "0.1em",
              textTransform: "uppercase",
              color: "var(--text-dim)",
            }}>{s.label}</div>
          </div>
        ))}
      </div>
    </FadeUp>
  );
}

// ── LANDING PAGE ─────────────────────────────────────────────────────────────

function AnimatedHeroTitle() {
  const words = useMemo(() => ["publication-ready", "validated", "audit-grade", "AI-scored", "reproducible"], []);
  const [index, setIndex] = useState(0);

  useEffect(() => {
    const id = setInterval(() => setIndex(i => (i + 1) % words.length), 2400);
    return () => clearInterval(id);
  }, [words]);

  return (
    <h1 className="hero-title">
      From raw data to
      <span style={{ display: "block", position: "relative", height: "1.2em", overflow: "hidden" }}>
        <AnimatePresence mode="wait">
          <motion.em
            key={words[index]}
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -20 }}
            transition={{ type: "spring", stiffness: 120, damping: 18 }}
            style={{ display: "block" }}
          >
            {words[index]}
          </motion.em>
        </AnimatePresence>
      </span>
      <span style={{ fontSize: "0.7em", fontStyle: "normal", color: "var(--text-muted)" }}>in seconds.</span>
    </h1>
  );
}

export default function LandingPage({ onLaunch, onDemo }) {
  return (
    <div className="landing">

      <section className="hero" style={{ position: "relative", overflow: "hidden" }}>
        <Spotlight style={{ top: "-20%", left: "-10%" }} />
        <div className="hero-eyebrow" style={{ position: "relative", zIndex: 1 }}>
          <span className="hero-eyebrow-dot" />
          Metabolomics validity auditing · AI-powered
        </div>
        <AnimatedHeroTitle />
        <p className="hero-sub">
          Upload a metabolomics CSV. Validex audits your statistical completeness, flags issues, scores confidence with AI, and returns a cleaned dataset — all in one step.
        </p>
        <div className="hero-cta">
          <ShimmerButton onClick={onLaunch}>Run your first audit →</ShimmerButton>
          <button className="btn-secondary" onClick={onDemo}>See an example report</button>
        </div>

        <KeywordMarquee />

        <div style={{ padding: "32px 0 8px" }}>
          <StatsRow />
        </div>

        <VideoShowcase />
      </section>

      {/* HOW IT WORKS */}
      <section className="section">
        <FadeUp><div className="section-label">How it works</div></FadeUp>
        <FadeUp delay={0.05}><h2 className="section-title">Four steps from upload to clean, scored report.</h2></FadeUp>
        <FadeUp delay={0.1}>
          <p className="section-sub">
            No configuration required. Validex adapts to your column naming conventions and study design automatically.
          </p>
        </FadeUp>
        <div className="steps-grid" style={{ gridTemplateColumns: "repeat(4, 1fr)" }}>
          {[
            { num: "01", icon: "📁", title: "Upload your CSV", desc: "Drag and drop any metabolomics results file. Works with untargeted and targeted exports from common platforms." },
            { num: "02", icon: "⚙️", title: "Set study context", desc: "Specify your design — paired vs independent, batch effects, sample size, and notes. Context shapes what Validex flags." },
            { num: "03", icon: "🤖", title: "Get AI insights", desc: "Ask any question about your data. Groq analyzes patterns, flags outliers, and suggests next steps." },
            { num: "04", icon: "🧹", title: "Download clean data", desc: "Review proposed removals — duplicates, outliers, missing values — then download a cleaned CSV with your approval." },
          ].map((step, i) => (
            <FadeUp key={i} delay={i * 0.08}>
              <div className="step-card">
                <div className="step-num">{step.num}</div>
                <span className="step-icon">{step.icon}</span>
                <div className="step-title">{step.title}</div>
                <p className="step-desc">{step.desc}</p>
              </div>
            </FadeUp>
          ))}
        </div>
      </section>

      {/* FEATURE: SCHEMA DETECTION — side by side, code mockup */}
      <div className="feature-split" style={{ borderTop: "1px solid var(--border)" }}>
        <FadeUp>
          <div className="feature-text">
            <div className="section-label">Schema detection</div>
            <h2 className="section-title">Finds your columns, whatever you call them.</h2>
            <p className="section-sub">
              Validex normalizes hundreds of column naming conventions — pval, p.val, P_Value, adjusted_p — and maps them to canonical statistical fields automatically.
            </p>
          </div>
        </FadeUp>
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

      {/* FEATURE: AI CONFIDENCE SCORING — full width video */}
      <FeatureSection
        label="AI confidence scoring"
        title="A score that actually reflects your study design."
        sub="Validex starts with an automated score based on statistical completeness. Add notes about your study — sample size, batch effects, validation methods — and AI adjusts the score to reflect the full picture."
        extras={
          <div style={{ display: "flex", flexDirection: "column", gap: 10 }}>
            {[
              { note: '"Pilot study, n=6 per group, no batch correction"', delta: "−18 pts", color: "var(--red)" },
              { note: '"Validated by orthogonal LC-MS/MS, n=120"', delta: "+12 pts", color: "var(--green)" },
            ].map((ex, i) => (
              <div key={i} style={{ display: "flex", alignItems: "center", gap: 12, background: "var(--bg-panel)", border: "1px solid var(--border)", borderRadius: 10, padding: "10px 14px" }}>
                <span style={{ fontFamily: "var(--font-mono)", fontSize: 12, fontWeight: 500, color: ex.color, flexShrink: 0, minWidth: 52 }}>{ex.delta}</span>
                <span style={{ fontSize: 12, color: "var(--text-muted)", fontFamily: "var(--font-mono)" }}>{ex.note}</span>
              </div>
            ))}
          </div>
        }
        videoSrc="/demo-ai-score.mp4"
        videoPoster="/demo-ai-score-poster.jpg"
        fallback={<AiScoreFallback />}
      />

      {/* FEATURE: AI ANALYSIS — full width video */}
      <FeatureSection
        label="AI analysis"
        title="Ask anything about your metabolite data."
        sub="Powered by Groq. Ask about key patterns, biomarker candidates, batch effects, statistical concerns, or next steps. The AI reads your actual data — not a summary."
        extras={
          <div style={{ display: "flex", flexDirection: "column", gap: 8 }}>
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
        }
        videoSrc="/demo-ai-analysis.mp4"
        videoPoster="/demo-ai-analysis-poster.jpg"
        fallback={<AiAnalysisFallback />}
      />

      {/* FEATURE: CLEAN DATA — full width video */}
      <FeatureSection
        label="Data cleaning"
        title="Review proposed changes before you download."
        sub="Validex detects duplicates, high-missing rows, and statistical outliers. You see exactly what would be removed and why — then approve and download the cleaned CSV. Nothing is deleted without your sign-off."
        extras={
          <div style={{ display: "flex", flexDirection: "column", gap: 10 }}>
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
            <div style={{ marginTop: 4, padding: "10px 14px", background: "rgba(74,222,128,0.04)", border: "1px solid rgba(74,222,128,0.15)", borderRadius: 8, fontSize: 13, color: "var(--green)" }}>
              ✓ Reviewed and approved → download_clean.csv
            </div>
          </div>
        }
        videoSrc="/demo-clean-data.mp4"
        videoPoster="/demo-clean-data-poster.jpg"
        fallback={<CleanDataFallback />}
      />

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
