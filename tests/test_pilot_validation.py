"""Tests for the pilot validation workspace scaffold.

Verifies that all template files exist with correct structure, the candidate
note helper works correctly, and the README states appropriate limitations.
"""
from __future__ import annotations

import csv
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent
PILOT_DIR = REPO_ROOT / "validation" / "pilot"
NOTES_DIR = PILOT_DIR / "notes"

PILOT_IDS = ["PILOT_001", "PILOT_002", "PILOT_003", "PILOT_004", "PILOT_005"]

REGISTRY_REQUIRED_COLUMNS = {
    "dataset_id", "source_title", "source_type", "source_url_or_doi",
    "license_or_access_note", "table_filename", "table_description",
    "organism_or_sample_context", "platform_if_known", "study_domain",
    "included", "exclusion_reason", "notes",
}

LABELS_REQUIRED_COLUMNS = {
    "dataset_id", "table_filename", "compound_id", "effect_size",
    "p_value", "fdr", "annotation", "expected_findings",
    "reviewer_id", "review_notes",
}


# ---------------------------------------------------------------------------
# Template file existence
# ---------------------------------------------------------------------------

def test_pilot_registry_template_exists():
    assert (PILOT_DIR / "registry.pilot.template.csv").exists()


def test_pilot_labels_template_exists():
    assert (PILOT_DIR / "labels.pilot.template.csv").exists()


def test_pilot_readme_exists():
    assert (PILOT_DIR / "README.md").exists()


def test_candidate_notes_template_exists():
    assert (NOTES_DIR / "candidate_notes_template.md").exists()


def test_tables_gitkeep_exists():
    assert (PILOT_DIR / "tables" / ".gitkeep").exists()


def test_results_gitkeep_exists():
    assert (PILOT_DIR / "results" / ".gitkeep").exists()


def test_pilot_results_readme_exists():
    assert (PILOT_DIR / "results" / "README.md").exists()


def test_pilot_results_readme_states_outputs_are_not_external_validation_claims():
    text = (PILOT_DIR / "results" / "README.md").read_text(encoding="utf-8").lower()
    assert "not external validation" in text
    assert "not committed by default" in text


def test_no_pilot_labels_are_created_without_local_table_files():
    table_files = [
        p for p in (PILOT_DIR / "tables").iterdir()
        if p.is_file() and p.name != ".gitkeep"
    ]
    labels_path = PILOT_DIR / "labels.pilot.csv"
    if not table_files:
        assert not labels_path.exists()


# ---------------------------------------------------------------------------
# Registry template structure
# ---------------------------------------------------------------------------

def _read_csv(path: Path) -> list[dict[str, str]]:
    with open(path, newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


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
    rows = _read_csv(PILOT_DIR / "labels.pilot.template.csv")
    assert rows, "labels.pilot.template.csv is empty"
    actual = set(rows[0].keys())
    missing = LABELS_REQUIRED_COLUMNS - actual
    assert not missing, f"Missing columns: {missing}"


def test_pilot_labels_template_has_all_pilot_ids():
    rows = _read_csv(PILOT_DIR / "labels.pilot.template.csv")
    ids = {r["dataset_id"] for r in rows}
    assert set(PILOT_IDS) == ids


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

PILOT_REGISTRY_PATH = PILOT_DIR / "registry.pilot.csv"
VALID_INCLUDED_VALUES = {"yes", "no", "pending", ""}


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
def test_no_table_csvs_committed_in_pilot_tables():
    """No CSV files should be committed in validation/pilot/tables/ (only .gitkeep)."""
    tables_dir = PILOT_DIR / "tables"
    committed_csvs = list(tables_dir.glob("*.csv"))
    assert committed_csvs == [], (
        f"CSV files committed in validation/pilot/tables/ — these should be git-ignored: "
        f"{[str(p) for p in committed_csvs]}"
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
