"""Regression tests for the audit engine.

Group C: Flagship Dataset C audit results.
Group D: Value-level validation of statistical columns.
Group E: Backend smoke test — endpoint must use the canonical audit path.
Group F: Ambiguity findings, score penalties, and confidence labels.
"""

from __future__ import annotations

import pandas as pd
import pytest
from fastapi.testclient import TestClient

from validex.audit import audit_dataframe
from validex.config import DEFAULT_CONFIG
from validex.server import create_app


# ---------------------------------------------------------------------------
# Shared fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def df_c():
    """Flagship Dataset C: effect size present, p-value and FDR absent."""
    return pd.DataFrame(
        {
            "compound_id": ["M1", "M2", "M3"],
            "logFC": [1.5, -0.3, 2.1],
            "Mean_Control": [10.0, 5.0, 8.0],
            "Mean_Case": [15.0, 4.0, 20.0],
            "Annotation": ["putative", "confirmed", "putative"],
        }
    )


@pytest.fixture
def df_complete():
    """Complete dataset with all required statistical columns."""
    return pd.DataFrame(
        {
            "compound_id": ["M1", "M2", "M3"],
            "logFC": [1.5, -0.3, 2.1],
            "p_value": [0.01, 0.20, 0.001],
            "fdr": [0.05, 0.40, 0.01],
            "Annotation": ["putative", "confirmed", "putative"],
        }
    )


# ---------------------------------------------------------------------------
# Group C: Flagship Dataset C audit
# ---------------------------------------------------------------------------


class TestDatasetCAudit:
    def test_compound_id_detected(self, df_c):
        result = audit_dataframe(df_c)
        assert result["detected"]["compound_id"] == "compound_id"

    def test_effect_size_detected(self, df_c):
        result = audit_dataframe(df_c)
        assert result["detected"]["effect_size"] == "logFC"

    def test_p_value_not_detected(self, df_c):
        result = audit_dataframe(df_c)
        assert result["detected"]["p_value"] is None

    def test_fdr_not_detected(self, df_c):
        result = audit_dataframe(df_c)
        assert result["detected"]["fdr"] is None

    def test_missing_p_value_finding_present(self, df_c):
        result = audit_dataframe(df_c)
        titles = [f["title"].lower() for f in result["flags"]]
        assert any("p-value" in t or "p_value" in t for t in titles), (
            f"Expected a missing-p-value flag, got: {result['flags']}"
        )

    def test_missing_fdr_finding_present(self, df_c):
        result = audit_dataframe(df_c)
        titles = [f["title"].lower() for f in result["flags"]]
        assert any("fdr" in t or "adjusted" in t for t in titles), (
            f"Expected a missing-FDR flag, got: {result['flags']}"
        )

    def test_missing_p_value_finding_is_high_severity(self, df_c):
        result = audit_dataframe(df_c)
        high_titles = [
            f["title"].lower() for f in result["flags"] if f["severity"] == "high"
        ]
        assert any("p-value" in t or "p_value" in t for t in high_titles)

    def test_score_materially_lower_than_complete(self, df_c, df_complete):
        score_c = audit_dataframe(df_c)["confidence"]
        score_complete = audit_dataframe(df_complete)["confidence"]
        assert score_c < score_complete, (
            f"Dataset C score ({score_c}) should be lower than complete ({score_complete})"
        )

    def test_complete_dataset_scores_100(self, df_complete):
        result = audit_dataframe(df_complete)
        assert result["confidence"] == 100


# ---------------------------------------------------------------------------
# Group D: Value-level validation
# ---------------------------------------------------------------------------


