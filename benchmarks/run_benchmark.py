#!/usr/bin/env python
"""Benchmark runner for Validex schema detection and audit accuracy.

Run from the repo root:
    python benchmarks/run_benchmark.py

Exits 0 if all fixtures pass, 1 if any fail.
"""
from __future__ import annotations

import json
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import pandas as pd

# Allow running as a script from the repo root, or as a module from tests/
_REPO_ROOT = Path(__file__).resolve().parent.parent
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from validex.audit import audit_dataframe  # noqa: E402

BENCHMARKS_DIR = Path(__file__).resolve().parent
FIXTURES_DIR = BENCHMARKS_DIR / "fixtures"
EXPECTED_DIR = BENCHMARKS_DIR / "expected"

# ---------------------------------------------------------------------------
# Finding code extraction
# ---------------------------------------------------------------------------

_FINDING_CODE_RULES: list[tuple[str, str]] = [
    ("invalid p-value", "invalid_p_value"),
    ("invalid fdr", "invalid_fdr"),
    ("missing p-value", "missing_p_value"),
    ("missing p_value", "missing_p_value"),
    ("missing p-values", "missing_p_value"),
    ("missing fdr", "missing_fdr"),
    ("ambiguous p_value", "ambiguous_p_value"),
    ("ambiguous fdr", "ambiguous_fdr"),
    ("consistency", "fdr_consistency_warning"),
]


def _flag_to_code(title: str) -> str:
    t = title.lower()
    for substring, code in _FINDING_CODE_RULES:
        if substring in t:
            return code
    return t.replace(" ", "_").replace("/", "_").replace("-", "_")


# ---------------------------------------------------------------------------
# Data structures
# ---------------------------------------------------------------------------

@dataclass
class FieldPrediction:
    fixture: str
    canonical: str
    expected: str | None
    actual: str | None

    @property
    def is_tp(self) -> bool:
        return self.expected is not None and self.actual == self.expected

    @property
    def is_fp(self) -> bool:
        return self.expected is None and self.actual is not None

    @property
    def is_fn(self) -> bool:
        return self.expected is not None and (self.actual is None or self.actual != self.expected)

    @property
    def is_tn(self) -> bool:
        return self.expected is None and self.actual is None


@dataclass
class BenchmarkResult:
    fixture: str
    passed: bool
    score: int
    audit_confidence: str
    expected_score_band: tuple[int, int]
    expected_confidence_label: str
    detected: dict[str, str | None]
    expected_schema: dict[str, str | None]
    actual_findings: list[str]
    required_findings: list[str]
    forbidden_findings: list[str]
    missing_required: list[str]
    unexpected_forbidden: list[str]
    schema_failures: list[str]
    field_predictions: list[FieldPrediction]
    known_limitations: list[str] = field(default_factory=list)


# ---------------------------------------------------------------------------
# Core runner
# ---------------------------------------------------------------------------

def run_single_fixture(
    fixture_path: Path,
    expected_schema: dict[str, str | None],
    expected_findings: dict[str, Any],
    expected_score: dict[str, Any],
) -> BenchmarkResult:
    """Run the audit on one fixture and compare to expectations."""
    df = pd.read_csv(fixture_path)
    result = audit_dataframe(df)

    actual_findings = [_flag_to_code(f["title"]) for f in result["flags"]]
    audit_confidence = result.get("audit_confidence", "unknown")

    required = expected_findings.get("required_findings", [])
    forbidden = expected_findings.get("forbidden_findings", [])
    known_limitations = expected_findings.get("known_limitations", [])

    score_band = expected_score.get("score_band", [0, 100])
    expected_confidence_label = expected_score.get("confidence_label", "")
    score = result["confidence"]
    detected = result["detected"]

    missing_required = [f for f in required if f not in actual_findings]
    unexpected_forbidden = [f for f in forbidden if f in actual_findings]
    score_ok = score_band[0] <= score <= score_band[1]
    confidence_ok = (not expected_confidence_label) or (audit_confidence == expected_confidence_label)

    schema_failures: list[str] = []
    field_predictions: list[FieldPrediction] = []

    for canonical, expected_col in expected_schema.items():
        actual_col = detected.get(canonical)
        pred = FieldPrediction(
            fixture=fixture_path.name,
            canonical=canonical,
            expected=expected_col,
            actual=actual_col,
        )
        field_predictions.append(pred)
        if not pred.is_tp and not pred.is_tn:
            schema_failures.append(
                f"{canonical}: expected={expected_col!r}, actual={actual_col!r}"
            )

    passed = (
        not missing_required
        and not unexpected_forbidden
        and score_ok
        and not schema_failures
        and confidence_ok
    )

    return BenchmarkResult(
        fixture=fixture_path.name,
        passed=passed,
        score=score,
        audit_confidence=audit_confidence,
        expected_score_band=(score_band[0], score_band[1]),
        expected_confidence_label=expected_confidence_label,
        detected=detected,
        expected_schema=expected_schema,
        actual_findings=actual_findings,
        required_findings=required,
        forbidden_findings=forbidden,
        missing_required=missing_required,
        unexpected_forbidden=unexpected_forbidden,
        schema_failures=schema_failures,
        field_predictions=field_predictions,
        known_limitations=known_limitations,
    )


