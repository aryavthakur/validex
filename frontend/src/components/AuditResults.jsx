import { useMemo, useState } from "react";
import { motion } from "framer-motion";
import StatCard from "./ui/StatCard";
import { encodeSharePayload } from "../App";
import {
  CANONICAL_FIELDS,
  ensureAuditViewModel,
  adaptCleanDataResponse,
} from "../lib/auditViewModel";

const API_BASE = import.meta.env.VITE_API_URL || "";

function scoreColor(score) {
  if (score === null || score === undefined) return "var(--text-dim)";
  return score >= 70 ? "var(--green)" : score >= 45 ? "var(--amber)" : "var(--red)";
}

function ScorePanel({ score, confidence, ai }) {
  return (
    <div style={{ display: "grid", gap: 10, justifyItems: "end" }}>
      <div className="score-display" aria-label="Deterministic audit score">
        <div style={{ display: "flex", alignItems: "baseline", gap: 6 }}>
          <span className="score-num" style={{ color: scoreColor(score) }}>{score ?? "Unavailable"}</span>
          {score !== null && score !== undefined && <span className="score-denom">/100</span>}
        </div>
        {score !== null && score !== undefined && (
          <div className="score-bar-track">
            <div className="score-bar-fill" style={{ width: `${score}%`, background: scoreColor(score) }} />
          </div>
        )}
        <div className="score-label-text">Deterministic audit score</div>
      </div>
      <div style={{ color: "var(--text-muted)", fontSize: 12, fontFamily: "var(--font-mono)", textTransform: "uppercase", letterSpacing: "0.08em" }}>
        Confidence: {confidence || "Unavailable"}
      </div>
      <div style={{ maxWidth: 380, fontSize: 12, lineHeight: 1.5, color: "var(--text-muted)", textAlign: "right" }}>
        {ai.available ? (
          <>
            <strong style={{ color: "var(--text)" }}>Optional local AI explanation:</strong>{" "}
            {ai.reason || "AI returned no explanatory text."}
          </>
        ) : (
          "Local AI explanation unavailable. Deterministic findings remain available and are not overridden by AI."
        )}
      </div>
    </div>
  );
}

function FlagCard({ flags }) {
  if (!flags.length) {
    return <div style={{ color: "var(--text-muted)", fontSize: 13, padding: "12px 0" }}>No findings detected.</div>;
  }
  return (
    <div>
      {flags.map((f, i) => (
        <motion.div
          className="flag-item"
          key={`${f.title || "finding"}-${i}`}
          initial={{ opacity: 0, scale: 0.98, y: 6 }}
          animate={{ opacity: 1, scale: 1, y: 0 }}
          transition={{ type: "spring", stiffness: 350, damping: 40, delay: i * 0.04 }}
        >
          <span className={`flag-sev ${f.severity || "info"}`}>{f.severity || "info"}</span>
          <div className="flag-body">
            <div className="flag-title">{f.title || "Audit finding"}</div>
            {f.why && <div className="flag-why">{f.why}</div>}
            {f.fix && <div className="flag-fix">Fix: {f.fix}</div>}
          </div>
        </motion.div>
      ))}
    </div>
  );
}

function SchemaMap({ schema }) {
  return (
    <div>
      {CANONICAL_FIELDS.map((field) => {
        const item = schema[field];
        return (
          <div className="schema-row" key={field} data-testid={`schema-${field}`}>
            <span className="schema-canon">{item.label}</span>
            <span className={item.value ? "schema-orig" : "schema-missing"}>
              {item.value || "Unavailable"}
            </span>
            <span className={`schema-badge ${item.value ? "ok" : "miss"}`}>
              {item.value ? "detected" : "not detected"}
            </span>
          </div>
        );
      })}
    </div>
  );
}

function SchemaAmbiguities({ schema }) {
  const rows = CANONICAL_FIELDS
    .map((field) => schema[field])
    .filter((item) => item.ambiguous);
  if (!rows.length) return null;
  return (
    <div className="card">
      <div className="card-label">Schema Ambiguities</div>
      {rows.map((item) => (
        <div className="schema-row" key={item.key}>
          <span className="schema-canon">{item.label}</span>
          <span style={{ fontSize: 12, color: "var(--amber)", fontFamily: "var(--font-mono)" }}>
            {item.candidateColumns.join(", ")}
          </span>
        </div>
      ))}
    </div>
  );
}

function UnavailablePanel({ title, children }) {
  return (
    <div style={{ color: "var(--text-muted)", fontSize: 13, padding: "12px 0", lineHeight: 1.6 }}>
      <strong style={{ color: "var(--text)" }}>{title}</strong>
      <div>{children}</div>
    </div>
  );
}

