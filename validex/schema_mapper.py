from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple

import pandas as pd

KNOWN_ALIASES: Dict[str, List[str]] = {
    "p_value": ["p", "pval", "pvalue", "p-value", "p.val", "p_value", "p value"],
    "fdr": ["fdr", "q", "qval", "qvalue", "q-value", "adj.p", "padj", "adj_p", "q value"],
    "fold_change": ["fc", "fold", "foldchange", "fold_change", "fold change", "logfc", "log2fc", "log2(fc)", "log2 fc"],
}


def _norm_header(value: str) -> str:
    value = value.strip().lower()
    value = value.replace("-", "_").replace(" ", "_").replace("/", "_")
    value = re.sub(r"[^\w]+", "_", value)
    return re.sub(r"_+", "_", value).strip("_")


@dataclass
class SchemaMap:
    canonical_to_original: Dict[str, str]
    canonical_to_normed: Dict[str, str]
    ambiguities: Dict[str, List[str]]
    missing: List[str]

    def rename_df(self, df: pd.DataFrame) -> pd.DataFrame:
        rename_map = {orig: canon for canon, orig in self.canonical_to_original.items()}
        return df.rename(columns=rename_map).copy()


def detect_schema(df: pd.DataFrame, aliases: Optional[Dict[str, List[str]]] = None) -> SchemaMap:
    aliases = aliases or KNOWN_ALIASES
    normed_to_originals: Dict[str, List[str]] = {}
    for column in df.columns:
        normed_to_originals.setdefault(_norm_header(str(column)), []).append(str(column))

    canonical_to_original: Dict[str, str] = {}
    canonical_to_normed: Dict[str, str] = {}
    ambiguities: Dict[str, List[str]] = {}
    missing: List[str] = []

    for canonical, alias_list in aliases.items():
        matched_originals: List[str] = []
        for alias in [canonical] + list(alias_list):
            matched_originals.extend(normed_to_originals.get(_norm_header(alias), []))

        seen = set()
        matched_originals = [item for item in matched_originals if not (item in seen or seen.add(item))]

        if not matched_originals:
            missing.append(canonical)
            continue
        if len(matched_originals) > 1:
            ambiguities[canonical] = matched_originals

        canonical_to_original[canonical] = matched_originals[0]
        canonical_to_normed[canonical] = _norm_header(matched_originals[0])

    return SchemaMap(canonical_to_original, canonical_to_normed, ambiguities, missing)


def normalize_columns(df: pd.DataFrame) -> Dict[str, str]:
    return detect_schema(df).canonical_to_original


def apply_canonical_schema(df: pd.DataFrame) -> Tuple[pd.DataFrame, SchemaMap]:
    sm = detect_schema(df)
    return sm.rename_df(df), sm
