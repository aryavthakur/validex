#!/usr/bin/env python
"""External validation runner for Validex.

Evaluates Validex schema detection and audit behavior against manually labeled
real published metabolomics result tables.

Usage:
    python validation/run_external_validation.py \\
        --registry validation/registry.csv \\
        --labels   validation/labels.csv \\
        --tables-dir validation/tables \\
        --output   validation/external_results.json

IMPORTANT: This runner requires real external tables, a completed registry CSV,
and completed labels CSV. It does not produce results when run on the example
files without actual table CSV files in --tables-dir.

No external validation results are claimed unless a completed labeled external
dataset is provided and the output JSON is committed with full protocol
documentation. See docs/external_validation_protocol.md.
"""

from __future__ import annotations

import argparse
import hashlib
import csv
import json
import sys
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import pandas as pd

# Allow running as a script from the repo root
_REPO_ROOT = Path(__file__).resolve().parent.parent
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from validex.audit import audit_dataframe  # noqa: E402
from validex import __version__  # noqa: E402


# ---------------------------------------------------------------------------
# Finding code extraction (mirrors benchmark logic)
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
    ("ambiguous compound_id", "ambiguous_compound_id"),
    ("ambiguous effect_size", "ambiguous_effect_size"),
    ("ambiguous annotation", "ambiguous_annotation"),
    ("consistency", "fdr_consistency_warning"),
]

# Finding codes that map to the generic "ambiguous_schema_field" label
_AMBIGUOUS_FINDING_CODES = {
    "ambiguous_p_value",
    "ambiguous_fdr",
    "ambiguous_compound_id",
    "ambiguous_effect_size",
    "ambiguous_annotation",
}


def _flag_to_code(title: str) -> str:
    t = title.lower()
    for substring, code in _FINDING_CODE_RULES:
        if substring in t:
            return code
    return t.replace(" ", "_").replace("/", "_").replace("-", "_")


# ---------------------------------------------------------------------------
# Registry and label data structures
# ---------------------------------------------------------------------------

REGISTRY_REQUIRED_COLUMNS = {
    "dataset_id",
    "source_title",
    "source_type",
    "source_url_or_doi",
    "license_or_access_note",
    "table_filename",
    "table_description",
    "organism_or_sample_context",
    "platform_if_known",
    "study_domain",
    "included",
    "exclusion_reason",
    "notes",
}

LABELS_REQUIRED_COLUMNS = {
    "dataset_id",
    "table_filename",
    "compound_id",
    "effect_size",
    "p_value",
    "fdr",
    "annotation",
    "expected_findings",
    "reviewer_id",
    "review_notes",
}

CANONICAL_FIELDS = ["compound_id", "effect_size", "p_value", "fdr", "annotation"]