def run_all_benchmarks(
    fixtures_dir: Path | None = None,
    expected_dir: Path | None = None,
) -> list[BenchmarkResult]:
    """Load all fixtures and run the benchmark suite. Returns list of results."""
    fixtures_dir = fixtures_dir or FIXTURES_DIR
    expected_dir = expected_dir or EXPECTED_DIR

    schema_exp: dict[str, dict[str, str | None]] = json.loads(
        (expected_dir / "expected_schema.json").read_text()
    )
    findings_exp: dict[str, dict[str, Any]] = json.loads(
        (expected_dir / "expected_findings.json").read_text()
    )
    scores_exp: dict[str, dict[str, Any]] = json.loads(
        (expected_dir / "expected_scores.json").read_text()
    )

    results: list[BenchmarkResult] = []
    for fixture_name, exp_schema in schema_exp.items():
        fixture_path = fixtures_dir / fixture_name
        if not fixture_path.exists():
            raise FileNotFoundError(f"Fixture not found: {fixture_path}")
        result = run_single_fixture(
            fixture_path,
            exp_schema,
            findings_exp.get(fixture_name, {}),
            scores_exp.get(fixture_name, {}),
        )
        results.append(result)

    return results


# ---------------------------------------------------------------------------
# Metrics
# ---------------------------------------------------------------------------

def compute_metrics(results: list[BenchmarkResult]) -> dict[str, Any]:
    """Compute precision, recall, and related counts from benchmark results."""
    all_preds = [p for r in results for p in r.field_predictions]

    tp = sum(1 for p in all_preds if p.is_tp)
    fp = sum(1 for p in all_preds if p.is_fp)
    fn = sum(1 for p in all_preds if p.is_fn)
    tn = sum(1 for p in all_preds if p.is_tn)

    precision = tp / (tp + fp) if (tp + fp) > 0 else 1.0
    recall = tp / (tp + fn) if (tp + fn) > 0 else 1.0

    return {
        "tp": tp,
        "fp": fp,
        "fn": fn,
        "tn": tn,
        "precision": precision,
        "recall": recall,
        "total_fixtures": len(results),
        "passed_fixtures": sum(1 for r in results if r.passed),
        "failed_fixtures": sum(1 for r in results if not r.passed),
    }


# ---------------------------------------------------------------------------
# Report printing
# ---------------------------------------------------------------------------

def _schema_summary(detected: dict[str, str | None]) -> str:
    parts = []
    for field_name, col in detected.items():
        if col is not None:
            parts.append(f"{field_name}={col!r}")
    return ", ".join(parts) if parts else "(none)"


def print_report(results: list[BenchmarkResult], metrics: dict[str, Any]) -> None:
    """Print a concise benchmark report to stdout."""
    col_w = [40, 6, 5, 8, 12, 40]
    header = (
        f"{'Fixture':<{col_w[0]}} {'Pass':>{col_w[1]}} {'Score':>{col_w[2]}} "
        f"{'Confid.':>{col_w[3]}} {'Score Band':>{col_w[4]}} {'Issues':<{col_w[5]}}"
    )
    sep = "=" * 120
    thin = "-" * 120

    print()
    print(sep)
    print("  Validex Benchmark Report")
    print(sep)
    print(header)
    print(thin)

    for r in results:
        status = "PASS" if r.passed else "FAIL"
        band = f"[{r.expected_score_band[0]}-{r.expected_score_band[1]}]"
        issues: list[str] = []
        if r.schema_failures:
            issues.append(f"schema: {'; '.join(r.schema_failures)}")
        if r.missing_required:
            issues.append(f"missing findings: {r.missing_required}")
        if r.unexpected_forbidden:
            issues.append(f"unexpected findings: {r.unexpected_forbidden}")
        if not (r.expected_score_band[0] <= r.score <= r.expected_score_band[1]):
            issues.append(f"score {r.score} outside {band}")
        if r.expected_confidence_label and r.audit_confidence != r.expected_confidence_label:
            issues.append(
                f"confidence {r.audit_confidence!r} != expected {r.expected_confidence_label!r}"
            )
        issue_str = "; ".join(issues) if issues else "-"
        print(
            f"{r.fixture:<{col_w[0]}} {status:>{col_w[1]}} {r.score:>{col_w[2]}} "
            f"{r.audit_confidence:>{col_w[3]}} {band:>{col_w[4]}} {issue_str:<{col_w[5]}}"
        )

    print(thin)
    print()
    print("  Schema Detection Metrics")
    print(f"  True Positives  (TP): {metrics['tp']}")
    print(f"  False Positives (FP): {metrics['fp']}")
    print(f"  False Negatives (FN): {metrics['fn']}")
    print(f"  True Negatives  (TN): {metrics['tn']}")
    print(f"  Precision: {metrics['precision']:.4f}")
    print(f"  Recall:    {metrics['recall']:.4f}")
    print()
    print(f"  Fixtures: {metrics['passed_fixtures']}/{metrics['total_fixtures']} passed")
    print(sep)
    print()

    if results:
        print("  Detected schema per fixture:")
        for r in results:
            print(f"    {r.fixture:<42} [{r.audit_confidence:<6}] {_schema_summary(r.detected)}")
        print()

    any_limits = any(r.known_limitations for r in results)
    if any_limits:
        print("  Known limitations:")
        for r in results:
            for note in r.known_limitations:
                print(f"    [{r.fixture}] {note}")
        print()


# ---------------------------------------------------------------------------
# Script entry point
# ---------------------------------------------------------------------------

def main() -> int:
    try:
        results = run_all_benchmarks()
    except Exception as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1

    metrics = compute_metrics(results)
    print_report(results, metrics)

    if metrics["failed_fixtures"] > 0:
        print(f"BENCHMARK FAILED: {metrics['failed_fixtures']} fixture(s) did not meet expectations.")
        return 1

    print("BENCHMARK PASSED: all fixtures met expectations.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
