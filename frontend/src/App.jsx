import { useState, useCallback, useEffect } from "react";
import { motion } from "framer-motion";
import { AnimatedBackground } from "./components/ui/background-paths";
import UploadZone from "./components/UploadZone";
import ContextForm from "./components/ContextForm";
import AuditResults from "./components/AuditResults";
import DataPreview from "./components/DataPreview";
import { Meteors } from "./components/ui/Meteors";
import { TypingAnimation } from "./components/ui/TypingAnimation";
import { Ripple } from "./components/ui/Ripple";
import {
  adaptAuditResponse,
  AUDIT_LOADING_MESSAGES,
} from "./lib/auditViewModel";

const API_BASE = import.meta.env.VITE_API_URL || "";

// ── SHARE URL ENCODING ────────────────────────────────────────────────────────
export function encodeSharePayload(results, context) {
  const payload = JSON.stringify({ results, context });
  return btoa(encodeURIComponent(payload));
}

export function decodeSharePayload(encoded) {
  const payload = decodeURIComponent(atob(encoded));
  return JSON.parse(payload);
}

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

function PrivacyIndicator({ privacyStatus, aiStatus, compact = false }) {
  const provider = privacyStatus?.provider === "ollama" ? "Ollama" : "Local";
  const model = privacyStatus?.model || "llama3.2:3b";
  const localOnly = privacyStatus?.local_only !== false;
  const unavailable = aiStatus && (!aiStatus.installed || !aiStatus.running || !aiStatus.model_installed);
  const setupMessage = !aiStatus?.installed
    ? "Validex needs Ollama for optional local AI explanations. Deterministic audit still works."
    : !aiStatus?.running
      ? "Ollama is not running. Run validex again after setup completes."
      : !aiStatus?.model_installed
        ? `Ollama model ${model} is not installed. Run validex again to pull it.`
        : null;
  return (
    <div style={{
      display: "grid",
      gap: compact ? 6 : 10,
      padding: compact ? "10px 12px" : "14px 16px",
      border: unavailable ? "1px solid rgba(245,158,11,0.28)" : "1px solid rgba(74,222,128,0.22)",
      background: unavailable ? "rgba(245,158,11,0.07)" : "rgba(74,222,128,0.06)",
      borderRadius: 8,
      marginBottom: compact ? 12 : 18,
    }}>
      <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", gap: 12 }}>
        <span style={{ fontFamily: "var(--font-mono)", fontSize: 11, color: unavailable ? "var(--amber)" : "var(--green)", textTransform: "uppercase", letterSpacing: "0.08em" }}>
          {unavailable ? "AI optional" : localOnly ? "Local AI available" : "Remote AI host"}
        </span>
        <span style={{ fontFamily: "var(--font-mono)", fontSize: 11, color: "var(--text-dim)" }}>
          AI provider: {provider}
        </span>
      </div>
      <div style={{ fontSize: compact ? 12 : 13, color: "var(--text-muted)", lineHeight: 1.5 }}>
        Deterministic audit runs without AI. Optional AI receives structured summaries, not raw rows. {localOnly ? "Ollama is configured on loopback." : "Ollama is configured on a non-loopback host; data may leave this device."} Model: {model}.
        {setupMessage && <span style={{ display: "block", marginTop: 6, color: "var(--amber)" }}>{setupMessage}</span>}
      </div>
    </div>
  );
}

