import { useRef } from "react";
import { motion, useInView } from "framer-motion";

// ── HELPERS ──────────────────────────────────────────────────────────────────

const SEV_COLOR = {
  critical: "rgba(248,113,113,0.85)",
  high:     "rgba(248,113,113,0.75)",
  med:      "rgba(245,158,11,0.8)",
  low:      "rgba(240,237,232,0.25)",
  info:     "rgba(240,237,232,0.15)",
};
const SEV_GLOW = {
  critical: "rgba(248,113,113,0.25)",
  high:     "rgba(248,113,113,0.18)",
  med:      "rgba(245,158,11,0.2)",
  low:      "rgba(255,255,255,0.05)",
  info:     "rgba(255,255,255,0.04)",
};
const SEV_WEIGHT = { critical: 5, high: 3, med: 2, low: 1, info: 0.5 };

function buildBars(results) {
  const analysis   = results.report_json?.analysis || {};
  const autoScore  = analysis.confidence ?? 100;
  const aiScore    = results.ai_score ?? null;
  const aiReason   = results.ai_score_reason ?? null;
  const flags      = analysis.flags || [];
  const missing    = results.schema?.missing || [];

  const totalDeduction = 100 - autoScore;
  const sources = [];

  // Flags are the primary source of deductions
  flags.forEach(f => {
    sources.push({
      label: f.title,
      why: f.why,
      severity: f.severity,
      weight: SEV_WEIGHT[f.severity] ?? 1,
    });
  });

  // Add missing schema columns if not already captured by a flag
  const flagTitlesLower = flags.map(f => f.title.toLowerCase());
  if (
    missing.length > 0 &&
    !flagTitlesLower.some(t => t.includes("schema") || t.includes("missing") || t.includes("column"))
  ) {
    sources.push({
      label: `Missing canonical columns (${missing.slice(0, 2).join(", ")}${missing.length > 2 ? "…" : ""})`,
      why: "Required statistical columns not detected.",
      severity: "high",
      weight: SEV_WEIGHT.high,
    });
  }

  // Catch-all if no sources but score is deducted
  if (sources.length === 0 && totalDeduction > 0) {
    sources.push({ label: "Audit deductions", why: "", severity: "med", weight: 2 });
  }

  const bars = [];

  if (sources.length > 0) {
    const totalWeight = sources.reduce((s, c) => s + c.weight, 0);
    let running = 100;

    sources.forEach((src, i) => {
      let pts = Math.round((src.weight / totalWeight) * totalDeduction);
      // Last item absorbs rounding error
      if (i === sources.length - 1) pts = running - autoScore;
      if (pts <= 0) return;

      bars.push({
        kind: "deduction",
        label: src.label,
        why: src.why,
        severity: src.severity,
        pts,
        leftPct: running - pts,
        widthPct: pts,
        runningAfter: running - pts,
      });
      running -= pts;
    });
  }

  // AI adjustment bar
  if (aiScore !== null) {
    const aiDelta = aiScore - autoScore;
    bars.push({
      kind: "ai",
      label: "AI context adjustment",
      why: aiReason || "",
      pts: aiDelta,
      leftPct: aiDelta >= 0 ? autoScore : aiScore,
      widthPct: Math.abs(aiDelta),
      severity: aiDelta >= 0 ? "info" : "med",
    });
  }

  return { bars, autoScore, aiScore };
}

// ── BAR ROW ───────────────────────────────────────────────────────────────────

