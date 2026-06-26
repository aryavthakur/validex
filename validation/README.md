# Validex External Validation Scaffold

**Status: scaffold only. No external validation results have been reported.**

This directory contains the infrastructure for running an external validation study of Validex on real published metabolomics result tables. The study has not been conducted yet.

---

## What is here

| File / directory | Purpose |
|-----------------|---------|
| `registry.example.csv` | Example registry format. Illustrative rows only — not real datasets. |
| `labels.example.csv` | Example label format. Illustrative rows only. |
| `external_results.example.json` | Example output structure for validation results. |
| `run_external_validation.py` | Validation runner script. |
| `tables/` | Directory for real external table CSV files (not committed unless redistribution is permitted). |

---

## Running external validation

When real labeled tables exist:

```bash
python validation/run_external_validation.py \
  --registry validation/registry.csv \
  --labels validation/labels.csv \
  --tables-dir validation/tables \
  --output validation/external_results.json
```

The runner will:
1. Load the registry and skip rows where `included != yes`.
2. Load the labels CSV and match rows by `dataset_id`.
3. For each included table, locate the CSV file in `--tables-dir`.
4. Run `validex.audit.audit_dataframe` on the table.
5. Compare detected schema and findings to reviewer labels.
6. Compute field-level precision, recall, and finding sensitivity.
7. Print a concise report.
8. Write JSON results to `--output` if provided.

---

## Adding a new external table

1. Read `docs/external_validation_protocol.md` in full.
2. Verify the table is eligible (real published study, legally accessible, post-analysis results).
3. Add a row to `registry.csv` (copy `registry.example.csv` as a template).
4. If redistribution is permitted, save the CSV to `validation/tables/<dataset_id>_<filename>.csv`.
5. Add a label row to `labels.csv` (copy `labels.example.csv` as a template).
6. Run the validation runner and review the output.

---

## Important constraints

- Do not add copyrighted supplementary files unless redistribution is explicitly permitted.
- Do not add patient-identifiable data.
- Do not add AI-generated or synthetic datasets as external validation data.
- Do not claim external validation is complete until the runner has been run on real labeled tables and results have been committed.
- The `tables/` directory is git-ignored unless table redistribution is permitted.

See `docs/external_validation_protocol.md` for the full protocol, eligibility criteria, labeling instructions, and claims discipline rules.
