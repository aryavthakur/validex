# Validex Release Checklist

A pre-release checklist for Validex 0.x releases. Work through each section before tagging a version.

---

## 1. Core Correctness Checks

- [ ] `validex/audit.py` is the sole canonical audit implementation.
- [ ] `validex/schema_mapper.py` is the sole canonical schema detection implementation.
- [ ] `validex/cli.py`, `validex/server.py`, and `benchmarks/run_benchmark.py` all import `audit_dataframe` or `run_audit` from `validex.audit` — not from any duplicate module.
- [ ] No active source file calls `find_col()` or uses substring-based schema detection.
- [ ] `backend/schema_mapper.py` re-exports from `validex.schema_mapper`; it contains no independent logic.
- [ ] `backend/main.py` delegates to `run_audit` from `validex.audit`.
- [ ] Dataset C columns (`compound_id`, `logFC`, `Mean_Control`, `Mean_Case`, `Annotation`) map `p_value` to None and `fdr` to None, flag `missing_p_value` and `missing_fdr`, and score exactly 40/100 with `audit_confidence: low`.

## 2. Benchmark Checks

- [ ] `python benchmarks/run_benchmark.py` reports **14/14 fixtures passed**.
- [ ] Field-level precision = **1.0000**.
- [ ] Field-level recall = **1.0000**.
- [ ] `audit_confidence` label is correct for every fixture (see `benchmarks/expected/expected_scores.json`).
- [ ] No fixture score expectation has been weakened since the last release.

## 3. API Checks

- [ ] `GET /api/health` returns `{"status": "ok"}`.
- [ ] `GET /health` returns `{"status": "ok"}` (legacy route).
- [ ] `POST /audit` response includes top-level `audit_confidence`, `score`, and `findings`.
- [ ] Complete standard input → `audit_confidence: high`, `score: 100`.
- [ ] Dataset C input → `audit_confidence: low`, `score: 40`.
- [ ] Ambiguous p-value input → `audit_confidence: medium`.
- [ ] Top-level `audit_confidence` matches `report_json.analysis.audit_confidence`.

## 4. CLI Checks

- [ ] `validex audit <csv>` prints `Validex score: <n>/100`.
- [ ] `validex audit <csv>` prints `Audit confidence: high/medium/low`.
- [ ] `validex audit <csv> --output <path>` writes a Markdown report and prints `Report written to:`.
- [ ] `validex audit <missing-file>` returns non-zero exit code.
- [ ] `validex status` runs without error.
- [ ] `validex config show` runs without error and includes `ai_provider: ollama`.
- [ ] `validex --help` shows all subcommands.

## 5. Documentation Checks

- [ ] `README.md` benchmark claim is scoped: "On this included benchmark suite".
- [ ] `README.md` does not claim external validation.
- [ ] `docs/scope_and_prior_art.md` links to `docs/references.md`.
- [ ] `docs/references.md` exists and all DOIs are cited correctly.
- [ ] `docs/release_checklist.md` is up to date.
- [ ] `docs/scope_and_prior_art.md` Section 5 no longer contains "Citation needed" placeholders.

## 6. Claims Discipline Checks

Do not release if any of the following language appears in README, docs, or docstrings:

- "Validex validates metabolomics studies."
- "Validex proves biological findings."
- "Validex guarantees reproducibility."
- "Validex is clinically validated."
- "Validex is publication-ready as a validated methods tool."
- "Validex replaces MetaboAnalyst, XCMS, MS-DIAL, MZmine, or expert curation."
- "Validex detects all possible reporting problems."
- Any claim citing journals, authors, or DOIs that have not been verified.

## 7. Packaging Checks

- [ ] `pyproject.toml` `version` matches `validex/__init__.py` `__version__`.
- [ ] `[tool.setuptools.packages.find]` includes only `["validex*"]` — benchmarks and docs are not packaged as runtime modules.
- [ ] `[project.scripts]` entry point `validex = "validex.cli:main"` is correct.
- [ ] `requires-python = ">=3.10"` is accurate.
- [ ] All runtime dependencies in `[project.dependencies]` are actually used.
- [ ] `httpx` is listed once only in `pyproject.toml`.
- [ ] `backend/requirements.txt` does not duplicate or conflict with `pyproject.toml`.
- [ ] `pip install -e .` completes without error.
- [ ] `validex --help` works after install.

## 8. Known Limitations Before Release

The following limitations must not be obscured in any release communication:

1. Validex is internally benchmarked on a synthetic fixture suite, not externally validated on published metabolomics datasets.
2. Validex audits reporting completeness and table interpretability, not biological truth.
3. Validex does not process raw LC-MS, GC-MS, MS/MS, or NMR instrument data.
4. Validex does not replace expert review, statistical review, or bioinformatics peer review.
5. Alias coverage is finite; novel export formats with column names outside the current alias sets will not be detected. Alias sets must be expanded through predefined review rules, not by weakening normalization.
6. Benchmark fixtures are small (5–7 rows) and purpose-built; they are regression tests, not representative cohort-scale validation data.
7. AI analysis features require a locally running Ollama instance; they are not activated or tested in the core audit pipeline.

## 9. Commands to Run

Run all of these before tagging a release. All must pass with zero failures.

```bash
# Full test suite
pytest

# Benchmark suite
python benchmarks/run_benchmark.py

# Install check (in a clean environment or after edits to pyproject.toml)
pip install -e .
validex --help
validex config show
```

If linting is configured:

```bash
# If ruff is installed
ruff check validex/ tests/ benchmarks/

# If mypy is installed
mypy validex/
```
