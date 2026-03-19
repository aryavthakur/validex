import { useState } from "react";

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

        <div style={{ marginBottom: 14 }}>
          <label style={{ display: "block", fontFamily: "var(--font-mono)", fontSize: 10, letterSpacing: "0.1em", textTransform: "uppercase", color: "var(--text-dim)", marginBottom: 7 }}>
            Your question
          </label>
          <textarea
            value={question}
            onChange={e => setQuestion(e.target.value)}
            rows={3}
            style={{
              width: "100%", background: "var(--bg-panel)", border: "1px solid var(--border)",
              borderRadius: 10, color: "var(--text)", fontFamily: "var(--font-sans)",
              fontSize: 13, padding: "10px 14px", outline: "none", resize: "vertical", lineHeight: 1.6,
            }}
          />
        </div>

        <div style={{ display: "flex", gap: 10, alignItems: "center", flexWrap: "wrap" }}>
          <button
            className={`btn-run${loading ? " running" : ""}`}
            onClick={runAnalysis}
            disabled={loading}
            style={{ flex: "none", width: "auto", padding: "11px 28px" }}
          >
            {loading ? (<><div className="spinner" />Analyzing…</>) : "▶ Run AI Analysis"}
          </button>
          {lambdaStatus && (
            <span style={{
              fontFamily: "var(--font-mono)", fontSize: 11,
              color: "var(--green)", background: "var(--green-subtle)",
              border: "1px solid rgba(74,222,128,0.15)",
              padding: "4px 10px", borderRadius: 99,
            }}>
              AI ● online
            </span>
          )}
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

      <div style={{ marginTop: 20 }}>
        <div style={{ fontFamily: "var(--font-mono)", fontSize: 10, letterSpacing: "0.12em", textTransform: "uppercase", color: "var(--text-dim)", marginBottom: 12 }}>
          Example questions
        </div>
        <div style={{ display: "flex", flexWrap: "wrap", gap: 8 }}>
          {[
            "Which metabolites are most significantly different between groups?",
            "Run a PCA on this data and describe the main variance",
            "Are there any outlier samples I should be concerned about?",
            "What statistical test is most appropriate for this study design?",
            "Identify potential biomarkers and rank them by importance",
            "Check for batch effects and suggest correction methods",
          ].map((q, i) => (
            <button key={i} onClick={() => setQuestion(q)} style={{
              background: "var(--bg-raised)", border: "1px solid var(--border)",
              borderRadius: 99, padding: "6px 14px", fontSize: 12,
              color: "var(--text-muted)", cursor: "pointer", fontFamily: "var(--font-sans)",
              transition: "all 0.15s",
            }}
              onMouseOver={e => { e.target.style.borderColor = "var(--border-hi)"; e.target.style.color = "var(--text)"; }}
              onMouseOut={e => { e.target.style.borderColor = "var(--border)"; e.target.style.color = "var(--text-muted)"; }}
            >
              {q}
            </button>
          ))}
        </div>
      </div>
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

  const TAB_LABELS = {
    summary: "Summary",
    schema: "Schema Map",
    report: "Full Report",
    data: "Data",
    ai: "🤖 AI Analysis",
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

      {/* Metrics */}
      <div className="metrics-row">
        <div className="metric-card">
          <div className="metric-label">Features</div>
          <div className="metric-value">{overview?.n_rows?.toLocaleString() ?? "—"}</div>
        </div>
        <div className="metric-card">
          <div className="metric-label">Columns</div>
          <div className="metric-value">{overview?.n_cols ?? "—"}</div>
        </div>
        <div className="metric-card">
          <div className="metric-label">Missing cells</div>
          <div className="metric-value">{overview?.missing_cells?.toLocaleString() ?? "—"}</div>
        </div>
      </div>

      {/* Tabs */}
      <div className="tabs">
        {Object.entries(TAB_LABELS).map(([t, label]) => (
          <button key={t} className={`tab-btn${tab === t ? " active" : ""}`} onClick={() => setTab(t)}>
            {label}
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

      <div style={{ marginTop: 48, textAlign: "center" }}>
        <button className="btn-primary" onClick={onReset}>
          {isDemo ? "Run your own audit →" : "← Run another audit"}
        </button>
      </div>
    </div>
  );
}
