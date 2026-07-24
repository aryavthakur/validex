import { useState, useEffect } from "react";

function parseCsvPreview(text, maxRows = 8) {
  const lines = text.split("\n").filter(Boolean);
  if (lines.length === 0) return { columns: [], rows: [] };
  const columns = lines[0].split(",").map(c => c.trim().replace(/^"|"$/g, ""));
  const rows = lines.slice(1, maxRows + 1).map(line => {
    const vals = line.split(",");
    return vals.map(v => v.trim().replace(/^"|"$/g, ""));
  });
  return { columns, rows };
}

export default function DataPreview({ file }) {
  const [preview, setPreview] = useState(null);
  const [stats, setStats] = useState(null);

  useEffect(() => {
    if (!file) return;
    const reader = new FileReader();
    reader.onload = (e) => {
      const text = e.target.result;
      const { columns, rows } = parseCsvPreview(text);
      setPreview({ columns, rows });

      // Quick stats
      const allLines = text.split("\n").filter(Boolean);
      const n_rows = allLines.length - 1;
      const n_cols = columns.length;
      const size = (file.size / 1024).toFixed(1);
      setStats({ n_rows, n_cols, size });
    };
    reader.readAsText(file);
  }, [file]);

  if (!preview) {
    return (
      <div className="card">
        <div className="card-title">Data Preview</div>
        <div style={{ color: "var(--text-muted)", fontSize: 13 }}>Loading preview…</div>
      </div>
    );
  }

  return (
    <div className="card">
      <div className="card-title">Data Preview</div>

      {stats && (
        <div className="preview-meta">
          <span className="meta-chip">📄 {file.name}</span>
          <span className="meta-chip">{stats.n_rows.toLocaleString()} rows</span>
          <span className="meta-chip">{stats.n_cols} cols</span>
          <span className="meta-chip">{stats.size} KB</span>
        </div>
      )}

      <div className="table-wrap">
        <table>
          <thead>
            <tr>
              {preview.columns.map((col, i) => (
                <th key={i}>{col}</th>
              ))}
            </tr>
          </thead>
          <tbody>
            {preview.rows.map((row, ri) => (
              <tr key={ri}>
                {row.map((cell, ci) => (
                  <td key={ci}>{cell || <span style={{ color: "var(--text-dim)" }}>—</span>}</td>
                ))}
              </tr>
            ))}
          </tbody>
        </table>
      </div>
      <div style={{ color: "var(--text-dim)", fontSize: 11, fontFamily: "var(--font-mono)", marginTop: 8 }}>
        Showing first 8 rows · Full data processed server-side
      </div>
    </div>
  );
}
