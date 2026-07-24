from __future__ import annotations

import re
from dataclasses import asdict, dataclass
from typing import Any, Dict, Iterable, List, Optional, Tuple

import pandas as pd  # type: ignore[import-untyped]

@dataclass(frozen=True)
class AliasDefinition:
    alias: str
    field: str
    rationale: str
    risk: str = "low"
    match_rule: str = "exact"
    deprecated: bool = False


ALIAS_REGISTRY_VERSION = "validex-alias-registry-v0.2.0"


ALIAS_DEFINITIONS: list[AliasDefinition] = [
    AliasDefinition("compound_id", "compound_id", "Canonical compound identifier."),
    AliasDefinition("compound", "compound_id", "Common shorthand for compound identifier."),
    AliasDefinition("compound_name", "compound_id", "Compound-name identifier column."),
    AliasDefinition("metabolite", "compound_id", "Common metabolite identifier column."),
    AliasDefinition("metabolite_name", "compound_id", "Metabolite-name identifier column."),
    AliasDefinition("feature", "compound_id", "Feature identifier shorthand."),
    AliasDefinition("feature_id", "compound_id", "Stable feature identifier."),
    AliasDefinition("feature_name", "compound_id", "Feature-name identifier column."),
    AliasDefinition("mz_rt", "compound_id", "Mass-retention-time feature identifier."),
    AliasDefinition("analyte_token", "compound_id", "General analyte identifier token.", "medium"),
    AliasDefinition("logfc", "effect_size", "Common log fold-change shorthand."),
    AliasDefinition("log_fc", "effect_size", "Common log fold-change shorthand."),
    AliasDefinition("log2fc", "effect_size", "Common log2 fold-change shorthand."),
    AliasDefinition("log2_fc", "effect_size", "Common log2 fold-change shorthand."),
    AliasDefinition("log2_fold_change", "effect_size", "Canonical log2 fold-change field."),
    AliasDefinition("fold_change", "effect_size", "Fold-change magnitude field."),
    AliasDefinition("fc", "effect_size", "Fold-change abbreviation.", "medium"),
    AliasDefinition("effect_size", "effect_size", "Canonical effect-size field."),
    AliasDefinition("estimate", "effect_size", "Model estimate used as effect magnitude.", "medium"),
    AliasDefinition("coefficient", "effect_size", "Model coefficient used as effect magnitude.", "medium"),
    AliasDefinition("delta_abundance", "effect_size", "Differential abundance magnitude.", "medium"),
    AliasDefinition("p_value", "p_value", "Canonical raw p-value field."),
    AliasDefinition("pvalue", "p_value", "Common raw p-value variant."),
    AliasDefinition("p_val", "p_value", "Common raw p-value abbreviation."),
    AliasDefinition("pval", "p_value", "Common raw p-value abbreviation."),
    AliasDefinition("p", "p_value", "Short raw p-value label.", "high"),
    AliasDefinition("raw_p", "p_value", "Raw p-value label."),
    AliasDefinition("raw_p_value", "p_value", "Raw p-value label."),
    AliasDefinition("raw_pval", "p_value", "Raw p-value label."),
    AliasDefinition("p_adjusted_input", "p_value", "Raw p-value input to adjustment.", "medium"),
    AliasDefinition("nominal_p", "p_value", "Nominal unadjusted p-value."),
    AliasDefinition("pvalue_raw", "p_value", "Raw p-value label."),
    AliasDefinition("nominal_probability", "p_value", "Nominal probability value used as raw p-value.", "medium"),
    AliasDefinition("fdr", "fdr", "Canonical false-discovery-rate field."),
    AliasDefinition("q_value", "fdr", "Common adjusted p-value/q-value field."),
    AliasDefinition("qvalue", "fdr", "Common adjusted p-value/q-value field."),
    AliasDefinition("q_val", "fdr", "Common adjusted p-value/q-value field."),
    AliasDefinition("qval", "fdr", "Common adjusted p-value/q-value field."),
    AliasDefinition("adjusted_p", "fdr", "Adjusted p-value field."),
    AliasDefinition("adjusted_p_value", "fdr", "Adjusted p-value field."),
    AliasDefinition("adj_p", "fdr", "Adjusted p-value abbreviation."),
    AliasDefinition("adj_p_value", "fdr", "Adjusted p-value abbreviation."),
    AliasDefinition("p_adj", "fdr", "Adjusted p-value abbreviation."),
    AliasDefinition("padj", "fdr", "Adjusted p-value abbreviation."),
    AliasDefinition("p_adjust", "fdr", "Adjusted p-value field."),
    AliasDefinition("p_adjusted", "fdr", "Adjusted p-value field."),
    AliasDefinition("p_adjusted_value", "fdr", "Adjusted p-value field."),
    AliasDefinition("fdr_adjusted_p_value", "fdr", "FDR-adjusted p-value field."),
    AliasDefinition("bh_p", "fdr", "Benjamini-Hochberg adjusted p-value.", "medium"),
    AliasDefinition("benjamini_hochberg", "fdr", "Benjamini-Hochberg adjusted p-value.", "medium"),
    AliasDefinition("false_discovery_rate", "fdr", "Expanded FDR field name."),
    AliasDefinition("corrected_probability", "fdr", "Multiple-testing corrected probability.", "medium"),
    AliasDefinition("annotation", "annotation", "Canonical annotation evidence field."),
    AliasDefinition("annotations", "annotation", "Canonical annotation evidence field."),
    AliasDefinition("annotation_level", "annotation", "Identification or annotation level field."),
    AliasDefinition("id_level", "annotation", "Identification level field."),
    AliasDefinition("identification_level", "annotation", "Identification level field."),
    AliasDefinition("msi_level", "annotation", "MSI identification confidence level."),
    AliasDefinition("identification_confidence", "annotation", "Identification-specific confidence field.", "medium"),
    AliasDefinition("metabolite_identification", "annotation", "Metabolite identification evidence field."),
    AliasDefinition("putative_id", "annotation", "Putative identification evidence field."),
    AliasDefinition("identity_evidence", "annotation", "Identification evidence field.", "medium"),
    AliasDefinition("library_match", "annotation", "Spectral library match evidence."),
    AliasDefinition("spectral_evidence", "annotation", "Spectral evidence for identification."),
    AliasDefinition("match_score", "annotation", "Identification match score.", "medium"),
]