export default function App() {
  const [view, setView] = useState("upload");
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
  const [privacyStatus, setPrivacyStatus] = useState(null);
  const [aiStatus, setAiStatus] = useState(null);

  useEffect(() => {
    fetch(`${API_BASE}/api/privacy/status`)
      .then((res) => (res.ok ? res.json() : null))
      .then((data) => setPrivacyStatus(data))
      .catch(() => setPrivacyStatus(null));
    fetch(`${API_BASE}/api/ai/status`)
      .then((res) => (res.ok ? res.json() : null))
      .then((data) => setAiStatus(data))
      .catch(() => setAiStatus(null));
  }, []);

  // Load shared report from URL hash on mount
  useEffect(() => {
    const hash = window.location.hash;
    if (hash.startsWith("#r=")) {
      try {
        const { results: sharedResults, context: sharedContext } = decodeSharePayload(hash.slice(3));
        const sharedViewModel = sharedResults?.kind ? sharedResults : adaptAuditResponse(sharedResults);
        setResults(sharedViewModel);
        setContext(prev => ({ ...prev, ...sharedContext }));
        setFile({ name: sharedViewModel.summary?.filename || "shared-report.csv" });
        setView("results");
        // Clean hash from URL without triggering a reload
        window.history.replaceState(null, "", window.location.pathname);
      } catch {
        // Malformed share URL — ignore, stay on landing
      }
    }
  }, []);

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
      setResults(adaptAuditResponse(data));
      setView("results");
    } catch (e) {
      setError(e.message || "Audit failed. Is the backend running?");
      setView("context");
    }
  };

  return (
    <div className="app-shell" style={{ position: "relative", zIndex: 1 }}>
      <AnimatedBackground />
      <Nav
        onLaunch={() => setView("upload")}
        onBack={() => setView("upload")}
        onReset={view !== "upload" ? handleReset : null}
        isDemo={false}
      />
      <StepBar view={view} />
      <main className="app-main" style={{ paddingTop: 92 }}>
        {(view === "upload" || view === "context") && (
          <PrivacyIndicator privacyStatus={privacyStatus} aiStatus={aiStatus} compact={view === "context"} />
        )}
        {view === "upload" && <UploadZone onFileAccepted={handleFileAccepted} />}
        {view === "context" && file && (
          <div className="context-layout">
            <div><DataPreview file={file} /></div>
            <div>
              <ContextForm
                context={context}
                onChange={setContext}
                onRun={handleRunAudit}
                running={false}
                error={error}
              />
            </div>
          </div>
        )}
        {view === "running" && <RunningView file={file} />}
        {view === "results" && results && (
          <AuditResults
            results={results}
            file={file}
            onReset={handleReset}
            isDemo={false}
            context={context}
          />
        )}
      </main>
    </div>
  );
}

const AUDIT_STEPS = AUDIT_LOADING_MESSAGES;

function RunningView({ file }) {
  const [stepIdx, setStepIdx] = useState(0);

  useEffect(() => {
    const id = setInterval(() => {
      setStepIdx((i) => (i + 1) % AUDIT_STEPS.length);
    }, 2200);
    return () => clearInterval(id);
  }, []);

  return (
    <div style={{
      position: "relative",
      display: "flex",
      flexDirection: "column",
      alignItems: "center",
      justifyContent: "center",
      minHeight: "60vh",
      overflow: "hidden",
      borderRadius: 18,
      margin: "0 auto",
      maxWidth: 560,
    }}>
      <Meteors number={18} color="rgba(200,185,154,0.5)" />
      <Ripple mainCircleSize={120} numCircles={6} />

      {/* Spinner ring */}
      <motion.div
        style={{
          width: 72, height: 72,
          borderRadius: "50%",
          border: "2px solid rgba(255,255,255,0.07)",
          borderTop: "2px solid var(--accent-warm)",
          marginBottom: 28,
        }}
        animate={{ rotate: 360 }}
        transition={{ duration: 1.1, repeat: Infinity, ease: "linear" }}
      />

      <div style={{
        fontFamily: "var(--font-serif)",
        fontSize: 22,
        color: "var(--text)",
        marginBottom: 10,
        letterSpacing: "-0.01em",
      }}>
        Auditing
        {file?.name && (
          <span style={{ color: "var(--accent-warm)", marginLeft: 8 }}>{file.name}</span>
        )}
      </div>

      <TypingAnimation
        key={stepIdx}
        text={AUDIT_STEPS[stepIdx]}
        duration={38}
        style={{
          fontFamily: "var(--font-mono)",
          fontSize: 13,
          color: "var(--text-dim)",
          letterSpacing: "0.06em",
          minHeight: 22,
        }}
      />

      {/* Step dots */}
      <div style={{ display: "flex", gap: 6, marginTop: 32 }}>
        {AUDIT_STEPS.map((_, i) => (
          <motion.div
            key={i}
            animate={{
              background: i === stepIdx
                ? "var(--accent-warm)"
                : i < stepIdx
                  ? "rgba(200,185,154,0.4)"
                  : "rgba(255,255,255,0.1)",
              width: i === stepIdx ? 20 : 6,
            }}
            transition={{ type: "spring", stiffness: 300, damping: 25 }}
            style={{ height: 6, borderRadius: 99 }}
          />
        ))}
      </div>
    </div>
  );
}

function Nav({ onLaunch, onBack, onReset, isDemo }) {
  return (
    <nav className="nav">
      <button className="nav-logo" type="button" onClick={onBack || onLaunch} style={{ cursor: "pointer", border: "none", background: "transparent" }}>
        <div className="nav-logo-mark">🧪</div>
        Validex
      </button>
      <div className="nav-actions">
        {isDemo && (
          <span className="nav-tag" style={{ color: "var(--accent-warm)", borderColor: "rgba(200,185,154,0.2)" }}>
            Demo mode
          </span>
        )}
        {!isDemo && <span className="nav-tag">Research preview</span>}
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
