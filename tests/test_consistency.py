"""Repo-level consistency tests.

These tests verify structural invariants — canonical code paths, claims
discipline, and packaging hygiene — that are not exercised by functional unit
tests.  They do not test scientific behavior; they protect the architecture.
"""

from __future__ import annotations

from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent
VALIDEX_SRC = REPO_ROOT / "validex"
BACKEND_SRC = REPO_ROOT / "backend"
DOCS_DIR = REPO_ROOT / "docs"


# ---------------------------------------------------------------------------
# Canonical audit path
# ---------------------------------------------------------------------------


def test_cli_uses_canonical_audit_dataframe():
    """validex.cli must import audit_dataframe from validex.audit."""
    import validex.audit as canonical
    import validex.cli as cli_mod

    # cli imports audit_dataframe at module level
    assert cli_mod.audit_dataframe is canonical.audit_dataframe


def test_server_uses_canonical_run_audit():
    """validex.server must use run_audit from validex.audit."""
    import validex.audit as canonical
    import validex.server as server_mod

    assert server_mod.run_audit is canonical.run_audit


def test_benchmark_uses_canonical_audit_dataframe():
    """benchmarks/run_benchmark.py must import audit_dataframe from validex.audit."""
    source = (REPO_ROOT / "benchmarks" / "run_benchmark.py").read_text(encoding="utf-8")
    assert "from validex.audit import audit_dataframe" in source, (
        "benchmarks/run_benchmark.py must import audit_dataframe from validex.audit"
    )


# ---------------------------------------------------------------------------
# No stale substring detection patterns in source
# ---------------------------------------------------------------------------


def _source_py_files(root: Path, exclude_dirs: tuple[str, ...] = ()) -> list[Path]:
    files = []
    for p in root.rglob("*.py"):
        parts = set(p.parts)
        if any(ex in parts for ex in exclude_dirs):
            continue
        files.append(p)
    return files


@pytest.mark.parametrize("forbidden", ["find_col("])
def test_no_find_col_in_source(forbidden):
    """No production source file should use the old find_col() helper."""
    exclude = ("tests", "__pycache__")
    offenders = []
    for path in _source_py_files(VALIDEX_SRC, exclude) + _source_py_files(
        BACKEND_SRC, exclude
    ):
        if forbidden in path.read_text(encoding="utf-8"):
            offenders.append(str(path))
    assert offenders == [], f"Found '{forbidden}' in: {offenders}"


def test_no_substring_detection_in_source():
    """No production source file should use 'k in c.lower()' style substring schema detection."""
    forbidden = "in c.lower()"
    exclude = ("tests", "__pycache__")
    offenders = []
    for path in _source_py_files(VALIDEX_SRC, exclude) + _source_py_files(
        BACKEND_SRC, exclude
    ):
        if forbidden in path.read_text(encoding="utf-8"):
            offenders.append(str(path))
    assert offenders == [], f"Found '{forbidden}' in: {offenders}"


# ---------------------------------------------------------------------------
# backend.schema_mapper is a re-export shim
# ---------------------------------------------------------------------------


def test_backend_schema_mapper_reexports_from_validex():
    """backend.schema_mapper must re-export the canonical validex.schema_mapper symbols."""
    import backend.schema_mapper as shim
    import validex.schema_mapper as canonical

    assert shim.detect_schema is canonical.detect_schema
    assert shim.normalize_header is canonical.normalize_header
    assert shim.KNOWN_ALIASES is canonical.KNOWN_ALIASES


# ---------------------------------------------------------------------------
# Documentation invariants
# ---------------------------------------------------------------------------


def test_readme_includes_benchmark_limitation():
    """README must include the scoping language 'On this included benchmark suite'."""
    readme = (REPO_ROOT / "README.md").read_text(encoding="utf-8")
    assert "On this included benchmark suite" in readme, (
        "README.md is missing the benchmark scope qualifier. "
        "Add: 'On this included benchmark suite, Validex currently achieves...'"
    )


def test_scope_doc_links_to_references():
    """docs/scope_and_prior_art.md must link to docs/references.md."""
    scope_doc = (DOCS_DIR / "scope_and_prior_art.md").read_text(encoding="utf-8")
    assert "references.md" in scope_doc, (
        "docs/scope_and_prior_art.md must contain a link to docs/references.md"
    )


def test_scope_doc_has_no_citation_placeholders():
    """docs/scope_and_prior_art.md must not contain 'Citation needed' placeholders."""
    scope_doc = (DOCS_DIR / "scope_and_prior_art.md").read_text(encoding="utf-8")
    assert "Citation needed" not in scope_doc, (
        "docs/scope_and_prior_art.md still contains 'Citation needed' placeholders. "
        "Replace them with verified references."
    )


def test_release_checklist_exists():
    """docs/release_checklist.md must exist."""
    assert (DOCS_DIR / "release_checklist.md").exists(), (
        "docs/release_checklist.md is missing. Create it before release."
    )


def test_release_checklist_includes_pytest_command():
    """docs/release_checklist.md must include the pytest command."""
    checklist = (DOCS_DIR / "release_checklist.md").read_text(encoding="utf-8")
    assert "pytest" in checklist


def test_release_checklist_includes_benchmark_command():
    """docs/release_checklist.md must include the benchmark runner command."""
    checklist = (DOCS_DIR / "release_checklist.md").read_text(encoding="utf-8")
    assert "benchmarks/run_benchmark.py" in checklist
