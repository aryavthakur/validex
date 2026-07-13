"""Tests for the pilot validation workspace scaffold.

Verifies that all template files exist with correct structure, the candidate
note helper works correctly, and the README states appropriate limitations.
"""
from __future__ import annotations

import csv
import re
import shutil
import subprocess
import sys
from pathlib import Path
from urllib.parse import urlparse

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent
PILOT_DIR = REPO_ROOT / "validation" / "pilot"
NOTES_DIR = PILOT_DIR / "notes"
TABLES_DIR = PILOT_DIR / "tables"
RESULTS_DIR = PILOT_DIR / "results"
PILOT_LABELS_PATH = PILOT_DIR / "labels.pilot.csv"
PILOT_REGISTRY_PATH = PILOT_DIR / "registry.pilot.csv"

PILOT_IDS = ["PILOT_001", "PILOT_002", "PILOT_003", "PILOT_004", "PILOT_005"]

REGISTRY_REQUIRED_COLUMNS = {
    "dataset_id", "source_title", "source_type", "source_url_or_doi",
    "license_or_access_note", "table_filename", "table_description",
    "organism_or_sample_context", "platform_if_known", "study_domain",
    "included", "evidence_status", "exclusion_reason", "notes",
}

LABELS_REQUIRED_COLUMNS = {
    "dataset_id", "table_filename", "compound_id", "effect_size",
    "p_value", "fdr", "annotation", "expected_findings",
    "reviewer_id", "review_notes",
}

ALLOWED_FINDING_CODES = {
    "",
    "missing_p_value",
    "missing_fdr",
    "invalid_p_value_column",
    "invalid_fdr_column",
    "ambiguous_schema_field",
}

CANONICAL_LABEL_FIELDS = (
    "compound_id",
    "effect_size",
    "p_value",
    "fdr",
    "annotation",
)
SUPPORTED_TABLE_EXTENSIONS = {".csv", ".tsv", ".xlsx", ".xls"}


# ---------------------------------------------------------------------------
# Template file existence
# ---------------------------------------------------------------------------

def test_pilot_registry_template_exists():
    assert (PILOT_DIR / "registry.pilot.template.csv").exists()


def test_pilot_labels_template_exists():
    assert (PILOT_DIR / "labels.pilot.template.csv").is_file()


def test_pilot_readme_exists():
    assert (PILOT_DIR / "README.md").exists()


def test_candidate_notes_template_exists():
    assert (NOTES_DIR / "candidate_notes_template.md").exists()


def test_tables_gitkeep_exists():
    assert (TABLES_DIR / ".gitkeep").is_file()


def test_pilot_results_readme_exists():
    assert RESULTS_DIR.is_dir()
    assert (RESULTS_DIR / "README.md").is_file()


def test_pilot_results_readme_states_outputs_are_not_external_validation_claims():
    text = (RESULTS_DIR / "README.md").read_text(encoding="utf-8").lower()
    assert "not external validation" in text
    assert "not committed by default" in text


# ---------------------------------------------------------------------------
# Registry template structure
# ---------------------------------------------------------------------------

