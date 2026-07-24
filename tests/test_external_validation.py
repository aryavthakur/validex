"""Tests for the external validation scaffold.

These tests verify:
- Example files have correct structure.
- Label parsing handles all three cases (absent, exact, AMBIGUOUS).
- Metric computation handles TP/FP/FN/TN correctly.
- Finding metric computation handles expected and actual findings.
- The runner errors cleanly when table files are missing.
- The runner correctly validates a temporary mini external dataset.
"""

from __future__ import annotations

import json
import csv
from pathlib import Path

import pytest

from validation.run_external_validation import (
    LABELS_REQUIRED_COLUMNS,
    REGISTRY_REQUIRED_COLUMNS,
    FieldResult,
    TableResult,
    _parse_field_label,
    _parse_findings,
    aggregate_metrics,
    parse_label_row,
    run_external_validation,
)

VALIDATION_DIR = Path(__file__).resolve().parent.parent / "validation"


# ---------------------------------------------------------------------------
# Example file structure tests
# ---------------------------------------------------------------------------


def test_registry_example_has_required_columns():
    """registry.example.csv must have all required columns."""
    path = VALIDATION_DIR / "registry.example.csv"
    with open(path, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        rows = list(reader)
    assert rows, "registry.example.csv is empty"
    actual_cols = set(rows[0].keys())
    assert REGISTRY_REQUIRED_COLUMNS <= actual_cols, (
        f"Missing columns in registry.example.csv: {REGISTRY_REQUIRED_COLUMNS - actual_cols}"
    )


def test_labels_example_has_required_columns():
    """labels.example.csv must have all required columns."""
    path = VALIDATION_DIR / "labels.example.csv"
    with open(path, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        rows = list(reader)
    assert rows, "labels.example.csv is empty"
    actual_cols = set(rows[0].keys())
    assert LABELS_REQUIRED_COLUMNS <= actual_cols, (
        f"Missing columns in labels.example.csv: {LABELS_REQUIRED_COLUMNS - actual_cols}"
    )


def test_external_results_example_has_required_keys():
    """external_results.example.json must have required top-level keys."""
    path = VALIDATION_DIR / "external_results.example.json"
    data = json.loads(path.read_text(encoding="utf-8"))
    required_keys = {
        "n_tables",
        "field_level",
        "finding_level",
        "exact_schema_match_rate",
        "score_distribution",
        "confidence_distribution",
        "tables",
        "failure_cases",
    }
    actual_keys = set(data.keys())
    assert required_keys <= actual_keys, (
        f"Missing keys in external_results.example.json: {required_keys - actual_keys}"
    )


def test_external_results_example_has_note_marking_it_as_example():
    """external_results.example.json must contain a note marking it as an example."""
    path = VALIDATION_DIR / "external_results.example.json"
    data = json.loads(path.read_text(encoding="utf-8"))
    assert "_note" in data or data.get("status") == "example_only", (
        "external_results.example.json must be clearly marked as an example"
    )


def test_registry_example_has_three_rows():
    """registry.example.csv should have the three EXAMPLE_ rows."""
    path = VALIDATION_DIR / "registry.example.csv"
    with open(path, newline="", encoding="utf-8") as f:
        rows = list(csv.DictReader(f))
    ids = {r["dataset_id"] for r in rows}
    assert {"EXAMPLE_001", "EXAMPLE_002", "EXAMPLE_003"} == ids


def test_labels_example_has_three_rows():
    """labels.example.csv should have the three EXAMPLE_ rows."""
    path = VALIDATION_DIR / "labels.example.csv"
    with open(path, newline="", encoding="utf-8") as f:
        rows = list(csv.DictReader(f))
    ids = {r["dataset_id"] for r in rows}
    assert {"EXAMPLE_001", "EXAMPLE_002", "EXAMPLE_003"} == ids


# ---------------------------------------------------------------------------
# Label parser tests
# ---------------------------------------------------------------------------


def test_parse_field_label_empty_is_none():
    """Empty string label means field is absent."""
    assert _parse_field_label("") is None
    assert _parse_field_label("   ") is None


def test_parse_field_label_exact_column():
    """Plain string label returns the column name."""
    assert _parse_field_label("p_value") == "p_value"
    assert _parse_field_label("  logFC  ") == "logFC"


def test_parse_field_label_ambiguous_two():
    """AMBIGUOUS:a|b returns list with both candidates."""
    result = _parse_field_label("AMBIGUOUS:p_value|pval")
    assert result == ["p_value", "pval"]


def test_parse_field_label_ambiguous_three():
    """AMBIGUOUS:a|b|c returns list with all three candidates."""
    result = _parse_field_label("AMBIGUOUS:FDR|padj|q_value")
    assert result == ["FDR", "padj", "q_value"]


def test_parse_findings_empty():
    """Empty string returns empty list."""
    assert _parse_findings("") == []
    assert _parse_findings("  ") == []


def test_parse_findings_single():
    """Single finding code returns single-element list."""
    assert _parse_findings("missing_p_value") == ["missing_p_value"]


def test_parse_findings_pipe_separated():
    """Pipe-separated findings return correct list."""
    result = _parse_findings("missing_p_value|missing_fdr")
    assert result == ["missing_p_value", "missing_fdr"]


def test_parse_label_row_complete():
    """parse_label_row correctly parses a complete row."""
    row = {
        "dataset_id": "TEST_001",
        "table_filename": "test.csv",
        "compound_id": "compound_id",
        "effect_size": "logFC",
        "p_value": "p_value",
        "fdr": "FDR",
        "annotation": "Annotation",
        "expected_findings": "",
        "reviewer_id": "reviewer_a",
        "review_notes": "Complete table",
    }
    label = parse_label_row(row)
    assert label.compound_id == "compound_id"
    assert label.effect_size == "logFC"
    assert label.p_value == "p_value"
    assert label.fdr == "FDR"
    assert label.annotation == "Annotation"
    assert label.expected_findings == []


def test_parse_label_row_missing_stats():
    """parse_label_row handles absent p_value and fdr."""
    row = {
        "dataset_id": "TEST_002",
        "table_filename": "test.csv",
        "compound_id": "compound_id",
        "effect_size": "logFC",
        "p_value": "",
        "fdr": "",
        "annotation": "Annotation",
        "expected_findings": "missing_p_value|missing_fdr",
        "reviewer_id": "reviewer_a",
        "review_notes": "",
    }
    label = parse_label_row(row)
    assert label.p_value is None
    assert label.fdr is None
    assert label.expected_findings == ["missing_p_value", "missing_fdr"]


def test_parse_label_row_ambiguous():
    """parse_label_row handles AMBIGUOUS label."""
    row = {
        "dataset_id": "TEST_003",
        "table_filename": "test.csv",
        "compound_id": "compound_id",
        "effect_size": "logFC",
        "p_value": "AMBIGUOUS:p_value|pval",
        "fdr": "FDR",
        "annotation": "Annotation",
        "expected_findings": "ambiguous_schema_field",
        "reviewer_id": "reviewer_a",
        "review_notes": "",
    }
    label = parse_label_row(row)
    assert label.p_value == ["p_value", "pval"]
    assert label.expected_findings == ["ambiguous_schema_field"]


# ---------------------------------------------------------------------------
# FieldResult metric tests
# ---------------------------------------------------------------------------


def test_field_result_tp_exact_match():
    r = FieldResult(canonical="p_value", expected="p_value", actual="p_value")
    assert r.is_tp
    assert not r.is_fp
    assert not r.is_fn
    assert not r.is_tn


def test_field_result_fp_unexpected_detection():
    r = FieldResult(canonical="p_value", expected=None, actual="some_col")
    assert not r.is_tp
    assert r.is_fp
    assert not r.is_fn
    assert not r.is_tn


def test_field_result_fn_missed_detection():
    r = FieldResult(canonical="p_value", expected="p_value", actual=None)
    assert not r.is_tp
    assert not r.is_fp
    assert r.is_fn
    assert not r.is_tn


def test_field_result_tn_correct_absent():
    r = FieldResult(canonical="p_value", expected=None, actual=None)
    assert not r.is_tp
    assert not r.is_fp
    assert not r.is_fn
    assert r.is_tn


def test_field_result_tp_ambiguous_candidate_match():
    """TP when expected is AMBIGUOUS and actual is one of the candidates."""
    r = FieldResult(canonical="p_value", expected=["p_value", "pval"], actual="pval")
    assert r.is_tp
    assert not r.is_fn


def test_field_result_fn_ambiguous_wrong_column():
    """FN when expected is AMBIGUOUS and actual is not in candidates."""
    r = FieldResult(
        canonical="p_value", expected=["p_value", "pval"], actual="something_else"
    )
    assert not r.is_tp
    assert r.is_fn


# ---------------------------------------------------------------------------
# Aggregate metric tests
# ---------------------------------------------------------------------------


def _make_table_result(
    dataset_id: str,
    field_results: list[FieldResult],
    expected_findings: list[str],
    actual_finding_codes: list[str],
) -> TableResult:
    """Helper: build a TableResult from components."""
    from validation.run_external_validation import _finding_matches

    missing_expected = [
        f for f in expected_findings if not _finding_matches(f, actual_finding_codes)
    ]
    covered: set[str] = set()
    for ec in expected_findings:
        if ec == "ambiguous_schema_field":
            from validation.run_external_validation import _AMBIGUOUS_FINDING_CODES

            covered.update(
                ac for ac in actual_finding_codes if ac in _AMBIGUOUS_FINDING_CODES
            )
        else:
            covered.add(ec)
    unexpected = [ac for ac in actual_finding_codes if ac not in covered]
    exact = all(r.is_tp or r.is_tn for r in field_results)
    return TableResult(
        dataset_id=dataset_id,
        table_filename=f"{dataset_id}.csv",
        score=100,
        audit_confidence="high",
        field_results=field_results,
        actual_finding_codes=actual_finding_codes,
        expected_finding_codes=expected_findings,
        missing_expected_findings=missing_expected,
        unexpected_findings=unexpected,
        exact_schema_match=exact,
    )


def test_aggregate_metrics_all_tp():
    """Aggregate metrics: all TP gives precision=1 recall=1."""
    fr = [FieldResult("p_value", "p_value", "p_value")]
    r = _make_table_result("T1", fr, [], [])
    metrics = aggregate_metrics([r])
    assert metrics["field_level"]["true_positives"] == 1
    assert metrics["field_level"]["false_positives"] == 0
    assert metrics["field_level"]["false_negatives"] == 0
    assert metrics["field_level"]["precision"] == 1.0
    assert metrics["field_level"]["recall"] == 1.0


def test_aggregate_metrics_fp_lowers_precision():
    """FP lowers precision below 1.0."""
    fr = [
        FieldResult("p_value", "p_value", "p_value"),  # TP
        FieldResult("fdr", None, "some_col"),  # FP
    ]
    r = _make_table_result("T1", fr, [], [])
    metrics = aggregate_metrics([r])
    assert metrics["field_level"]["false_positives"] == 1
    assert metrics["field_level"]["precision"] < 1.0
    assert metrics["field_level"]["recall"] == 1.0


def test_aggregate_metrics_fn_lowers_recall():
    """FN lowers recall below 1.0."""
    fr = [
        FieldResult("p_value", "p_value", "p_value"),  # TP
        FieldResult("fdr", "FDR", None),  # FN
    ]
    r = _make_table_result("T1", fr, [], [])
    metrics = aggregate_metrics([r])
    assert metrics["field_level"]["false_negatives"] == 1
    assert metrics["field_level"]["recall"] < 1.0
    assert metrics["field_level"]["precision"] == 1.0


def test_finding_metrics_tp():
    """Finding TP when expected finding is emitted."""
    fr = [FieldResult("p_value", None, None)]
    r = _make_table_result("T1", fr, ["missing_p_value"], ["missing_p_value"])
    assert r.finding_tp == 1
    assert r.finding_fp == 0
    assert r.finding_fn == 0


def test_finding_metrics_fn():
    """Finding FN when expected finding is not emitted."""
    fr = [FieldResult("p_value", None, None)]
    r = _make_table_result("T1", fr, ["missing_p_value"], [])
    assert r.finding_tp == 0
    assert r.finding_fn == 1


def test_finding_metrics_fp():
    """Finding FP when unexpected finding is emitted."""
    fr = [FieldResult("p_value", "p_value", "p_value")]
    r = _make_table_result("T1", fr, [], ["missing_p_value"])
    assert r.finding_fp == 1


def test_finding_metrics_ambiguous_schema_field_generic_code():
    """Generic 'ambiguous_schema_field' expected code matches any specific ambiguous_* actual code."""
    fr = [FieldResult("p_value", ["p_value", "pval"], "p_value")]
    r = _make_table_result("T1", fr, ["ambiguous_schema_field"], ["ambiguous_p_value"])
    assert r.finding_tp == 1
    assert r.finding_fn == 0
    assert r.finding_fp == 0


# ---------------------------------------------------------------------------
# Runner error handling
# ---------------------------------------------------------------------------


def test_runner_errors_on_missing_registry(tmp_path):
    """Runner raises FileNotFoundError when registry does not exist."""
    with pytest.raises(FileNotFoundError, match="Registry file not found"):
        run_external_validation(
            registry_path=tmp_path / "nonexistent_registry.csv",
            labels_path=tmp_path / "labels.csv",
            tables_dir=tmp_path / "tables",
        )


def test_runner_errors_on_missing_labels(tmp_path):
    """Runner raises FileNotFoundError when labels file does not exist."""
    registry_path = tmp_path / "registry.csv"
    registry_path.write_text(
        "dataset_id,source_title,source_type,source_url_or_doi,license_or_access_note,"
        "table_filename,table_description,organism_or_sample_context,platform_if_known,"
        "study_domain,included,exclusion_reason,notes\n"
        "T1,Test,other,doi:0,CC BY,table.csv,Test,Human,unknown,metabolomics,yes,,\n"
    )
    with pytest.raises(FileNotFoundError, match="Labels file not found"):
        run_external_validation(
            registry_path=registry_path,
            labels_path=tmp_path / "nonexistent_labels.csv",
            tables_dir=tmp_path / "tables",
        )


def test_runner_errors_on_missing_table_csv(tmp_path):
    """Runner raises FileNotFoundError when a referenced table CSV does not exist."""
    tables_dir = tmp_path / "tables"
    tables_dir.mkdir()

    registry_path = tmp_path / "registry.csv"
    registry_path.write_text(
        "dataset_id,source_title,source_type,source_url_or_doi,license_or_access_note,"
        "table_filename,table_description,organism_or_sample_context,platform_if_known,"
        "study_domain,included,exclusion_reason,notes\n"
        "T1,Test,other,doi:0,CC BY,missing_table.csv,Test,Human,unknown,metabolomics,yes,,\n"
    )
    labels_path = tmp_path / "labels.csv"
    labels_path.write_text(
        "dataset_id,table_filename,compound_id,effect_size,p_value,fdr,annotation,"
        "expected_findings,reviewer_id,review_notes\n"
        "T1,missing_table.csv,compound_id,logFC,p_value,FDR,Annotation,,reviewer_a,\n"
    )

    with pytest.raises(FileNotFoundError, match="Missing table file"):
        run_external_validation(
            registry_path=registry_path,
            labels_path=labels_path,
            tables_dir=tables_dir,
        )


# ---------------------------------------------------------------------------
# End-to-end runner test with temporary mini external dataset
# ---------------------------------------------------------------------------


def _write_csv(path: Path, content: str) -> None:
    path.write_text(content, encoding="utf-8")


def test_runner_end_to_end_mini_dataset(tmp_path):
    """Runner correctly validates a temporary two-table mini external dataset.

    Table 1: complete standard table — expects compound_id, effect_size, p_value, fdr, annotation.
    Table 2: missing stats table — expects compound_id, effect_size, annotation; no p_value or fdr.
    """
    tables_dir = tmp_path / "tables"
    tables_dir.mkdir()

    # Table 1: complete
    _write_csv(
        tables_dir / "complete.csv",
        "compound_id,logFC,p_value,FDR,Annotation\n"
        "M1,1.5,0.01,0.05,confirmed\n"
        "M2,-0.3,0.20,0.40,putative\n",
    )

    # Table 2: missing p_value and FDR
    _write_csv(
        tables_dir / "missing_stats.csv",
        "compound_id,logFC,Annotation\nM1,1.5,confirmed\nM2,-0.3,putative\n",
    )

    registry_path = tmp_path / "registry.csv"
    registry_path.write_text(
        "dataset_id,source_title,source_type,source_url_or_doi,license_or_access_note,"
        "table_filename,table_description,organism_or_sample_context,platform_if_known,"
        "study_domain,included,exclusion_reason,notes\n"
        "EXT_001,Complete Table,other,doi:example,test,complete.csv,Complete standard,Human,unknown,metabolomics,yes,,\n"
        "EXT_002,Missing Stats,other,doi:example,test,missing_stats.csv,Missing stats,Human,unknown,metabolomics,yes,,\n"
    )

    labels_path = tmp_path / "labels.csv"
    labels_path.write_text(
        "dataset_id,table_filename,compound_id,effect_size,p_value,fdr,annotation,"
        "expected_findings,reviewer_id,review_notes\n"
        "EXT_001,complete.csv,compound_id,logFC,p_value,FDR,Annotation,,reviewer_a,Complete\n"
        "EXT_002,missing_stats.csv,compound_id,logFC,,,Annotation,"
        "missing_p_value|missing_fdr,reviewer_a,Missing stats\n"
    )

    output = run_external_validation(
        registry_path=registry_path,
        labels_path=labels_path,
        tables_dir=tables_dir,
        verbose=False,
    )

    # Basic shape
    assert output["n_tables"] == 2

    # Field-level: complete table has 5 TPs; missing stats table has 3 TPs + 2 TNs
    # All present fields should be detected correctly → precision=1.0, recall=1.0
    assert output["field_level"]["precision"] == 1.0
    assert output["field_level"]["recall"] == 1.0
    assert output["field_level"]["false_positives"] == 0
    assert output["field_level"]["false_negatives"] == 0

    # Findings: EXT_002 should emit missing_p_value + missing_fdr
    assert output["finding_level"]["recall"] == 1.0
    assert output["finding_level"]["false_negatives"] == 0

    # EXT_002 expected findings should both be detected
    ext002_table = next(t for t in output["tables"] if t["dataset_id"] == "EXT_002")
    assert ext002_table["finding_fn"] == 0
    assert ext002_table["finding_tp"] == 2

    # Score check
    ext001_table = next(t for t in output["tables"] if t["dataset_id"] == "EXT_001")
    assert ext001_table["score"] == 100
    assert ext001_table["audit_confidence"] == "high"
    assert ext002_table["score"] == 40
    assert ext002_table["audit_confidence"] == "low"


def test_runner_writes_json_output(tmp_path):
    """Runner writes a JSON file when --output is provided."""
    tables_dir = tmp_path / "tables"
    tables_dir.mkdir()
    _write_csv(
        tables_dir / "complete.csv",
        "compound_id,logFC,p_value,FDR,Annotation\nM1,1.5,0.01,0.05,confirmed\n",
    )

    registry_path = tmp_path / "registry.csv"
    registry_path.write_text(
        "dataset_id,source_title,source_type,source_url_or_doi,license_or_access_note,"
        "table_filename,table_description,organism_or_sample_context,platform_if_known,"
        "study_domain,included,exclusion_reason,notes\n"
        "EXT_001,Test,other,doi:x,test,complete.csv,Test,Human,unknown,metabolomics,yes,,\n"
    )
    labels_path = tmp_path / "labels.csv"
    labels_path.write_text(
        "dataset_id,table_filename,compound_id,effect_size,p_value,fdr,annotation,"
        "expected_findings,reviewer_id,review_notes\n"
        "EXT_001,complete.csv,compound_id,logFC,p_value,FDR,Annotation,,reviewer_a,\n"
    )
    output_path = tmp_path / "results.json"

    run_external_validation(
        registry_path=registry_path,
        labels_path=labels_path,
        tables_dir=tables_dir,
        output_path=output_path,
        verbose=False,
    )

    assert output_path.exists()
    data = json.loads(output_path.read_text(encoding="utf-8"))
    assert "n_tables" in data
    assert data["n_tables"] == 1