function BarRow({ bar, index, inView, autoScore, aiScore }) {
  const scoreColor = bar.kind === "final-auto"
    ? (autoScore >= 70 ? "#4ade80" : autoScore >= 45 ? "#f59e0b" : "#f87171")
    : bar.kind === "final-ai"
      ? (aiScore >= 70 ? "#4ade80" : aiScore >= 45 ? "#f59e0b" : "#f87171")
      : SEV_COLOR[bar.severity] || SEV_COLOR.med;

  const glowColor = bar.kind === "final-auto" || bar.kind === "final-ai"
    ? "transparent"
    : SEV_GLOW[bar.severity] || "transparent";

  const isBase  = bar.kind === "base";
  const isFinal = bar.kind === "final-auto" || bar.kind === "final-ai";
  const isAI    = bar.kind === "ai";

  const fillColor = isBase
    ? "rgba(240,237,232,0.1)"
    : isFinal
      ? scoreColor
      : isAI
        ? (bar.pts >= 0 ? "rgba(74,222,128,0.6)" : "rgba(245,158,11,0.6)")
        : scoreColor;

  const valueLabel = isBase
    ? "100"
    : isFinal
      ? String(bar.value)
      : isAI
        ? (bar.pts >= 0 ? `+${bar.pts}` : String(bar.pts))
        : `−${bar.pts}`;

  const valueLabelColor = isBase
    ? "var(--text-dim)"
    : isFinal
      ? scoreColor
      : isAI
        ? (bar.pts >= 0 ? "#4ade80" : "#f59e0b")
        : SEV_COLOR[bar.severity] || "var(--text-muted)";

  return (
    <div style={{ marginBottom: isFinal ? 0 : 10 }}>
      {/* Label row */}
      <div style={{
        display: "flex",
        alignItems: "center",
        justifyContent: "space-between",
        marginBottom: 5,
        gap: 10,
      }}>
        <div style={{ display: "flex", alignItems: "center", gap: 7, minWidth: 0, flex: 1 }}>
          {!isBase && !isFinal && (
            <span style={{
              fontFamily: "var(--font-mono)",
              fontSize: 8,
              letterSpacing: "0.12em",
              textTransform: "uppercase",
              padding: "2px 6px",
              borderRadius: 4,
              flexShrink: 0,
              ...(isAI
                ? { color: bar.pts >= 0 ? "#4ade80" : "#fcd34d", background: bar.pts >= 0 ? "rgba(74,222,128,0.1)" : "rgba(245,158,11,0.1)", border: `1px solid ${bar.pts >= 0 ? "rgba(74,222,128,0.2)" : "rgba(245,158,11,0.2)"}` }
                : { color: fillColor, background: glowColor, border: `1px solid ${glowColor}` }
              ),
            }}>
              {isAI ? "AI" : bar.severity}
            </span>
          )}
          <span style={{
            fontSize: isFinal ? 12 : 12,
            fontFamily: isFinal || isBase ? "var(--font-mono)" : "var(--font-sans)",
            color: isFinal ? valueLabelColor : isBase ? "var(--text-dim)" : "var(--text-muted)",
            letterSpacing: isFinal || isBase ? "0.06em" : "normal",
            textTransform: isFinal || isBase ? "uppercase" : "none",
            fontWeight: isFinal ? 500 : 400,
            overflow: "hidden",
            textOverflow: "ellipsis",
            whiteSpace: "nowrap",
          }}>
            {bar.label}
          </span>
        </div>
        <span style={{
          fontFamily: "var(--font-mono)",
          fontSize: isFinal ? 18 : 12,
          color: valueLabelColor,
          fontWeight: isFinal ? 600 : 400,
          flexShrink: 0,
        }}>
          {valueLabel}
        </span>
      </div>

      {/* Track */}
      <div style={{
        position: "relative",
        height: isFinal ? 12 : isBase ? 10 : 8,
        background: "rgba(255,255,255,0.05)",
        borderRadius: 99,
        overflow: "hidden",
      }}>
        <motion.div
          initial={{ width: 0 }}
          animate={inView ? { width: `${bar.widthPct}%` } : { width: 0 }}
          transition={{
            duration: 0.9,
            delay: index * 0.12,
            ease: [0.16, 1, 0.3, 1],
          }}
          style={{
            position: "absolute",
            left: `${bar.leftPct}%`,
            top: 0,
            height: "100%",
            borderRadius: 99,
            background: fillColor,
            boxShadow: isFinal ? `0 0 12px ${fillColor}55` : "none",
          }}
        />
      </div>

      {/* Tooltip-style "why" on hover — just shown below for deductions */}
      {!isBase && !isFinal && bar.why && (
        <div style={{
          fontSize: 10,
          color: "var(--text-dim)",
          fontFamily: "var(--font-sans)",
          lineHeight: 1.5,
          marginTop: 4,
          paddingLeft: 1,
          opacity: 0.7,
        }}>
          {bar.why.length > 100 ? bar.why.slice(0, 100) + "…" : bar.why}
        </div>
      )}
    </div>
  );
}

