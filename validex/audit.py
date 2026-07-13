from __future__ import annotations

import json
import math
import os
from dataclasses import asdict, dataclass, field as dataclass_field
from enum import Enum
from typing import Any

import pandas as pd  # type: ignore[import-untyped]

from .ingestion import IngestionMetadata, ingest_csv_path
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
_INVALID_EVIDENCE_LIMIT = 20
_MISSING_TOKENS = {"", "na", "n/a", "null", "none", "missing", "."}


class NumericCellCategory(str, Enum):
    VALID_NUMERIC = "VALID_NUMERIC"
    MISSING = "MISSING"
    NONNUMERIC = "NONNUMERIC"
    NONFINITE = "NONFINITE"
    OUT_OF_RANGE = "OUT_OF_RANGE"


@dataclass
class NumericValidation:
    field: str
    column: str
    total_row_count: int
    valid_numeric_count: int = 0
    missing_count: int = 0
    nonnumeric_count: int = 0
    nonfinite_count: int = 0
    out_of_range_count: int = 0
    valid_fraction: float = 0.0
    evidence_limit: int = _INVALID_EVIDENCE_LIMIT
    invalid_evidence: list[dict[str, Any]] = dataclass_field(default_factory=list)

    @property
    def invalid_count(self) -> int:
        return self.nonnumeric_count + self.nonfinite_count + self.out_of_range_count

    def as_dict(self) -> dict[str, Any]:
        payload = asdict(self)
        payload["invalid_count"] = self.invalid_count
        return payload


# ---------------------------------------------------------------------------
# Value-level validators
# ---------------------------------------------------------------------------


def _coerce_numeric(df: pd.DataFrame, column: str) -> pd.Series:
    return pd.to_numeric(df[column], errors="coerce")


def _classify_probability_value(value: Any) -> tuple[NumericCellCategory, float | None]:
    if value is None:
        return NumericCellCategory.MISSING, None
    if isinstance(value, bool):
        return NumericCellCategory.NONNUMERIC, None
    if isinstance(value, float) and math.isnan(value):
        return NumericCellCategory.NONFINITE, None

    if isinstance(value, str):
        stripped = value.strip()
        if stripped.lower() in _MISSING_TOKENS:
            return NumericCellCategory.MISSING, None
        original = stripped
    else:
        original = value

    try:
        numeric = float(original)
    except (TypeError, ValueError):
        return NumericCellCategory.NONNUMERIC, None

    if not math.isfinite(numeric):
        return NumericCellCategory.NONFINITE, None
    if numeric < 0 or numeric > 1:
        return NumericCellCategory.OUT_OF_RANGE, numeric
    return NumericCellCategory.VALID_NUMERIC, numeric


def _append_invalid_evidence(
    validation: NumericValidation,
    row_index: int,
    value: Any,
    category: NumericCellCategory,
) -> None:
    if len(validation.invalid_evidence) >= validation.evidence_limit:
        return
    validation.invalid_evidence.append(
        {
            "row_number": row_index + 2,
            "column": validation.column,
            "original_value": str(value),
            "error_category": category.value,
        }
    )


def _validate_probability_column(
    df: pd.DataFrame,
    field: str,
    column: str,
    min_valid_fraction: float = 0.8,
) -> NumericValidation:
    """Classify every source cell in a probability column.

    The valid fraction is calculated over the full row count, not over pandas'
    coerced non-null subset. This prevents garbage rows from disappearing before
    score and confidence are computed.
    """
    validation = NumericValidation(
        field=field,
        column=column,
        total_row_count=int(len(df)),
    )
    if column not in df.columns:
        return validation

    for row_index, value in enumerate(df[column].tolist()):
        category, _numeric = _classify_probability_value(value)
        if category is NumericCellCategory.VALID_NUMERIC:
            validation.valid_numeric_count += 1
        elif category is NumericCellCategory.MISSING:
            validation.missing_count += 1
        elif category is NumericCellCategory.NONNUMERIC:
            validation.nonnumeric_count += 1
            _append_invalid_evidence(validation, row_index, value, category)
        elif category is NumericCellCategory.NONFINITE:
            validation.nonfinite_count += 1
            _append_invalid_evidence(validation, row_index, value, category)
        elif category is NumericCellCategory.OUT_OF_RANGE:
            validation.out_of_range_count += 1
            _append_invalid_evidence(validation, row_index, value, category)

    if validation.total_row_count:
        validation.valid_fraction = (
            validation.valid_numeric_count / validation.total_row_count
        )
    return validation