class TestValueValidation:
    def test_valid_p_value_accepted(self):
        df = pd.DataFrame(
            {
                "compound_id": ["A", "B", "C"],
                "p_value": [0.01, 0.05, 0.20],
                "fdr": [0.03, 0.10, 0.40],
            }
        )
        result = audit_dataframe(df)
        assert result["detected"]["p_value"] == "p_value"

    def test_invalid_p_value_rejected(self):
        df = pd.DataFrame(
            {
                "compound_id": ["A", "B", "C"],
                "p_value": [2.5, -0.1, "abc"],
                "fdr": [0.05, 0.10, 0.20],
            }
        )
        result = audit_dataframe(df)
        assert result["detected"]["p_value"] is None
        titles = [f["title"].lower() for f in result["flags"]]
        assert any("invalid" in t for t in titles), (
            f"Expected an invalid-p-value flag, got: {result['flags']}"
        )

    def test_valid_fdr_accepted(self):
        df = pd.DataFrame(
            {
                "compound_id": ["A", "B", "C"],
                "p_value": [0.01, 0.10, 0.30],
                "fdr": [0.03, 0.10, 0.40],
            }
        )
        result = audit_dataframe(df)
        assert result["detected"]["fdr"] == "fdr"

    def test_invalid_fdr_rejected(self):
        df = pd.DataFrame(
            {
                "compound_id": ["A", "B", "C"],
                "p_value": [0.01, 0.10, 0.30],
                "fdr": [1.2, -0.5, "bad"],
            }
        )
        result = audit_dataframe(df)
        assert result["detected"]["fdr"] is None
        titles = [f["title"].lower() for f in result["flags"]]
        assert any("invalid" in t for t in titles), (
            f"Expected an invalid-FDR flag, got: {result['flags']}"
        )

    def test_fdr_frequently_smaller_than_p_value_triggers_warning(self):
        # FDR << p_value on every row is suspicious
        df = pd.DataFrame(
            {
                "compound_id": ["A", "B", "C"],
                "p_value": [0.5, 0.8, 0.9],
                "fdr": [0.01, 0.02, 0.03],
            }
        )
        result = audit_dataframe(df)
        titles = [f["title"].lower() for f in result["flags"]]
        assert any("consistency" in t or "fdr" in t for t in titles), (
            f"Expected a consistency warning, got: {result['flags']}"
        )


# ---------------------------------------------------------------------------
# Group E: Backend smoke test
# ---------------------------------------------------------------------------

# ---------------------------------------------------------------------------
# Group F: Ambiguity findings, score penalties, and confidence labels
# ---------------------------------------------------------------------------