def _load_csv(path: Path) -> list[dict[str, str]]:
    with open(path, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        return [dict(row) for row in reader]


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _safe_manifest_path(base: Path, raw: str | None) -> Path | None:
    if not raw:
        return None
    path = Path(raw)
    if path.is_absolute():
        raise ValueError(f"Manifest path must be relative, not absolute: {raw}")
    resolved = (base / path).resolve()
    if base.resolve() != resolved and base.resolve() not in resolved.parents:
        raise ValueError(f"Manifest path escapes validation directory: {raw}")
    if any(part == ".." for part in path.parts):
        raise ValueError(f"Manifest path must not contain '..': {raw}")
    if resolved.is_symlink():
        raise ValueError(f"Manifest path must not be a symlink: {raw}")
    return resolved


@dataclass(frozen=True)
class ManifestDataset:
    dataset_id: str
    title: str
    source: str
    version: str
    license: str
    redistribution_allowed: bool
    local_path: Path | None
    download_url: str | None
    sha256: str | None
    data_category: str
    expected_schema: dict[str, str]
    ground_truth_source: str
    preprocessing: list[str]
    enabled_by_default: bool
    required_for_release: bool
    notes: str


def load_manifest(manifest_path: Path) -> list[ManifestDataset]:
    base = manifest_path.resolve().parent
    raw = json.loads(manifest_path.read_text(encoding="utf-8"))
    datasets = raw.get("datasets")
    if not isinstance(datasets, list):
        raise ValueError("Manifest must contain a datasets list")
    parsed: list[ManifestDataset] = []
    seen_dataset_ids: set[str] = set()
    for item in datasets:
        if not isinstance(item, dict):
            raise ValueError("Each manifest dataset must be an object")
        dataset_id = str(item.get("dataset_id", "")).strip()
        if not dataset_id:
            raise ValueError("Manifest dataset is missing dataset_id")
        if dataset_id in seen_dataset_ids:
            raise ValueError(f"Manifest contains duplicate dataset_id: {dataset_id}")
        seen_dataset_ids.add(dataset_id)
        local_path = _safe_manifest_path(base, item.get("local_path"))
        sha256 = item.get("sha256")
        required = bool(item.get("required_for_release", False))
        redistribution_allowed = bool(item.get("redistribution_allowed", False))
        license_name = str(item.get("license", "")).strip()
        if required and local_path is not None and not sha256:
            raise ValueError(f"{dataset_id}: release-required local dataset needs sha256")
        if redistribution_allowed and license_name.lower() in {"", "unknown", "tbd"}:
            raise ValueError(f"{dataset_id}: redistributed dataset has unknown license")
        parsed.append(
            ManifestDataset(
                dataset_id=dataset_id,
                title=str(item.get("title", "")).strip(),
                source=str(item.get("source", "")).strip(),
                version=str(item.get("version", "")).strip(),
                license=license_name,
                redistribution_allowed=redistribution_allowed,
                local_path=local_path,
                download_url=item.get("download_url"),
                sha256=sha256,
                data_category=str(item.get("data_category", "unknown")).strip(),
                expected_schema=dict(item.get("expected_schema", {})),
                ground_truth_source=str(item.get("ground_truth_source", "")).strip(),
                preprocessing=list(item.get("preprocessing", [])),
                enabled_by_default=bool(item.get("enabled_by_default", False)),
                required_for_release=required,
                notes=str(item.get("notes", "")).strip(),
            )
        )
    return parsed


def run_manifest_validation(
    manifest_path: Path,
    output_path: Path | None = None,
    report_path: Path | None = None,
) -> dict[str, Any]:
    datasets = load_manifest(manifest_path)
    dataset_reports: list[dict[str, Any]] = []
    blockers: list[str] = []
    processed = 0
    for dataset in datasets:
        status = "unavailable"
        checksum_actual = None
        if dataset.local_path is not None and dataset.local_path.exists():
            checksum_actual = sha256_file(dataset.local_path)
            if dataset.sha256 and checksum_actual != dataset.sha256:
                status = "checksum_mismatch"
                if dataset.required_for_release:
                    blockers.append(f"{dataset.dataset_id}: checksum mismatch")
            elif dataset.enabled_by_default and dataset.local_path.suffix.lower() == ".csv":
                df = pd.read_csv(dataset.local_path)
                audit_dataframe(df)
                processed += 1
                status = "processed"
            else:
                status = "available_not_processed"
        elif dataset.required_for_release:
            blockers.append(f"{dataset.dataset_id}: required dataset is unavailable")
        dataset_reports.append(
            {
                "dataset_id": dataset.dataset_id,
                "title": dataset.title,
                "source": dataset.source,
                "version": dataset.version,
                "license": dataset.license,
                "redistribution_allowed": dataset.redistribution_allowed,
                "data_category": dataset.data_category,
                "enabled_by_default": dataset.enabled_by_default,
                "required_for_release": dataset.required_for_release,
                "sha256": dataset.sha256,
                "sha256_actual": checksum_actual,
                "ground_truth_source": dataset.ground_truth_source,
                "preprocessing": dataset.preprocessing,
                "status": status,
                "notes": dataset.notes,
            }
        )
    status = (
        "FAILED"
        if blockers
        else ("COMPLETED" if processed else "EXTERNAL_VALIDATION_INCOMPLETE")
    )
    output = {
        "protocol_version": "2.0",
        "status": status,
        "software": {"name": "validex", "version": __version__},
        "timestamp_utc": datetime.now(timezone.utc).isoformat(),
        "manifest": str(manifest_path),
        "n_datasets": len(datasets),
        "n_processed": processed,
        "datasets": dataset_reports,
        "blockers": blockers,
        "metrics": {
            "independent_external_dataset_performance": None,
            "synthetic_benchmark_performance": "Run python benchmarks/run_benchmark.py separately.",
        },
        "limitations": [
            "No independent external-validation performance metric is reported unless a legally usable labeled external dataset is present.",
            "Synthetic and repository fixtures are regression evidence, not independent external validation.",
            "AI is excluded from external validation.",
        ],
        "reproduction_commands": [
            f"python validation/run_external_validation.py --manifest {manifest_path.as_posix()}"
        ],
    }
    if output_path:
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(json.dumps(output, indent=2) + "\n", encoding="utf-8")
    if report_path:
        report_path.parent.mkdir(parents=True, exist_ok=True)
        lines = [
            "# Validex External Validation Report",
            "",
            f"Status: {status}",
            f"Software version: {__version__}",
            f"Datasets in manifest: {len(datasets)}",
            f"Datasets processed: {processed}",
            "",
            "## Limitations",
            "",
            "- Independent external validation is incomplete unless processed datasets are reported above.",
            "- Synthetic benchmarks are separate from external validation.",
            "- AI is excluded.",
        ]
        report_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return output


def _check_required_columns(
    rows: list[dict[str, str]], required: set[str], path: Path
) -> None:
    if not rows:
        return
    actual = set(rows[0].keys())
    missing = required - actual
    if missing:
        raise ValueError(
            f"{path}: missing required columns: {sorted(missing)}. "
            f"Found columns: {sorted(actual)}"
        )


# ---------------------------------------------------------------------------
# Label parsing
# ---------------------------------------------------------------------------


@dataclass
class ParsedLabel:
    """Parsed canonical field label for one table."""

    dataset_id: str
    table_filename: str
    # Each canonical field: None = absent, str = expected exact column, list = AMBIGUOUS candidates
    compound_id: str | list[str] | None
    effect_size: str | list[str] | None
    p_value: str | list[str] | None
    fdr: str | list[str] | None
    annotation: str | list[str] | None
    expected_findings: list[str]
    reviewer_id: str
    review_notes: str

    def field_value(self, canonical: str) -> str | list[str] | None:
        return getattr(self, canonical, None)


def _parse_field_label(raw: str) -> str | list[str] | None:
    """Parse a single field label cell.

    Returns:
        None           — field is labeled as absent (empty string)
        str            — exact expected original column name
        list[str]      — AMBIGUOUS: field present but multiple candidates
    """
    raw = raw.strip()
    if raw == "":
        return None
    if raw.startswith("AMBIGUOUS:"):
        candidates = raw[len("AMBIGUOUS:") :].split("|")
        return [c.strip() for c in candidates if c.strip()]
    return raw


def _parse_findings(raw: str) -> list[str]:
    """Parse pipe-separated expected findings string into a list of codes."""
    if not raw.strip():
        return []
    return [f.strip() for f in raw.strip().split("|") if f.strip()]


def parse_label_row(row: dict[str, str]) -> ParsedLabel:
    return ParsedLabel(
        dataset_id=row["dataset_id"].strip(),
        table_filename=row["table_filename"].strip(),
        compound_id=_parse_field_label(row.get("compound_id", "")),
        effect_size=_parse_field_label(row.get("effect_size", "")),
        p_value=_parse_field_label(row.get("p_value", "")),
        fdr=_parse_field_label(row.get("fdr", "")),
        annotation=_parse_field_label(row.get("annotation", "")),
        expected_findings=_parse_findings(row.get("expected_findings", "")),
        reviewer_id=row.get("reviewer_id", "").strip(),
        review_notes=row.get("review_notes", "").strip(),
    )


# ---------------------------------------------------------------------------
# Metric computation
# ---------------------------------------------------------------------------


@dataclass
class FieldResult:
    canonical: str
    expected: str | list[str] | None  # None = absent, str/list = present
    actual: str | None  # None = not detected, str = detected column

    @property
    def is_tp(self) -> bool:
        """Correct detection of a present field."""
        if self.expected is None:
            return False
        if isinstance(self.expected, list):
            # AMBIGUOUS: TP if actual is one of the candidates
            return self.actual is not None and self.actual in self.expected
        return self.actual == self.expected

    @property
    def is_fp(self) -> bool:
        """Detection of a field labeled as absent."""
        return self.expected is None and self.actual is not None

    @property
    def is_fn(self) -> bool:
        """Missed detection of a field labeled as present."""
        if self.expected is None:
            return False
        if isinstance(self.expected, list):
            return self.actual is None or self.actual not in self.expected
        return self.actual != self.expected

    @property
    def is_tn(self) -> bool:
        """Correct non-detection of an absent field."""
        return self.expected is None and self.actual is None


@dataclass
class TableResult:
    dataset_id: str
    table_filename: str
    score: int
    audit_confidence: str
    field_results: list[FieldResult]
    actual_finding_codes: list[str]
    expected_finding_codes: list[str]
    missing_expected_findings: list[str]
    unexpected_findings: list[str]
    exact_schema_match: bool

    @property
    def field_tp(self) -> int:
        return sum(1 for r in self.field_results if r.is_tp)

    @property
    def field_fp(self) -> int:
        return sum(1 for r in self.field_results if r.is_fp)

    @property
    def field_fn(self) -> int:
        return sum(1 for r in self.field_results if r.is_fn)

    @property
    def field_tn(self) -> int:
        return sum(1 for r in self.field_results if r.is_tn)

    @property
    def finding_tp(self) -> int:
        return sum(
            1
            for f in self.expected_finding_codes
            if _finding_matches(f, self.actual_finding_codes)
        )

    @property
    def finding_fp(self) -> int:
        return len(self.unexpected_findings)

    @property
    def finding_fn(self) -> int:
        return len(self.missing_expected_findings)


def _normalize_finding_code(code: str) -> str:
    """Normalize an expected finding code for comparison.

    The generic 'ambiguous_schema_field' label matches any specific ambiguous_* code.
    """
    return code.strip().lower()


def _finding_matches(expected_code: str, actual_codes: list[str]) -> bool:
    """Return True if expected_code is satisfied by any code in actual_codes."""
    ec = _normalize_finding_code(expected_code)
    if ec == "ambiguous_schema_field":
        return any(ac in _AMBIGUOUS_FINDING_CODES for ac in actual_codes)
    return ec in actual_codes


def compute_table_result(
    dataset_id: str,
    label: ParsedLabel,
    audit_result: dict[str, Any],
) -> TableResult:
    detected = audit_result["detected"]
    actual_finding_codes = [_flag_to_code(f["title"]) for f in audit_result["flags"]]

    field_results: list[FieldResult] = []
    for canonical in CANONICAL_FIELDS:
        expected = label.field_value(canonical)
        actual = detected.get(canonical)
        field_results.append(
            FieldResult(canonical=canonical, expected=expected, actual=actual)
        )

    exact_schema_match = all(r.is_tp or r.is_tn for r in field_results)

    expected_codes = label.expected_findings
    missing_expected = [
        c for c in expected_codes if not _finding_matches(c, actual_finding_codes)
    ]
    # FP findings: emitted by Validex but not expected
    # For generic "ambiguous_schema_field" expected codes, any ambiguous_* actual code satisfies them
    # Build the set of "covered" actual codes
    covered_actuals: set[str] = set()
    for ec in expected_codes:
        if _normalize_finding_code(ec) == "ambiguous_schema_field":
            covered_actuals.update(
                ac for ac in actual_finding_codes if ac in _AMBIGUOUS_FINDING_CODES
            )
        else:
            covered_actuals.add(_normalize_finding_code(ec))
    unexpected = [ac for ac in actual_finding_codes if ac not in covered_actuals]

    return TableResult(
        dataset_id=dataset_id,
        table_filename=label.table_filename,
        score=audit_result["confidence"],
        audit_confidence=audit_result["audit_confidence"],
        field_results=field_results,
        actual_finding_codes=actual_finding_codes,
        expected_finding_codes=expected_codes,
        missing_expected_findings=missing_expected,
        unexpected_findings=unexpected,
        exact_schema_match=exact_schema_match,
    )


def aggregate_metrics(results: list[TableResult]) -> dict[str, Any]:
    tp = sum(r.field_tp for r in results)
    fp = sum(r.field_fp for r in results)
    fn = sum(r.field_fn for r in results)
    tn = sum(r.field_tn for r in results)

    precision = tp / (tp + fp) if (tp + fp) > 0 else 1.0
    recall = tp / (tp + fn) if (tp + fn) > 0 else 1.0

    f_tp = sum(r.finding_tp for r in results)
    f_fp = sum(r.finding_fp for r in results)
    f_fn = sum(r.finding_fn for r in results)
    finding_precision = f_tp / (f_tp + f_fp) if (f_tp + f_fp) > 0 else 1.0
    finding_recall = f_tp / (f_tp + f_fn) if (f_tp + f_fn) > 0 else 1.0

    exact_match_rate = (
        sum(1 for r in results if r.exact_schema_match) / len(results)
        if results
        else 0.0
    )

    scores = [r.score for r in results]
    conf_dist: dict[str, int] = {"high": 0, "medium": 0, "low": 0}
    for r in results:
        conf_dist[r.audit_confidence] = conf_dist.get(r.audit_confidence, 0) + 1

    return {
        "n_tables": len(results),
        "field_level": {
            "true_positives": tp,
            "false_positives": fp,
            "false_negatives": fn,
            "true_negatives": tn,
            "precision": round(precision, 4),
            "recall": round(recall, 4),
        },
        "exact_schema_match_rate": round(exact_match_rate, 4),
        "finding_level": {
            "true_positives": f_tp,
            "false_positives": f_fp,
            "false_negatives": f_fn,
            "precision": round(finding_precision, 4),
            "recall": round(finding_recall, 4),
        },
        "score_distribution": {
            "min": min(scores) if scores else None,
            "max": max(scores) if scores else None,
            "mean": round(sum(scores) / len(scores), 1) if scores else None,
            "values": scores,
        },
        "confidence_distribution": conf_dist,
    }


# ---------------------------------------------------------------------------
# Runner
# ---------------------------------------------------------------------------


def run_external_validation(
    registry_path: Path,
    labels_path: Path,
    tables_dir: Path,
    output_path: Path | None = None,
    verbose: bool = True,
) -> dict[str, Any]:
    """Run external validation. Returns a results dict.

    Raises ValueError if files are malformed.
    Raises FileNotFoundError if referenced table CSV files are missing.
    """
    if not registry_path.exists():
        raise FileNotFoundError(f"Registry file not found: {registry_path}")
    if not labels_path.exists():
        raise FileNotFoundError(f"Labels file not found: {labels_path}")

    registry_rows = _load_csv(registry_path)
    if not registry_rows:
        raise ValueError(f"Registry file is empty: {registry_path}")
    _check_required_columns(registry_rows, REGISTRY_REQUIRED_COLUMNS, registry_path)

    labels_rows = _load_csv(labels_path)
    if not labels_rows:
        raise ValueError(f"Labels file is empty: {labels_path}")
    _check_required_columns(labels_rows, LABELS_REQUIRED_COLUMNS, labels_path)

    # Index labels by dataset_id
    labels_index: dict[str, ParsedLabel] = {}
    for row in labels_rows:
        label = parse_label_row(row)
        labels_index[label.dataset_id] = label

    # Filter registry to included entries
    included = [
        r for r in registry_rows if r.get("included", "").strip().lower() == "yes"
    ]
    if not included:
        print(
            "WARNING: No included entries found in registry. "
            "Set included=yes for tables to validate.",
            file=sys.stderr,
        )

    results: list[TableResult] = []
    missing_tables: list[str] = []

    for reg_row in included:
        dataset_id = reg_row["dataset_id"].strip()
        table_filename = reg_row["table_filename"].strip()

        if not table_filename:
            print(
                f"  SKIP {dataset_id}: no table_filename (redistribution may not be permitted)."
            )
            continue

        table_path = tables_dir / table_filename
        if not table_path.exists():
            missing_tables.append(str(table_path))
            continue

        if dataset_id not in labels_index:
            print(
                f"  SKIP {dataset_id}: no label row found in labels file.",
                file=sys.stderr,
            )
            continue

        label = labels_index[dataset_id]
        df = pd.read_csv(table_path)
        audit_result = audit_dataframe(df)
        table_result = compute_table_result(dataset_id, label, audit_result)
        results.append(table_result)

        if verbose:
            status = "OK" if table_result.exact_schema_match else "SCHEMA_MISMATCH"
            fn_count = table_result.field_fn
            fp_count = table_result.field_fp
            print(
                f"  {dataset_id:<20} [{status}] "
                f"score={table_result.score:3d} conf={table_result.audit_confidence:<6} "
                f"FP={fp_count} FN={fn_count}"
            )

    if missing_tables:
        msg = (
            "Missing table file(s):\n"
            + "\n".join(f"  {t}" for t in missing_tables)
            + "\n\nTable CSV files must be present in --tables-dir. "
            "If redistribution is not permitted, download them separately."
        )
        raise FileNotFoundError(msg)

    metrics = aggregate_metrics(results)

    table_details = []
    for r in results:
        fp_details = [
            {"canonical": fr.canonical, "actual": fr.actual}
            for fr in r.field_results
            if fr.is_fp
        ]
        fn_details = [
            {"canonical": fr.canonical, "expected": str(fr.expected)}
            for fr in r.field_results
            if fr.is_fn
        ]
        table_details.append(
            {
                "dataset_id": r.dataset_id,
                "table_filename": r.table_filename,
                "score": r.score,
                "audit_confidence": r.audit_confidence,
                "field_tp": r.field_tp,
                "field_fp": r.field_fp,
                "field_fn": r.field_fn,
                "field_tn": r.field_tn,
                "finding_tp": r.finding_tp,
                "finding_fp": r.finding_fp,
                "finding_fn": r.finding_fn,
                "exact_schema_match": r.exact_schema_match,
                "false_positive_details": fp_details,
                "false_negative_details": fn_details,
            }
        )

    output = {
        "protocol_version": "1.0",
        "status": "completed" if results else "no_tables_processed",
        **metrics,
        "tables": table_details,
        "failure_cases": [],
    }

    if output_path:
        output_path.parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(output, f, indent=2)
        if verbose:
            print(f"\nResults written to: {output_path}")

    return output


def print_report(output: dict[str, Any]) -> None:
    fl = output.get("field_level", {})
    find = output.get("finding_level", {})
    print()
    print("=" * 70)
    print("  Validex External Validation Report")
    print("=" * 70)
    print(f"  Tables processed:          {output.get('n_tables', 0)}")
    print(
        f"  Exact schema match rate:   {output.get('exact_schema_match_rate', 0):.4f}"
    )
    print()
    print("  Field-level metrics:")
    print(f"    True Positives  (TP): {fl.get('true_positives', 0)}")
    print(f"    False Positives (FP): {fl.get('false_positives', 0)}")
    print(f"    False Negatives (FN): {fl.get('false_negatives', 0)}")
    print(f"    True Negatives  (TN): {fl.get('true_negatives', 0)}")
    print(f"    Precision:            {fl.get('precision', 0):.4f}")
    print(f"    Recall:               {fl.get('recall', 0):.4f}")
    print()
    print("  Finding-level metrics:")
    print(f"    True Positives  (TP): {find.get('true_positives', 0)}")
    print(f"    False Positives (FP): {find.get('false_positives', 0)}")
    print(f"    False Negatives (FN): {find.get('false_negatives', 0)}")
    print(f"    Precision:            {find.get('precision', 0):.4f}")
    print(f"    Recall:               {find.get('recall', 0):.4f}")
    print()
    dist = output.get("confidence_distribution", {})
    print(
        f"  Confidence distribution: high={dist.get('high', 0)} medium={dist.get('medium', 0)} low={dist.get('low', 0)}"
    )
    print("=" * 70)
    print()
    if output.get("status") == "no_tables_processed":
        print(
            "  NOTE: No tables were processed. Add labeled tables to run external validation."
        )
        print("  See docs/external_validation_protocol.md for the full protocol.")
    elif output.get("status") == "completed":
        print(
            "  IMPORTANT: These results apply only to the labeled external dataset used."
        )
        print("  They do not imply general accuracy on arbitrary metabolomics tables.")
        print("  See docs/external_validation_protocol.md for claims discipline rules.")
    print()


# ---------------------------------------------------------------------------
# CLI entry point
# ---------------------------------------------------------------------------


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="run_external_validation",
        description=(
            "Run Validex external validation on labeled real-world metabolomics tables. "
            "Requires a completed registry CSV, labels CSV, and table files. "
            "See docs/external_validation_protocol.md."
        ),
    )
    p.add_argument("--manifest", default=None, help="Path to validation manifest JSON.")
    p.add_argument("--registry", default=None, help="Path to registry CSV file.")
    p.add_argument("--labels", default=None, help="Path to labels CSV file.")
    p.add_argument(
        "--tables-dir", default=None, help="Directory containing table CSV files."
    )
    p.add_argument(
        "--output", default=None, help="Optional path to write JSON results."
    )
    p.add_argument("--report", default=None, help="Optional path to write Markdown report.")
    return p


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    output_path = Path(args.output) if args.output else None
    report_path = Path(args.report) if args.report else None

    if args.manifest:
        try:
            output = run_manifest_validation(
                manifest_path=Path(args.manifest),
                output_path=output_path,
                report_path=report_path,
            )
        except (FileNotFoundError, ValueError) as exc:
            print(f"ERROR: {exc}", file=sys.stderr)
            return 1
        print(f"External validation status: {output['status']}")
        if output["status"] == "FAILED":
            for blocker in output["blockers"]:
                print(f"BLOCKER: {blocker}", file=sys.stderr)
            return 1
        if output["status"] == "EXTERNAL_VALIDATION_INCOMPLETE":
            print(
                "WARNING: independent external validation is incomplete; no performance claim is made."
            )
        return 0

    if not args.registry or not args.labels or not args.tables_dir:
        parser.error("either --manifest or all of --registry, --labels, and --tables-dir are required")

    registry_path = Path(args.registry)
    labels_path = Path(args.labels)
    tables_dir = Path(args.tables_dir)

    print(f"Registry:   {registry_path}")
    print(f"Labels:     {labels_path}")
    print(f"Tables dir: {tables_dir}")
    print()

    try:
        output = run_external_validation(
            registry_path=registry_path,
            labels_path=labels_path,
            tables_dir=tables_dir,
            output_path=output_path,
        )
    except (FileNotFoundError, ValueError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1

    print_report(output)
    return 0


if __name__ == "__main__":
    sys.exit(main())