def _read_csv_document(path: Path) -> tuple[list[str], list[dict[str, str]]]:
    with open(path, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        header = list(reader.fieldnames or [])
        return header, list(reader)


def _read_csv(path: Path) -> list[dict[str, str]]:
    return _read_csv_document(path)[1]


def test_pilot_registry_template_has_required_columns():
    rows = _read_csv(PILOT_DIR / "registry.pilot.template.csv")
    assert rows, "registry.pilot.template.csv is empty"
    actual = set(rows[0].keys())
    missing = REGISTRY_REQUIRED_COLUMNS - actual
    assert not missing, f"Missing columns: {missing}"


def test_pilot_registry_template_has_all_pilot_ids():
    rows = _read_csv(PILOT_DIR / "registry.pilot.template.csv")
    ids = {r["dataset_id"] for r in rows}
    assert set(PILOT_IDS) == ids


# ---------------------------------------------------------------------------
# Labels template structure
# ---------------------------------------------------------------------------

def test_pilot_labels_template_has_required_columns():
    header, _ = _read_csv_document(PILOT_DIR / "labels.pilot.template.csv")
    actual = set(header)
    missing = LABELS_REQUIRED_COLUMNS - actual
    assert not missing, f"Missing columns: {missing}"
    assert len(header) == len(set(header)), "labels template has duplicate columns"


def test_pilot_labels_template_contains_headers_only():
    _, rows = _read_csv_document(PILOT_DIR / "labels.pilot.template.csv")
    assert rows == [], (
        "labels.pilot.template.csv must preserve the schema without presenting "
        "uninspected pilot rows as reproducible labels"
    )


# ---------------------------------------------------------------------------
# Git-backed repository policy
# ---------------------------------------------------------------------------


def _require_git_checkout(repo_root: Path = REPO_ROOT) -> None:
    """Skip repository-policy checks when Git metadata is unavailable."""
    if shutil.which("git") is None:
        pytest.skip("repository-policy test requires the Git executable")
    if not (repo_root / ".git").exists():
        pytest.skip("repository-policy test requires a source checkout with .git metadata")

    try:
        result = subprocess.run(
            ["git", "rev-parse", "--is-inside-work-tree"],
            cwd=repo_root,
            capture_output=True,
            text=True,
            check=False,
        )
    except FileNotFoundError:
        pytest.skip("repository-policy test requires the Git executable")

    if result.returncode != 0 or result.stdout.strip() != "true":
        pytest.fail(
            "Git metadata exists but the checkout could not be inspected: "
            f"return code {result.returncode}; stderr: {result.stderr.strip() or '<empty>'}"
        )


def _is_git_ignored(path: Path, repo_root: Path = REPO_ROOT) -> bool:
    """Return Git's ignore decision, failing on command errors."""
    _require_git_checkout(repo_root)
    relative_path = path.relative_to(repo_root)
    try:
        result = subprocess.run(
            ["git", "check-ignore", "-q", "--", str(relative_path)],
            cwd=repo_root,
            capture_output=True,
            text=True,
            check=False,
        )
    except FileNotFoundError:
        pytest.skip("repository-policy test requires the Git executable")

    if result.returncode == 0:
        return True
    if result.returncode == 1:
        return False
    pytest.fail(
        "git check-ignore failed with return code "
        f"{result.returncode} for {relative_path}: {result.stderr.strip() or '<empty>'}"
    )


def _git_tracked_files_under(path: Path, repo_root: Path = REPO_ROOT) -> list[str]:
    """List tracked paths below path, failing with Git's diagnostic on errors."""
    _require_git_checkout(repo_root)
    relative_path = path.relative_to(repo_root)
    try:
        result = subprocess.run(
            ["git", "ls-files", "--", str(relative_path)],
            cwd=repo_root,
            capture_output=True,
            text=True,
            check=False,
        )
    except FileNotFoundError:
        pytest.skip("repository-policy test requires the Git executable")
    if result.returncode != 0:
        pytest.fail(
            "git ls-files failed with return code "
            f"{result.returncode} for {relative_path}: {result.stderr.strip() or '<empty>'}"
        )
    return [line for line in result.stdout.splitlines() if line]


@pytest.mark.repo_policy
def test_results_scaffold_is_tracked_and_generated_outputs_are_ignored():
    readme_path = RESULTS_DIR / "README.md"
    tracked = _git_tracked_files_under(RESULTS_DIR)
    assert str(readme_path.relative_to(REPO_ROOT)) in tracked
    assert not _is_git_ignored(readme_path)
    assert _is_git_ignored(RESULTS_DIR / "example.json")
    assert _is_git_ignored(RESULTS_DIR / "nested" / "example.csv")


@pytest.mark.repo_policy
def test_tables_scaffold_is_tracked_and_supported_local_tables_are_ignored():
    gitkeep_path = TABLES_DIR / ".gitkeep"
    tracked = _git_tracked_files_under(TABLES_DIR)
    assert str(gitkeep_path.relative_to(REPO_ROOT)) in tracked
    assert not _is_git_ignored(gitkeep_path)
    for extension in sorted(SUPPORTED_TABLE_EXTENSIONS):
        for candidate_extension in {extension, extension.upper()}:
            assert _is_git_ignored(TABLES_DIR / f"example{candidate_extension}"), (
                f"pilot {candidate_extension} source tables must remain local-only"
            )


@pytest.mark.repo_policy
def test_generated_labels_are_ignored_and_template_is_tracked():
    template_path = PILOT_DIR / "labels.pilot.template.csv"
    tracked = _git_tracked_files_under(PILOT_DIR)
    assert str(template_path.relative_to(REPO_ROOT)) in tracked
    assert str(PILOT_LABELS_PATH.relative_to(REPO_ROOT)) not in tracked
    assert not _is_git_ignored(template_path)
    assert _is_git_ignored(PILOT_LABELS_PATH)


@pytest.mark.parametrize("returncode, expected", [(0, True), (1, False)])
def test_git_check_ignore_handles_documented_return_codes(
    monkeypatch, returncode, expected
):
    monkeypatch.setattr(
        sys.modules[__name__], "_require_git_checkout", lambda _repo_root: None
    )
    monkeypatch.setattr(
        subprocess,
        "run",
        lambda *args, **kwargs: subprocess.CompletedProcess(
            args=args[0], returncode=returncode, stdout="", stderr=""
        ),
    )
    assert _is_git_ignored(REPO_ROOT / "generated.txt") is expected


def test_git_check_ignore_reports_unexpected_command_errors(monkeypatch):
    monkeypatch.setattr(
        sys.modules[__name__], "_require_git_checkout", lambda _repo_root: None
    )
    monkeypatch.setattr(
        subprocess,
        "run",
        lambda *args, **kwargs: subprocess.CompletedProcess(
            args=args[0], returncode=128, stdout="", stderr="fatal: broken checkout"
        ),
    )
    with pytest.raises(pytest.fail.Exception, match="return code 128.*broken checkout"):
        _is_git_ignored(REPO_ROOT / "generated.txt")


def test_require_git_checkout_skips_without_git_metadata(tmp_path, monkeypatch):
    monkeypatch.setattr(shutil, "which", lambda _executable: "/usr/bin/git")
    with pytest.raises(pytest.skip.Exception, match=".git metadata"):
        _require_git_checkout(tmp_path)


def test_require_git_checkout_skips_without_git_executable(tmp_path, monkeypatch):
    monkeypatch.setattr(shutil, "which", lambda _executable: None)
    with pytest.raises(pytest.skip.Exception, match="Git executable"):
        _require_git_checkout(tmp_path)


# ---------------------------------------------------------------------------
# Optional local pilot workspace validation
# ---------------------------------------------------------------------------


def _discover_local_pilot_tables(tables_dir: Path = TABLES_DIR) -> list[Path]:
    return sorted(
        path for path in tables_dir.iterdir()
        if path.is_file() and path.name != ".gitkeep"
    )


def _mapping_candidates(raw: str, dataset_id: str, field: str) -> list[str]:
    value = raw.strip()
    if not value:
        return []
    if not value.startswith("AMBIGUOUS:"):
        assert not value.upper().startswith("AMBIGUOUS"), (
            f"{dataset_id} {field} has malformed ambiguous mapping: {value!r}"
        )
        return [value]

    candidates = [candidate.strip() for candidate in value.removeprefix("AMBIGUOUS:").split("|")]
    assert len(candidates) >= 2 and all(candidates), (
        f"{dataset_id} {field} must serialize ambiguity as AMBIGUOUS:column_a|column_b"
    )
    assert len(candidates) == len(set(candidates)), (
        f"{dataset_id} {field} repeats an ambiguous mapping candidate"
    )
    return candidates


def _delimited_table_header(table_path: Path) -> list[str] | None:
    if table_path.suffix.lower() not in {".csv", ".tsv"}:
        return None
    delimiter = "\t" if table_path.suffix.lower() == ".tsv" else ","
    with open(table_path, newline="", encoding="utf-8-sig") as table_file:
        header = next(csv.reader(table_file, delimiter=delimiter), [])
    assert header, f"Local pilot table has no header row: {table_path}"
    assert len(header) == len(set(header)), f"Local pilot table has duplicate headers: {table_path}"
    return header


def _validate_labels_against_local_tables(
    labels_path: Path,
    table_files: list[Path],
    registry_ids: set[str],
) -> None:
    header, rows = _read_csv_document(labels_path)
    assert LABELS_REQUIRED_COLUMNS <= set(header), (
        f"{labels_path} is missing columns: {sorted(LABELS_REQUIRED_COLUMNS - set(header))}"
    )
    assert len(header) == len(set(header)), f"{labels_path} has duplicate columns"
    assert rows, f"{labels_path} is populated local output but contains no label rows"

    dataset_ids = [row["dataset_id"].strip() for row in rows]
    assert all(dataset_ids), "Local pilot label dataset IDs must be non-empty"
    assert len(dataset_ids) == len(set(dataset_ids)), (
        f"Local pilot label dataset IDs must be unique: {dataset_ids}"
    )

    available_tables = {path.name: path for path in table_files}
    for row in rows:
        dataset_id = row["dataset_id"].strip()
        assert dataset_id in registry_ids, (
            f"Local pilot label {dataset_id!r} has no registry entry"
        )

        filename = row["table_filename"].strip()
        assert filename and Path(filename).name == filename and not Path(filename).is_absolute(), (
            f"{dataset_id} table_filename must be a safe basename: {filename!r}"
        )
        assert Path(filename).suffix.lower() in SUPPORTED_TABLE_EXTENSIONS, (
            f"{dataset_id} references unsupported pilot table type: {filename!r}"
        )
        assert filename in available_tables and available_tables[filename].exists(), (
            f"Local labels reference missing local table for {dataset_id}: "
            f"expected {filename!r} under the local tables directory"
        )

        table_header = _delimited_table_header(available_tables[filename])
        has_blank_mapping = False
        for field in CANONICAL_LABEL_FIELDS:
            candidates = _mapping_candidates(row[field], dataset_id, field)
            has_blank_mapping = has_blank_mapping or not candidates
            if table_header is not None:
                missing_headers = [candidate for candidate in candidates if candidate not in table_header]
                assert not missing_headers, (
                    f"{dataset_id} {field} references headers absent from {filename}: "
                    f"{missing_headers}"
                )
        if has_blank_mapping:
            assert row["review_notes"].strip(), (
                f"{dataset_id} has blank canonical mappings; review_notes must explain them"
            )

        raw_findings = row["expected_findings"].strip()
        finding_codes = [code.strip() for code in raw_findings.split("|")] if raw_findings else [""]
        invalid_codes = [code for code in finding_codes if code not in ALLOWED_FINDING_CODES]
        assert not invalid_codes, (
            f"Invalid expected finding codes for {dataset_id}: {invalid_codes}"
        )


def _validate_local_pilot_workspace(
    tables_dir: Path,
    labels_path: Path,
    registry_ids: set[str],
) -> None:
    table_files = _discover_local_pilot_tables(tables_dir)
    for table_path in table_files:
        assert table_path.suffix.lower() in SUPPORTED_TABLE_EXTENSIONS, (
            f"Unsupported local pilot table extension: {table_path.name}"
        )

    if not table_files:
        assert not labels_path.exists(), (
            "labels.pilot.csv is generated from local pilot tables and should not "
            "exist when no local pilot tables are available"
        )
        return
    if labels_path.exists():
        _validate_labels_against_local_tables(labels_path, table_files, registry_ids)


def test_clean_workspace_does_not_require_generated_labels(tmp_path):
    tables_dir = tmp_path / "tables"
    tables_dir.mkdir()
    _validate_local_pilot_workspace(tables_dir, tmp_path / "labels.pilot.csv", {"PILOT_001"})


def test_real_local_pilot_workspace_is_structurally_consistent_when_populated():
    registry_ids = {row["dataset_id"].strip() for row in _read_csv(PILOT_REGISTRY_PATH)}
    _validate_local_pilot_workspace(TABLES_DIR, PILOT_LABELS_PATH, registry_ids)


def _write_local_labels(path: Path, annotation: str, table_filename: str = "synthetic.csv") -> None:
    expected_findings = "ambiguous_schema_field" if annotation.startswith("AMBIGUOUS:") else ""
    path.write_text(
        "dataset_id,table_filename,compound_id,effect_size,p_value,fdr,annotation,"
        "expected_findings,reviewer_id,review_notes\n"
        f"PILOT_001,{table_filename},Compound,log2FC,P value,FDR,{annotation},"
        f"{expected_findings},reviewer,synthetic fixture only\n",
        encoding="utf-8",
    )


def test_local_labels_fail_when_referenced_table_is_missing(tmp_path):
    labels_path = tmp_path / "labels.pilot.csv"
    _write_local_labels(labels_path, "Class", table_filename="missing.csv")
    with pytest.raises(AssertionError, match="missing local table.*missing.csv"):
        _validate_labels_against_local_tables(labels_path, [], {"PILOT_001"})


@pytest.mark.parametrize("annotation", ["Class", "AMBIGUOUS:Main class|Sub class"])
def test_local_label_validation_accepts_generic_mappings_and_effect_size(tmp_path, annotation):
    table_path = tmp_path / "synthetic.csv"
    table_path.write_text(
        "Compound,log2FC,P value,FDR,Class,Main class,Sub class\n"
        "synthetic,1.2,0.01,0.02,A,A1,A2\n",
        encoding="utf-8",
    )
    labels_path = tmp_path / "labels.pilot.csv"
    _write_local_labels(labels_path, annotation)

    _validate_labels_against_local_tables(labels_path, [table_path], {"PILOT_001"})


# ---------------------------------------------------------------------------
# Candidate notes template content
# ---------------------------------------------------------------------------

def test_candidate_notes_template_includes_license_field():
    text = (NOTES_DIR / "candidate_notes_template.md").read_text(encoding="utf-8")
    assert "License or Reuse Note" in text or "license" in text.lower(), (
        "candidate_notes_template.md must include a license or reuse note field"
    )


def test_candidate_notes_template_includes_redistribution_warning():
    text = (NOTES_DIR / "candidate_notes_template.md").read_text(encoding="utf-8")
    assert "redistribut" in text.lower(), (
        "candidate_notes_template.md must include a redistribution warning"
    )


def test_candidate_notes_template_includes_all_required_sections():
    text = (NOTES_DIR / "candidate_notes_template.md").read_text(encoding="utf-8")
    required_markers = [
        "Dataset ID",
        "Source Title",
        "DOI or URL",
        "Access Date",
        "License",
        "Expected Findings",
        "Reviewer",
        "Final Inclusion Decision",
    ]
    for marker in required_markers:
        assert marker in text, f"candidate_notes_template.md missing section: '{marker}'"


# ---------------------------------------------------------------------------
# create_candidate_note.py helper
# ---------------------------------------------------------------------------

def test_create_candidate_note_creates_file(tmp_path):
    """Helper creates a note file for a given dataset ID."""
    from validation.pilot.create_candidate_note import create_candidate_note

    output_path = create_candidate_note("PILOT_001", output_dir=tmp_path)

    assert output_path.exists()
    assert output_path.name == "PILOT_001_notes.md"


def test_create_candidate_note_replaces_dataset_id_in_title(tmp_path):
    """Helper substitutes the dataset ID into the note file title."""
    from validation.pilot.create_candidate_note import create_candidate_note

    output_path = create_candidate_note("PILOT_042", output_dir=tmp_path)
    text = output_path.read_text(encoding="utf-8")
    assert "PILOT_042" in text


def test_create_candidate_note_refuses_to_overwrite_without_force(tmp_path):
    """Helper raises FileExistsError when the note file already exists."""
    from validation.pilot.create_candidate_note import create_candidate_note

    create_candidate_note("PILOT_001", output_dir=tmp_path)
    with pytest.raises(FileExistsError):
        create_candidate_note("PILOT_001", output_dir=tmp_path, force=False)


def test_create_candidate_note_overwrites_with_force(tmp_path):
    """Helper overwrites an existing note file when force=True."""
    from validation.pilot.create_candidate_note import create_candidate_note

    first = create_candidate_note("PILOT_001", output_dir=tmp_path)
    first.write_text("old content", encoding="utf-8")

    create_candidate_note("PILOT_001", output_dir=tmp_path, force=True)
    text = first.read_text(encoding="utf-8")
    assert "old content" not in text
    assert "PILOT_001" in text


def test_create_candidate_note_creates_output_dir(tmp_path):
    """Helper creates the output directory if it does not exist."""
    from validation.pilot.create_candidate_note import create_candidate_note

    nested = tmp_path / "deep" / "nested" / "dir"
    assert not nested.exists()
    create_candidate_note("PILOT_001", output_dir=nested)
    assert nested.exists()


# ---------------------------------------------------------------------------
# inspect_table_headers.py helper
# ---------------------------------------------------------------------------

def test_inspect_table_headers_prints_headers_for_temporary_csv(tmp_path, capsys):
    """Header helper prints CSV columns and a safe preview."""
    from validation.pilot.inspect_table_headers import main

    csv_path = tmp_path / "pilot.csv"
    csv_path.write_text(
        "Metabolite,FC (1x PBS / 0.5x PBS),FDR\n"
        "glucose,1.25,0.04\n",
        encoding="utf-8",
    )

    assert main([str(csv_path)]) == 0
    captured = capsys.readouterr()
    assert "--- Column headers ---" in captured.out
    assert "Metabolite" in captured.out
    assert "FC (1x PBS / 0.5x PBS)" in captured.out
    assert "glucose" in captured.out


def test_inspect_table_headers_handles_missing_file_with_clear_error(tmp_path, capsys):
    """Header helper returns nonzero and names a missing path."""
    from validation.pilot.inspect_table_headers import main

    missing_path = tmp_path / "missing.csv"

    assert main([str(missing_path)]) == 1
    captured = capsys.readouterr()
    assert "ERROR:" in captured.err
    assert "File not found" in captured.err
    assert str(missing_path) in captured.err


def test_inspect_table_headers_refuses_to_overwrite_output_without_force(tmp_path, capsys):
    """Header helper will not overwrite converted output unless --force is passed."""
    from validation.pilot.inspect_table_headers import main

    tsv_path = tmp_path / "pilot.tsv"
    tsv_path.write_text("Metabolite\tp-value\ncitrate\t0.01\n", encoding="utf-8")
    output_path = tmp_path / "converted.csv"
    output_path.write_text("existing\n", encoding="utf-8")

    assert main([str(tsv_path), "--output", str(output_path)]) == 1
    captured = capsys.readouterr()
    assert "already exists" in captured.err
    assert output_path.read_text(encoding="utf-8") == "existing\n"


def test_inspect_table_headers_writes_converted_csv_from_tsv_with_force(tmp_path):
    """Header helper can write a converted CSV from a supported temporary format."""
    from validation.pilot.inspect_table_headers import main

    tsv_path = tmp_path / "pilot.tsv"
    tsv_path.write_text("Metabolite\tp-value\ncitrate\t0.01\n", encoding="utf-8")
    output_path = tmp_path / "converted.csv"

    assert main([str(tsv_path), "--output", str(output_path)]) == 0
    rows = _read_csv(output_path)
    assert rows == [{"Metabolite": "citrate", "p-value": "0.01"}]


# ---------------------------------------------------------------------------
# README claims discipline
# ---------------------------------------------------------------------------

def test_pilot_readme_states_pilot_is_not_external_validation():
    text = (PILOT_DIR / "README.md").read_text(encoding="utf-8")
    assert "not sufficient to claim external validation" in text or (
        "not external validation" in text.lower()
    ), "Pilot README must state that a pilot run is not sufficient to claim external validation"


def test_pilot_readme_includes_licensing_warning():
    text = (PILOT_DIR / "README.md").read_text(encoding="utf-8")
    assert "Do not commit supplementary tables unless the license clearly permits redistribution" in text


def test_pilot_002_suffix_qualified_p_value_decision_is_documented():
    text = (NOTES_DIR / "PILOT_002_notes.md").read_text(encoding="utf-8")
    assert "Should Validex support suffix-qualified statistical columns?" in text
    assert "deferred" in text.lower()


def test_main_readme_mentions_pilot_runs_are_workflow_tests():
    text = (REPO_ROOT / "README.md").read_text(encoding="utf-8")
    assert "Pilot runs are workflow tests" in text or "pilot runs are workflow tests" in text.lower(), (
        "README.md must state that pilot runs are workflow tests, not external validation claims"
    )


def test_main_readme_links_to_pilot_readme():
    text = (REPO_ROOT / "README.md").read_text(encoding="utf-8")
    assert "validation/pilot/README.md" in text


# ---------------------------------------------------------------------------
# registry.pilot.csv tests (populated candidate metadata)
# ---------------------------------------------------------------------------

VALID_INCLUDED_VALUES = {"yes", "no", "pending"}
VALID_LICENSE_STATUSES = {
    "redistributable_confirmed",
    "public_access_but_redistribution_unclear",
    "requires_verification",
}
VALID_EVIDENCE_STATUSES = {
    "pending",
    "locally_inspected",
    "locally_validated",
    "excluded",
}


@pytest.mark.skipif(
    not (PILOT_DIR / "registry.pilot.csv").exists(),
    reason="registry.pilot.csv not yet created",
)
def test_pilot_registry_csv_has_required_columns():
    rows = _read_csv(PILOT_REGISTRY_PATH)
    assert rows, "registry.pilot.csv is empty"
    actual = set(rows[0].keys())
    missing = REGISTRY_REQUIRED_COLUMNS - actual
    assert not missing, f"Missing columns: {missing}"


@pytest.mark.skipif(
    not (PILOT_DIR / "registry.pilot.csv").exists(),
    reason="registry.pilot.csv not yet created",
)
def test_pilot_registry_csv_dataset_ids_are_unique():
    rows = _read_csv(PILOT_REGISTRY_PATH)
    ids = [r["dataset_id"] for r in rows]
    assert len(ids) == len(set(ids)), f"Duplicate dataset_id values: {ids}"


@pytest.mark.skipif(
    not (PILOT_DIR / "registry.pilot.csv").exists(),
    reason="registry.pilot.csv not yet created",
)
def test_pilot_registry_csv_included_values_are_valid():
    rows = _read_csv(PILOT_REGISTRY_PATH)
    for row in rows:
        val = row.get("included", "").strip().lower()
        assert val in VALID_INCLUDED_VALUES, (
            f"Invalid 'included' value {val!r} for dataset_id={row['dataset_id']!r}. "
            f"Must be one of: {VALID_INCLUDED_VALUES}"
        )


def test_pilot_registry_csv_evidence_status_values_are_valid():
    rows = _read_csv(PILOT_REGISTRY_PATH)
    for row in rows:
        evidence_status = row.get("evidence_status", "").strip().lower()
        assert evidence_status in VALID_EVIDENCE_STATUSES, (
            f"Invalid evidence_status {evidence_status!r} for "
            f"dataset_id={row['dataset_id']!r}; expected one of "
            f"{sorted(VALID_EVIDENCE_STATUSES)}"
        )


@pytest.mark.skipif(
    not (PILOT_DIR / "registry.pilot.csv").exists(),
    reason="registry.pilot.csv not yet created",
)
def test_pilot_registry_csv_filled_rows_have_license_notes():
    """Every row with a source_title must have a non-empty license_or_access_note."""
    rows = _read_csv(PILOT_REGISTRY_PATH)
    for row in rows:
        if row.get("source_title", "").strip():
            assert row.get("license_or_access_note", "").strip(), (
                f"dataset_id={row['dataset_id']!r} has source_title but empty license_or_access_note"
            )


def test_pilot_registry_csv_uses_meaningful_provenance_values():
    rows = _read_csv(PILOT_REGISTRY_PATH)
    forbidden_placeholders = ("previously recorded", "stage 9")
    doi_pattern = re.compile(r"^10\.\d{4,9}/\S+$", re.IGNORECASE)

    for row in rows:
        dataset_id = row["dataset_id"].strip()
        source = row["source_url_or_doi"].strip()
        assert not any(phrase in source.lower() for phrase in forbidden_placeholders), (
            f"{dataset_id} uses a vague provenance placeholder: {source!r}"
        )

        if source.lower() not in {"unknown", "not recorded", "requires verification"}:
            parsed = urlparse(source)
            if parsed.scheme:
                assert parsed.scheme in {"http", "https"} and parsed.netloc, (
                    f"{dataset_id} has an invalid source URL: {source!r}"
                )
                if parsed.netloc.lower() == "doi.org":
                    assert doi_pattern.match(parsed.path.lstrip("/")), (
                        f"{dataset_id} has an invalid DOI URL: {source!r}"
                    )
            else:
                assert doi_pattern.match(source), (
                    f"{dataset_id} source must be a URL, DOI, or explicit unknown sentinel: {source!r}"
                )

        license_note = row["license_or_access_note"].strip()
        license_status = license_note.split(" (", 1)[0]
        assert license_status in VALID_LICENSE_STATUSES, (
            f"{dataset_id} has unsupported license status {license_status!r}; "
            f"expected one of {sorted(VALID_LICENSE_STATUSES)}"
        )


@pytest.mark.skipif(
    not (PILOT_DIR / "registry.pilot.csv").exists(),
    reason="registry.pilot.csv not yet created",
)
def test_pilot_registry_csv_does_not_claim_validation_results():
    """registry.pilot.csv must not contain validation result claims."""
    text = PILOT_REGISTRY_PATH.read_text(encoding="utf-8")
    forbidden_phrases = [
        "externally validated",
        "validation complete",
        "proven accurate",
        "clinically validated",
    ]
    for phrase in forbidden_phrases:
        assert phrase.lower() not in text.lower(), (
            f"registry.pilot.csv contains a forbidden validation claim phrase: {phrase!r}"
        )


@pytest.mark.skipif(
    not (PILOT_DIR / "registry.pilot.csv").exists(),
    reason="registry.pilot.csv not yet created",
)
@pytest.mark.repo_policy
def test_no_local_pilot_source_tables_are_tracked():
    """Supported pilot source tables must remain local-only."""
    tracked_tables = [
        path for path in _git_tracked_files_under(TABLES_DIR)
        if Path(path).suffix.lower() in SUPPORTED_TABLE_EXTENSIONS
    ]
    assert tracked_tables == [], (
        "Pilot source tables are tracked but must stay local-only: "
        f"{tracked_tables}"
    )


@pytest.mark.skipif(
    not (PILOT_DIR / "registry.pilot.csv").exists(),
    reason="registry.pilot.csv not yet created",
)
def test_candidate_note_files_exist_for_filled_pilot_rows():
    """Every registry row with a source_title must have a corresponding note file."""
    rows = _read_csv(PILOT_REGISTRY_PATH)
    for row in rows:
        dataset_id = row.get("dataset_id", "").strip()
        source_title = row.get("source_title", "").strip()
        if source_title and dataset_id:
            note_file = NOTES_DIR / f"{dataset_id}_notes.md"
            assert note_file.exists(), (
                f"Note file missing for {dataset_id}: {note_file}"
            )


def test_candidate_note_statuses_match_registry_and_separate_evidence_types():
    rows = _read_csv(PILOT_REGISTRY_PATH)
    for row in rows:
        dataset_id = row["dataset_id"].strip()
        note_path = NOTES_DIR / f"{dataset_id}_notes.md"
        text = note_path.read_text(encoding="utf-8")
        status_match = re.search(
            r"Current evidence status:\s*"
            r"(pending|locally_inspected|locally_validated|excluded)",
            text,
            re.IGNORECASE,
        )
        assert status_match, f"{note_path} must state an explicit current evidence status"
        assert status_match.group(1).lower() == row["evidence_status"].strip().lower(), (
            f"{dataset_id} evidence status disagrees between registry and candidate note"
        )
        assert "Expected finding before validation:" in text
        assert "Observed local finding:" in text
        assert "Reproducibility:" in text