class TestAmbiguity:
    """Ambiguous schema fields must produce findings, reduce score, and set medium confidence."""

    @pytest.fixture
    def df_ambig_p(self):
        """Two columns both matching p_value aliases."""
        return pd.DataFrame(
            {
                "compound_id": ["A", "B", "C"],
                "logFC": [1.0, -0.5, 2.0],
                "p_value": [0.01, 0.05, 0.20],
                "pval": [0.01, 0.05, 0.20],
                "FDR": [0.05, 0.15, 0.40],
                "Annotation": ["confirmed", "putative", "unknown"],
            }
        )

    @pytest.fixture
    def df_ambig_fdr(self):
        """Two columns both matching fdr aliases."""
        return pd.DataFrame(
            {
                "compound_id": ["A", "B", "C"],
                "logFC": [1.0, -0.5, 2.0],
                "p_value": [0.01, 0.05, 0.20],
                "FDR": [0.05, 0.15, 0.40],
                "padj": [0.05, 0.15, 0.40],
                "Annotation": ["confirmed", "putative", "unknown"],
            }
        )

    def test_ambiguous_p_value_produces_finding(self, df_ambig_p):
        result = audit_dataframe(df_ambig_p)
        titles = [f["title"].lower() for f in result["flags"]]
        assert any("ambiguous" in t and "p_value" in t for t in titles), (
            f"Expected ambiguity finding for p_value, got: {result['flags']}"
        )

    def test_ambiguous_fdr_produces_finding(self, df_ambig_fdr):
        result = audit_dataframe(df_ambig_fdr)
        titles = [f["title"].lower() for f in result["flags"]]
        assert any("ambiguous" in t and "fdr" in t for t in titles), (
            f"Expected ambiguity finding for fdr, got: {result['flags']}"
        )

    def test_ambiguous_p_value_finding_has_selected_and_candidates(self, df_ambig_p):
        result = audit_dataframe(df_ambig_p)
        ambig_flags = [f for f in result["flags"] if "Ambiguous" in f.get("title", "")]
        p_flags = [f for f in ambig_flags if f.get("field") == "p_value"]
        assert p_flags, "No ambiguity flag found for p_value"
        flag = p_flags[0]
        assert flag.get("selected_column") is not None
        assert isinstance(flag.get("candidate_columns"), list)
        assert len(flag["candidate_columns"]) > 1

    def test_ambiguous_fdr_finding_is_medium_severity(self, df_ambig_fdr):
        result = audit_dataframe(df_ambig_fdr)
        ambig_flags = [
            f
            for f in result["flags"]
            if "Ambiguous" in f.get("title", "") and f.get("field") == "fdr"
        ]
        assert ambig_flags, "No ambiguity flag found for fdr"
        assert ambig_flags[0]["severity"] == "medium"

    def test_ambiguous_p_value_score_lower_than_complete(self, df_ambig_p):
        """Ambiguity in a critical field must reduce the score."""
        df_complete = pd.DataFrame(
            {
                "compound_id": ["A", "B", "C"],
                "logFC": [1.0, -0.5, 2.0],
                "p_value": [0.01, 0.05, 0.20],
                "FDR": [0.05, 0.15, 0.40],
                "Annotation": ["confirmed", "putative", "unknown"],
            }
        )
        score_ambig = audit_dataframe(df_ambig_p)["confidence"]
        score_complete = audit_dataframe(df_complete)["confidence"]
        assert score_ambig < score_complete, (
            f"Ambiguous p_value score ({score_ambig}) should be < complete ({score_complete})"
        )

    def test_ambiguous_fdr_score_lower_than_complete(self, df_ambig_fdr):
        """Ambiguity in fdr must reduce the score."""
        df_complete = pd.DataFrame(
            {
                "compound_id": ["A", "B", "C"],
                "logFC": [1.0, -0.5, 2.0],
                "p_value": [0.01, 0.05, 0.20],
                "FDR": [0.05, 0.15, 0.40],
                "Annotation": ["confirmed", "putative", "unknown"],
            }
        )
        score_ambig = audit_dataframe(df_ambig_fdr)["confidence"]
        score_complete = audit_dataframe(df_complete)["confidence"]
        assert score_ambig < score_complete

    def test_ambiguous_p_value_score_is_95(self, df_ambig_p):
        """p_value ambiguity alone → -5 points from 100 = 95."""
        result = audit_dataframe(df_ambig_p)
        assert result["confidence"] == 95

    def test_ambiguous_fdr_score_is_95(self, df_ambig_fdr):
        """fdr ambiguity alone → -5 points from 100 = 95."""
        result = audit_dataframe(df_ambig_fdr)
        assert result["confidence"] == 95


