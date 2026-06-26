import { useState, useMemo, useRef } from "react";
import { useInView } from "framer-motion";
import {
  LineChart, Line, XAxis, YAxis, Tooltip, ReferenceLine,
  ResponsiveContainer, Legend, CartesianGrid,
} from "recharts";

// ── STATS UTILITIES ───────────────────────────────────────────────────────────

function normCDF(x) {
  const sign = x < 0 ? -1 : 1;
  const ax = Math.abs(x) / Math.SQRT2;
  const t = 1 / (1 + 0.3275911 * ax);
  const poly = t * (0.254829592 + t * (-0.284496736 + t * (1.421413741 + t * (-1.453152027 + t * 1.061405429))));
  return 0.5 * (1 + sign * (1 - poly * Math.exp(-ax * ax)));
}

function normInv(p) {
  const a = [-3.969683028665376e1, 2.209460984245205e2, -2.759285104469687e2, 1.383577518672690e2, -3.066479806614716e1, 2.506628277459239];
  const b = [-5.447609879822406e1, 1.615858368580409e2, -1.556989798598866e2, 6.680131188771972e1, -1.328068155288572e1];
  const c = [-7.784894002430293e-3, -3.223964580411365e-1, -2.400758277161838, -2.549732539343734, 4.374664141464968, 2.938163982698783];
  const d = [7.784695709041462e-3, 3.224671290700398e-1, 2.445134137142996, 3.754408661907416];
  const plo = 0.02425, phi = 1 - plo;
  if (p <= 0) return -Infinity;
  if (p >= 1) return Infinity;
  if (p < plo) {
    const q = Math.sqrt(-2 * Math.log(p));
    return (((((c[0]*q+c[1])*q+c[2])*q+c[3])*q+c[4])*q+c[5]) / ((((d[0]*q+d[1])*q+d[2])*q+d[3])*q+1);
  }
  if (p <= phi) {
    const q = p - 0.5, r = q * q;
    return (((((a[0]*r+a[1])*r+a[2])*r+a[3])*r+a[4])*r+a[5])*q / (((((b[0]*r+b[1])*r+b[2])*r+b[3])*r+b[4])*r+1);
  }
  const q = Math.sqrt(-2 * Math.log(1 - p));
  return -(((((c[0]*q+c[1])*q+c[2])*q+c[3])*q+c[4])*q+c[5]) / ((((d[0]*q+d[1])*q+d[2])*q+d[3])*q+1);
}

function computePower(n, d, alpha, nTests) {
  const alphaAdj = alpha / nTests;
  const zCrit = normInv(1 - alphaAdj / 2);
  const lambda = d * Math.sqrt(n / 2);
  return Math.max(0, Math.min(1, normCDF(lambda - zCrit) + normCDF(-lambda - zCrit)));
}

function nForPower(target, d, alpha, nTests) {
  let lo = 2, hi = 5000;
  for (let i = 0; i < 40; i++) {
    const mid = Math.ceil((lo + hi) / 2);
    computePower(mid, d, alpha, nTests) >= target ? (hi = mid) : (lo = mid + 1);
  }
  return hi;
}

function medianAbsLog2FC(histogram) {
  if (!histogram) return null;
  const { counts, bin_edges } = histogram;
  const total = counts.reduce((s, c) => s + c, 0);
  let cum = 0;
  for (let i = 0; i < counts.length; i++) {
    cum += counts[i];
    if (cum >= total / 2) return Math.abs((bin_edges[i] + bin_edges[i + 1]) / 2);
  }
  return null;
}

// ── DESIGN TOKENS ─────────────────────────────────────────────────────────────

const C = {
  dim:    "rgba(240,237,232,0.28)",
  muted:  "rgba(240,237,232,0.5)",
  border: "rgba(255,255,255,0.07)",
  green:  "#4ade80",
  amber:  "#f59e0b",
  red:    "#f87171",
  warm:   "#c8b99a",
};

// ── CUSTOM TOOLTIP ────────────────────────────────────────────────────────────

function PowerTooltip({ active, payload, label, detectedD }) {
  if (!active || !payload?.length) return null;
  return (
    <div style={{
      background: "#1a1a1a", border: `1px solid ${C.border}`,
      borderRadius: 10, padding: "10px 14px",
      fontFamily: "monospace", fontSize: 11, minWidth: 160,
    }}>
      <div style={{ color: C.dim, marginBottom: 8, letterSpacing: "0.06em" }}>
        n = {label} per group
      </div>
      {payload
        .slice()
        .sort((a, b) => b.value - a.value)
        .map((p, i) => (
          <div key={i} style={{ display: "flex", justifyContent: "space-between", gap: 16, color: p.color, marginBottom: 3 }}>
            <span>{p.name}</span>
            <span style={{ fontWeight: 600 }}>{Math.round(p.value * 100)}%</span>
          </div>
        ))}
    </div>
  );
}

