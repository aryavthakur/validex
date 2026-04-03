import { useState } from "react";
import { motion, AnimatePresence } from "framer-motion";
import StatCard from "./ui/StatCard";

const API_BASE = import.meta.env.VITE_API_URL || "http://localhost:8000";

function ScoreBar({ score, label, color }) {
  const cls = score >= 70 ? "high" : score >= 45 ? "med" : "low";
  const resolvedColor = color || (score >= 70 ? "var(--green)" : score >= 45 ? "var(--amber)" : "var(--red)");
  return (
    <div className="score-display">
      <div style={{ display: "flex", alignItems: "baseline", gap: 6 }}>
        <span className={`score-num ${cls}`} style={color ? { color } : {}}>{score}</span>
        <span className="score-denom">/100</span>
      </div>
      <div className="score-bar-track">
        <div className={`score-bar-fill ${cls}`} style={{ width: `${score}%`, background: color || undefined }} />
      </div>
      <div className="score-label-text">{label || "Confidence Score"}</div>
    </div>
  );
}

function DualScore({ score, aiScore, aiReason }) {
  if (aiScore === null || aiScore === undefined) {
    return <ScoreBar score={score} />;
  }

  const diff = aiScore - score;
  const diffLabel = diff > 0 ? "+" + diff : String(diff);
  const diffColor = diff > 0 ? "var(--green)" : diff < 0 ? "var(--red)" : "var(--text-dim)";

  return (
    <div style={{ display: "flex", flexDirection: "column", alignItems: "flex-end", gap: 12 }}>
      <div style={{ display: "flex", gap: 24, alignItems: "flex-start" }}>
        <div style={{ textAlign: "right" }}>
          <ScoreBar score={score} label="Automated score" />
        </div>
        <div style={{ textAlign: "right" }}>
          <ScoreBar score={aiScore} label="AI-adjusted score" />
        </div>
      </div>
      <div style={{
        display: "flex", alignItems: "center", gap: 8,
        background: "var(--bg-panel)", border: "1px solid var(--border)",
        borderRadius: 8, padding: "8px 12px", maxWidth: 360,
      }}>
        <span style={{
          fontFamily: "var(--font-mono)", fontSize: 12, fontWeight: 500,
          color: diffColor, flexShrink: 0,
        }}>
          {diffLabel} pts
        </span>
        <span style={{ fontSize: 12, color: "var(--text-muted)", lineHeight: 1.5 }}>
          {aiReason}
        </span>
      </div>
    </div>
  );
}

function FlagCard({ flags }) {
  if (!flags?.length) return (
    <div style={{ color: "var(--text-muted)", fontSize: 13, padding: "12px 0" }}>No flags detected.</div>
  );
  return (
    <div>
      {flags.map((f, i) => (
        <div className="flag-item" key={i}>
          <span className={`flag-sev ${f.severity}`}>{f.severity}</span>
          <div className="flag-body">
            <div className="flag-title">{f.title}</div>
            <div className="flag-why">{f.why}</div>
            {f.fix && <div className="flag-fix">Fix: {f.fix}</div>}
          </div>
        </div>
      ))}
    </div>
  );
}

function SchemaMap({ schema }) {
  const CANONICALS = ["p_value", "fdr", "fold_change", "log2fc", "feature"];
  const c2o = schema?.canonical_to_original || {};
  const missing = schema?.missing || [];
  return (
    <div>
      {CANONICALS.map(canon => {
        const orig = c2o[canon];
        const isMissing = missing.includes(canon);
        return (
          <div className="schema-row" key={canon}>
            <span className="schema-canon">{canon}</span>
            {isMissing ? (
              <>
                <span className="schema-missing">not detected</span>
                <span className="schema-badge miss">missing</span>
              </>
            ) : (
              <>
                <span className="schema-orig">{orig || "—"}</span>
                <span className="schema-badge ok">mapped</span>
              </>
            )}
          </div>
        );
      })}
    </div>
  );
}

