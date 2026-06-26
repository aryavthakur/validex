"""Pytest integration for the Validex benchmark suite.

Verifies that:
- All fixture files exist and contain data.
- All expected JSON files are valid and internally consistent.
- The benchmark runner passes all fixtures programmatically.
- Schema detection precision and recall are 1.0 across the suite.

Do not skip or xfail tests here.  Known limitations are encoded explicitly
in expected_findings.json, not by weakening assertions.
"""
from __future__ import annotations

import json
from pathlib import Path

import pandas as pd
import pytest

# Import the benchmark runner.  benchmarks/ is a package (has __init__.py)
# and the repo root is on pythonpath (see pyproject.toml pythonpath setting).
from benchmarks.run_benchmark import (
    EXPECTED_DIR,
    FIXTURES_DIR,
    BenchmarkResult,
    _flag_to_code,
    compute_metrics,
    run_all_benchmarks,
)

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _load_expected_schema() -> dict:
    return json.loads((EXPECTED_DIR / "expected_schema.json").read_text())


def _load_expected_findings() -> dict:
    return json.loads((EXPECTED_DIR / "expected_findings.json").read_text())


def _load_expected_scores() -> dict:
    return json.loads((EXPECTED_DIR / "expected_scores.json").read_text())


# ---------------------------------------------------------------------------
# Fixture file existence and validity
# ---------------------------------------------------------------------------

class TestFixtureFiles:
    def test_all_fixture_csvs_exist(self):
        schema = _load_expected_schema()
        for fixture_name in schema:
            path = FIXTURES_DIR / fixture_name
            assert path.exists(), f"Fixture file missing: {path}"

    def test_every_fixture_has_at_least_one_data_row(self):
        schema = _load_expected_schema()
        for fixture_name in schema:
            df = pd.read_csv(FIXTURES_DIR / fixture_name)
            assert len(df) >= 1, f"Fixture has no data rows: {fixture_name}"

    def test_fixtures_directory_has_expected_count(self):
        schema = _load_expected_schema()
        csv_files = list(FIXTURES_DIR.glob("*.csv"))
        assert len(csv_files) == len(schema), (
            f"Expected {len(schema)} CSV fixtures, found {len(csv_files)}"
        )


# ---------------------------------------------------------------------------
# Expected JSON validity
# ---------------------------------------------------------------------------

class TestExpectedJsonFiles:
    def test_expected_schema_json_is_valid(self):
        schema = _load_expected_schema()
        assert isinstance(schema, dict)
        assert len(schema) > 0

    def test_expected_findings_json_is_valid(self):
        findings = _load_expected_findings()
        assert isinstance(findings, dict)
        for fixture_name, entry in findings.items():
            assert "required_findings" in entry, (
                f"{fixture_name} missing 'required_findings'"
            )
            assert "forbidden_findings" in entry, (
                f"{fixture_name} missing 'forbidden_findings'"
            )

    def test_expected_scores_json_is_valid(self):
        scores = _load_expected_scores()
        assert isinstance(scores, dict)
        for fixture_name, entry in scores.items():
            band = entry.get("score_band", [])
            assert len(band) == 2, f"{fixture_name}: score_band must have 2 elements"
            assert band[0] <= band[1], (
                f"{fixture_name}: score_band min must be <= max"
            )

    def test_every_schema_fixture_has_findings_entry(self):
        schema = _load_expected_schema()
        findings = _load_expected_findings()
        for fixture_name in schema:
            assert fixture_name in findings, (
                f"No findings entry for fixture: {fixture_name}"
            )

    def test_every_schema_fixture_has_scores_entry(self):
        schema = _load_expected_schema()
        scores = _load_expected_scores()
        for fixture_name in schema:
            assert fixture_name in scores, (
                f"No scores entry for fixture: {fixture_name}"
            )

    def test_schema_fields_are_five_canonicals(self):
        expected_fields = {"compound_id", "effect_size", "p_value", "fdr", "annotation"}
        schema = _load_expected_schema()
        for fixture_name, entry in schema.items():
            assert set(entry.keys()) == expected_fields, (
                f"{fixture_name}: expected exactly 5 canonical fields, got {set(entry.keys())}"
            )


# ---------------------------------------------------------------------------
# Benchmark runner — programmatic all-pass
# ---------------------------------------------------------------------------

