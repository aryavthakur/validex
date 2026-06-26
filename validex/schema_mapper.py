from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Dict, Iterable, List, Optional, Tuple

import pandas as pd

KNOWN_ALIASES: Dict[str, List[str]] = {
    "compound_id": [
        "compound_id",
        "compound",
        "compound_name",
        "metabolite",
        "metabolite_name",
        "feature",
        "feature_id",
        "feature_name",
        "mz_rt",
    ],
    "effect_size": [
        "logfc",
        "log_fc",
        "log2fc",
        "log2_fc",
        "log2_fold_change",
        "fold_change",
        "fc",
        "effect_size",
        "estimate",
        "coefficient",
    ],
    "p_value": [
        "p_value",
        "pvalue",
        "p_val",
        "pval",
        "p",
        "raw_p",
        "raw_p_value",
        "raw_pval",
        "p_adjusted_input",
        "nominal_p",
        "pvalue_raw",
    ],
    "fdr": [
        "fdr",
        "q_value",
        "qvalue",
        "q_val",
        "qval",
        "adjusted_p",
        "adjusted_p_value",
        "adj_p",
        "adj_p_value",
        "p_adj",
        "padj",
        "p_adjust",
        "p_adjusted",
        "p_adjusted_value",
        "bh_p",
        "benjamini_hochberg",
        "false_discovery_rate",
    ],
    "annotation": [
        "annotation",
        "annotations",
        "id_level",
        "identification_level",
        "msi_level",
        "confidence",
        "confidence_level",
        "identification_confidence",
        "metabolite_identification",
        "putative_id",
    ],
}


def normalize_header(header: str) -> str:
    """Normalize a column header for strict alias matching.

    Steps:
    1. Strip surrounding whitespace.
    2. Convert to lowercase.
    3. Replace spaces, hyphens, periods, slashes, and repeated separators with underscores.
    4. Remove unsupported punctuation.
    5. Collapse repeated underscores.
    6. Strip leading and trailing underscores.
    """
    value = str(header).strip().lower()
    value = re.sub(r"[ \-./]+", "_", value)
    value = re.sub(r"[^\w]+", "_", value)
    value = re.sub(r"_+", "_", value).strip("_")
    return value


# Keep old private name for any internal callers
_norm_header = normalize_header


@dataclass
class SchemaMap:
    """Result of schema detection."""

    canonical_to_original: Dict[str, str]
    canonical_to_normed: Dict[str, str]
    ambiguities: Dict[str, List[str]]
    missing: List[str]

    def rename_df(self, df: pd.DataFrame) -> pd.DataFrame:
        """Return a copy of df with matched columns renamed to canonical names."""
        rename_map = {orig: canon for canon, orig in self.canonical_to_original.items()}
        return df.rename(columns=rename_map).copy()


def detect_schema(
    columns: Iterable[str],
    aliases: Optional[Dict[str, List[str]]] = None,
) -> SchemaMap:
    """Detect canonical fields from an iterable of column names.

    Matching uses exact alias lookup after normalization — no substring matching.
    A column named 'compound_id' or 'pathway' will never match 'p_value'
    merely because they contain the letter 'p'.
    """
    aliases = aliases or KNOWN_ALIASES

    normed_to_originals: Dict[str, List[str]] = {}
    for col in columns:
        key = normalize_header(str(col))
        normed_to_originals.setdefault(key, []).append(str(col))

    canonical_to_original: Dict[str, str] = {}
    canonical_to_normed: Dict[str, str] = {}
    ambiguities: Dict[str, List[str]] = {}
    missing: List[str] = []

    for canonical, alias_list in aliases.items():
        candidates = [canonical] + list(alias_list)

        matched_originals: List[str] = []
        for alias in candidates:
            alias_norm = normalize_header(alias)
            matched_originals.extend(normed_to_originals.get(alias_norm, []))

        seen: set = set()
        matched_originals = [x for x in matched_originals if not (x in seen or seen.add(x))]  # type: ignore[func-returns-value]

        if not matched_originals:
            missing.append(canonical)
            continue

        if len(matched_originals) > 1:
            ambiguities[canonical] = matched_originals

        canonical_to_original[canonical] = matched_originals[0]
        canonical_to_normed[canonical] = normalize_header(matched_originals[0])

    return SchemaMap(
        canonical_to_original=canonical_to_original,
        canonical_to_normed=canonical_to_normed,
        ambiguities=ambiguities,
        missing=missing,
    )


def normalize_columns(df: pd.DataFrame) -> Dict[str, str]:
    """Backward-compatible API: returns canonical -> original column mapping."""
    return detect_schema(df.columns).canonical_to_original


def apply_canonical_schema(df: pd.DataFrame) -> Tuple[pd.DataFrame, SchemaMap]:
    """Convenience helper: detects schema and returns (renamed_df, schema_map)."""
    sm = detect_schema(df.columns)
    return sm.rename_df(df), sm