class TestConfidenceLabel:
    """audit_confidence must reflect field completeness and ambiguity status."""

    @pytest.fixture
    def df_complete(self):
        return pd.DataFrame(
            {
                "compound_id": ["A", "B", "C"],
                "logFC": [1.0, -0.5, 2.0],
                "p_value": [0.01, 0.05, 0.20],
                "fdr": [0.05, 0.15, 0.40],
                "Annotation": ["confirmed", "putative", "unknown"],
            }
        )

    def test_complete_standard_is_high(self, df_complete):
        result = audit_dataframe(df_complete)
        assert result["audit_confidence"] == "high"

    def test_dataset_c_is_low(self):
        df = pd.DataFrame(
            {
                "compound_id": ["A", "B", "C"],
                "logFC": [1.0, -0.5, 2.0],
                "Mean_Control": [10.0, 5.0, 8.0],
                "Mean_Case": [15.0, 4.0, 20.0],
                "Annotation": ["confirmed", "putative", "unknown"],
            }
        )
        result = audit_dataframe(df)
        assert result["audit_confidence"] == "low"

    def test_missing_fdr_is_medium(self):
        df = pd.DataFrame(
            {
                "compound_id": ["A", "B", "C"],
                "logFC": [1.0, -0.5, 2.0],
                "p_value": [0.01, 0.05, 0.20],
                "Annotation": ["confirmed", "putative", "unknown"],
            }
        )
        result = audit_dataframe(df)
        assert result["audit_confidence"] == "medium"

    def test_invalid_p_value_is_low(self):
        df = pd.DataFrame(
            {
                "compound_id": ["A", "B", "C"],
                "p_value": [2.5, -0.1, "abc"],
                "fdr": [0.05, 0.10, 0.20],
            }
        )
        result = audit_dataframe(df)
        assert result["audit_confidence"] == "low"

    def test_invalid_fdr_is_medium(self):
        df = pd.DataFrame(
            {
                "compound_id": ["A", "B", "C"],
                "p_value": [0.01, 0.05, 0.20],
                "fdr": [1.5, -0.2, "bad"],
            }
        )
        result = audit_dataframe(df)
        assert result["audit_confidence"] == "medium"

    def test_ambiguous_p_value_is_medium(self):
        df = pd.DataFrame(
            {
                "compound_id": ["A", "B", "C"],
                "logFC": [1.0, -0.5, 2.0],
                "p_value": [0.01, 0.05, 0.20],
                "pval": [0.01, 0.05, 0.20],
                "FDR": [0.05, 0.15, 0.40],
                "Annotation": ["confirmed", "putative", "unknown"],
            }
        )
        result = audit_dataframe(df)
        assert result["audit_confidence"] == "medium"

    def test_ambiguous_fdr_is_medium(self):
        df = pd.DataFrame(
            {
                "compound_id": ["A", "B", "C"],
                "logFC": [1.0, -0.5, 2.0],
                "p_value": [0.01, 0.05, 0.20],
                "FDR": [0.05, 0.15, 0.40],
                "padj": [0.05, 0.15, 0.40],
                "Annotation": ["confirmed", "putative", "unknown"],
            }
        )
        result = audit_dataframe(df)
        assert result["audit_confidence"] == "medium"

    def test_adversarial_p_words_is_low(self):
        df = pd.DataFrame(
            {
                "compound_id": ["A", "B"],
                "sample": ["S1", "S2"],
                "pathway": ["glycolysis", "tca"],
                "logFC": [1.0, -0.5],
                "Annotation": ["confirmed", "putative"],
            }
        )
        result = audit_dataframe(df)
        assert result["audit_confidence"] == "low"

    def test_adversarial_fdr_words_is_medium(self):
        df = pd.DataFrame(
            {
                "compound_id": ["A", "B"],
                "quant": [100, 200],
                "adjacent": ["adj1", "adj2"],
                "logFC": [1.0, -0.5],
                "p_value": [0.01, 0.05],
                "Annotation": ["confirmed", "putative"],
            }
        )
        result = audit_dataframe(df)
        assert result["audit_confidence"] == "medium"


class TestPilotSTAudit:
    @pytest.fixture
    def df_pilot_st(self):
        return pd.DataFrame(
            {
                "Metabolite": ["A", "B", "C"],
                "F value": [4.2, 8.1, 2.0],
                "P-value": [0.01, 0.05, 0.20],
                "FDR adjusted P-value": [0.03, 0.08, 0.25],
                "Main class": ["Lipids", "Amino acids", "Lipids"],
                "Sub class": ["PC", "Branched chain", "TG"],
            }
        )

    def test_pilot_style_dataframe_detects_probability_columns(self, df_pilot_st):
        result = audit_dataframe(df_pilot_st)
        assert result["detected"]["p_value"] == "P-value"
        assert result["detected"]["fdr"] == "FDR adjusted P-value"

    def test_pilot_style_dataframe_does_not_report_missing_probability_columns(
        self, df_pilot_st
    ):
        result = audit_dataframe(df_pilot_st)
        titles = [f["title"].lower() for f in result["flags"]]
        assert not any(
            "missing p-value" in t or "missing p-values" in t for t in titles
        )
        assert not any("missing fdr" in t for t in titles)

    def test_pilot_style_dataframe_rejects_class_taxonomy_as_annotation(self, df_pilot_st):
        result = audit_dataframe(df_pilot_st)
        assert result["detected"]["annotation"] is None
        rejected = result["rejected_schema_candidates"]["annotation"]
        assert [item["column"] for item in rejected] == ["Main class", "Sub class"]

    def test_pilot_style_dataframe_does_not_treat_f_value_as_effect_size(
        self, df_pilot_st
    ):
        result = audit_dataframe(df_pilot_st)
        assert result["detected"]["effect_size"] is None


