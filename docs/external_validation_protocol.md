# Validex External Validation Protocol

**Status: scaffold only. No external validation results have been reported.**

This document defines the protocol for an external validation study of Validex on real published metabolomics result tables. The study has not been conducted yet. This document defines how it must be conducted when it is.

---

## 1. Purpose

The external validation study is intended to estimate Validex performance on real published metabolomics result tables, separately from the internal synthetic benchmark.

The internal synthetic benchmark (`benchmarks/`) uses purpose-built CSV fixtures. It is a regression and behavior suite. It does not establish performance on real-world tables with novel export formats, unusual column names, or platform-specific conventions. External validation is required before any performance claims can be made about real-world behavior.

---

## 2. Scope

The study evaluates **downstream result-table auditing only**. Specifically:

**In scope:**
1. Schema detection (canonical field detection from column headers)
2. Missing field detection (missing p-value, missing FDR)
3. Invalid p-value or FDR value detection (out-of-range or non-numeric values)
4. Ambiguous schema field detection (multiple columns matching the same alias)
5. Audit score and confidence label behavior

**Out of scope:**
1. Raw LC-MS or MS/MS data preprocessing
2. Peak picking or chromatographic peak detection
3. Chromatographic alignment or retention time correction
4. Metabolite identification correctness
5. Experimental design validity
6. Biological truth of reported findings
7. Clinical utility
8. Statistical analysis correctness
9. Repository compliance (MetaboLights, Metabolomics Workbench submission standards)

---

## 3. What Counts as an Eligible External Dataset

A candidate table must meet all of the following criteria:

1. It comes from a real published metabolomics study or an official repository record (MetaboLights, Metabolomics Workbench, or equivalent).
2. It is legally accessible for review and use under the applicable license.
3. It is a post-analysis metabolomics result table or feature-level result table — not a raw abundance matrix, raw instrument file, or processing intermediate.
4. It contains enough column headers and data rows for schema auditing (minimum: 2 data rows, at least 3 columns).
5. It is stored in the `validation/tables/` directory only if the applicable license permits redistribution or local storage for research purposes. If redistribution is not permitted, only the registry metadata and labels should be committed; the table file must be downloaded separately by the reviewer.
6. It represents a distinct publication, platform, or table format not already covered by the existing 14 synthetic fixtures.

---

## 4. What Must Not Be Included

The following must never be added to the repository or used in the external validation study:

1. Copyrighted supplementary files or publisher PDFs unless the applicable license explicitly permits redistribution.
2. Patient-identifiable or personally identifiable information.
3. Raw instrument files (mzML, mzXML, .raw, .wiff, .d, or similar).
4. Private unpublished lab data.
5. Tables copied or transcribed from paper figures or tables without clear source attribution and licensing clarity.
6. AI-generated or synthetic datasets presented as real external data.

---

## 5. Registry Fields

Each candidate table must have an entry in the registry CSV (`validation/registry.csv` or `validation/registry.example.csv` for examples). Registry columns:

| Column | Description |
|--------|-------------|
| `dataset_id` | Unique identifier, e.g. `EXT_001`. Use `EXAMPLE_NNN` for illustrative examples. |
| `source_title` | Title of the source publication or repository record. |
| `source_type` | One of: `journal_supplement`, `repository_record`, `preprint_supplement`, `other`. |
| `source_url_or_doi` | URL or DOI of the source. Use a DOI where available. |
| `license_or_access_note` | License (e.g. CC BY 4.0) or access note (e.g. "Freely available, no redistribution license stated"). |
| `table_filename` | Filename of the CSV table in `validation/tables/`. Empty if redistribution is not permitted. |
| `table_description` | One-sentence description of the table contents. |
| `organism_or_sample_context` | Organism or sample context (e.g. "Human plasma", "Mouse liver"). |
| `platform_if_known` | Analysis platform if known (e.g. "XCMS", "MetaboAnalyst", "MS-DIAL", "unknown"). |
| `study_domain` | Domain (e.g. "lipidomics", "metabolomics", "mixed"). |
| `included` | `yes` if the table passes eligibility criteria, `no` if excluded. |
| `exclusion_reason` | Reason for exclusion if `included = no`. Empty otherwise. |
| `notes` | Any reviewer notes. |