// ── MAIN COMPONENT ────────────────────────────────────────────────────────────

export function PowerAnalysis({ histogram, overview, context }) {
  const ref = useRef(null);
  useInView(ref, { once: true, margin: "-40px" });

  const nFeatures = overview?.n_rows ?? 100;
  const alpha     = parseFloat(context?.alpha ?? "0.05");
  const defaultN  = context?.small_n ? 6 : 20;
  const [nPerGroup, setNPerGroup] = useState(defaultN);

  const detectedD = useMemo(() => medianAbsLog2FC(histogram) ?? 0.5, [histogram]);

  const alphaAdj = alpha / nFeatures;
  const fmtAlpha = alphaAdj < 0.001 ? alphaAdj.toExponential(1) : alphaAdj.toFixed(4);

  const currentPower = useMemo(
    () => computePower(nPerGroup, detectedD, alpha, nFeatures),
    [nPerGroup, detectedD, alpha, nFeatures]
  );

  const n80 = useMemo(() => nForPower(0.8, detectedD, alpha, nFeatures), [detectedD, alpha, nFeatures]);
  const n90 = useMemo(() => nForPower(0.9, detectedD, alpha, nFeatures), [detectedD, alpha, nFeatures]);

  // Generate smooth curve (n=3 to 120)
  const curveData = useMemo(() => {
    const points = [];
    for (let n = 3; n <= 120; n++) {
      points.push({
        n,
        small:    computePower(n, 0.2, alpha, nFeatures),
        medium:   computePower(n, 0.5, alpha, nFeatures),
        detected: computePower(n, detectedD, alpha, nFeatures),
        large:    computePower(n, 0.8, alpha, nFeatures),
      });
    }
    return points;
  }, [detectedD, alpha, nFeatures]);

  const verdict = currentPower >= 0.8
    ? { label: "Adequately powered", color: C.green,  icon: "✓" }
    : currentPower >= 0.6
    ? { label: "Marginal",           color: C.amber,  icon: "⚠" }
    : { label: "Underpowered",       color: C.red,    icon: "✗" };

  const LINES = [
    { key: "small",    name: "Small (d=0.2)",                color: "rgba(248,113,113,0.5)", dash: "4 2" },
    { key: "medium",   name: "Medium (d=0.5)",               color: C.amber,                 dash: "4 2" },
    { key: "detected", name: `Detected (d=${detectedD.toFixed(2)})`, color: C.green,         dash: "" },
    { key: "large",    name: "Large (d=0.8)",                color: C.warm,                  dash: "4 2" },
  ];

  return (
    <div ref={ref}>
      <div className="card-label" style={{ marginBottom: 20 }}>Statistical Power Analysis</div>

      {/* Parameters */}
      <div style={{
        display: "grid", gridTemplateColumns: "repeat(3, 1fr)", gap: 1,
        background: "var(--border)", borderRadius: 10, overflow: "hidden", marginBottom: 24,
      }}>
        {[
          { label: "Effect size (median |log₂FC|)", value: detectedD.toFixed(2), sub: "Cohen's d proxy" },
          { label: "Features tested",               value: nFeatures.toLocaleString(), sub: `Bonferroni α = ${fmtAlpha}` },
          { label: "Significance level",             value: `α = ${alpha}`, sub: "as specified" },
        ].map((p, i) => (
          <div key={i} style={{ background: "var(--bg-raised)", padding: "12px 14px" }}>
            <div style={{ fontFamily: "var(--font-mono)", fontSize: 9, letterSpacing: "0.1em", textTransform: "uppercase", color: "var(--text-dim)", marginBottom: 4 }}>{p.label}</div>
            <div style={{ fontFamily: "var(--font-serif)", fontSize: 20, color: "var(--text)", lineHeight: 1 }}>{p.value}</div>
            <div style={{ fontFamily: "var(--font-mono)", fontSize: 9, color: "var(--text-dim)", marginTop: 3 }}>{p.sub}</div>
          </div>
        ))}
      </div>

      {/* Slider */}
      <div style={{ marginBottom: 20 }}>
        <div style={{ display: "flex", justifyContent: "space-between", alignItems: "baseline", marginBottom: 8 }}>
          <label style={{ fontFamily: "var(--font-mono)", fontSize: 10, letterSpacing: "0.1em", textTransform: "uppercase", color: "var(--text-dim)" }}>
            n per group
          </label>
          <span style={{ fontFamily: "var(--font-serif)", fontSize: 24, color: "var(--text)" }}>{nPerGroup}</span>
        </div>
        <input
          type="range" min={3} max={120} step={1} value={nPerGroup}
          onChange={e => setNPerGroup(Number(e.target.value))}
          style={{ width: "100%" }}
        />
        <div style={{ display: "flex", justifyContent: "space-between", fontFamily: "var(--font-mono)", fontSize: 10, color: "var(--text-dim)", marginTop: 4 }}>
          <span>n=3</span><span>n=120</span>
        </div>
      </div>

      {/* Verdict */}
      <div style={{
        display: "flex", alignItems: "center", gap: 14,
        padding: "14px 18px", borderRadius: 10, marginBottom: 24,
        background: `${verdict.color}11`, border: `1px solid ${verdict.color}33`,
      }}>
        <div style={{
          width: 52, height: 52, borderRadius: "50%", flexShrink: 0,
          background: `${verdict.color}18`, border: `1px solid ${verdict.color}44`,
          display: "flex", alignItems: "center", justifyContent: "center",
          fontFamily: "var(--font-serif)", fontSize: 26, color: verdict.color,
        }}>
          {Math.round(currentPower * 100)}
        </div>
        <div>
          <div style={{ fontFamily: "var(--font-mono)", fontSize: 9, letterSpacing: "0.12em", textTransform: "uppercase", color: verdict.color, marginBottom: 3 }}>
            {verdict.icon} {verdict.label}
          </div>
          <div style={{ fontSize: 12, color: "var(--text-muted)", lineHeight: 1.6 }}>
            Power = {Math.round(currentPower * 100)}% at n={nPerGroup} for the detected effect (d={detectedD.toFixed(2)}).
            {currentPower < 0.8 && ` Need n≥${n80} for 80% power, n≥${n90} for 90%.`}
            {currentPower >= 0.8 && " Adequately powered for the observed effect size."}
          </div>
        </div>
      </div>

      {/* Power curve chart */}
      <div style={{ marginBottom: 8 }}>
        <div style={{ fontFamily: "var(--font-mono)", fontSize: 9, letterSpacing: "0.1em", textTransform: "uppercase", color: "var(--text-dim)", marginBottom: 16 }}>
          Power curve — effect size comparison
        </div>

        <ResponsiveContainer width="100%" height={240}>
          <LineChart data={curveData} margin={{ top: 4, right: 16, bottom: 4, left: -8 }}>
            <CartesianGrid stroke={C.border} strokeDasharray="3 3" vertical={false} />
            <XAxis
              dataKey="n"
              tick={{ fill: C.dim, fontSize: 9, fontFamily: "monospace" }}
              axisLine={{ stroke: C.border }}
              tickLine={false}
              label={{ value: "n per group", position: "insideBottom", offset: -2, fill: C.dim, fontSize: 9, fontFamily: "monospace" }}
            />
            <YAxis
              tickFormatter={v => `${Math.round(v * 100)}%`}
              domain={[0, 1]}
              tick={{ fill: C.dim, fontSize: 9, fontFamily: "monospace" }}
              axisLine={false}
              tickLine={false}
              width={36}
            />
            <Tooltip content={<PowerTooltip detectedD={detectedD} />} />

            {/* 80% threshold line */}
            <ReferenceLine
              y={0.8} stroke="rgba(255,255,255,0.2)" strokeDasharray="4 3"
              label={{ value: "80%", position: "right", fill: C.dim, fontSize: 9, fontFamily: "monospace" }}
            />
            {/* Current n line */}
            <ReferenceLine
              x={nPerGroup} stroke={verdict.color} strokeDasharray="4 3" strokeWidth={1.5}
              label={{ value: `n=${nPerGroup}`, position: "top", fill: verdict.color, fontSize: 9, fontFamily: "monospace" }}
            />

            {LINES.map(l => (
              <Line
                key={l.key}
                type="monotone"
                dataKey={l.key}
                name={l.name}
                stroke={l.color}
                strokeWidth={l.key === "detected" ? 2.5 : 1.5}
                strokeDasharray={l.dash}
                dot={false}
                activeDot={{ r: 3, fill: l.color }}
              />
            ))}
          </LineChart>
        </ResponsiveContainer>

        {/* Legend */}
        <div style={{ display: "flex", gap: 16, flexWrap: "wrap", marginTop: 10, paddingLeft: 28, fontFamily: "monospace", fontSize: 10 }}>
          {LINES.map(l => (
            <span key={l.key} style={{ display: "flex", alignItems: "center", gap: 5, color: C.dim }}>
              <span style={{ width: 16, height: 2, background: l.color, display: "inline-block", borderRadius: 1 }} />
              <span style={{ color: l.key === "detected" ? l.color : C.dim }}>{l.name}</span>
            </span>
          ))}
        </div>
      </div>

      <div style={{ marginTop: 16, padding: "10px 14px", background: "rgba(255,255,255,0.02)", border: "1px solid var(--border)", borderRadius: 8, fontSize: 11, color: "var(--text-dim)", lineHeight: 1.7 }}>
        Two-sample t-test with Bonferroni correction across {nFeatures} features. Effect size from median |log₂FC|. Drag the slider to explore sample size scenarios.
      </div>
    </div>
  );
}
