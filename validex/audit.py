from __future__ import annotations

import json
import os
from typing import Any

import pandas as pd

from .schema_mapper import detect_schema

# Canonical fields considered critical for ambiguity penalty purposes
_CRITICAL_FIELDS = {"compound_id", "effect_size", "p_value", "fdr"}
_ANNOTATION_FIELDS = {"annotation"}

# Ambiguity penalty per critical field (in score points)
_AMBIGUITY_PENALTY: dict[str, int] = {
    "compound_id": 5,
    "effect_size": 5,
    "p_value": 5,
    "fdr": 5,
    "annotation": 3,
}
_MAX_AMBIGUITY_PENALTY = 15


# ---------------------------------------------------------------------------
# Value-level validators
# ---------------------------------------------------------------------------

def _coerce_numeric(df: pd.DataFrame, column: str) -> pd.Series:
    return pd.to_numeric(df[column], errors="coerce")


def _validate_probability_column(
    df: pd.DataFrame,
    column: str,
    min_valid_fraction: float = 0.8,
) -> bool:
    """Return True if >=min_valid_fraction of non-missing values are in [0, 1]."""
    if column not in df.columns:
        return False
    numeric = _coerce_numeric(df, column)
    non_missing = numeric.dropna()
    if len(non_missing) == 0:
        return False
    in_range = (non_missing >= 0) & (non_missing <= 1)
    return float(in_range.sum()) / len(non_missing) >= min_valid_fraction


def _validate_fdr_consistency(
    df: pd.DataFrame,
    p_col: str,
    fdr_col: str,
    min_valid_fraction: float = 0.8,
) -> bool:
    """Return True (no warning) when FDR >= p-value for at least min_valid_fraction of rows."""
    p_num = _coerce_numeric(df, p_col)
    fdr_num = _coerce_numeric(df, fdr_col)
    both_valid = p_num.notna() & fdr_num.notna()
    n = int(both_valid.sum())
    if n == 0:
        return True
    fdr_ge_p = int((fdr_num[both_valid] >= p_num[both_valid]).sum())
    return fdr_ge_p / n >= min_valid_fraction


# ---------------------------------------------------------------------------
# Confidence label
# ---------------------------------------------------------------------------

def _compute_confidence_label(
    p_col: str | None,
    fdr_col: str | None,
    ambiguous_critical: set[str],
) -> str:
    """Return 'high', 'medium', or 'low' based on field completeness and ambiguity.

    Rules (in priority order):
    - low  : p_value missing or invalid (None), regardless of other fields
    - medium: p_value valid but fdr missing/invalid, OR any critical field ambiguous
    - high : p_value valid, fdr valid, no critical field ambiguous
    """
    if p_col is None:
        return "low"
    if fdr_col is None or ambiguous_critical:
        return "medium"
    return "high"


# ---------------------------------------------------------------------------
# Core audit logic
# ---------------------------------------------------------------------------