function Histogram({ histogram }) {
  if (!histogram) return (
    <div style={{ color: "var(--text-muted)", fontSize: 13, padding: "12px 0" }}>No numeric effect size column detected.</div>
  );
  const { counts, bin_edges, column } = histogram;
  const max = Math.max(...counts, 1);
  return (
    <div>
      <div style={{ color: "var(--text-muted)", fontSize: 11, fontFamily: "var(--font-mono)", marginBottom: 10, letterSpacing: "0.04em" }}>{column}</div>
      <div className="histogram-bars">
        {counts.map((c, i) => (
          <div key={i} className="histogram-bar" style={{ height: `${(c / max) * 100}%` }}
            title={`${bin_edges[i]?.toFixed(2)}–${bin_edges[i+1]?.toFixed(2)}: ${c}`} />
        ))}
      </div>
      <div className="histogram-axis">
        <span>{bin_edges[0]?.toFixed(2)}</span>
        <span>0</span>
        <span>{bin_edges[bin_edges.length-1]?.toFixed(2)}</span>
      </div>
    </div>
  );
}

function Interpretations({ items }) {
  if (!items?.length) return <div style={{ color: "var(--text-muted)", fontSize: 13 }}>No interpretations.</div>;
  return (
    <div>
      {items.map((txt, i) => (
        <div className="interp-item" key={i}>
          <div className="interp-bullet" />
          <span>{txt}</span>
        </div>
      ))}
    </div>
  );
}

