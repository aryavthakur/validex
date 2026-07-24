# Validex

**Research-preview deterministic audit tool for downstream metabolomics result tables.**

Validex performs header-level field recognition and value-level probability validation on CSV, TSV, and XLSX files containing downstream metabolomics or lipidomics results. It is designed to detect whether expected statistical and biological fields (compound identifiers, effect sizes, p-values, FDR/q-values, and annotation evidence) can be recognized and represented from machine-readable inputs.

## Intended Users

Researchers, bioinformaticians, and data curators working with downstream metabolomics result tables who need deterministic, reproducible field-recognition audits.

## Problem Addressed

Downstream metabolomics tables use heterogeneous headers and file formats. Validex provides a deterministic audit of whether expected fields can be recognized, without interpreting biological findings or validating statistical conclusions.

## Deterministic Design

All Validex audit stages are deterministic: ingestion, alias-governed header matching, candidate ranking, structural selection, probability-field usability gating, and output serialization. No machine learning, stochastic procedure, or external cloud service is used during auditing. An optional local-only AI analysis feature (via Ollama) is available but not required.

## Supported Input Formats

- CSV (comma-separated values)
- TSV (tab-separated values)
- XLSX (Excel workbooks with explicit sheet selection)

## Main Output Concepts

- **Detected fields**: Usability-gated field assignments (null if a probability column fails validation)
- **Ambiguity records**: Structural detection results independent of usability
- **Candidate records**: All matched alias candidates per field
- **Statistical validation**: Per-cell probability classification with validity fractions
- **Audit confidence**: High / medium / low based on completeness and data quality
- **Findings**: User-facing warnings with severity levels

## Getting Started

- [Installation guide](INSTALLATION.md)
- [Quickstart tutorial](QUICKSTART.md)

## Manuscript Status

A submission-ready manuscript is available at `validation_study/synthetic_benchmark/synthesis/20260724_manuscript/submission/MANUSCRIPT_SUBMISSION_DRAFT.md`. The manuscript has not undergone independent peer review.

## Synthetic Evaluation Summary

Validex 0.2.0 was evaluated on a prospectively frozen synthetic held-out benchmark:

| Metric | Value |
|--------|-------|
| Exact-table agreement | **147/160** |
| Ingestion success | 160/160 |
| XLSX ingestion success | 26/26 |
| Compound identifier F1 | 1.000 |
| Effect size F1 | 1.000 |
| P-value F1 | 0.958 |
| FDR F1 | 0.954 |
| Annotation F1 | 1.000 |

These results are from synthetic engineering fixtures, not a probability sample of real-world tables.

## Benchmark Adjudication

Post hoc adjudication determined that the 13 non-exact cases resulted from a **benchmark-reference defect** (the ground truth expected structural column names in a usability-gated output field). No product defect was identified. Structural field recognition succeeded in all 160 held-out cases. See `submission/BENCHMARK_REFERENCE_CORRECTION_NOTE.md`.

The frozen primary result of **147/160** was not recalculated. The adjudication is a post hoc interpretive correction.

## Real-World Feasibility

A public corpus feasibility study screened 187 uncontaminated candidate tables from public repositories. Zero tables met the frozen eligibility criteria. No quantitative real-world Validex evaluation was completed.

## Claim Boundaries

Validex does **not** claim or establish:
- Clinical validation
- Biological validation
- Independent expert validation
- Broad real-world accuracy
- Generalization to all metabolomics result tables

## Repository Structure

```
validex_0_2_worktree/          # Locked Validex 0.2.0 product source (local worktree)
validation_study/
  synthetic_benchmark/         # v2 benchmark: specs, fixtures, outputs, analysis
    synthesis/20260724_manuscript/  # Manuscript synthesis and adjudication
      submission/              # Submission-ready manuscript, tables, figures
      probability_contract_adjudication/  # 13-case adjudication
  release_readiness/           # Public-release audit and retrieval manifests
  scripts/                     # Verification and processing scripts
```

## Reproducibility

All frozen artifacts are hashed with SHA-256 and inventoried. Verification scripts check metric consistency, artifact preservation, and claim boundaries:

```bash
python3 validation_study/scripts/verify_validex_submission_package.py
python3 validation_study/scripts/verify_validex_commit_scope.py
```

## Citation

See [CITATION.cff](CITATION.cff) for citation metadata.

## License

This repository is released under the [MIT License](LICENSE).

## Contributing

Validex is in research-preview status. Contribution guidelines will be established after initial public release and peer review.

## Research-Preview Warning

Validex is a research-preview tool. It has not undergone independent scientific peer review or real-world expert validation. Do not use it for clinical decisions or as the sole basis for scientific conclusions.
