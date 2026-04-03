import { useState, useCallback } from "react";
import LandingPage from "./components/LandingPage";
import { AnimatedBackground } from "./components/ui/background-paths";
import UploadZone from "./components/UploadZone";
import ContextForm from "./components/ContextForm";
import AuditResults from "./components/AuditResults";
import DataPreview from "./components/DataPreview";
import { DEMO_RESULTS } from "./demoData";

const API_BASE = import.meta.env.VITE_API_URL || "http://localhost:8000";

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
        <AnimatedBackground />
        <Nav onLaunch={() => setView("upload")} />
        <LandingPage onLaunch={() => setView("upload")} onDemo={handleDemo} />
      </>
    );
  }

  return (
    <div className="app-shell" style={{ position: "relative", zIndex: 1 }}>
      <AnimatedBackground />
      <Nav
        onLaunch={() => setView("upload")}
        onBack={() => setView("landing")}
        onReset={view !== "upload" ? handleReset : null}
        isDemo={results === DEMO_RESULTS}
      />
      <main className="app-main">
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