def _probability_column_is_usable(
    validation: NumericValidation, min_valid_fraction: float = 0.8
) -> bool:
    return (
        validation.total_row_count > 0
        and validation.valid_fraction >= min_valid_fraction
    )


def _validate_fdr_consistency(
    df: pd.DataFrame,
    p_col: str,
    fdr_col: str,
    min_valid_fraction: float = 0.8,
) -> bool:
    """Return True (no warning) when FDR >= p-value for at least min_valid_fraction of rows."""
    p_num = pd.to_numeric(df[p_col], errors="coerce")
    fdr_num = pd.to_numeric(df[fdr_col], errors="coerce")
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
    *,
    has_compound_id: bool,
    has_effect_size: bool,
    has_annotation: bool,
    has_duplicate_identifiers: bool,
    has_invalid_statistical_cells: bool,
    has_fdr_consistency_warning: bool,
    has_usable_data_rows: bool,
) -> str:
    """Return 'high', 'medium', or 'low' using explicit completeness gates.

    Rules (in priority order):
    - low: no usable rows or p_value missing/invalid.
    - medium: p_value valid but any trust/completeness limiter remains.
    - high: p_value and FDR valid, complete schema context, and no trust limiters.
    """
    if not has_usable_data_rows or p_col is None:
        return "low"
    if (
        fdr_col is None
        or ambiguous_critical
        or not has_compound_id
        or not has_effect_size
        or not has_annotation
        or has_duplicate_identifiers
        or has_invalid_statistical_cells
        or has_fdr_consistency_warning
    ):
        return "medium"
    return "high"


# ---------------------------------------------------------------------------
# Core audit logic
# ---------------------------------------------------------------------------


