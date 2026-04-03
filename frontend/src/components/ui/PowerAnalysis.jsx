import { useState, useMemo, useRef } from "react";
import { motion, useInView } from "framer-motion";

// ── STATS UTILITIES ───────────────────────────────────────────────────────────

// Standard normal CDF (Abramowitz & Stegun approximation)
function normCDF(x) {
  const sign = x < 0 ? -1 : 1;
  const ax = Math.abs(x) / Math.SQRT2;
  const t = 1 / (1 + 0.3275911 * ax);
  const poly = t * (0.254829592 + t * (-0.284496736 + t * (1.421413741 + t * (-1.453152027 + t * 1.061405429))));
  return 0.5 * (1 + sign * (1 - poly * Math.exp(-ax * ax)));
}

// Inverse normal CDF (rational approximation — Peter Acklam)
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

// Power of a two-sample t-test (normal approximation) with Bonferroni correction
function computePower(n, d, alpha, nTests) {
  const alphaAdj = alpha / nTests;
  const zCrit = normInv(1 - alphaAdj / 2);
  const lambda = d * Math.sqrt(n / 2);
  return normCDF(lambda - zCrit) + normCDF(-lambda - zCrit);
}

// n required to reach target power (binary search)
function nForPower(target, d, alpha, nTests) {
  let lo = 2, hi = 5000;
  for (let i = 0; i < 40; i++) {
    const mid = Math.ceil((lo + hi) / 2);
    computePower(mid, d, alpha, nTests) >= target ? (hi = mid) : (lo = mid + 1);
  }
  return hi;
}

// Estimate median |log2FC| from histogram
function medianAbsLog2FC(histogram) {
  if (!histogram) return null;
  const { counts, bin_edges } = histogram;
  const midpoints = counts.map((_, i) => Math.abs((bin_edges[i] + bin_edges[i + 1]) / 2));
  const total = counts.reduce((s, c) => s + c, 0);
  let cum = 0;
  for (let i = 0; i < counts.length; i++) {
    cum += counts[i];
    if (cum >= total / 2) return midpoints[i];
  }
  return midpoints[midpoints.length - 1];
}

// ── POWER BAR CHART ───────────────────────────────────────────────────────────

const CURVE_NS = [4, 6, 8, 10, 15, 20, 30, 50, 100];

function PowerBar({ n, power, isSelected, index, inView }) {
  const pct = Math.round(power * 100);
  const color = power >= 0.8 ? "#4ade80" : power >= 0.6 ? "#f59e0b" : "#f87171";
  return (
    <div style={{ display: "flex", alignItems: "center", gap: 10, marginBottom: 7 }}>
      <div style={{
        fontFamily: "var(--font-mono)", fontSize: 9, width: 32, textAlign: "right",
        color: isSelected ? "var(--text)" : "var(--text-dim)",
        fontWeight: isSelected ? 600 : 400,
      }}>
        n={n}
      </div>
      <div style={{
        flex: 1, position: "relative", height: isSelected ? 12 : 8,
        background: "rgba(255,255,255,0.05)", borderRadius: 99, overflow: "hidden",
      }}>
        {/* 80% threshold line */}
        <div style={{
          position: "absolute", left: "80%", top: 0, bottom: 0,
          width: 1, background: "rgba(255,255,255,0.12)", zIndex: 1,
        }} />
        <motion.div
          initial={{ width: 0 }}
          animate={inView ? { width: `${pct}%` } : { width: 0 }}
          transition={{ duration: 0.7, delay: index * 0.05, ease: [0.16, 1, 0.3, 1] }}
          style={{
            height: "100%", borderRadius: 99,
            background: color,
            boxShadow: isSelected ? `0 0 8px ${color}88` : "none",
          }}
        />
      </div>
      <div style={{
        fontFamily: "var(--font-mono)", fontSize: 10, width: 34,
        color: isSelected ? color : "var(--text-dim)",
        fontWeight: isSelected ? 600 : 400,
      }}>
        {pct}%
      </div>
      {power >= 0.8 && (
        <span style={{ fontSize: 9, color: "#4ade80" }}>✓</span>
      )}
    </div>
  );
}

// ── MAIN COMPONENT ────────────────────────────────────────────────────────────