function HistogramPanel({ histogram, effectField }) {
  if (!histogram.available) {
    return (
      <UnavailablePanel title="Effect size distribution unavailable">
        {effectField.value
          ? "The backend did not return histogram data for this audit."
          : "The source table did not provide a recognized effect-size field."}
      </UnavailablePanel>
    );
  }
  const { counts = [], bin_edges = [], column } = histogram.data || {};
  const max = Math.max(...counts, 1);
  return (
    <div>
      <div style={{ color: "var(--text-muted)", fontSize: 11, fontFamily: "var(--font-mono)", marginBottom: 10 }}>{column}</div>
      <div className="histogram-bars">
        {counts.map((count, i) => (
          <div
            key={i}
            className="histogram-bar"
            style={{ height: `${(count / max) * 100}%` }}
            title={`${bin_edges[i]?.toFixed?.(2) ?? ""}-${bin_edges[i + 1]?.toFixed?.(2) ?? ""}: ${count}`}
          />
        ))}
      </div>
    </div>
  );
}

function renderInline(text) {
  const parts = [];
  const pattern = /(`[^`]+`|\*\*[^*]+\*\*)/g;
  let lastIndex = 0;
  let match;
  while ((match = pattern.exec(text)) !== null) {
    if (match.index > lastIndex) parts.push(text.slice(lastIndex, match.index));
    const token = match[0];
    if (token.startsWith("`")) {
      parts.push(<code key={`${match.index}-code`}>{token.slice(1, -1)}</code>);
    } else {
      parts.push(<strong key={`${match.index}-strong`}>{token.slice(2, -2)}</strong>);
    }
    lastIndex = match.index + token.length;
  }
  if (lastIndex < text.length) parts.push(text.slice(lastIndex));
  return parts;
}

export function ReportMarkdown({ md = "" }) {
  if (!String(md).trim()) {
    return (
      <div className="report-md">
        <UnavailablePanel title="Report unavailable">The backend response did not include report content.</UnavailablePanel>
      </div>
    );
  }

  const blocks = [];
  const lines = String(md).split(/\r?\n/);
  let list = [];

  const flushList = () => {
    if (list.length) {
      blocks.push(
        <ul key={`list-${blocks.length}`}>
          {list.map((item, i) => <li key={i}>{renderInline(item)}</li>)}
        </ul>
      );
      list = [];
    }
  };

  lines.forEach((line, index) => {
    const trimmed = line.trim();
    if (!trimmed) {
      flushList();
      return;
    }
    if (trimmed.startsWith("- ")) {
      list.push(trimmed.slice(2));
      return;
    }
    flushList();
    if (trimmed === "---") {
      blocks.push(<hr key={`hr-${index}`} />);
    } else if (trimmed.startsWith("### ")) {
      blocks.push(<h3 key={index}>{renderInline(trimmed.slice(4))}</h3>);
    } else if (trimmed.startsWith("## ")) {
      blocks.push(<h2 key={index}>{renderInline(trimmed.slice(3))}</h2>);
    } else if (trimmed.startsWith("# ")) {
      blocks.push(<h1 key={index}>{renderInline(trimmed.slice(2))}</h1>);
    } else {
      blocks.push(<p key={index}>{renderInline(trimmed)}</p>);
    }
  });
  flushList();

  return <div className="report-md">{blocks}</div>;
}

function downloadText(content, filename, mime) {
  const blob = new Blob([content], { type: mime });
  const url = URL.createObjectURL(blob);
  const a = document.createElement("a");
  a.href = url;
  a.download = filename;
  a.click();
  URL.revokeObjectURL(url);
}

function downloadBase64Csv(base64, filename) {
  if (!base64) return;
  const bytes = atob(base64);
  const arr = new Uint8Array(bytes.length);
  for (let i = 0; i < bytes.length; i += 1) arr[i] = bytes.charCodeAt(i);
  const blob = new Blob([arr], { type: "text/csv" });
  const url = URL.createObjectURL(blob);
  const a = document.createElement("a");
  a.href = url;
  a.download = filename;
  a.click();
  URL.revokeObjectURL(url);
}

