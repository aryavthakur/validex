import { useRef } from "react";
import { motion, useInView } from "framer-motion";

// ── CRITERIA BUILDER ──────────────────────────────────────────────────────────

function buildCriteria(results, context) {
  const schema   = results.schema || {};
  const overview = results.overview || {};
  const analysis = results.report_json?.analysis || {};
  const flags    = analysis.flags || [];
  const c2o      = schema.canonical_to_original || {};
  const missing  = schema.missing || [];
  const ambig    = schema.ambiguities || {};
  const score    = analysis.confidence ?? 0;

  const totalCells = (overview.n_rows || 1) * (overview.n_cols || 1);
  const missingPct = overview.missing_cells / totalCells;

  const hasCriticalFlag = flags.some(f => f.severity === "critical");
  const hasHighFlag     = flags.some(f => f.severity === "high");
  const hasBatchFlag    = flags.some(f =>
    f.title.toLowerCase().includes("batch") || f.why?.toLowerCase().includes("batch")
  );

  const hasP      = !!c2o.p_value;
  const hasFDR    = !!c2o.fdr;
  const hasFC     = !!(c2o.fold_change || c2o.log2fc);
  const hasLog2FC = !!c2o.log2fc;
  const hasFeature = !!c2o.feature;
  const fcAmbig   = !!ambig.fold_change || !!ambig.log2fc;
  const missingSchema = missing.length > 0;

  const designSpecified = !!(context?.design_type && context.design_type !== "");
  const batchConsidered = context?.has_batches
    ? !hasBatchFlag
    : true; // if no batches, criterion is N/A (mark pass)
  const notesProvided = !!(context?.notes && context.notes.trim().length > 10);
  const alphaSpecified = !!(context?.alpha && context.alpha !== "0.05");

  return [
    {
      category: "Data Completeness",
      items: [
        {
          id: "p_value",
          label: "p-values reported",
          standard: "MSI Level 1",
          pass: hasP,
          detail: hasP
            ? `Detected as "${c2o.p_value}"`
            : "No p-value column detected. Required for statistical reporting.",
        },
        {
          id: "fdr",
          label: "Multiple testing correction applied",
          standard: "MSI Level 1",
          pass: hasFDR,
          detail: hasFDR
            ? `FDR/q-values detected as "${c2o.fdr}"`
            : "No FDR or q-value column detected. Required to control false positives across multiple features.",
        },
        {
          id: "effect_size",
          label: "Effect sizes reported",
          standard: "MSI Level 1",
          pass: hasFC,
          detail: hasFC
            ? `Fold change detected${hasLog2FC ? " (log₂FC included)" : " (log₂FC missing)"}`
            : "No fold change or log₂FC column detected. Magnitude of differences must be reported.",
        },
        {
          id: "feature_id",
          label: "Feature identifiers present",
          standard: "MSI Level 1",
          pass: hasFeature,
          detail: hasFeature
            ? `Feature ID column detected as "${c2o.feature}"`
            : "No feature identifier column detected. Each metabolite must be uniquely identified.",
        },
        {
          id: "missing_data",
          label: "Data completeness ≥ 95%",
          standard: "MSI Level 2",
          pass: missingPct < 0.05,
          warn: missingPct >= 0.05 && missingPct < 0.15,
          detail: overview.missing_cells === 0
            ? "No missing values detected."
            : `${overview.missing_cells} missing cells (${(missingPct * 100).toFixed(1)}%). ${missingPct >= 0.05 ? "Exceeds 5% threshold — imputation or removal required." : "Within acceptable range."}`,
        },
      ],
    },
    {
      category: "Statistical Reporting",
      items: [
        {
          id: "no_ambiguity",
          label: "Column mappings unambiguous",
          standard: "Good Practice",
          pass: !fcAmbig && !missingSchema,
          warn: missingSchema && !fcAmbig,
          detail: fcAmbig
            ? `Ambiguous column match for: ${Object.keys(ambig).join(", ")}. Rename columns to eliminate ambiguity.`
            : missingSchema
            ? `Missing canonical columns: ${missing.join(", ")}. Add required columns to your export.`
            : "All detected columns are unambiguous.",
        },
        {
          id: "log2fc",
          label: "log₂ fold change included",
          standard: "MSI Level 2",
          pass: hasLog2FC,
          warn: hasFC && !hasLog2FC,
          detail: hasLog2FC
            ? `log₂FC detected as "${c2o.log2fc}"`
            : hasFC
            ? "Fold change detected but log₂FC absent. Log₂FC is preferred for symmetry and statistical interpretation."
            : "Neither fold change nor log₂FC detected.",
        },
        {
          id: "no_critical_flags",
          label: "No critical audit flags",
          standard: "MSI Level 1",
          pass: !hasCriticalFlag,
          warn: hasHighFlag && !hasCriticalFlag,
          detail: hasCriticalFlag
            ? "Critical flags detected — resolve before submission."
            : hasHighFlag
            ? "High-severity flags detected — review recommended before submission."
            : "No critical or high-severity flags.",
        },
        {
          id: "confidence_score",
          label: "Audit confidence score ≥ 70",
          standard: "Validex",
          pass: score >= 70,
          warn: score >= 55 && score < 70,
          detail: `Current score: ${score}/100. ${score >= 70 ? "Meets threshold." : score >= 55 ? "Marginal — address flagged issues." : "Below threshold — significant issues must be resolved."}`,
        },
      ],
    },
    {
      category: "Study Design Documentation",
      items: [
        {
          id: "design_type",
          label: "Statistical design specified",
          standard: "MSI Level 2",
          pass: designSpecified,
          detail: designSpecified
            ? `Design documented: ${context.design_type}, ${context.group_count}`
            : "Study design not specified. Document whether groups are independent or paired.",
        },
        {
          id: "batch_correction",
          label: "Batch effects addressed",
          standard: "MSI Level 2",
          pass: batchConsidered,
          warn: context?.has_batches && hasBatchFlag,
          detail: context?.has_batches
            ? hasBatchFlag
              ? "Batch effects flagged but not addressed. Apply batch correction (e.g. ComBat, LOESS) before analysis."
              : "Batches present and no batch-related flags detected."
            : "No batch effects reported for this dataset.",
        },
        {
          id: "notes",
          label: "Study context documented",
          standard: "Good Practice",
          pass: notesProvided,
          warn: !notesProvided,
          detail: notesProvided
            ? "Contextual notes provided."
            : "No study context notes provided. Document sample collection, QC procedures, and any deviations.",
        },
      ],
    },
  ];
}

