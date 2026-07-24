# Validex Benchmark Suite

## What This Suite Tests

The benchmark suite evaluates the Validex scientific core against 14 deterministic fixture tables that cover:

- **Correct positive detection** — tables where all required fields are present and correctly named.
- **Missing field detection** — tables where p-values, FDR, or both are absent; the audit must flag them.
- **Value-level validation** — tables where a detected column exists but contains out-of-range or non-numeric values.
- **Ambiguity handling** — tables where multiple columns match the same canonical field; the audit must warn.
- **Adversarial column names** — tables whose column names contain common substrings like `p`, `adj`, or `q` that must **not** trigger false detections.
- **Realistic tool export formats** — MetaboAnalyst-style, MS-DIAL-style, and XCMS-style headers, plus mixed case and punctuation variants.

For each fixture the runner checks:
1. Schema detection: which original column was assigned to each canonical field (`compound_id`, `effect_size`, `p_value`, `fdr`, `annotation`).
2. Required findings: audit flags that must be present.
3. Forbidden findings: audit flags that must not be present.
4. Score band: the audit confidence score must fall within the expected range.
5. Confidence label: `high`, `medium`, or `low`, reflecting field completeness and ambiguity.

## What This Suite Does NOT Test

- Biological truth or the correctness of upstream experimental designs.
- Statistical power or correctness of the underlying analysis.
- Whether detected p-values represent valid statistical tests.
- Whether detected FDR values use the correct correction method.
- Large-scale performance or memory behaviour on real datasets.
- Non-CSV input formats.

## How to Run

From the repo root:

```bash
python benchmarks/run_benchmark.py
```

Exits with code `0` if all fixtures pass, `1` if any fail.

The benchmark is also integrated into the pytest suite:

```bash
pytest tests/test_benchmark.py -v
```

Or run the complete test suite (includes benchmark tests):

```bash
pytest
```

## How to Add a New Fixture

1. Add your CSV to `benchmarks/fixtures/`. Use 5–10 rows. Keep it human-readable.
2. Add a corresponding entry to `benchmarks/expected/expected_schema.json`.
   - Provide the expected original column name for each of the 5 canonical fields, or `null` if that field is not expected to be detected.
3. Add a corresponding entry to `benchmarks/expected/expected_findings.json`.
   - `required_findings`: finding codes that must appear (e.g., `missing_p_value`).
   - `forbidden_findings`: finding codes that must not appear.
   - `known_limitations`: optional notes for fields that are intentionally not detected.
4. Add a corresponding entry to `benchmarks/expected/expected_scores.json`.
   - `score_band`: `[min, max]`. Use a tight band unless there is genuine uncertainty.
5. Run `python benchmarks/run_benchmark.py` and confirm the new fixture passes.
6. Run `pytest` and confirm no regressions.

**Finding codes** used in expected JSON:

| Code | Meaning |
|---|---|
| `missing_p_value` | No valid p-value column found |
| `missing_fdr` | No valid FDR column found |
| `invalid_p_value` | p-value column detected but fails value validation |
| `invalid_fdr` | FDR column detected but fails value validation |
| `ambiguous_p_value` | Multiple columns match the p_value alias set |
| `ambiguous_fdr` | Multiple columns match the fdr alias set |
| `fdr_consistency_warning` | FDR values are frequently smaller than p-values |

## Precision and Recall

Precision and recall are computed at the **canonical field level**, not the fixture level.

For each fixture × canonical field pair, the runner compares the expected original column (from `expected_schema.json`) to the actual detected original column (from `audit_dataframe(df)["detected"]`):

| Expected | Actual | Outcome |
|---|---|---|
| non-null, matches actual | same column | True Positive (TP) |
| null | null | True Negative (TN) |
| null | non-null | False Positive (FP) |
| non-null | null or different column | False Negative (FN) |

```
Precision = TP / (TP + FP)
Recall    = TP / (TP + FN)
```

A **false positive** means the schema mapper claimed a column mapped to a canonical field when it should not have.
A **false negative** means the schema mapper failed to detect a field that was present.

The benchmark asserts `precision == 1.0` and `recall == 1.0` across the included fixture suite.

## Why Adversarial Headers Are Included

The original schema detection code used naive substring matching:
- `find_col(["p", "pvalue"])` — any column containing the letter `p` (e.g., `compound_id`, `pathway`, `phenotype`, `platform`, `replicate`, `sample`) could be detected as a p-value column.
- `find_col(["fdr", "q", "adj"])` — any column containing `q` or `adj` (e.g., `quant`, `request`, `quality`, `acquisition`, `adjacent`) could be detected as an FDR column.

The adversarial fixtures exist to prevent this class of regression from returning. If any of those columns are re-detected as `p_value` or `fdr`, the benchmark will fail with a false positive.

## Known Limitations

- **msdial_like.csv**: The `MS/MS assigned` column normalises to `ms_ms_assigned`, which is not in the `annotation` alias set. Annotation is therefore not detected for this fixture. This is documented in `expected_findings.json` as a known limitation. It is not a detection error.
- All fixtures use small in-memory tables (5–7 rows). Detection precision is header-level only; value distributions in these tables are not representative of real metabolomics datasets.
- The benchmark validates schema detection and audit behavior. It does not validate biological truth or upstream experimental reproducibility.

## Score and Confidence Interpretation

### Score

The score starts at 100 and penalties are subtracted:

| Condition | Penalty |
|---|---|
| Missing or invalid p-value | −40 |
| Missing or invalid FDR | −20 |
| Ambiguous p_value field | −5 |
| Ambiguous fdr field | −5 |
| Ambiguous compound_id field | −5 |
| Ambiguous effect_size field | −5 |
| Ambiguous annotation field | −3 |
| Maximum ambiguity penalty | −15 (cap) |

A score of **100** means the table is complete, all statistical values are in a valid probability range, and no critical field is ambiguous. A complete table that contains one field with two plausible aliases will score **95**, not 100.

### Confidence Label

| Label | Condition |
|---|---|
| `high` | p-value valid, FDR valid, no ambiguous critical field |
| `medium` | p-value valid but FDR missing/invalid, OR any critical field ambiguous |
| `low` | p-value missing or invalid |

The confidence label is separate from the score. A table that scores 80 (missing FDR) has `medium` confidence. A table that scores 40 (missing p-value and FDR) has `low` confidence.

### Limitation

The benchmark is a regression and behavior suite, not a real-world validation study. It does not establish performance across published metabolomics supplements or expert-labeled external datasets.