export function CleanData({ file }) {
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState(null);
  const [error, setError] = useState(null);

  const runExport = async () => {
    setLoading(true);
    setError(null);
    setResult(null);
    const formData = new FormData();
    formData.append("file", file);
    try {
      const res = await fetch(`${API_BASE}/clean-data`, { method: "POST", body: formData });
      const data = await res.json().catch(() => ({}));
      if (!res.ok) throw new Error(data.detail || `CSV export failed (${res.status})`);
      setResult(adaptCleanDataResponse(data));
    } catch (e) {
      setError(e.message || "CSV export failed.");
    } finally {
      setLoading(false);
    }
  };

  const handleDownload = () => {
    try {
      downloadBase64Csv(result?.cleanCsvBase64, result?.downloadFilename || "validex.validated.csv");
    } catch {
      setError("Validated CSV output could not be decoded.");
    }
  };

  return (
    <div>
      <div className="card" style={{ marginBottom: 16 }}>
        <div className="card-label">Validated CSV Export</div>
        <p style={{ fontSize: 13, color: "var(--text-muted)", marginBottom: 18, lineHeight: 1.7 }}>
          This endpoint validates that the CSV can be parsed by Validex and returns a preserved CSV export. It does not remove rows, detect outliers, validate normalization, or certify publication readiness.
        </p>
        <button
          className={`btn-run${loading ? " running" : ""}`}
          onClick={runExport}
          disabled={loading || !file}
          aria-disabled={loading || !file}
          title={!file ? "Choose a CSV file before exporting." : undefined}
          style={{ width: "auto", padding: "11px 28px" }}
        >
          {loading ? (<><div className="spinner" />Preparing...</>) : "Prepare validated CSV export"}
        </button>
        {loading && <div role="status" style={{ marginTop: 14, color: "var(--text-muted)", fontSize: 13 }}>Preparing validated CSV export...</div>}
        {error && <div role="alert" className="error-box" style={{ marginTop: 14 }}>Error: {error}</div>}
      </div>

      {result && (
        <>
          <div style={{ display: "grid", gridTemplateColumns: "repeat(4, 1fr)", gap: 12, marginBottom: 16 }}>
            {[
              { label: "Original rows", value: result.summary.originalRows ?? "Unavailable" },
              { label: "Rows removed", value: result.summary.rowsRemoved ?? "Unavailable" },
              { label: "Rows kept", value: result.summary.rowsKept ?? "Unavailable" },
              { label: "Columns", value: result.summary.originalColumns.length || "Unavailable" },
            ].map((item) => (
              <div key={item.label} className="metric-card">
                <div className="metric-label">{item.label}</div>
                <div className="metric-value">{item.value}</div>
              </div>
            ))}
          </div>
          <div className="card" style={{ marginBottom: 16 }}>
            <div className="card-label">Export Status</div>
            <div style={{ color: "var(--text-muted)", fontSize: 14, lineHeight: 1.7 }}>
              {result.message}
            </div>
            <div style={{ marginTop: 12, color: "var(--text)", fontFamily: "var(--font-mono)", fontSize: 12 }}>
              {result.summary.filename}
            </div>
            {result.issues.length === 0 && (
              <div style={{ color: "var(--text-muted)", fontSize: 13, paddingTop: 12 }}>
                No clean-data issues were returned by the backend.
              </div>
            )}
          </div>
          {result.hasDownload ? (
            <div style={{ textAlign: "center", padding: "16px 0" }}>
              <button className="btn-primary" onClick={handleDownload}>
                Download validated CSV
              </button>
            </div>
          ) : (
            <div role="alert" className="error-box">Validated CSV output was unavailable in the backend response.</div>
          )}
        </>
      )}
    </div>
  );
}