// ── ITEM ROW ──────────────────────────────────────────────────────────────────

function CheckItem({ item, index, inView }) {
  const status = !item.pass && !item.warn ? "fail"
    : item.warn ? "warn"
    : "pass";

  const colors = {
    pass: { dot: "#4ade80", bg: "rgba(74,222,128,0.07)",  border: "rgba(74,222,128,0.15)",  text: "#4ade80",  label: "PASS" },
    warn: { dot: "#f59e0b", bg: "rgba(245,158,11,0.07)",  border: "rgba(245,158,11,0.15)",  text: "#f59e0b",  label: "WARN" },
    fail: { dot: "#f87171", bg: "rgba(248,113,113,0.07)", border: "rgba(248,113,113,0.15)", text: "#f87171",  label: "FAIL" },
  }[status];

  return (
    <motion.div
      initial={{ opacity: 0, x: -8 }}
      animate={inView ? { opacity: 1, x: 0 } : { opacity: 0, x: -8 }}
      transition={{ duration: 0.4, delay: index * 0.05, ease: [0.16, 1, 0.3, 1] }}
      style={{
        display: "flex", gap: 12, padding: "12px 14px",
        borderRadius: 10, marginBottom: 6,
        background: colors.bg, border: `1px solid ${colors.border}`,
      }}
    >
      {/* Status dot */}
      <div style={{
        width: 8, height: 8, borderRadius: "50%",
        background: colors.dot, flexShrink: 0, marginTop: 5,
        boxShadow: `0 0 6px ${colors.dot}88`,
      }} />

      <div style={{ flex: 1, minWidth: 0 }}>
        <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", gap: 8, marginBottom: 3 }}>
          <span style={{ fontSize: 13, color: "var(--text)", fontWeight: 450, lineHeight: 1.3 }}>{item.label}</span>
          <div style={{ display: "flex", alignItems: "center", gap: 6, flexShrink: 0 }}>
            <span style={{
              fontFamily: "var(--font-mono)", fontSize: 8, letterSpacing: "0.1em",
              color: "var(--text-dim)", background: "rgba(255,255,255,0.05)",
              border: "1px solid var(--border)", padding: "1px 5px", borderRadius: 3,
            }}>{item.standard}</span>
            <span style={{
              fontFamily: "var(--font-mono)", fontSize: 8, letterSpacing: "0.12em",
              color: colors.text, fontWeight: 600,
            }}>{colors.label}</span>
          </div>
        </div>
        <div style={{ fontSize: 11, color: "var(--text-dim)", lineHeight: 1.6 }}>{item.detail}</div>
      </div>
    </motion.div>
  );
}