class TestValidex02AuditContracts:
    def test_audit_exposes_structured_schema_candidates_and_ambiguity_status(self):
        df = pd.DataFrame(
            {
                "compound_id": ["A", "B"],
                "p_value": [0.01, 0.04],
                "nominal probability": [0.01, 0.04],
                "adjusted_p": [0.02, 0.05],
                "MSI level": ["2", "3"],
                "library match": ["HMDB:1", "HMDB:2"],
            }
        )

        result = audit_dataframe(df)

        assert result["schema_candidates"]["p_value"][0]["column"] == "p_value"
        assert result["schema_candidates"]["p_value"][1]["column"] == "nominal probability"
        assert result["ambiguity"]["p_value"]["status"] == "multiple_valid_preferred"
        assert result["ambiguity"]["p_value"]["selected_column"] == "p_value"
        assert result["ambiguity"]["annotation"]["status"] == "multiple_valid_no_preference"
        assert result["detected"]["annotation"] is None

    def test_audit_reports_missing_comparable_fdr_row_count(self):
        df = pd.DataFrame(
            {
                "compound_id": ["A", "B", "C"],
                "p_value": ["0.01", "bad", "0.03"],
                "fdr": ["0.02", "0.05", "missing"],
            }
        )

        result = audit_dataframe(df)

        assert result["fdr_ordering"]["comparable_row_count"] == 1
        assert result["fdr_ordering"]["warning"] is False