def audit_dataframe(
    df: pd.DataFrame,
    context: dict[str, Any] | None = None,
    metadata: IngestionMetadata | None = None,
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
    statistical_validation: dict[str, dict[str, Any]] = {}

    # ------------------------------------------------------------------
    # Value-level validation: p_value
    # ------------------------------------------------------------------
    p_col: str | None = p_col_raw
    if p_col_raw is not None:
        p_validation = _validate_probability_column(df, "p_value", p_col_raw)
        statistical_validation["p_value"] = p_validation.as_dict()
    else:
        p_validation = None
    if p_validation is not None and not _probability_column_is_usable(p_validation):
        p_col = None
        msg = (
            f"Column '{p_col_raw}' was detected as p-value but contains values "
            "outside [0, 1], nonfinite values, nonnumeric values, or too much missing data. "
            "It cannot be used as a valid p-value column."
        )
        interpretations.append(msg)
        flags.append(
            {
                "severity": "high",
                "title": "Invalid p-value column",
                "field": "p_value",
                "column": p_col_raw,
                "counts": p_validation.as_dict(),
                "why": msg,
                "fix": "Ensure the p-value column contains numeric probability values between 0 and 1.",
            }
        )
    elif p_validation is not None and p_validation.invalid_count > 0:
        msg = (
            f"Column '{p_col_raw}' contains invalid p-value cells. "
            "The column is still usable, but the invalid cells reduce audit trust."
        )
        confidence -= 10
        interpretations.append(msg)
        flags.append(
            {
                "severity": "medium",
                "title": "Invalid p-value cells",
                "field": "p_value",
                "column": p_col_raw,
                "counts": p_validation.as_dict(),
                "why": msg,
                "fix": "Correct or remove invalid p-value cells before interpreting significance.",
            }
        )

    # ------------------------------------------------------------------
    # Value-level validation: fdr
    # ------------------------------------------------------------------
    fdr_col: str | None = fdr_col_raw
    if fdr_col_raw is not None:
        fdr_validation = _validate_probability_column(df, "fdr", fdr_col_raw)
        statistical_validation["fdr"] = fdr_validation.as_dict()
    else:
        fdr_validation = None
    if fdr_validation is not None and not _probability_column_is_usable(fdr_validation):
        fdr_col = None
        msg = (
            f"Column '{fdr_col_raw}' was detected as FDR but contains values "
            "outside [0, 1], nonfinite values, nonnumeric values, or too much missing data. "
            "It cannot be used as a valid FDR column."
        )
        interpretations.append(msg)
        flags.append(
            {
                "severity": "high",
                "title": "Invalid FDR column",
                "field": "fdr",
                "column": fdr_col_raw,
                "counts": fdr_validation.as_dict(),
                "why": msg,
                "fix": "Ensure the FDR column contains numeric probability values between 0 and 1.",
            }
        )
    elif fdr_validation is not None and fdr_validation.invalid_count > 0:
        msg = (
            f"Column '{fdr_col_raw}' contains invalid FDR/q-value cells. "
            "The column is still usable, but the invalid cells reduce audit trust."
        )
        confidence -= 10
        interpretations.append(msg)
        flags.append(
            {
                "severity": "medium",
                "title": "Invalid FDR cells",
                "field": "fdr",
                "column": fdr_col_raw,
                "counts": fdr_validation.as_dict(),
                "why": msg,
                "fix": "Correct or remove invalid FDR/q-value cells before interpreting multiple-testing correction.",
            }
        )

    # ------------------------------------------------------------------
    # FDR consistency check (only when both are valid)
    # ------------------------------------------------------------------
    fdr_consistency_warning = False
    if p_col and fdr_col and not _validate_fdr_consistency(df, p_col, fdr_col):
        fdr_consistency_warning = True
        confidence -= 15
        msg = (
            f"FDR values in '{fdr_col}' are frequently smaller than p-values in '{p_col}'. "
            "This may indicate that p-value and FDR columns are swapped or miscalculated."
        )
        interpretations.append(msg)
        flags.append(
            {
                "severity": "med",
                "title": "FDR/p-value consistency warning",
                "why": msg,
                "fix": "Verify that FDR correction was applied correctly and that columns are not swapped.",
            }
        )

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
        flags.append(
            {
                "severity": severity,
                "title": f"Ambiguous {canonical} column",
                "field": canonical,
                "selected_column": chosen,
                "candidate_columns": ambig_cols,
                "why": msg,
                "fix": f"Rename columns to unambiguously identify the '{canonical}' field.",
            }
        )

        penalty = _AMBIGUITY_PENALTY.get(canonical, 0)
        ambiguity_penalty += penalty

    ambiguity_penalty = min(ambiguity_penalty, _MAX_AMBIGUITY_PENALTY)
    confidence -= ambiguity_penalty

    # ------------------------------------------------------------------
    # Completeness checks beyond minimum p/FDR auditability
    # ------------------------------------------------------------------
    completeness = {
        "minimum_auditability": bool(n_rows > 0 and p_col is not None),
        "statistical_completeness": bool(
            p_col is not None and fdr_col is not None and effect_col is not None
        ),
        "biological_interpretability": bool(
            compound_col is not None and annotation_col is not None
        ),
        "publication_readiness_claimed": False,
    }

    if n_rows == 0:
        confidence -= 50
        msg = "No usable data rows are available for auditing."
        interpretations.append(msg)
        flags.append(
            {
                "severity": "high",
                "title": "No usable data rows",
                "why": msg,
                "fix": "Provide a CSV containing at least one data row.",
            }
        )

    if compound_col is None:
        confidence -= 10
        msg = "No compound or feature identifier column was detected. Rows cannot be traced to unique analytes."
        interpretations.append(msg)
        flags.append(
            {
                "severity": "medium",
                "title": "Missing compound identifiers",
                "why": msg,
                "fix": "Add a stable compound, metabolite, or feature identifier column.",
            }
        )

    if effect_col is None:
        confidence -= 10
        msg = "No effect-size or fold-change column was detected. Magnitude of change cannot be assessed."
        interpretations.append(msg)
        flags.append(
            {
                "severity": "medium",
                "title": "Missing effect-size evidence",
                "why": msg,
                "fix": "Include an effect-size field such as fold change, log2 fold change, or a documented magnitude measure.",
            }
        )

    if annotation_col is None:
        confidence -= 5
        msg = (
            "No annotation column was detected. Biological interpretability is limited."
        )
        interpretations.append(msg)
        flags.append(
            {
                "severity": "low",
                "title": "Missing annotation evidence",
                "why": msg,
                "fix": "Include metabolite annotation or identification-confidence information where available.",
            }
        )

    duplicate_identifier_count = 0
    if compound_col is not None:
        identifiers = df[compound_col].astype("string").str.strip()
        usable_identifiers = identifiers[identifiers.notna() & (identifiers != "")]
        duplicated = usable_identifiers[usable_identifiers.duplicated(keep=False)]
        duplicate_identifier_count = int(duplicated.nunique())
        if duplicate_identifier_count:
            confidence -= 10
            examples = (
                duplicated.drop_duplicates().head(_INVALID_EVIDENCE_LIMIT).tolist()
            )
            msg = (
                f"Compound identifier column '{compound_col}' contains duplicate identifiers. "
                "Rows may not correspond to unique compounds or features."
            )
            interpretations.append(msg)
            flags.append(
                {
                    "severity": "medium",
                    "title": "Duplicate compound identifiers",
                    "field": "compound_id",
                    "column": compound_col,
                    "duplicate_identifier_count": duplicate_identifier_count,
                    "examples": examples,
                    "why": msg,
                    "fix": "Ensure each row has a stable unique feature or compound identifier, or add replicate grouping metadata.",
                }
            )

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
        recommendations.append(
            "Run a statistical test (e.g., t-test or ANOVA) to obtain p-values."
        )
        flags.append(
            {
                "severity": "high",
                "title": "Missing p-values",
                "why": msg,
                "fix": recommendations[-1],
            }
        )

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
        flags.append(
            {
                "severity": "high" if p_col is None else "med",
                "title": "Missing FDR / adjusted p-values",
                "why": msg,
                "fix": recommendations[-1],
            }
        )

    # ------------------------------------------------------------------
    # Both present and valid
    # ------------------------------------------------------------------
    if p_col and fdr_col:
        interpretations.append(
            "Both p-values and FDR-adjusted q-values are present, "
            "indicating statistically interpretable results."
        )

    confidence = max(confidence, 0)

    has_invalid_statistical_cells = any(
        stats.get("invalid_count", 0) > 0 for stats in statistical_validation.values()
    )
    audit_confidence = _compute_confidence_label(
        p_col,
        fdr_col,
        ambiguous_critical,
        has_compound_id=compound_col is not None,
        has_effect_size=effect_col is not None,
        has_annotation=annotation_col is not None,
        has_duplicate_identifiers=duplicate_identifier_count > 0,
        has_invalid_statistical_cells=has_invalid_statistical_cells,
        has_fdr_consistency_warning=fdr_consistency_warning,
        has_usable_data_rows=n_rows > 0,
    )

    result = {
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
        "statistical_validation": statistical_validation,
        "completeness": completeness,
    }
    if metadata is not None:
        result["ingestion"] = asdict(metadata)
    return result


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

    ingested = ingest_csv_path(csv_path)
    df = ingested.dataframe
    result = audit_dataframe(df, context, metadata=ingested.metadata)

    n_rows = result["n_rows"]
    n_cols = result["n_cols"]
    detected = result["detected"]
    confidence = result["confidence"]
    audit_confidence = result["audit_confidence"]
    interpretations = result["interpretations"]
    recommendations = result["recommendations"]
    flags = result["flags"]
    # Collect ambiguous fields and invalid fields for the report
    ambiguity_flags = [f for f in flags if "Ambiguous" in f.get("title", "")]
    invalid_flags = [f for f in flags if "Invalid" in f.get("title", "")]
    missing_flags = [f for f in flags if "Missing" in f.get("title", "")]

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

    md.extend(
        [
            "## Scientific Interpretation",
        ]
    )
    non_schema_interps = [
        i
        for i in interpretations
        if not any(kw in i for kw in ("Multiple columns matched", "Validex selected"))
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
    md.extend(
        [
            "\n## Overall Confidence Score",
            f"**{confidence} / 100** — Schema confidence: **{audit_confidence}**",
            "",
            "> *" + _DISCLAIMER + "*",
            "",
        ]
    )
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
                        "statistical_validation": result["statistical_validation"],
                        "completeness": result["completeness"],
                        "ingestion": result.get("ingestion"),
                    }
                },
                handle,
                allow_nan=False,
            )

    return report_text