function DataPreview({ preview }) {
  if (!preview.columns.length) {
    return <UnavailablePanel title="Preview unavailable">The backend response did not include preview rows.</UnavailablePanel>;
  }
  return (
    <div className="table-wrap" style={{ maxHeight: 480, overflowY: "auto" }}>
      <table>
        <thead>
          <tr>{preview.columns.map((column) => <th key={column}>{column}</th>)}</tr>
        </thead>
        <tbody>
          {preview.rows.map((row, rowIndex) => (
            <tr key={rowIndex}>
              {preview.columns.map((_, cellIndex) => (
                <td key={cellIndex}>{row[cellIndex] ?? <span style={{ color: "var(--text-dim)" }}>Unavailable</span>}</td>
              ))}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

export default function AuditResults({ results, file, onReset, isDemo, context }) {
  const [tab, setTab] = useState("summary");
  const [shareState, setShareState] = useState(null);
  const vm = useMemo(() => ensureAuditViewModel(results, { demo: isDemo }), [results, isDemo]);

  const handleShare = () => {
    try {
      const encoded = encodeSharePayload(vm, context);
      const url = `${window.location.origin}${window.location.pathname}#r=${encoded}`;
      navigator.clipboard.writeText(url).then(() => {
        setShareState("copied");
        setTimeout(() => setShareState(null), 2500);
      });
    } catch {
      const encoded = encodeSharePayload(vm, context);
      window.location.hash = `r=${encoded}`;
    }
  };

  const tabs = {
    summary: "Summary",
    schema: "Schema Map",
    report: "Full Report",
    data: "Data",
    ai: "AI Explanation",
    clean: "Validated Export",
  };

  return (
    <div>
      <div className="results-header">
        <div>
          <h1 className="results-title">CSV Audit Report</h1>
          <div className="results-filename">{vm.summary.filename || file?.name || "Unnamed CSV"}</div>
          <button
            type="button"
            onClick={handleShare}
            aria-label="Share report link"
            style={{
              marginTop: 8,
              display: "inline-flex",
              alignItems: "center",
              gap: 6,
              padding: "5px 12px",
              borderRadius: 99,
              border: "1px solid var(--border-mid)",
              background: shareState === "copied" ? "rgba(74,222,128,0.1)" : "var(--bg-raised)",
              color: shareState === "copied" ? "var(--green)" : "var(--text-muted)",
              fontFamily: "var(--font-mono)",
              fontSize: 10,
              letterSpacing: "0.06em",
              cursor: "pointer",
            }}
          >
            {shareState === "copied" ? "Link copied" : "Share report"}
          </button>
        </div>
        <ScorePanel score={vm.score.value} confidence={vm.score.confidence} ai={vm.ai} />
      </div>

      <div className="metrics-row">
        <StatCard value={vm.summary.nRows ?? "Unavailable"} label="Rows" />
        <StatCard value={vm.summary.nCols ?? "Unavailable"} label="Columns" />
        <StatCard value={vm.summary.missingCells ?? "Unavailable"} label="Missing cells" warn={(vm.summary.missingCells ?? 0) > 0} />
      </div>

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
        {Object.entries(tabs).map(([key, label]) => (
          <button
            key={key}
            type="button"
            onClick={() => setTab(key)}
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
              fontWeight: tab === key ? 500 : 400,
              color: tab === key ? "var(--text)" : "var(--text-muted)",
              background: tab === key ? "var(--bg-card)" : "transparent",
              whiteSpace: "nowrap",
            }}
          >
            {label}
          </button>
        ))}
      </div>

      {tab === "summary" && (
        <div className="results-grid">
          <div className="card">
            <div className="card-label">Deterministic Score Inputs</div>
            <FlagCard flags={vm.findings} />
          </div>
          <div className="card">
            <div className="card-label">Detected Statistical Fields</div>
            <SchemaMap schema={vm.detectedSchema} />
          </div>
          <div className="card">
            <div className="card-label">Effect Size Distribution</div>
            <HistogramPanel histogram={vm.histogram} effectField={vm.detectedSchema.effect_size} />
          </div>
          <div className="card results-wide">
            <div className="card-label">Audit Scope</div>
            <div style={{ color: "var(--text-muted)", fontSize: 14, lineHeight: 1.7 }}>
              Validex audits CSV result-table structure, supported schema fields, p-value and FDR-like values, duplicate identifiers, schema ambiguity, and deterministic findings. It does not certify biological validity, publication readiness, statistical power, normalization, or journal acceptance.
            </div>
          </div>
        </div>
      )}

      {tab === "schema" && (
        <div className="results-grid">
          <div className="card">
            <div className="card-label">Detected Columns</div>
            <SchemaMap schema={vm.detectedSchema} />
          </div>
          <SchemaAmbiguities schema={vm.detectedSchema} />
        </div>
      )}

      {tab === "report" && (
        <div className="card">
          <div className="card-label">Full Report</div>
          <div className="downloads">
            <button className="btn-dl" type="button" onClick={() => downloadText(vm.report.markdown, "validity_report.md", "text/markdown")}>Markdown</button>
            {Object.keys(vm.report.json).length > 0 && (
              <button className="btn-dl" type="button" onClick={() => downloadText(JSON.stringify(vm.report.json, null, 2), "validity_report.json", "application/json")}>JSON</button>
            )}
          </div>
          <div style={{ marginTop: 24 }}>
            <ReportMarkdown md={vm.report.markdown} />
          </div>
        </div>
      )}

      {tab === "data" && (
        <div className="card">
          <div className="card-label">CSV Preview</div>
          <DataPreview preview={vm.preview} />
          <div style={{ color: "var(--text-dim)", fontSize: 11, fontFamily: "var(--font-mono)", marginTop: 8 }}>
            Showing backend preview rows when available.
          </div>
        </div>
      )}

      {tab === "ai" && (
        <div className="card">
          <div className="card-label">Optional Local AI Explanation</div>
          <div style={{ color: "var(--text-muted)", fontSize: 14, lineHeight: 1.7 }}>
            {vm.ai.available
              ? (vm.ai.reason || "Local AI returned a score but no explanatory text.")
              : "Local AI explanation unavailable. This does not affect the deterministic audit score or findings."}
          </div>
        </div>
      )}

      {tab === "clean" && <CleanData file={file} />}

      <div style={{ marginTop: 48, textAlign: "center" }}>
        <button className="btn-primary" type="button" onClick={onReset}>
          {isDemo ? "Run your own audit" : "Run another audit"}
        </button>
      </div>
    </div>
  );
}