class TestPhase1ScientificRegressions:
    def test_one_valid_row_plus_garbage_rows_is_not_perfect_or_high_confidence(self):
        df = pd.DataFrame(
            {
                "compound_id": ["A", "B", "C", "D"],
                "logFC": [1.2, -0.4, 0.3, 2.1],
                "p_value": ["0.01", "garbage", "not-a-number", ""],
                "fdr": ["0.02", "garbage", "not-a-number", ""],
                "Annotation": ["confirmed", "putative", "unknown", "unknown"],
            }
        )

        result = audit_dataframe(df)

        assert result["confidence"] < 100
        assert result["audit_confidence"] != "high"
        assert result["statistical_validation"]["p_value"]["total_row_count"] == 4
        assert result["statistical_validation"]["p_value"]["valid_numeric_count"] == 1
        assert result["statistical_validation"]["p_value"]["valid_fraction"] == 0.25

    def test_invalid_statistical_cells_are_counted_over_all_rows(self):
        df = pd.DataFrame(
            {
                "compound_id": ["A", "B", "C", "D", "E"],
                "logFC": [1.2, -0.4, 0.3, 2.1, -1.1],
                "p_value": ["0.01", "0.02", "0.03", "bad", "text"],
                "fdr": ["0.02", "0.03", "0.04", "bad", "text"],
                "Annotation": [
                    "confirmed",
                    "putative",
                    "unknown",
                    "unknown",
                    "confirmed",
                ],
            }
        )

        result = audit_dataframe(df)

        p_stats = result["statistical_validation"]["p_value"]
        assert p_stats["total_row_count"] == 5
        assert p_stats["valid_numeric_count"] == 3
        assert p_stats["nonnumeric_count"] == 2
        assert p_stats["valid_fraction"] == 0.6
        assert result["confidence"] < 100

    def test_p_value_and_q_value_only_table_is_partial_not_high_confidence(self):
        df = pd.DataFrame(
            {
                "p_value": [0.01, 0.02, 0.03],
                "q_value": [0.02, 0.03, 0.05],
            }
        )

        result = audit_dataframe(df)

        assert result["detected"]["p_value"] == "p_value"
        assert result["detected"]["fdr"] == "q_value"
        assert result["confidence"] < 100
        assert result["audit_confidence"] != "high"
        titles = [f["title"].lower() for f in result["flags"]]
        assert any("compound" in title or "identifier" in title for title in titles)
        assert any("effect" in title for title in titles)

    def test_duplicate_compound_identifiers_reduce_trust(self):
        df = pd.DataFrame(
            {
                "compound_id": ["A", "A", "B"],
                "logFC": [1.2, -0.4, 0.3],
                "p_value": [0.01, 0.02, 0.03],
                "fdr": [0.02, 0.03, 0.04],
                "Annotation": ["confirmed", "putative", "unknown"],
            }
        )

        result = audit_dataframe(df)

        assert result["confidence"] < 100
        assert result["audit_confidence"] != "high"
        titles = [f["title"].lower() for f in result["flags"]]
        assert any("duplicate" in title and "identifier" in title for title in titles)

    def test_adjusted_values_below_raw_p_values_reduce_trust(self):
        df = pd.DataFrame(
            {
                "compound_id": ["A", "B", "C"],
                "logFC": [1.2, -0.4, 0.3],
                "p_value": [0.50, 0.60, 0.70],
                "fdr": [0.01, 0.02, 0.03],
                "Annotation": ["confirmed", "putative", "unknown"],
            }
        )

        result = audit_dataframe(df)

        assert result["confidence"] < 100
        assert result["audit_confidence"] != "high"
        titles = [f["title"].lower() for f in result["flags"]]
        assert any("consistency" in title for title in titles)

    def test_nonfinite_values_are_reported_as_invalid_cells(self):
        df = pd.DataFrame(
            {
                "compound_id": ["A", "B", "C"],
                "logFC": [1.2, -0.4, 0.3],
                "p_value": [0.01, float("inf"), float("-inf")],
                "fdr": [0.02, float("inf"), 0.04],
                "Annotation": ["confirmed", "putative", "unknown"],
            }
        )

        result = audit_dataframe(df)

        assert result["statistical_validation"]["p_value"]["nonfinite_count"] == 2
        assert result["statistical_validation"]["fdr"]["nonfinite_count"] == 1
        assert result["confidence"] < 100

    def test_nan_is_classified_as_missing_not_nonfinite(self):
        """NaN in probability columns represents a missing cell, not a
        nonfinite mathematical result (e.g. pandas coerces None to NaN
        in string-typed columns)."""
        df = pd.DataFrame(
            {
                "compound_id": ["A", "B", "C"],
                "logFC": [1.2, -0.4, 0.3],
                "p_value": [0.01, float("nan"), 0.03],
                "fdr": [0.02, 0.03, float("nan")],
                "Annotation": ["confirmed", "putative", "unknown"],
            }
        )

        result = audit_dataframe(df)

        assert result["statistical_validation"]["p_value"]["missing_count"] == 1
        assert result["statistical_validation"]["p_value"]["nonfinite_count"] == 0
        assert result["statistical_validation"]["fdr"]["missing_count"] == 1
        assert result["statistical_validation"]["fdr"]["nonfinite_count"] == 0

    def test_boolean_values_are_not_accepted_as_numeric_probabilities(self):
        df = pd.DataFrame(
            {
                "compound_id": ["A", "B", "C"],
                "logFC": [1.2, -0.4, 0.3],
                "p_value": [True, False, 0.03],
                "fdr": [0.02, 0.03, 0.04],
                "Annotation": ["confirmed", "putative", "unknown"],
            }
        )

        result = audit_dataframe(df)

        p_stats = result["statistical_validation"]["p_value"]
        assert p_stats["nonnumeric_count"] == 2
        assert p_stats["valid_numeric_count"] == 1
        assert result["detected"]["p_value"] is None

    def test_out_of_range_values_are_reported_as_invalid_cells(self):
        df = pd.DataFrame(
            {
                "compound_id": ["A", "B", "C"],
                "logFC": [1.2, -0.4, 0.3],
                "p_value": [0.01, -0.01, 1.2],
                "fdr": [0.02, 0.03, 0.04],
                "Annotation": ["confirmed", "putative", "unknown"],
            }
        )

        result = audit_dataframe(df)

        assert result["statistical_validation"]["p_value"]["out_of_range_count"] == 2
        assert result["detected"]["p_value"] is None
        assert result["audit_confidence"] == "low"

    def test_scientific_notation_is_valid_numeric_evidence(self):
        df = pd.DataFrame(
            {
                "compound_id": ["A", "B", "C"],
                "logFC": [1.2, -0.4, 0.3],
                "p_value": ["1e-3", "2E-2", "5e-1"],
                "fdr": ["2e-3", "3E-2", "8e-1"],
                "Annotation": ["confirmed", "putative", "unknown"],
            }
        )

        result = audit_dataframe(df)

        assert result["confidence"] == 100
        assert result["audit_confidence"] == "high"

    def test_missing_values_only_do_not_count_as_valid_probability_evidence(self):
        df = pd.DataFrame(
            {
                "compound_id": ["A", "B", "C"],
                "logFC": [1.2, -0.4, 0.3],
                "p_value": ["", None, "NA"],
                "fdr": ["", None, "NA"],
                "Annotation": ["confirmed", "putative", "unknown"],
            }
        )

        result = audit_dataframe(df)

        assert result["statistical_validation"]["p_value"]["missing_count"] == 3
        assert result["detected"]["p_value"] is None
        assert result["audit_confidence"] == "low"

    def test_adding_invalid_statistical_values_never_improves_score(self):
        valid = pd.DataFrame(
            {
                "compound_id": ["A", "B", "C"],
                "logFC": [1.2, -0.4, 0.3],
                "p_value": [0.01, 0.02, 0.03],
                "fdr": [0.02, 0.03, 0.04],
                "Annotation": ["confirmed", "putative", "unknown"],
            }
        )
        invalid = pd.DataFrame(
            {
                "compound_id": ["A", "B", "C", "D"],
                "logFC": [1.2, -0.4, 0.3, 2.1],
                "p_value": [0.01, 0.02, 0.03, "bad"],
                "fdr": [0.02, 0.03, 0.04, "bad"],
                "Annotation": ["confirmed", "putative", "unknown", "unknown"],
            }
        )

        assert (
            audit_dataframe(invalid)["confidence"]
            <= audit_dataframe(valid)["confidence"]
        )

    def test_removing_required_evidence_never_improves_confidence(self):
        complete = pd.DataFrame(
            {
                "compound_id": ["A", "B", "C"],
                "logFC": [1.2, -0.4, 0.3],
                "p_value": [0.01, 0.02, 0.03],
                "fdr": [0.02, 0.03, 0.04],
                "Annotation": ["confirmed", "putative", "unknown"],
            }
        )
        incomplete = complete[["p_value", "fdr"]]

        confidence_rank = {"low": 0, "medium": 1, "high": 2}
        assert (
            confidence_rank[audit_dataframe(incomplete)["audit_confidence"]]
            <= confidence_rank[audit_dataframe(complete)["audit_confidence"]]
        )