---

## 6. Labeling Instructions

Each included table must be manually labeled by at least one reviewer. Two-reviewer agreement is preferred. Disagreements should be resolved by discussion and documented in `notes`.

### Canonical Schema Labels

For each of the following canonical fields, record the exact original column name as it appears in the CSV header:

| Canonical field | Record |
|-----------------|--------|
| `compound_id` | Exact original column name if present, empty string if absent. |
| `effect_size` | Exact original column name if present, empty string if absent. |
| `p_value` | Exact original column name if present, empty string if absent, or `AMBIGUOUS:col1|col2` if multiple plausible columns exist. |
| `fdr` | Exact original column name if present, empty string if absent, or `AMBIGUOUS:col1|col2` if multiple plausible columns exist. |
| `annotation` | Exact original column name if present, empty string if absent. |

### Optional Labels

The following additional fields may be labeled for reference but are not used in the current metric calculation:

`control_mean`, `case_mean`, `sample_size`, `group`, `mz`, `rt`

### Label Examples

```
compound_id = compound_id
effect_size = logFC
p_value     = p_value
fdr         = FDR
annotation  = Annotation
```

```
compound_id = Metabolite
effect_size = log2 fold change
p_value     = raw p
fdr         = AMBIGUOUS:FDR|padj
annotation  =
```

### AMBIGUOUS Label Meaning

`AMBIGUOUS:col1|col2` means the reviewer found multiple columns that are plausible matches for the same canonical field and could not determine the intended column from context alone. When a label is AMBIGUOUS, Validex is expected to detect at least one of the listed columns and to emit an ambiguous schema field finding.

---

## 7. Supported Canonical Fields

The following canonical fields are currently supported for detection:

| Canonical field | Aliases include (not exhaustive) |
|-----------------|----------------------------------|
| `compound_id` | compound_id, metabolite, feature_id, mz_rt |
| `effect_size` | logFC, log2FC, fold_change, estimate |
| `p_value` | p_value, pvalue, pval, raw_p, nominal_p |
| `fdr` | fdr, q_value, padj, adjusted_p, benjamini_hochberg |
| `annotation` | annotation, confidence, msi_level, identification_level |

The full alias list is in `validex/schema_mapper.py` (`KNOWN_ALIASES`). Novel column names not in the alias list will not be detected. This is an expected limitation of the alias-based approach.

---

## 8. Finding Label Instructions

Reviewers should label expected findings for each table from the following controlled vocabulary:

| Finding code | Meaning |
|--------------|---------|
| `missing_p_value` | No p-value column is present or detectable. |
| `missing_fdr` | No FDR or adjusted p-value column is present or detectable. |
| `invalid_p_value_column` | A p-value column is present but contains out-of-range values. |
| `invalid_fdr_column` | An FDR column is present but contains out-of-range values. |
| `ambiguous_schema_field` | Two or more columns match the same canonical alias. |

Record expected findings as a pipe-separated list in the labels CSV `expected_findings` column. Empty string means no findings are expected.

---

## 9. Reviewer Workflow

1. Identify a candidate table from a published study or repository.
2. Check eligibility criteria (Section 3) and exclusion criteria (Section 4).
3. Add a row to the registry CSV with all required fields.
4. If redistribution is permitted, save the table as a CSV in `validation/tables/<dataset_id>_<table_filename>.csv`.
5. Open the table and manually identify canonical fields.
6. Complete a row in the labels CSV for the table.
7. Record expected findings based on the labels.
8. If two reviewers labeled independently, compare labels and resolve disagreements. Document resolution in `notes`.
9. Run the external validation runner:
   ```bash
   python validation/run_external_validation.py \
     --registry validation/registry.csv \
     --labels validation/labels.csv \
     --tables-dir validation/tables \
     --output validation/external_results.json
   ```
