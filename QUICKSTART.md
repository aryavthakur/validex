# Quickstart Guide

## Research-Preview Warning

Validex is a research-preview tool. Results are deterministic engineering assessments, not clinical or biological validation.

## 1. Set Up

```bash
python3 -m venv .venv && source .venv/bin/activate
pip install -e validex_0_2_worktree/
```

## 2. Run Validex on a Demonstration Table

Use one of the project-generated synthetic benchmark fixtures:

```bash
validex audit validation_study/synthetic_benchmark/generated/v2/development/SYNV2_0001.csv
```

This produces a Markdown report and a JSON output showing the audit result.

## 3. Specify an XLSX Sheet

For XLSX workbooks with multiple sheets:

```bash
validex audit path/to/workbook.xlsx --sheet "Sheet1"
```

## 4. Understanding the Output

### Detected Fields

The `detected` section shows which canonical fields Validex identified as usable:

```json
{
  "detected": {
    "compound_id": "compound_id",
    "effect_size": "logFC",
    "p_value": "p_value",
    "fdr": "fdr",
    "annotation": "Annotation"
  }
}
```

A `null` value means the field was not identified or was identified but failed usability validation.

### Ambiguity Records

The `ambiguity` section shows structural detection results independently of usability:

```json
{
  "ambiguity": {
    "p_value": {
      "status": "one_valid_candidate",
      "selected_column": "p_value",
      "candidate_columns": ["p_value"]
    }
  }
}
```

**Key distinction:** `ambiguity.selected_column` reflects structural header recognition. `detected.p_value` reflects usability-gated status. A column can be structurally recognized but not usable if its values fail validation.

### Probability Usability

For p-value and FDR columns, Validex validates every cell. A column is usable only when at least 80% of rows contain valid numeric values in the range [0, 1]. Invalid cells are classified as nonnumeric, out-of-range, nonfinite, or missing.

### FDR Comparable-Row Handling

When both p-value and FDR columns are present, Validex checks whether FDR values are consistently greater than or equal to p-values. A warning is issued if they are not, suggesting possible column swap or miscalculation.

### Audit Confidence

Confidence is classified as `high`, `medium`, or `low` based on field completeness, probability validity, ambiguity, and data quality.

### Provenance

The output includes ingestion metadata (filename, original columns, format) for audit traceability.

## 5. Limitations

- Validex audits table structure and field recognition — it does not validate biological truth or statistical correctness
- The 80% usability threshold is a policy parameter; it has not been independently optimized
- Alias matching is governed by a fixed registry; unlisted header synonyms will not match
- No machine learning or external AI is used in the deterministic audit
