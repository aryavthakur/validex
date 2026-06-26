"""Regression tests for strict alias-based schema detection.

Group A: False positive prevention — columns that must never match the wrong field.
Group B: Valid alias coverage — columns that must match their canonical field.
Group C: Flagship Dataset C schema-level detection.
"""
from __future__ import annotations

import pytest
import pandas as pd

from validex.schema_mapper import detect_schema, normalize_header


# ---------------------------------------------------------------------------
# Group A: False positive prevention
# ---------------------------------------------------------------------------

class TestFalsePositives:
    """No column should be misidentified merely because it contains a short substring."""

    @pytest.mark.parametrize("col", [
        "compound_id",
        "sample",
        "pathway",
        "platform",
        "phenotype",
        "replicate",
    ])
    def test_column_not_detected_as_p_value(self, col):
        sm = detect_schema([col, "logFC"])
        assert "p_value" not in sm.canonical_to_original, (
            f"'{col}' was incorrectly detected as p_value"
        )

    @pytest.mark.parametrize("col", [
        "quant",
        "request",
        "quality",
        "acquisition",
        "adjacent",
    ])
    def test_column_not_detected_as_fdr(self, col):
        sm = detect_schema([col, "logFC"])
        assert "fdr" not in sm.canonical_to_original, (
            f"'{col}' was incorrectly detected as fdr"
        )


# ---------------------------------------------------------------------------
# Group B: Valid alias coverage
# ---------------------------------------------------------------------------

class TestValidAliases:
    """Columns with recognised aliases must map to the correct canonical field."""

    @pytest.mark.parametrize("col,expected", [
        ("p_value", "p_value"),
        ("p value", "p value"),    # space-separated
        ("P.Value", "P.Value"),    # dot-separated, mixed case
        ("pval", "pval"),
        ("raw_p", "raw_p"),
        ("pvalue", "pvalue"),
        ("nominal_p", "nominal_p"),
    ])
    def test_p_value_aliases(self, col, expected):
        sm = detect_schema([col])
        assert sm.canonical_to_original.get("p_value") == expected

    @pytest.mark.parametrize("col,expected", [
        ("FDR", "FDR"),
        ("q_value", "q_value"),
        ("padj", "padj"),
        ("adjusted_p", "adjusted_p"),
        ("p.adjust", "p.adjust"),   # period normalises to underscore → p_adjust
        ("adj_p", "adj_p"),
        ("p_adj", "p_adj"),
    ])
    def test_fdr_aliases(self, col, expected):
        sm = detect_schema([col])
        assert sm.canonical_to_original.get("fdr") == expected


# ---------------------------------------------------------------------------
# Group C: Flagship Dataset C — schema detection
# ---------------------------------------------------------------------------

class TestDatasetCSchema:
    """compound_id, logFC, Mean_Control, Mean_Case, Annotation — missing p and FDR."""

    COLUMNS = ["compound_id", "logFC", "Mean_Control", "Mean_Case", "Annotation"]

    def test_compound_id_detected(self):
        sm = detect_schema(self.COLUMNS)
        assert sm.canonical_to_original.get("compound_id") == "compound_id"

    def test_effect_size_detected_as_logfc(self):
        sm = detect_schema(self.COLUMNS)
        assert sm.canonical_to_original.get("effect_size") == "logFC"

    def test_p_value_not_detected(self):
        sm = detect_schema(self.COLUMNS)
        assert "p_value" not in sm.canonical_to_original
        assert "p_value" in sm.missing

    def test_fdr_not_detected(self):
        sm = detect_schema(self.COLUMNS)
        assert "fdr" not in sm.canonical_to_original
        assert "fdr" in sm.missing

    def test_annotation_detected(self):
        sm = detect_schema(self.COLUMNS)
        assert sm.canonical_to_original.get("annotation") == "Annotation"


# ---------------------------------------------------------------------------
# normalize_header unit tests
# ---------------------------------------------------------------------------

class TestNormalizeHeader:
    @pytest.mark.parametrize("raw,expected", [
        ("p value", "p_value"),
        ("P.Value", "p_value"),
        ("p-val", "p_val"),
        ("Adjusted P", "adjusted_p"),
        ("log2 Fold Change", "log2_fold_change"),
        ("  logFC  ", "logfc"),
        ("FDR", "fdr"),
        ("p.adjust", "p_adjust"),
    ])
    def test_normalize_header(self, raw, expected):
        assert normalize_header(raw) == expected