10. Review the output for false positives and false negatives. Assign failure reason categories (Section 11).

---

## 10. Metrics

The following metrics are computed by the external validation runner:

### Schema Detection Metrics (field level)

- **True Positive (TP):** Validex detected the correct column for a canonical field that the reviewer labeled as present.
- **False Positive (FP):** Validex detected a column for a canonical field that the reviewer labeled as absent.
- **False Negative (FN):** Validex failed to detect any column (or detected the wrong column) for a canonical field the reviewer labeled as present.
- **True Negative (TN):** Validex correctly detected nothing for a canonical field the reviewer labeled as absent.

Computed from these:
- **Field-level precision** = TP / (TP + FP)
- **Field-level recall** = TP / (TP + FN)
- **Exact schema match rate** = fraction of tables where all five canonical fields are correctly detected

### Finding Metrics

- **Finding precision** = TP_findings / (TP_findings + FP_findings)
- **Finding recall (sensitivity)** = TP_findings / (TP_findings + FN_findings)

Where a finding is a TP if the reviewer labeled it as expected and Validex emitted it; FP if Validex emitted it but reviewer did not expect it; FN if reviewer expected it but Validex did not emit it.

### Score Distribution

The distribution of audit scores (0–100) and confidence labels (high/medium/low) across the external dataset.

---

## 11. Failure Analysis

Every false positive and false negative must be assigned a reason category:

| Category | Description |
|----------|-------------|
| `unseen_synonym` | Column name is a valid synonym not in the current alias list. |
| `malformed_header` | Column name contains unexpected characters that break normalization. |
| `multi_header_table` | The table uses multiple header rows; the CSV parser sees only one. |
| `non_english_header` | Column name is in a non-English language. |
| `platform_specific_export` | Export format from a specific tool uses non-standard column names. |
| `ambiguous_biological_meaning` | The column could plausibly belong to multiple canonical fields. |
| `value_validation_edge_case` | Values pass the alias check but fail value-level probability validation. |
| `parser_or_file_format_issue` | The file uses encoding, delimiter, or quoting that causes misparse. |
| `reviewer_disagreement` | Two reviewers disagree on the expected label. |
| `other` | None of the above categories apply. |

---

## 12. Evidence-Level Language

### Before external validation is run

All documentation must say:

> External validation scaffold exists, but no external validation results have been reported.

### After external validation is run

Documentation may say:

> Validex was evaluated on N externally sourced result tables under the protocol in `docs/external_validation_protocol.md`. [Precision: X, Recall: Y, Exact schema match rate: Z]

### Language that is never allowed

- "Validated generally."
- "Proven accurate."
- "Works on all metabolomics tables."
- "Clinically validated."
- "Publication ready as a validated tool."
- Any precision or recall claim without the N, protocol reference, and date.

---

## 13. Claims Allowed After External Validation

After a completed, documented external validation study:

1. "Validex was evaluated on N externally sourced metabolomics result tables under the protocol in `docs/external_validation_protocol.md`."
2. "On this external dataset, Validex achieved field-level precision of X and recall of Y."
3. "The most common failure category was [category] (see failure analysis)."
4. "Known limitations identified during external validation: [list]."

---

## 14. Claims Still Not Allowed After External Validation

Even with completed external validation:

1. "Validex validates metabolomics studies."
2. "Validex proves biological findings."
3. "Validex guarantees reproducibility."
4. "Validex is clinically validated."
5. "Validex replaces MetaboAnalyst, XCMS, MS-DIAL, MZmine, or expert curation."
6. "Validex detects all possible reporting problems."
7. "Validex guarantees correct metabolite identification."
8. Performance claims generalized beyond the specific dataset used.
9. Any claim citing performance on datasets not included in the external validation study.