def _registry_to_aliases() -> Dict[str, List[str]]:
    aliases: Dict[str, List[str]] = {}
    for definition in ALIAS_DEFINITIONS:
        if definition.deprecated:
            continue
        aliases.setdefault(definition.field, []).append(definition.alias)
    return aliases


KNOWN_ALIASES: Dict[str, List[str]] = _registry_to_aliases()

LEGACY_KNOWN_ALIASES: Dict[str, List[str]] = {
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
        "fdr_adjusted_p_value",
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
        "main_class",
        "sub_class",
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
class SchemaCandidate:
    field: str
    column: str
    normalized_column: str
    alias: str
    match_rule: str
    rationale: str
    risk: str
    selected: bool = False
    selection_reason: str | None = None

    def as_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class SchemaMap:
    """Result of schema detection."""

    canonical_to_original: Dict[str, str | None]
    canonical_to_normed: Dict[str, str | None]
    ambiguities: Dict[str, List[str]]
    missing: List[str]
    candidates: Dict[str, List[SchemaCandidate]]
    ambiguity_status: Dict[str, str]
    selection_reasons: Dict[str, str]
    rejected_candidates: Dict[str, List[dict[str, str]]]
    alias_registry_version: str = ALIAS_REGISTRY_VERSION

    def rename_df(self, df: pd.DataFrame) -> pd.DataFrame:
        """Return a copy of df with matched columns renamed to canonical names."""
        rename_map = {
            orig: canon
            for canon, orig in self.canonical_to_original.items()
            if orig is not None
        }
        return df.rename(columns=rename_map).copy()


_ANNOTATION_REJECT_PATTERNS = [
    (re.compile(r"^(main|sub)_class$"), "class taxonomy is not identification evidence"),
    (re.compile(r".*_class$"), "class taxonomy is not identification evidence"),
    (re.compile(r"^(model|classification)_confidence$"), "model/classification confidence is not identification evidence"),
    (re.compile(r"^confidence(_level)?$"), "generic confidence is not identification evidence"),
    (re.compile(r".*pathway.*"), "pathway description is not identification evidence"),
    (re.compile(r"sample_annotation"), "sample annotation is not compound identification evidence"),
]


def _rejection_reason(field: str, normalized_header: str) -> str | None:
    if field != "annotation":
        return None
    for pattern, reason in _ANNOTATION_REJECT_PATTERNS:
        if pattern.fullmatch(normalized_header):
            return reason
    return None


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
    definitions_by_field_alias: dict[tuple[str, str], AliasDefinition] = {
        (definition.field, normalize_header(definition.alias)): definition
        for definition in ALIAS_DEFINITIONS
        if not definition.deprecated
    }

    normed_to_originals: Dict[str, List[str]] = {}
    for col in columns:
        key = normalize_header(str(col))
        normed_to_originals.setdefault(key, []).append(str(col))

    canonical_to_original: Dict[str, str | None] = {}
    canonical_to_normed: Dict[str, str | None] = {}
    ambiguities: Dict[str, List[str]] = {}
    missing: List[str] = []
    candidates_by_field: Dict[str, List[SchemaCandidate]] = {}
    ambiguity_status: Dict[str, str] = {}
    selection_reasons: Dict[str, str] = {}
    rejected_candidates: Dict[str, List[dict[str, str]]] = {}

    for canonical, alias_list in aliases.items():
        if canonical == "annotation":
            for normed_header, originals in normed_to_originals.items():
                rejected_reason = _rejection_reason(canonical, normed_header)
                if rejected_reason:
                    for original in originals:
                        rejected_candidates.setdefault(canonical, []).append(
                            {"column": original, "reason": rejected_reason}
                        )
        candidates = [canonical] + list(alias_list)

        matched_candidates: List[SchemaCandidate] = []
        for alias in candidates:
            alias_norm = normalize_header(alias)
            definition = definitions_by_field_alias.get(
                (canonical, alias_norm),
                AliasDefinition(alias_norm, canonical, "Caller-supplied alias.", "medium"),
            )
            for original in normed_to_originals.get(alias_norm, []):
                rejected_reason = _rejection_reason(canonical, alias_norm)
                if rejected_reason:
                    rejected_candidates.setdefault(canonical, []).append(
                        {"column": original, "reason": rejected_reason}
                    )
                    continue
                matched_candidates.append(
                    SchemaCandidate(
                        field=canonical,
                        column=original,
                        normalized_column=normalize_header(original),
                        alias=alias_norm,
                        match_rule=definition.match_rule,
                        rationale=definition.rationale,
                        risk=definition.risk,
                    )
                )

        seen: set[str] = set()
        deduped_candidates: list[SchemaCandidate] = []
        for candidate in matched_candidates:
            if candidate.column in seen:
                continue
            seen.add(candidate.column)
            deduped_candidates.append(candidate)
        matched_candidates = deduped_candidates
        candidates_by_field[canonical] = matched_candidates

        if not matched_candidates:
            missing.append(canonical)
            ambiguity_status[canonical] = "no_valid_candidate"
            continue

        selected: SchemaCandidate | None = None
        reason = ""
        canonical_norm = normalize_header(canonical)
        canonical_matches = [
            candidate for candidate in matched_candidates if candidate.alias == canonical_norm
        ]
        if len(matched_candidates) == 1:
            selected = matched_candidates[0]
            reason = "single_valid_candidate"
            ambiguity_status[canonical] = "one_valid_candidate"
        elif canonical_matches:
            selected = canonical_matches[0]
            reason = "canonical_header_preferred"
            ambiguity_status[canonical] = "multiple_valid_preferred"
        elif canonical == "annotation":
            reason = "multiple_valid_no_defensible_preference"
            ambiguity_status[canonical] = "multiple_valid_no_preference"
        else:
            selected = matched_candidates[0]
            reason = "first_registered_alias_preferred"
            ambiguity_status[canonical] = "multiple_valid_preferred"

        if len(matched_candidates) > 1:
            ambiguities[canonical] = [candidate.column for candidate in matched_candidates]

        if selected is not None:
            selected.selected = True
            selected.selection_reason = reason
            canonical_to_original[canonical] = selected.column
            canonical_to_normed[canonical] = selected.normalized_column
        else:
            canonical_to_original[canonical] = None
            canonical_to_normed[canonical] = None
            missing.append(canonical)
        selection_reasons[canonical] = reason

    return SchemaMap(
        canonical_to_original=canonical_to_original,
        canonical_to_normed=canonical_to_normed,
        ambiguities=ambiguities,
        missing=missing,
        candidates=candidates_by_field,
        ambiguity_status=ambiguity_status,
        selection_reasons=selection_reasons,
        rejected_candidates=rejected_candidates,
    )


def normalize_columns(df: pd.DataFrame) -> Dict[str, str]:
    """Backward-compatible API: returns canonical -> original column mapping."""
    return detect_schema(df.columns).canonical_to_original


def apply_canonical_schema(df: pd.DataFrame) -> Tuple[pd.DataFrame, SchemaMap]:
    """Convenience helper: detects schema and returns (renamed_df, schema_map)."""
    sm = detect_schema(df.columns)
    return sm.rename_df(df), sm