class TestBenchmarkRunner:
    """Run the full benchmark suite programmatically and assert all pass."""

    @pytest.fixture(scope="class")
    def results(self) -> list[BenchmarkResult]:
        return run_all_benchmarks()

    @pytest.fixture(scope="class")
    def metrics(self, results) -> dict:
        return compute_metrics(results)

    def test_runner_loads_all_fixtures(self, results):
        schema = _load_expected_schema()
        assert len(results) == len(schema)

    def test_all_fixtures_pass(self, results):
        failed = [r.fixture for r in results if not r.passed]
        assert not failed, (
            f"The following fixtures failed:\n" +
            "\n".join(
                f"  {r.fixture}: schema={r.schema_failures}, "
                f"missing={r.missing_required}, forbidden={r.unexpected_forbidden}, "
                f"score={r.score} band={r.expected_score_band}, "
                f"confidence={r.audit_confidence!r} expected={r.expected_confidence_label!r}"
                for r in results if not r.passed
            )
        )

    def test_all_results_have_audit_confidence(self, results):
        for r in results:
            assert r.audit_confidence in ("high", "medium", "low"), (
                f"{r.fixture}: unexpected audit_confidence value {r.audit_confidence!r}"
            )

    def test_confidence_labels_match_expected(self, results):
        scores = _load_expected_scores()
        mismatches = [
            f"{r.fixture}: got {r.audit_confidence!r}, expected {r.expected_confidence_label!r}"
            for r in results
            if r.expected_confidence_label and r.audit_confidence != r.expected_confidence_label
        ]
        assert not mismatches, "Confidence label mismatches:\n" + "\n".join(
            f"  {m}" for m in mismatches
        )

    def test_ambiguous_pvalues_scores_below_100(self, results):
        r = next(x for x in results if x.fixture == "ambiguous_pvalues.csv")
        assert r.score < 100, f"ambiguous_pvalues.csv should score < 100, got {r.score}"

    def test_ambiguous_fdr_scores_below_100(self, results):
        r = next(x for x in results if x.fixture == "ambiguous_fdr.csv")
        assert r.score < 100, f"ambiguous_fdr.csv should score < 100, got {r.score}"

    def test_precision_is_1_0(self, metrics):
        assert metrics["precision"] == 1.0, (
            f"Precision is {metrics['precision']:.4f} (FP={metrics['fp']}). "
            "A false positive means a canonical field was detected when it should not have been."
        )

    def test_recall_is_1_0(self, metrics):
        assert metrics["recall"] == 1.0, (
            f"Recall is {metrics['recall']:.4f} (FN={metrics['fn']}). "
            "A false negative means a canonical field was not detected when it should have been."
        )

    def test_no_schema_false_positives(self, results):
        fps = [
            f"{r.fixture}/{p.canonical}: detected={p.actual!r}"
            for r in results
            for p in r.field_predictions
            if p.is_fp
        ]
        assert not fps, f"Schema false positives found:\n" + "\n".join(f"  {x}" for x in fps)

    def test_no_schema_false_negatives(self, results):
        fns = [
            f"{r.fixture}/{p.canonical}: expected={p.expected!r}, got={p.actual!r}"
            for r in results
            for p in r.field_predictions
            if p.is_fn
        ]
        assert not fns, f"Schema false negatives found:\n" + "\n".join(f"  {x}" for x in fns)


# ---------------------------------------------------------------------------
# Specific fixture assertions
# ---------------------------------------------------------------------------

class TestDatasetCFixture:
    """The flagship Dataset C case must produce the correct audit outcome."""

    @pytest.fixture(scope="class")
    def dataset_c_result(self):
        results = run_all_benchmarks()
        return next(r for r in results if r.fixture == "missing_pvalues_dataset_c.csv")

    def test_compound_id_detected(self, dataset_c_result):
        assert dataset_c_result.detected["compound_id"] == "compound_id"

    def test_effect_size_detected(self, dataset_c_result):
        assert dataset_c_result.detected["effect_size"] == "logFC"

    def test_p_value_not_detected(self, dataset_c_result):
        assert dataset_c_result.detected["p_value"] is None

    def test_fdr_not_detected(self, dataset_c_result):
        assert dataset_c_result.detected["fdr"] is None

    def test_missing_p_value_finding_present(self, dataset_c_result):
        assert "missing_p_value" in dataset_c_result.actual_findings

    def test_missing_fdr_finding_present(self, dataset_c_result):
        assert "missing_fdr" in dataset_c_result.actual_findings

    def test_score_is_40(self, dataset_c_result):
        assert dataset_c_result.score == 40

    def test_fixture_passes(self, dataset_c_result):
        assert dataset_c_result.passed


class TestAdversarialFixtures:
    """Columns that contain common substrings must never trigger false detections."""

    @pytest.fixture(scope="class")
    def all_results(self):
        return {r.fixture: r for r in run_all_benchmarks()}

    def test_adversarial_p_words_no_p_value_detection(self, all_results):
        r = all_results["adversarial_p_words.csv"]
        assert r.detected["p_value"] is None, (
            "compound_id/sample/pathway/phenotype/platform/replicate must not be detected as p_value"
        )

    def test_adversarial_p_words_no_fdr_detection(self, all_results):
        r = all_results["adversarial_p_words.csv"]
        assert r.detected["fdr"] is None

    def test_adversarial_fdr_words_no_fdr_detection(self, all_results):
        r = all_results["adversarial_fdr_words.csv"]
        assert r.detected["fdr"] is None, (
            "quant/request/quality/acquisition/adjacent must not be detected as fdr"
        )

    def test_adversarial_fdr_words_p_value_correctly_detected(self, all_results):
        r = all_results["adversarial_fdr_words.csv"]
        assert r.detected["p_value"] == "p_value"


class TestFindingCodeExtraction:
    """Verify that flag title → finding code mapping is correct."""

    @pytest.mark.parametrize("title,expected_code", [
        ("Missing p-values", "missing_p_value"),
        ("Missing FDR / adjusted p-values", "missing_fdr"),
        ("Invalid p-value column", "invalid_p_value"),
        ("Invalid FDR column", "invalid_fdr"),
        ("Ambiguous p_value column", "ambiguous_p_value"),
        ("Ambiguous fdr column", "ambiguous_fdr"),
        ("FDR/p-value consistency warning", "fdr_consistency_warning"),
    ])
    def test_flag_to_code(self, title, expected_code):
        assert _flag_to_code(title) == expected_code