// ── MAIN COMPONENT ─────────────────────────────────────────────────────────────

export function ScoreWaterfall({ results }) {
  const ref = useRef(null);
  const inView = useInView(ref, { once: true, margin: "-40px" });
  const { bars, autoScore, aiScore } = buildBars(results);

  const autoColor = autoScore >= 70 ? "#4ade80" : autoScore >= 45 ? "#f59e0b" : "#f87171";
  const aiColor   = aiScore !== null
    ? (aiScore >= 70 ? "#4ade80" : aiScore >= 45 ? "#f59e0b" : "#f87171")
    : null;

  // Full list of rows to render
  const rows = [
    {
      kind: "base",
      label: "BASELINE",
      leftPct: 0,
      widthPct: 100,
    },
    ...bars,
    {
      kind: "final-auto",
      label: "AUDIT SCORE",
      value: autoScore,
      leftPct: 0,
      widthPct: autoScore,
    },
    ...(aiScore !== null ? [{
      kind: "final-ai",
      label: "AI-ADJUSTED",
      value: aiScore,
      leftPct: 0,
      widthPct: aiScore,
    }] : []),
  ];

  if (bars.length === 0 && autoScore === 100) {
    return (
      <div ref={ref} style={{ padding: "16px 0" }}>
        <div className="card-label" style={{ marginBottom: 12 }}>Score Breakdown</div>
        <div style={{ display: "flex", alignItems: "center", gap: 10, color: "var(--green)", fontSize: 13 }}>
          <span style={{ fontSize: 18 }}>✓</span>
          No deductions — perfect score.
        </div>
      </div>
    );
  }

  return (
    <div ref={ref}>
      <div className="card-label" style={{ marginBottom: 20 }}>Score Breakdown</div>

      <div style={{ display: "flex", gap: 24, marginBottom: 28 }}>
        <div>
          <div style={{
            fontFamily: "var(--font-mono)", fontSize: 9, letterSpacing: "0.14em",
            textTransform: "uppercase", color: "var(--text-dim)", marginBottom: 4,
          }}>Audit score</div>
          <div style={{ fontFamily: "var(--font-serif)", fontSize: 40, color: autoColor, lineHeight: 1 }}>
            {autoScore}<span style={{ fontSize: 16, opacity: 0.35 }}>/100</span>
          </div>
        </div>
        {aiScore !== null && (
          <>
            <div style={{ display: "flex", alignItems: "center", color: "var(--text-dim)", fontSize: 18 }}>→</div>
            <div>
              <div style={{
                fontFamily: "var(--font-mono)", fontSize: 9, letterSpacing: "0.14em",
                textTransform: "uppercase", color: "var(--text-dim)", marginBottom: 4,
              }}>AI-adjusted</div>
              <div style={{ fontFamily: "var(--font-serif)", fontSize: 40, color: aiColor, lineHeight: 1 }}>
                {aiScore}<span style={{ fontSize: 16, opacity: 0.35 }}>/100</span>
              </div>
            </div>
          </>
        )}
      </div>

      <div>
        {rows.map((row, i) => {
          const isSeparatorBefore = row.kind === "final-auto";
          return (
            <div key={i}>
              {isSeparatorBefore && (
                <div style={{
                  height: 1,
                  background: "var(--border)",
                  margin: "14px 0",
                }} />
              )}
              <BarRow
                bar={row}
                index={i}
                inView={inView}
                autoScore={autoScore}
                aiScore={aiScore}
              />
            </div>
          );
        })}
      </div>
    </div>
  );
}