function ReportMarkdown({ md }) {
  const html = md
    .replace(/^### (.+)$/gm, "<h3>$1</h3>")
    .replace(/^## (.+)$/gm, "<h2>$1</h2>")
    .replace(/^# (.+)$/gm, "<h1>$1</h1>")
    .replace(/\*\*(.+?)\*\*/g, "<strong>$1</strong>")
    .replace(/^- (.+)$/gm, "<li>$1</li>")
    .replace(/(<li>.*<\/li>\n?)+/g, m => `<ul>${m}</ul>`)
    .replace(/^---$/gm, "<hr>")
    .replace(/\n\n/g, "</p><p>")
    .replace(/^(?!<[hul]|<hr)(.*)/gm, m => m ? `<p>${m}</p>` : "");
  return <div className="report-md" dangerouslySetInnerHTML={{ __html: html }} />;
}

function LambdaAnalysis({ file, context }) {
  const [analysis, setAnalysis] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [lambdaStatus, setLambdaStatus] = useState(null);
  const [question, setQuestion] = useState(
    "Analyze this metabolite dataset. Summarize key patterns, identify statistical concerns, and suggest the most important metabolites to investigate further."
  );

  const checkLambda = async () => {
    setLambdaStatus("ok");
    return true;
  };

  const runAnalysis = async () => {
    setLoading(true);
    setError(null);
    setAnalysis(null);

    const isUp = await checkLambda();
    if (!isUp) {
      setError("AI analysis unavailable. Please try again.");
      setLoading(false);
      return;
    }

    const formData = new FormData();
    formData.append("file", file);
    formData.append("question", question);
    if (context) formData.append("context", JSON.stringify(context));

    try {
      const res = await fetch(`${API_BASE}/lambda-analyze`, {
        method: "POST",
        body: formData,
      });
      const data = await res.json();
      if (!res.ok) throw new Error(data.detail || `Server error ${res.status}`);
      setAnalysis(data.analysis);
    } catch (e) {
      setError(e.message || "Analysis failed.");
    }
    setLoading(false);
  };

  return (
    <div>
      <div className="card" style={{ marginBottom: 16 }}>
        <div className="card-label">AI-Powered Analysis · Llama 3.3 70B</div>
        <p style={{ fontSize: 13, color: "var(--text-muted)", marginBottom: 18, lineHeight: 1.7 }}>
          Ask any question about your metabolite data. The AI will analyze it and provide expert-level insights.
        </p>

        {/* AI Prompt Box — styled input with send button */}
        <div style={{
          position: "relative",
          background: "var(--bg-panel)",
          border: "1px solid var(--border-mid)",
          borderRadius: 14,
          overflow: "hidden",
          transition: "border-color 0.2s, box-shadow 0.2s",
        }}
          onFocusCapture={e => { e.currentTarget.style.borderColor = "rgba(255,255,255,0.22)"; e.currentTarget.style.boxShadow = "0 0 0 3px rgba(255,255,255,0.04)"; }}
          onBlurCapture={e => { e.currentTarget.style.borderColor = "rgba(255,255,255,0.11)"; e.currentTarget.style.boxShadow = "none"; }}
        >
          <textarea
            value={question}
            onChange={e => setQuestion(e.target.value)}
            rows={3}
            placeholder="Ask anything about your metabolomics data…"
            onKeyDown={e => { if (e.key === "Enter" && (e.metaKey || e.ctrlKey)) runAnalysis(); }}
            style={{
              width: "100%", background: "transparent", border: "none",
              color: "var(--text)", fontFamily: "var(--font-sans)",
              fontSize: 14, padding: "14px 16px 8px", outline: "none",
              resize: "none", lineHeight: 1.65,
            }}
          />
          <div style={{
            display: "flex", alignItems: "center", justifyContent: "space-between",
            padding: "8px 12px 12px",
          }}>
            {lambdaStatus ? (
              <span style={{
                fontFamily: "var(--font-mono)", fontSize: 10,
                color: "var(--green)", background: "var(--green-subtle)",
                border: "1px solid rgba(74,222,128,0.15)",
                padding: "3px 9px", borderRadius: 99, letterSpacing: "0.06em",
              }}>
                ● AI online
              </span>
            ) : (
              <span style={{ fontSize: 11, color: "var(--text-dim)", fontFamily: "var(--font-mono)" }}>
                ⌘↵ to send
              </span>
            )}
            <button
              onClick={runAnalysis}
              disabled={loading || !question.trim()}
              style={{
                display: "flex", alignItems: "center", justifyContent: "center",
                width: 36, height: 36, borderRadius: 10,
                background: loading || !question.trim() ? "var(--bg-hover)" : "var(--text)",
                border: "none", cursor: loading || !question.trim() ? "not-allowed" : "pointer",
                color: "#090909", transition: "all 0.15s",
                flexShrink: 0,
              }}
            >
              {loading
                ? <div className="spinner" style={{ width: 14, height: 14, borderWidth: 2, borderColor: "var(--text-dim) transparent transparent transparent" }} />
                : <span style={{ fontSize: 14, lineHeight: 1, color: loading || !question.trim() ? "var(--text-dim)" : "#090909" }}>↑</span>
              }
            </button>
          </div>
        </div>

        {error && <div className="error-box" style={{ marginTop: 14 }}>⚠ {error}</div>}
      </div>

      {loading && (
        <div className="card" style={{ textAlign: "center", padding: "40px 24px" }}>
          <div className="spinner" style={{ width: 24, height: 24, margin: "0 auto 16px", borderWidth: 2 }} />
          <div style={{ color: "var(--text-muted)", fontSize: 14, marginBottom: 6 }}>Analyzing your data…</div>
          <div style={{ color: "var(--text-dim)", fontSize: 12, fontFamily: "var(--font-mono)" }}>
            Llama 3.3 70B is processing your dataset. This may take 15–40 seconds.
          </div>
        </div>
      )}

      {analysis && !loading && (
        <div className="card">
          <div className="card-label">AI Analysis Result</div>
          <div style={{ fontSize: 14, lineHeight: 1.85, color: "var(--text-muted)", whiteSpace: "pre-wrap", fontFamily: "var(--font-sans)" }}>
            {analysis.split("\n").map((line, i) => {
              if (line.startsWith("# ")) return <h2 key={i} style={{ fontFamily: "var(--font-serif)", fontSize: 20, color: "var(--text)", fontWeight: 400, margin: "20px 0 8px" }}>{line.slice(2)}</h2>;
              if (line.startsWith("## ")) return <h3 key={i} style={{ fontFamily: "var(--font-serif)", fontSize: 16, color: "var(--text)", fontWeight: 400, margin: "16px 0 6px" }}>{line.slice(3)}</h3>;
              if (line.startsWith("**") && line.endsWith("**")) return <strong key={i} style={{ color: "var(--text)", display: "block", marginTop: 8 }}>{line.slice(2, -2)}</strong>;
              if (line.startsWith("- ") || line.startsWith("• ")) return (
                <div key={i} style={{ display: "flex", gap: 10, marginBottom: 4 }}>
                  <span style={{ color: "var(--accent-warm)", flexShrink: 0, marginTop: 2 }}>•</span>
                  <span>{line.slice(2)}</span>
                </div>
              );
              if (line.trim() === "") return <div key={i} style={{ height: 8 }} />;
              return <div key={i}>{line}</div>;
            })}
          </div>
          <div style={{ marginTop: 20, paddingTop: 16, borderTop: "1px solid var(--border)", display: "flex", gap: 10 }}>
            <button className="btn-dl" onClick={() => {
              const blob = new Blob([analysis], { type: "text/plain" });
              const url = URL.createObjectURL(blob);
              const a = document.createElement("a");
              a.href = url; a.download = "ai_analysis.txt"; a.click();
              URL.revokeObjectURL(url);
            }}>↓ Download analysis</button>
            <button className="btn-dl" onClick={() => { setAnalysis(null); setError(null); }}>← Ask another question</button>
          </div>
        </div>
      )}

      {!analysis && !loading && !error && (
        <div className="card" style={{ border: "1px dashed var(--border)", background: "transparent", textAlign: "center", padding: "40px 24px" }}>
          <div style={{ fontSize: 28, marginBottom: 12 }}>🤖</div>
          <div style={{ color: "var(--text-muted)", fontSize: 14, marginBottom: 6 }}>Llama 3.3 70B ready</div>
          <div style={{ color: "var(--text-dim)", fontSize: 12, fontFamily: "var(--font-mono)", lineHeight: 1.8 }}>
            Ask any question about your data above.
          </div>
        </div>
      )}

      <div style={{ marginTop: 16 }}>
        <div style={{ fontFamily: "var(--font-mono)", fontSize: 9, letterSpacing: "0.14em", textTransform: "uppercase", color: "var(--text-dim)", marginBottom: 10 }}>
          Suggestions
        </div>
        <div style={{ display: "flex", flexWrap: "wrap", gap: 6 }}>
          {[
            { icon: "◈", text: "Which metabolites differ most between groups?" },
            { icon: "⊙", text: "Are there outlier samples I should remove?" },
            { icon: "⌬", text: "What statistical test fits this design?" },
            { icon: "◎", text: "Identify potential biomarkers by importance" },
            { icon: "⊞", text: "Run a PCA and describe main variance" },
            { icon: "⊗", text: "Check for batch effects and suggest corrections" },
          ].map((q, i) => (
            <button key={i} onClick={() => setQuestion(q.text)} style={{
              display: "flex", alignItems: "center", gap: 6,
              background: "var(--bg-raised)", border: "1px solid var(--border)",
              borderRadius: 8, padding: "6px 12px", fontSize: 12,
              color: "var(--text-muted)", cursor: "pointer", fontFamily: "var(--font-sans)",
              transition: "all 0.15s",
            }}
              onMouseOver={e => { e.currentTarget.style.borderColor = "var(--border-hi)"; e.currentTarget.style.color = "var(--text)"; e.currentTarget.style.background = "var(--bg-hover)"; }}
              onMouseOut={e => { e.currentTarget.style.borderColor = "var(--border)"; e.currentTarget.style.color = "var(--text-muted)"; e.currentTarget.style.background = "var(--bg-raised)"; }}
            >
              <span style={{ color: "var(--accent-warm)", fontSize: 10 }}>{q.icon}</span>
              {q.text}
            </button>
          ))}
        </div>
      </div>
    </div>
  );
}


function CleanData({ file }) {
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState(null);
  const [error, setError] = useState(null);
  const [approved, setApproved] = useState(false);
  const [missingThreshold, setMissingThreshold] = useState(50);
  const [outlierStd, setOutlierStd] = useState(3);

  const runCleaning = async () => {
    setLoading(true);
    setError(null);
    setResult(null);
    setApproved(false);
    const formData = new FormData();
    formData.append("file", file);
    formData.append("missing_threshold", missingThreshold / 100);
    formData.append("outlier_std", outlierStd);
    formData.append("remove_duplicates", "true");
    try {
      const res = await fetch(`${API_BASE}/clean-data`, { method: "POST", body: formData });
      const data = await res.json();
      if (!res.ok) throw new Error(data.detail || "Cleaning failed");
      setResult(data);
    } catch (e) {
      setError(e.message);
    }
    setLoading(false);
  };

  const downloadClean = () => {
    if (!result?.clean_csv_b64) return;
    const bytes = atob(result.clean_csv_b64);
    const arr = new Uint8Array(bytes.length);
    for (let i = 0; i < bytes.length; i++) arr[i] = bytes.charCodeAt(i);
    const blob = new Blob([arr], { type: "text/csv" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url; a.download = result.summary.clean_filename; a.click();
    URL.revokeObjectURL(url);
  };

  const sevStyle = (sev) => ({
    high: { color: "var(--red)", background: "var(--red-subtle)", border: "1px solid rgba(248,113,113,0.2)" },
    med:  { color: "#fcd34d", background: "var(--amber-subtle)", border: "1px solid rgba(245,158,11,0.2)" },
    low:  { color: "var(--text-dim)", background: "rgba(255,255,255,0.03)", border: "1px solid var(--border)" },
  }[sev] || {});

  return (
    <div>
      <div className="card" style={{ marginBottom: 16 }}>
        <div className="card-label">Data Cleaning Settings</div>
        <p style={{ fontSize: 13, color: "var(--text-muted)", marginBottom: 18, lineHeight: 1.7 }}>
          Analyzes your dataset for missing values, outliers, and duplicates. You review the proposed changes before downloading. Nothing is deleted without your approval.
        </p>
        <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 16, marginBottom: 20 }}>
          <div>
            <label style={{ display: "block", fontFamily: "var(--font-mono)", fontSize: 10, letterSpacing: "0.1em", textTransform: "uppercase", color: "var(--text-dim)", marginBottom: 7 }}>
              Missing value threshold: {missingThreshold}%
            </label>
            <input type="range" min={10} max={90} step={5} value={missingThreshold} onChange={e => setMissingThreshold(Number(e.target.value))} style={{ width: "100%" }} />
            <div style={{ display: "flex", justifyContent: "space-between", fontSize: 11, color: "var(--text-dim)", fontFamily: "var(--font-mono)", marginTop: 4 }}>
              <span>10% (strict)</span><span>90% (lenient)</span>
            </div>
          </div>
          <div>
            <label style={{ display: "block", fontFamily: "var(--font-mono)", fontSize: 10, letterSpacing: "0.1em", textTransform: "uppercase", color: "var(--text-dim)", marginBottom: 7 }}>
              Outlier threshold: {outlierStd}σ
            </label>
            <input type="range" min={2} max={5} step={0.5} value={outlierStd} onChange={e => setOutlierStd(Number(e.target.value))} style={{ width: "100%" }} />
            <div style={{ display: "flex", justifyContent: "space-between", fontSize: 11, color: "var(--text-dim)", fontFamily: "var(--font-mono)", marginTop: 4 }}>
              <span>2σ (strict)</span><span>5σ (lenient)</span>
            </div>
          </div>
        </div>
        <button className={`btn-run${loading ? " running" : ""}`} onClick={runCleaning} disabled={loading} style={{ width: "auto", padding: "11px 28px" }}>
          {loading ? (<><div className="spinner" />Analyzing…</>) : "▶ Analyze & Preview Clean"}
        </button>
        {error && <div className="error-box" style={{ marginTop: 14 }}>⚠ {error}</div>}
      </div>

      {result && (<>
        <div style={{ display: "grid", gridTemplateColumns: "repeat(4, 1fr)", gap: 12, marginBottom: 16 }}>
          {[
            { label: "Original rows", value: result.summary.original_rows },
            { label: "Rows to remove", value: result.summary.rows_removed, warn: result.summary.rows_removed > 0 },
            { label: "Rows kept", value: result.summary.rows_kept },
            { label: "Columns", value: result.summary.original_cols },
          ].map((m, i) => (
            <div key={i} className="metric-card" style={m.warn ? { borderColor: "rgba(245,158,11,0.3)" } : {}}>
              <div className="metric-label">{m.label}</div>
              <div className="metric-value" style={m.warn ? { color: "var(--amber)" } : {}}>{m.value}</div>
            </div>
          ))}
        </div>

        <div className="card" style={{ marginBottom: 16 }}>
          <div className="card-label">Issues Found</div>
          {result.issues.length === 0 ? (
            <div style={{ color: "var(--green)", fontSize: 14, padding: "8px 0" }}>✓ No issues found — dataset is already clean!</div>
          ) : result.issues.map((issue, i) => (
            <div key={i} style={{ display: "flex", gap: 14, padding: "14px 0", borderBottom: i < result.issues.length - 1 ? "1px solid var(--border)" : "none" }}>
              <span style={{ fontFamily: "var(--font-mono)", fontSize: 9, fontWeight: 500, letterSpacing: "0.1em", textTransform: "uppercase", padding: "3px 8px", borderRadius: 4, flexShrink: 0, marginTop: 2, height: "fit-content", ...sevStyle(issue.severity) }}>
                {issue.severity}
              </span>
              <div style={{ flex: 1 }}>
                <div style={{ fontSize: 14, color: "var(--text)", marginBottom: 3 }}>{issue.title}</div>
                <div style={{ fontSize: 13, color: "var(--text-muted)", lineHeight: 1.6, marginBottom: issue.action ? 5 : 0 }}>{issue.detail}</div>
                {issue.action && issue.rows_affected > 0 && <div style={{ fontSize: 11, color: "var(--accent-warm)", fontFamily: "var(--font-mono)" }}>Proposed fix: {issue.action}</div>}
                {issue.action && issue.rows_affected === 0 && <div style={{ fontSize: 11, color: "var(--text-dim)", fontFamily: "var(--font-mono)" }}>Suggestion: {issue.action}</div>}
              </div>
            </div>
          ))}
        </div>

        {result.removed_preview?.length > 0 && (
          <div className="card" style={{ marginBottom: 16 }}>
            <div className="card-label">Rows to be removed (preview)</div>
            <div className="table-wrap" style={{ maxHeight: 240, overflowY: "auto" }}>
              <table>
                <thead><tr>
                  <th>Row #</th>
                  {Object.keys(result.removed_preview[0].data).slice(0, 6).map((k, i) => <th key={i}>{k}</th>)}
                  {Object.keys(result.removed_preview[0].data).length > 6 && <th>…</th>}
                </tr></thead>
                <tbody>{result.removed_preview.map((row, i) => (
                  <tr key={i}>
                    <td style={{ color: "var(--red)", fontFamily: "var(--font-mono)" }}>{row.original_index}</td>
                    {Object.values(row.data).slice(0, 6).map((v, j) => <td key={j}>{v === null ? <span style={{ color: "var(--red)" }}>—</span> : String(v)}</td>)}
                    {Object.values(row.data).length > 6 && <td style={{ color: "var(--text-dim)" }}>…</td>}
                  </tr>
                ))}</tbody>
              </table>
            </div>
          </div>
        )}

        <div className="card" style={{ marginBottom: 16 }}>
          <div className="card-label">Cleaned Dataset Preview ({result.summary.rows_kept} rows)</div>
          <div className="table-wrap" style={{ maxHeight: 300, overflowY: "auto" }}>
            <table>
              <thead><tr>{result.preview.columns.map((c, i) => <th key={i}>{c}</th>)}</tr></thead>
              <tbody>{result.preview.rows.map((row, ri) => (
                <tr key={ri}>{row.map((cell, ci) => <td key={ci}>{cell ?? <span style={{ color: "var(--text-dim)" }}>—</span>}</td>)}</tr>
              ))}</tbody>
            </table>
          </div>
        </div>

        {result.summary.rows_removed > 0 ? (
          <div className="card" style={{ background: approved ? "rgba(74,222,128,0.04)" : "var(--bg-raised)", borderColor: approved ? "rgba(74,222,128,0.2)" : "var(--border)" }}>
            <div style={{ display: "flex", alignItems: "flex-start", gap: 12, marginBottom: approved ? 16 : 0 }}>
              <input type="checkbox" id="approve-clean" checked={approved} onChange={e => setApproved(e.target.checked)} style={{ marginTop: 3, cursor: "pointer", width: 16, height: 16, flexShrink: 0 }} />
              <label htmlFor="approve-clean" style={{ fontSize: 14, color: "var(--text)", cursor: "pointer", lineHeight: 1.6 }}>
                I have reviewed the changes above. Remove {result.summary.rows_removed} row{result.summary.rows_removed > 1 ? "s" : ""} and download the cleaned dataset ({result.summary.rows_kept} rows remaining).
              </label>
            </div>
            {approved && <button className="btn-primary" onClick={downloadClean} style={{ marginTop: 8 }}>↓ Download {result.summary.clean_filename}</button>}
          </div>
        ) : (
          <div style={{ textAlign: "center", padding: "16px 0" }}>
            <button className="btn-primary" onClick={downloadClean}>↓ Download cleaned dataset (no changes needed)</button>
          </div>
        )}
      </>)}
    </div>
  );
}

function downloadText(content, filename, mime) {
  const blob = new Blob([content], { type: mime });
  const url = URL.createObjectURL(blob);
  const a = document.createElement("a");
  a.href = url; a.download = filename; a.click();
  URL.revokeObjectURL(url);
}

export default function AuditResults({ results, file, onReset, isDemo, context }) {
  const [tab, setTab] = useState("summary");
  const { overview, schema, report_md, report_json, histogram, ai_score, ai_score_reason } = results;
  const analysis = report_json?.analysis || {};
  const score = analysis.confidence ?? null;
  const flags = analysis.flags || [];
  const interpretations = analysis.interpretations || [];
  const recommendations = analysis.recommendations || [];

  const TAB_ICONS = {
    summary: "◈",
    schema: "⌥",
    report: "☰",
    data: "⊞",
    ai: "◎",
    clean: "⟳",
  };

  const TAB_LABELS = {
    summary: "Summary",
    schema: "Schema Map",
    report: "Full Report",
    data: "Data",
    ai: "AI Analysis",
    clean: "Clean Data",
  };

  return (
    <div>
      {/* Header */}
      <div className="results-header">
        <div>
          <h1 className="results-title">Validity Report</h1>
          <div className="results-filename">{overview?.filename}</div>
        </div>
        {score !== null && (
          <DualScore score={score} aiScore={ai_score} aiReason={ai_score_reason} />
        )}
      </div>

      {/* Metrics — animated stat cards */}
      <div className="metrics-row">
        <StatCard value={overview?.n_rows?.toLocaleString() ?? "—"} label="Features" />
        <StatCard value={overview?.n_cols ?? "—"} label="Columns" />
        <StatCard value={overview?.missing_cells?.toLocaleString() ?? "—"} label="Missing cells" warn={(overview?.missing_cells ?? 0) > 0} />
      </div>

      {/* Tabs — Feature108 style */}
      <div style={{
        display: "flex",
        gap: 4,
        flexWrap: "wrap",
        padding: "6px",
        background: "var(--bg-raised)",
        borderRadius: 14,
        border: "1px solid var(--border)",
        margin: "24px 0 0",
      }}>
        {Object.entries(TAB_LABELS).map(([t, label]) => (
          <button
            key={t}
            onClick={() => setTab(t)}
            style={{
              position: "relative",
              display: "flex",
              alignItems: "center",
              gap: 7,
              padding: "8px 16px",
              borderRadius: 10,
              border: "none",
              cursor: "pointer",
              fontFamily: "var(--font-sans)",
              fontSize: 13,
              fontWeight: tab === t ? 500 : 400,
              color: tab === t ? "var(--text)" : "var(--text-muted)",
              background: "transparent",
              transition: "all 0.18s ease",
              whiteSpace: "nowrap",
            }}
          >
            {tab === t && (
              <motion.div
                layoutId="active-tab-pill"
                style={{
                  position: "absolute",
                  inset: 0,
                  borderRadius: 10,
                  background: "var(--bg-card)",
                  border: "1px solid var(--border-mid)",
                  zIndex: 0,
                }}
                transition={{ type: "spring", stiffness: 400, damping: 30 }}
              />
            )}
            <span style={{ position: "relative", zIndex: 1 }}>
              {TAB_ICONS[t]} {label}
            </span>
          </button>
        ))}
      </div>

      {/* SUMMARY */}
      {tab === "summary" && (
        <div className="results-grid">
          <div className="card">
            <div className="card-label">Flags</div>
            <FlagCard flags={flags} />
          </div>
          <div className="card">
            <div className="card-label">Effect Size Distribution</div>
            <Histogram histogram={histogram} />
          </div>
          <div className="card results-wide">
            <div className="card-label">Scientific Interpretations</div>
            <Interpretations items={interpretations} />
          </div>
          {recommendations?.length > 0 && (
            <div className="card results-wide">
              <div className="card-label">Recommendations</div>
              <Interpretations items={recommendations} />
            </div>
          )}
        </div>
      )}

      {/* SCHEMA */}
      {tab === "schema" && (
        <div className="results-grid">
          <div className="card">
            <div className="card-label">Detected Columns</div>
            <SchemaMap schema={schema} />
          </div>
          {schema?.ambiguities && Object.keys(schema.ambiguities).length > 0 && (
            <div className="card">
              <div className="card-label">Ambiguities</div>
              {Object.entries(schema.ambiguities).map(([canon, cols]) => (
                <div className="schema-row" key={canon}>
                  <span className="schema-canon">{canon}</span>
                  <span style={{ fontSize: 12, color: "var(--amber)", fontFamily: "var(--font-mono)" }}>{cols.join(", ")}</span>
                </div>
              ))}
            </div>
          )}
        </div>
      )}

      {/* REPORT */}
      {tab === "report" && (
        <div className="card">
          <div className="card-label">Full Report</div>
          <div className="downloads">
            <button className="btn-dl" onClick={() => downloadText(report_md, "validity_report.md", "text/markdown")}>↓ Markdown</button>
            {report_json && (
              <button className="btn-dl" onClick={() => downloadText(JSON.stringify(report_json, null, 2), "validity_report.json", "application/json")}>↓ JSON</button>
            )}
          </div>
          <div style={{ marginTop: 24 }}>
            <ReportMarkdown md={report_md} />
          </div>
        </div>
      )}

      {/* DATA */}
      {tab === "data" && (
        <div className="card">
          <div className="card-label">Raw Data Preview</div>
          <div className="table-wrap" style={{ maxHeight: 480, overflowY: "auto" }}>
            {results.preview?.columns && (
              <table>
                <thead><tr>{results.preview.columns.map((c, i) => <th key={i}>{c}</th>)}</tr></thead>
                <tbody>
                  {results.preview.rows.map((row, ri) => (
                    <tr key={ri}>{row.map((cell, ci) => (
                      <td key={ci}>{cell ?? <span style={{ color: "var(--text-dim)" }}>—</span>}</td>
                    ))}</tr>
                  ))}
                </tbody>
              </table>
            )}
          </div>
          <div style={{ color: "var(--text-dim)", fontSize: 11, fontFamily: "var(--font-mono)", marginTop: 8 }}>
            Showing first 100 rows
          </div>
        </div>
      )}

      {/* AI ANALYSIS */}
      {tab === "ai" && (
        <LambdaAnalysis file={file} context={context} />
      )}

      {/* CLEAN DATA */}
      {tab === "clean" && (
        <CleanData file={file} />
      )}

      <div style={{ marginTop: 48, textAlign: "center" }}>
        <button className="btn-primary" onClick={onReset}>
          {isDemo ? "Run your own audit →" : "← Run another audit"}
        </button>
      </div>
    </div>
  );
}