// ── MAIN COMPONENT ────────────────────────────────────────────────────────────

export function PublicationChecklist({ results, context }) {
  const ref = useRef(null);
  const inView = useInView(ref, { once: true, margin: "-40px" });
  const categories = buildCriteria(results, context);

  const allItems  = categories.flatMap(c => c.items);
  const passing   = allItems.filter(i => i.pass && !i.warn).length;
  const warning   = allItems.filter(i => i.warn).length;
  const failing   = allItems.filter(i => !i.pass && !i.warn).length;
  const total     = allItems.length;
  const pct       = Math.round((passing / total) * 100);

  const scoreColor = pct >= 80 ? "#4ade80" : pct >= 60 ? "#f59e0b" : "#f87171";
  const readiness  = pct >= 80 ? "Submission-ready" : pct >= 60 ? "Needs attention" : "Not ready for submission";

  let itemIndex = 0;

  return (
    <div ref={ref}>
      <div className="card-label" style={{ marginBottom: 20 }}>Publication Readiness Checklist</div>

      {/* Score header */}
      <div style={{
        display: "flex", alignItems: "center", gap: 20,
        padding: "18px 20px", borderRadius: 12, marginBottom: 24,
        background: `${scoreColor}0e`, border: `1px solid ${scoreColor}2a`,
      }}>
        <div style={{ textAlign: "center", flexShrink: 0 }}>
          <div style={{ fontFamily: "var(--font-serif)", fontSize: 48, color: scoreColor, lineHeight: 1 }}>{passing}</div>
          <div style={{ fontFamily: "var(--font-mono)", fontSize: 9, color: "var(--text-dim)", letterSpacing: "0.1em", textTransform: "uppercase" }}>of {total} passed</div>
        </div>
        <div style={{ width: 1, height: 56, background: "var(--border)" }} />
        <div>
          <div style={{ fontFamily: "var(--font-mono)", fontSize: 10, letterSpacing: "0.1em", textTransform: "uppercase", color: scoreColor, marginBottom: 4 }}>
            {readiness}
          </div>
          <div style={{ display: "flex", gap: 14, fontSize: 12, color: "var(--text-muted)" }}>
            <span style={{ color: "#4ade80" }}>✓ {passing} passing</span>
            {warning > 0 && <span style={{ color: "#f59e0b" }}>⚠ {warning} warnings</span>}
            {failing > 0 && <span style={{ color: "#f87171" }}>✗ {failing} failing</span>}
          </div>
          <div style={{ marginTop: 8, height: 5, width: 240, borderRadius: 99, background: "rgba(255,255,255,0.06)", overflow: "hidden" }}>
            <div style={{ height: "100%", width: `${pct}%`, background: scoreColor, borderRadius: 99, transition: "width 1s ease" }} />
          </div>
        </div>
        <div style={{ marginLeft: "auto", textAlign: "right" }}>
          <div style={{ fontFamily: "var(--font-mono)", fontSize: 9, color: "var(--text-dim)", letterSpacing: "0.1em", textTransform: "uppercase", marginBottom: 2 }}>Standards</div>
          <div style={{ fontSize: 11, color: "var(--text-muted)", lineHeight: 1.8 }}>
            MSI Levels 1–2<br/>Good Practice
          </div>
        </div>
      </div>

      {/* Criteria by category */}
      {categories.map(cat => (
        <div key={cat.category} style={{ marginBottom: 20 }}>
          <div style={{
            fontFamily: "var(--font-mono)", fontSize: 9, letterSpacing: "0.14em",
            textTransform: "uppercase", color: "var(--text-dim)", marginBottom: 10,
            paddingBottom: 6, borderBottom: "1px solid var(--border)",
          }}>
            {cat.category}
          </div>
          {cat.items.map(item => {
            const idx = itemIndex++;
            return <CheckItem key={item.id} item={item} index={idx} inView={inView} />;
          })}
        </div>
      ))}

      <div style={{ marginTop: 8, padding: "10px 14px", background: "rgba(255,255,255,0.02)", border: "1px solid var(--border)", borderRadius: 8, fontSize: 11, color: "var(--text-dim)", lineHeight: 1.7 }}>
        Criteria mapped to MSI (Metabolomics Standards Initiative) reporting levels. MSI Level 1 = minimum required for publication. Level 2 = recommended. Good Practice = strongly advised.
      </div>
    </div>
  );
}
