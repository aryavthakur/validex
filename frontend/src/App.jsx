import { useState, useCallback } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { Analytics } from "@vercel/analytics/react";
import LandingPage from "./components/LandingPage";
import { AnimatedBackground } from "./components/ui/background-paths";
import UploadZone from "./components/UploadZone";
import ContextForm from "./components/ContextForm";
import AuditResults from "./components/AuditResults";
import DataPreview from "./components/DataPreview";
import { DEMO_RESULTS } from "./demoData";

const API_BASE = import.meta.env.VITE_API_URL || "http://localhost:8000";

const STEPS = ["Upload", "Context", "Audit", "Results"];
const VIEW_TO_STEP = { upload: 0, context: 1, running: 2, results: 3 };

function StepBar({ view }) {
  const current = VIEW_TO_STEP[view] ?? 0;
  const pct = ((current) / (STEPS.length - 1)) * 100;
  return (
    <div style={{
      position: "fixed", top: 56, left: 0, right: 0, zIndex: 190,
      height: 36, display: "flex", alignItems: "center",
      padding: "0 32px",
      background: "rgba(9,9,9,0.7)", backdropFilter: "blur(12px)",
      borderBottom: "1px solid var(--border)",
    }}>
      {/* Track */}
      <div style={{
        position: "relative", flex: 1, height: 2,
        background: "rgba(255,255,255,0.07)", borderRadius: 99,
      }}>
        <motion.div
          style={{
            position: "absolute", left: 0, top: 0, height: "100%",
            background: "linear-gradient(to right, var(--accent-warm), var(--green))",
            borderRadius: 99, originX: 0,
          }}
          animate={{ width: `${pct}%` }}
          transition={{ type: "spring", stiffness: 120, damping: 20 }}
        />
        {/* Dots */}
        {STEPS.map((label, i) => {
          const done = i < current;
          const active = i === current;
          return (
            <div key={i} style={{
              position: "absolute",
              left: `${(i / (STEPS.length - 1)) * 100}%`,
              top: "50%",
              transform: "translate(-50%, -50%)",
              display: "flex", flexDirection: "column", alignItems: "center",
              gap: 5,
            }}>
              <motion.div
                animate={{
                  width: active ? 10 : 6,
                  height: active ? 10 : 6,
                  background: done || active ? (active ? "var(--green)" : "var(--accent-warm)") : "rgba(255,255,255,0.2)",
                  boxShadow: active ? "0 0 8px var(--green)" : "none",
                }}
                style={{ borderRadius: "50%", marginTop: active ? -2 : 0 }}
                transition={{ type: "spring", stiffness: 300, damping: 25 }}
              />
              <span style={{
                position: "absolute", top: 10,
                fontFamily: "var(--font-mono)", fontSize: 9,
                letterSpacing: "0.08em", textTransform: "uppercase",
                color: active ? "var(--text)" : done ? "var(--text-dim)" : "var(--text-dim)",
                whiteSpace: "nowrap",
              }}>
                {label}
              </span>
            </div>
          );
        })}
      </div>
    </div>
  );
}

export default function App() {
  const [view, setView] = useState("landing");
  const [file, setFile] = useState(null);
  const [context, setContext] = useState({
    metabolomics_type: "untargeted",
    study_goal: "exploratory",
    design_type: "independent",
    group_count: "two_groups",
    has_batches: false,
    small_n: false,
    alpha: "0.05",
    comparison_label: "",
    notes: "",
  });
  const [results, setResults] = useState(null);
  const [error, setError] = useState(null);

  const handleFileAccepted = useCallback((f) => {
    setFile(f);
    setView("context");
    setResults(null);
    setError(null);
  }, []);

  const handleReset = () => {
    setFile(null);
    setView("upload");
    setResults(null);
    setError(null);
  };

  const handleDemo = () => {
    setResults(DEMO_RESULTS);
    setFile({ name: DEMO_RESULTS.overview.filename });
    setView("results");
  };

  const handleRunAudit = async () => {
    if (!file) return;
    setView("running");
    setError(null);
    const formData = new FormData();
    formData.append("file", file);
    formData.append("context", JSON.stringify(context));
    try {
      const res = await fetch(`${API_BASE}/audit`, { method: "POST", body: formData });
      if (!res.ok) {
        const err = await res.json().catch(() => ({}));
        throw new Error(err.detail || `Server error ${res.status}`);
      }
      const data = await res.json();
      setResults(data);
      setView("results");
    } catch (e) {
      setError(e.message || "Audit failed. Is the backend running?");
      setView("context");
    }
  };

  if (view === "landing") {
    return (
      <>
        <Analytics />
        <AnimatedBackground />
        <Nav onLaunch={() => setView("upload")} />
        <LandingPage onLaunch={() => setView("upload")} onDemo={handleDemo} />
      </>
    );
  }

  return (
    <div className="app-shell" style={{ position: "relative", zIndex: 1 }}>
      <Analytics />
      <AnimatedBackground />
      <Nav
        onLaunch={() => setView("upload")}
        onBack={() => setView("landing")}
        onReset={view !== "upload" ? handleReset : null}
        isDemo={results === DEMO_RESULTS}
      />
      <StepBar view={view} />
      <main className="app-main" style={{ paddingTop: 92 }}>
        {view === "upload" && <UploadZone onFileAccepted={handleFileAccepted} />}
        {(view === "context" || view === "running") && file && (
          <div className="context-layout">
            <div><DataPreview file={file} /></div>
            <div>
              <ContextForm
                context={context}
                onChange={setContext}
                onRun={handleRunAudit}
                running={view === "running"}
                error={error}
              />
            </div>
          </div>
        )}
        {view === "results" && results && (
          <AuditResults
            results={results}
            file={file}
            onReset={handleReset}
            isDemo={results === DEMO_RESULTS}
            context={context}
          />
        )}
      </main>
    </div>
  );
}

function Nav({ onLaunch, onBack, onReset, isDemo }) {
  return (
    <nav className="nav">
      <a className="nav-logo" onClick={onBack || onLaunch} style={{ cursor: "pointer" }}>
        <div className="nav-logo-mark">🧪</div>
        Validex
      </a>
      <div className="nav-actions">
        {isDemo && (
          <span className="nav-tag" style={{ color: "var(--accent-warm)", borderColor: "rgba(200,185,154,0.2)" }}>
            Demo mode
          </span>
        )}
        {!isDemo && <span className="nav-tag">Beta</span>}
        {onReset && (
          <button className="btn-ghost-nav" onClick={onReset}>← New audit</button>
        )}
        {!onReset && (
          <button className="btn-nav" onClick={onLaunch}>Run Audit</button>
        )}
      </div>
    </nav>
  );
}