export function PowerAnalysis({ histogram, overview, context }) {
  const ref = useRef(null);
  const inView = useInView(ref, { once: true, margin: "-40px" });

  const nFeatures = overview?.n_rows ?? 100;
  const alpha = parseFloat(context?.alpha ?? "0.05");
  const defaultN = context?.small_n ? 6 : 20;
  const [nPerGroup, setNPerGroup] = useState(defaultN);

  const effectSize = useMemo(() => medianAbsLog2FC(histogram), [histogram]);
  const d = effectSize ?? 0.5; // fallback to moderate effect if no histogram

  const alphaAdj = alpha / nFeatures;

  const currentPower = useMemo(
    () => computePower(nPerGroup, d, alpha, nFeatures),
    [nPerGroup, d, alpha, nFeatures]
  );

  const n80 = useMemo(() => nForPower(0.8, d, alpha, nFeatures), [d, alpha, nFeatures]);
  const n90 = useMemo(() => nForPower(0.9, d, alpha, nFeatures), [d, alpha, nFeatures]);

  const curveData = useMemo(
    () => CURVE_NS.map(n => ({ n, power: computePower(n, d, alpha, nFeatures) })),
    [d, alpha, nFeatures]
  );

  const verdict = currentPower >= 0.8
    ? { label: "Adequately powered", color: "#4ade80", icon: "✓" }
    : currentPower >= 0.6
    ? { label: "Marginal — consider increasing n", color: "#f59e0b", icon: "⚠" }
    : { label: "Underpowered — results may be unreliable", color: "#f87171", icon: "✗" };

  const fmtAlpha = alphaAdj < 0.001
    ? alphaAdj.toExponential(1)
    : alphaAdj.toFixed(4);

  return (
    <div ref={ref}>
      <div className="card-label" style={{ marginBottom: 20 }}>Statistical Power Analysis</div>

      {/* Parameters summary */}
      <div style={{
        display: "grid", gridTemplateColumns: "repeat(3, 1fr)", gap: 1,
        background: "var(--border)", borderRadius: 10, overflow: "hidden", marginBottom: 24,
      }}>
        {[
          { label: "Effect size (median |log₂FC|)", value: effectSize != null ? effectSize.toFixed(2) : "n/a", sub: "Cohen's d proxy" },
          { label: "Features (tests)", value: nFeatures.toLocaleString(), sub: `Bonferroni α = ${fmtAlpha}` },
          { label: "Significance level", value: `α = ${alpha}`, sub: "as specified" },
        ].map((p, i) => (
          <div key={i} style={{ background: "var(--bg-raised)", padding: "12px 14px" }}>
            <div style={{ fontFamily: "var(--font-mono)", fontSize: 9, letterSpacing: "0.1em", textTransform: "uppercase", color: "var(--text-dim)", marginBottom: 4 }}>{p.label}</div>
            <div style={{ fontFamily: "var(--font-serif)", fontSize: 20, color: "var(--text)", lineHeight: 1 }}>{p.value}</div>
            <div style={{ fontFamily: "var(--font-mono)", fontSize: 9, color: "var(--text-dim)", marginTop: 3 }}>{p.sub}</div>
          </div>
        ))}
      </div>

      {/* n slider */}
      <div style={{ marginBottom: 20 }}>
        <div style={{ display: "flex", justifyContent: "space-between", alignItems: "baseline", marginBottom: 8 }}>
          <label style={{ fontFamily: "var(--font-mono)", fontSize: 10, letterSpacing: "0.1em", textTransform: "uppercase", color: "var(--text-dim)" }}>
            n per group
          </label>
          <span style={{ fontFamily: "var(--font-serif)", fontSize: 24, color: "var(--text)" }}>{nPerGroup}</span>
        </div>
        <input
          type="range" min={3} max={150} step={1} value={nPerGroup}
          onChange={e => setNPerGroup(Number(e.target.value))}
          style={{ width: "100%" }}
        />
        <div style={{ display: "flex", justifyContent: "space-between", fontFamily: "var(--font-mono)", fontSize: 10, color: "var(--text-dim)", marginTop: 4 }}>
          <span>n=3</span><span>n=150</span>
        </div>
      </div>

      {/* Verdict */}
      <div style={{
        display: "flex", alignItems: "center", gap: 14,
        padding: "14px 18px", borderRadius: 10, marginBottom: 24,
        background: `${verdict.color}11`,
        border: `1px solid ${verdict.color}33`,
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
            At n={nPerGroup} per group, power = {Math.round(currentPower * 100)}% for the median effect size (d={d.toFixed(2)}).
            {currentPower < 0.8 && ` Increase to n≥${n80} for 80% power, n≥${n90} for 90% power.`}
            {currentPower >= 0.8 && " This study is adequately powered to detect the typical observed effect."}
          </div>
        </div>
      </div>

      {/* Power curve */}
      <div style={{ marginBottom: 8 }}>
        <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 12 }}>
          <div style={{ fontFamily: "var(--font-mono)", fontSize: 9, letterSpacing: "0.1em", textTransform: "uppercase", color: "var(--text-dim)" }}>
            Power by sample size
          </div>
          <div style={{ fontFamily: "var(--font-mono)", fontSize: 9, color: "var(--text-dim)", display: "flex", alignItems: "center", gap: 6 }}>
            <div style={{ width: 16, height: 1, background: "rgba(255,255,255,0.15)" }} />
            80% threshold
          </div>
        </div>
        {curveData.map(({ n, power }, i) => (
          <PowerBar
            key={n} n={n} power={power}
            isSelected={n === nPerGroup || (i < curveData.length - 1 && nPerGroup >= n && nPerGroup < curveData[i + 1].n)}
            index={i} inView={inView}
          />
        ))}
      </div>

      <div style={{ marginTop: 16, padding: "10px 14px", background: "rgba(255,255,255,0.02)", border: "1px solid var(--border)", borderRadius: 8, fontSize: 11, color: "var(--text-dim)", lineHeight: 1.7 }}>
        Power computed for two-sample t-test with Bonferroni correction across {nFeatures} tests.
        Effect size estimated from median |log₂FC| in your dataset. True power depends on variance structure and distributional assumptions.
      </div>
    </div>
  );
}