def audit_dataframe(
    df: pd.DataFrame,
    context: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Run the full audit on a DataFrame. Returns a structured result dict."""
    n_rows, n_cols = df.shape
    schema = detect_schema(df.columns)

    compound_col = schema.canonical_to_original.get("compound_id")
    effect_col = schema.canonical_to_original.get("effect_size")
    p_col_raw = schema.canonical_to_original.get("p_value")
    fdr_col_raw = schema.canonical_to_original.get("fdr")
    annotation_col = schema.canonical_to_original.get("annotation")

    confidence = 100
    interpretations: list[str] = []
    recommendations: list[str] = []
    flags: list[dict[str, Any]] = []

    # ------------------------------------------------------------------
    # Value-level validation: p_value
    # ------------------------------------------------------------------
    p_col: str | None = p_col_raw
    if p_col_raw is not None and not _validate_probability_column(df, p_col_raw):
        p_col = None
        msg = (
            f"Column '{p_col_raw}' was detected as p-value but contains values "
            "outside [0, 1] or is not numeric. It cannot be used as a valid p-value column."
        )
        interpretations.append(msg)
        flags.append({
            "severity": "high",
            "title": "Invalid p-value column",
            "why": msg,
            "fix": "Ensure the p-value column contains numeric probability values between 0 and 1.",
        })

    # ------------------------------------------------------------------
    # Value-level validation: fdr
    # ------------------------------------------------------------------
    fdr_col: str | None = fdr_col_raw
    if fdr_col_raw is not None and not _validate_probability_column(df, fdr_col_raw):
        fdr_col = None
        msg = (
            f"Column '{fdr_col_raw}' was detected as FDR but contains values "
            "outside [0, 1] or is not numeric. It cannot be used as a valid FDR column."
        )
        interpretations.append(msg)
        flags.append({
            "severity": "high",
            "title": "Invalid FDR column",
            "why": msg,
            "fix": "Ensure the FDR column contains numeric probability values between 0 and 1.",
        })

    # ------------------------------------------------------------------
    # FDR consistency check (only when both are valid)
    # ------------------------------------------------------------------
    if p_col and fdr_col and not _validate_fdr_consistency(df, p_col, fdr_col):
        msg = (
            f"FDR values in '{fdr_col}' are frequently smaller than p-values in '{p_col}'. "
            "This may indicate that p-value and FDR columns are swapped or miscalculated."
        )
        interpretations.append(msg)
        flags.append({
            "severity": "med",
            "title": "FDR/p-value consistency warning",
            "why": msg,
            "fix": "Verify that FDR correction was applied correctly and that columns are not swapped.",
        })

    # ------------------------------------------------------------------
    # Ambiguity findings
    # ------------------------------------------------------------------
    ambiguous_critical: set[str] = set()
    ambiguity_penalty = 0

    for canonical, ambig_cols in schema.ambiguities.items():
        chosen = schema.canonical_to_original[canonical]
        is_critical = canonical in _CRITICAL_FIELDS

        if is_critical:
            ambiguous_critical.add(canonical)
            severity = "medium"
        else:
            severity = "low"

        msg = (
            f"Multiple columns matched '{canonical}': {ambig_cols}. "
            f"Validex selected '{chosen}' deterministically. "
            "Review the table manually to confirm the intended column."
        )
        interpretations.append(msg)
        flags.append({
            "severity": severity,
            "title": f"Ambiguous {canonical} column",
            "field": canonical,
            "selected_column": chosen,
            "candidate_columns": ambig_cols,
            "why": msg,
            "fix": f"Rename columns to unambiguously identify the '{canonical}' field.",
        })

        penalty = _AMBIGUITY_PENALTY.get(canonical, 0)
        ambiguity_penalty += penalty

    ambiguity_penalty = min(ambiguity_penalty, _MAX_AMBIGUITY_PENALTY)
    confidence -= ambiguity_penalty

    # ------------------------------------------------------------------
    # Missing p-value finding
    # ------------------------------------------------------------------
    if p_col is None:
        confidence -= 40
        if effect_col:
            msg = (
                "Fold-change values are present without corresponding p-values. "
                "Statistical significance cannot be assessed."
            )
        else:
            msg = "No p-value column was detected. Statistical significance cannot be assessed."
        interpretations.append(msg)
        recommendations.append("Run a statistical test (e.g., t-test or ANOVA) to obtain p-values.")
        flags.append({
            "severity": "high",
            "title": "Missing p-values",
            "why": msg,
            "fix": recommendations[-1],
        })

    # ------------------------------------------------------------------
    # Missing FDR finding
    # ------------------------------------------------------------------
    if fdr_col is None:
        confidence -= 20
        if p_col:
            msg = (
                "P-values are present without FDR/q-values. "
                "This increases false positive risk in high-dimensional data."
            )
            recommendations.append(
                "Apply FDR correction (e.g., Benjamini-Hochberg) to control multiple comparisons."
            )
        else:
            msg = (
                "No FDR or adjusted p-value column was detected. "
                "Multiple-testing correction status is unknown."
            )
            recommendations.append("Apply FDR correction after obtaining p-values.")
        interpretations.append(msg)
        flags.append({
            "severity": "high" if p_col is None else "med",
            "title": "Missing FDR / adjusted p-values",
            "why": msg,
            "fix": recommendations[-1],
        })

    # ------------------------------------------------------------------
    # Both present and valid
    # ------------------------------------------------------------------
    if p_col and fdr_col:
        interpretations.append(
            "Both p-values and FDR-adjusted q-values are present, "
            "indicating statistically interpretable results."
        )

    confidence = max(confidence, 0)

    audit_confidence = _compute_confidence_label(p_col, fdr_col, ambiguous_critical)

    return {
        "n_rows": n_rows,
        "n_cols": n_cols,
        "schema": schema,
        "detected": {
            "compound_id": compound_col,
            "effect_size": effect_col,
            "p_value": p_col,
            "fdr": fdr_col,
            "annotation": annotation_col,
        },
        "confidence": confidence,
        "audit_confidence": audit_confidence,
        "interpretations": interpretations,
        "recommendations": recommendations,
        "flags": flags,
    }


# ---------------------------------------------------------------------------
# File-based entry point (CLI and server)
# ---------------------------------------------------------------------------

_DISCLAIMER = (
    "Validex audits downstream reporting completeness and table interpretability. "
    "It does not validate biological truth, upstream preprocessing correctness, "
    "experimental design quality, or metabolite identification certainty."
)


def run_audit(
    csv_path: str,
    report_path: str,
    json_path: str | None = None,
    context: dict[str, Any] | None = None,
) -> str:
    if not os.path.exists(csv_path):
        raise FileNotFoundError("Input CSV not found: " + csv_path)

    df = pd.read_csv(csv_path)
    result = audit_dataframe(df, context)

    n_rows = result["n_rows"]
    n_cols = result["n_cols"]
    detected = result["detected"]
    confidence = result["confidence"]
    audit_confidence = result["audit_confidence"]
    interpretations = result["interpretations"]
    recommendations = result["recommendations"]
    flags = result["flags"]
    schema = result["schema"]

    # Collect ambiguous fields and invalid fields for the report
    ambiguity_flags = [
        f for f in flags
        if "Ambiguous" in f.get("title", "")
    ]
    invalid_flags = [
        f for f in flags
        if "Invalid" in f.get("title", "")
    ]
    missing_flags = [
        f for f in flags
        if "Missing" in f.get("title", "")
    ]

    md = [
        "# Metabolomics Validity Report\n",
        "## Dataset Overview",
        f"- Number of features (rows): {n_rows}",
        f"- Number of columns: {n_cols}\n",
        "## Detected Schema",
        f"- Compound identifier: {detected['compound_id']}",
        f"- Effect size / fold change: {detected['effect_size']}",
        f"- p-value: {detected['p_value']}",
        f"- FDR / q-value: {detected['fdr']}",
        f"- Annotation: {detected['annotation']}\n",
    ]

    if ambiguity_flags:
        md.append("## Ambiguous Schema Fields")
        for f in ambiguity_flags:
            selected = f.get("selected_column", "unknown")
            candidates = f.get("candidate_columns", [])
            md.append(
                f"- **{f['field']}**: multiple columns matched ({candidates}). "
                f"Selected '{selected}' for audit. Review manually."
            )
        md.append("")

    if invalid_flags:
        md.append("## Invalid Statistical Columns")
        for f in invalid_flags:
            md.append(f"- {f['title']}: {f['why']}")
        md.append("")

    if missing_flags:
        md.append("## Missing Critical Fields")
        for f in missing_flags:
            md.append(f"- {f['title']}: {f['why']}")
        md.append("")

    md.extend([
        "## Scientific Interpretation",
    ])
    non_schema_interps = [
        i for i in interpretations
        if not any(
            kw in i for kw in ("Multiple columns matched", "Validex selected")
        )
    ]
    md.extend(
        [f"- {item}" for item in non_schema_interps]
        or ["- No major statistical issues detected."]
    )
    md.append("\n## Recommendations")
    md.extend(
        [f"- {item}" for item in recommendations]
        or ["- No immediate corrective actions required."]
    )
    md.extend([
        "\n## Overall Confidence Score",
        f"**{confidence} / 100** — Schema confidence: **{audit_confidence}**",
        "",
        "> *" + _DISCLAIMER + "*",
        "",
    ])
    report_text = "\n".join(md)

    report_dir = os.path.dirname(report_path)
    if report_dir:
        os.makedirs(report_dir, exist_ok=True)
    with open(report_path, "w", encoding="utf-8") as handle:
        handle.write(report_text)

    if json_path:
        json_dir = os.path.dirname(json_path)
        if json_dir:
            os.makedirs(json_dir, exist_ok=True)
        with open(json_path, "w", encoding="utf-8") as handle:
            json.dump(
                {
                    "analysis": {
                        "confidence": confidence,
                        "audit_confidence": audit_confidence,
                        "flags": flags,
                        "interpretations": interpretations,
                        "recommendations": recommendations,
                    }
                },
                handle,
            )

    return report_text
