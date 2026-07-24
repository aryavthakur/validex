---
title: 'Validex: Deterministic Audit of Downstream Metabolomics Result Tables'
tags:
  - Python
  - metabolomics
  - lipidomics
  - data quality
  - deterministic audit
  - field recognition
authors:
  - name: Aryav Thakur
    orcid: # [ORCID REQUIRED]
    affiliation: "1, 2, 3"
    corresponding: true
  - name: Jaxon Munson
    orcid: # [ORCID REQUIRED OR CONFIRM NONE]
    affiliation: "1, 2, 3"
  - name: Sanjoy Bhattacharya
    orcid: # [ORCID REQUIRED]
    affiliation: "1, 2, 3"
affiliations:
  - name: Bascom Palmer Eye Institute, University of Miami Miller School of Medicine, Miami, Florida 33136, USA
    index: 1
  - name: Miami Integrative Metabolomics Research Center, Miami, Florida 33136, USA
    index: 2
  - name: University of Miami Miller School of Medicine, Miami, Florida 33136, USA
    index: 3
date: 24 July 2026
bibliography: paper.bib
---

# Summary

Validex is a deterministic audit tool for downstream metabolomics and lipidomics result tables. It addresses the practical problem that computational workflows consuming these tables must determine whether expected statistical and biological fields — compound identifiers, effect sizes, p-values, false discovery rate (FDR) values, and annotation evidence — can be recognized from heterogeneous column headers and validated at the cell level.

Validex performs header-level field recognition using a governed alias registry, followed by value-level probability validation with a configurable usability threshold. It supports CSV, TSV, and XLSX inputs with explicit spreadsheet-sheet selection. All audit stages are deterministic: given identical input, the output is identical. No machine-learning model, stochastic procedure, or external cloud service is used during auditing.

The tool produces structured audit output including detected fields (usability-gated), ambiguity records (structural detection), statistical validation evidence, confidence labels, and user-facing findings. It is available as both a command-line interface and a local web application.

# Statement of Need

Downstream metabolomics and lipidomics analyses produce result tables containing statistical summaries — p-values, FDR-corrected q-values, fold changes, compound identifiers, and identification-confidence annotations [@sumner2007proposed]. These tables use heterogeneous column headers across studies, laboratories, and software platforms. When downstream workflows or meta-analyses consume these tables, they face a reproducibility challenge: verifying whether expected fields are present, correctly identified, and statistically valid.

Currently, researchers inspect table headers manually, a process that is time-consuming, difficult to reproduce, and error-prone when tables use non-standard column naming. No existing tool specifically performs deterministic, rule-based auditing of downstream metabolomics result-table structure and probability-field validity.

Validex fills this gap by providing a reproducible, deterministic audit that can be applied consistently across tables from different sources. Its intended users are metabolomics researchers, bioinformaticians, and data curators who need to verify table structure before downstream analysis or reporting.

# Software Design

Validex processes input tables through five deterministic stages:

1. **Ingestion**: CSV, TSV, and XLSX files are parsed into a normalized data frame. XLSX workbooks support explicit sheet selection.

2. **Structural field recognition**: Column headers are normalized and matched against a governed alias registry containing validated synonyms for each canonical field. Candidates are generated, ranked, and selected deterministically. The schema mapper records structural detection results, candidate lists, ambiguity status, and selection reasons.

3. **Value-level probability validation**: For probability fields (p-value and FDR), every cell is classified as valid numeric, missing, nonnumeric, nonfinite, or out of range. A probability column is considered usable only when its valid fraction meets or exceeds 80% of total rows.

4. **Usability gating**: If a probability column fails the usability threshold, its active detected field is set to null. The structurally recognized column name is preserved independently in the ambiguity record.

5. **Audit output**: The audit produces detected fields (usability-gated), ambiguity records (structural), statistical validation evidence, confidence labels, completeness assessments, and user-facing findings with severity levels.

Additional features include FDR comparable-row handling (checking whether FDR values are consistently greater than or equal to p-values), duplicate-identifier detection, output provenance, and structured error reporting.

# Quality Control

Validex includes 350 automated tests covering field detection, alias matching, probability validation, XLSX ingestion, ambiguity resolution, edge cases, and regression scenarios. A clean-environment installation test has been verified on macOS with Python 3.13.

A prospectively frozen synthetic held-out benchmark (160 cases) produced 147/160 exact-table agreement. Post hoc adjudication determined that all 13 disagreements resulted from a benchmark-reference defect — the ground truth expected structural column names in a usability-gated output field — not from product errors. Structural field recognition succeeded in all 160 cases. The benchmark, outputs, and adjudication evidence are included in the repository with SHA-256 hash verification.

No quantitative real-world validation has been completed. A public corpus feasibility study screened 187 candidate tables from public repositories but identified zero eligible tables under the frozen criteria. Real-world evaluation using independently supplied metabolomics tables is planned as future work. Validex remains a research-preview tool.

# Availability

Validex is available under the MIT License at `<VALIDEX_REPOSITORY_URL>`. Installation requires Python 3.10 or later. Documentation, a quickstart tutorial, and the synthetic benchmark are included in the repository.

# Acknowledgments

The authors acknowledge the research environments and institutional support provided by the Bascom Palmer Eye Institute, the Miami Integrative Metabolomics Research Center, and the University of Miami Miller School of Medicine.

AI tools (Claude, Anthropic) assisted with software development, corpus screening, and documentation. The authors are responsible for all scientific conclusions.

# References