class TestBackendSmoke:
    def test_audit_endpoint_dataset_c_does_not_detect_p_value(self):
        """Uploading Dataset C columns must not produce a detected p_value in the schema."""
        app = create_app(config=DEFAULT_CONFIG)
        client = TestClient(app)

        csv_content = (
            "compound_id,logFC,Mean_Control,Mean_Case,Annotation\n"
            "M1,1.5,10,15,putative\n"
            "M2,-0.3,5,4,confirmed\n"
        )

        response = client.post(
            "/audit",
            files={"file": ("dataset_c.csv", csv_content.encode(), "text/csv")},
            data={"context": "{}"},
        )

        assert response.status_code == 200
        data = response.json()
        schema = data.get("schema", {})
        assert "p_value" not in schema.get("canonical_to_original", {}), (
            "Backend endpoint incorrectly detected p_value for Dataset C"
        )

    def test_audit_endpoint_complete_dataset_detects_p_and_fdr(self):
        """A complete CSV must surface p_value and fdr in the schema response."""
        app = create_app(config=DEFAULT_CONFIG)
        client = TestClient(app)

        csv_content = (
            "compound_id,logFC,p_value,fdr,Annotation\n"
            "M1,1.5,0.01,0.05,putative\n"
            "M2,-0.3,0.20,0.40,confirmed\n"
        )

        response = client.post(
            "/audit",
            files={"file": ("complete.csv", csv_content.encode(), "text/csv")},
            data={"context": "{}"},
        )

        assert response.status_code == 200
        data = response.json()
        schema = data.get("schema", {})
        assert "p_value" in schema.get("canonical_to_original", {})
        assert "fdr" in schema.get("canonical_to_original", {})
