# Validex: Scope, Prior Art, and Claims Discipline

This document defines what Validex does and does not do, where it sits in the metabolomics analysis workflow, adjacent tool categories, prior-art areas that require formal citation, the current evidence level, and which claims are and are not supported by that evidence.

---

## 1. What Validex Does

Validex audits post-analysis metabolomics result tables for reporting completeness and interpretability signals.

Specifically, Validex:

- Parses uploaded CSV result tables.
- Detects which columns correspond to canonical scientific fields: compound identifier, effect size or fold change, raw p-value, FDR or adjusted p-value, and annotation or identification confidence.
- Uses strict alias-based schema detection with header normalization. Detection is exact-match after normalization, not substring matching.
- Validates that detected p-value and FDR columns contain numeric values within a valid probability range [0, 1].
- Flags missing critical statistical fields (missing p-values, missing FDR).
- Flags invalid statistical columns (out-of-range or non-numeric values).
- Flags ambiguous schema fields (multiple columns matching the same canonical alias set).
- Reports an audit score (0–100) and an audit confidence label (high, medium, low).
- Generates a Markdown and JSON audit report.

---

## 2. What Validex Does Not Do

Validex does not:

1. Process raw LC-MS, GC-MS, MS/MS, or NMR instrument files.
2. Perform peak picking or chromatographic peak detection.
3. Perform chromatographic alignment or retention time correction.
4. Perform metabolite identification or spectral matching.
5. Perform statistical testing from raw abundance matrices (t-test, ANOVA, PERMANOVA, etc.).
6. Validate experimental design, sample size, or statistical power.
7. Validate biological truth or interpret biological meaning.
8. Replace expert review, statistical review, or bioinformatics peer review.
9. Guarantee downstream reproducibility.
10. Detect all possible reporting problems in metabolomics result tables.

---

## 3. Where Validex Sits in the Metabolomics Workflow

Validex operates on **downstream result tables** — the output of upstream analysis steps. A typical metabolomics workflow preceding Validex input includes:

```
Raw instrument data (LC-MS, GC-MS, NMR, ...)
    ↓
Raw data processing (peak picking, alignment, normalization)
    ↓
Metabolite annotation / identification
    ↓
Statistical analysis (differential abundance, correction for multiple testing)
    ↓
Result table  ←  [Validex audits this]
    ↓
Interpretation, reporting, submission to repository
```

Validex does not touch any step above the result table. It audits whether the result table contains the expected reporting fields and whether the statistical columns it finds are value-plausible.

---

## 4. Adjacent Tool Categories

These tool categories are adjacent to or upstream of Validex. Validex does not replicate, replace, or validate any of them.

### 4.1 Raw Data and Peak Processing Tools

Tools that process raw instrument files into feature tables (peak lists, abundance matrices). Examples include XCMS, MS-DIAL, MZmine, and OpenMS. Validex receives their output but does not audit the correctness of their processing.

### 4.2 Statistical Analysis Platforms

Tools that apply differential abundance testing, normalization, and multiple testing correction to feature tables. Examples include MetaboAnalyst and custom R or Python workflows. Validex can detect whether statistical output fields are present and value-plausible, but it does not re-run or validate the statistical analysis itself.

### 4.3 Metabolomics Repositories and Curation Systems

Public repositories such as MetaboLights and Metabolomics Workbench have curation requirements and submission formats. Validex is not a submission validator for any repository and does not enforce repository-specific formats.

### 4.4 Reporting Standards and Minimum Information Frameworks

The Metabolomics Standards Initiative (MSI) and related bodies define minimum information requirements for metabolomics reporting. Validex is not an MSI compliance checker. It audits a limited subset of fields that overlap with reporting completeness concerns.

### 4.5 FAIR and Metadata Validators

Tools that assess Findability, Accessibility, Interoperability, and Reusability (FAIR) compliance of datasets. Validex is narrower than FAIR assessment: it focuses only on statistical reporting fields in result tables.

### 4.6 Multiple Testing and Omics Reporting Practices

Omics studies routinely require FDR correction to control false discovery rates. Validex checks whether an FDR-adjusted column is present and value-plausible, but it does not audit which correction method was used or whether the correction was applied correctly.

---

## 5. Prior-Art References

The following references identify relevant prior art. Full details and grouped citations are in [`docs/references.md`](references.md).

**Reporting standards and data formats**

- Sumner, L.W. et al. (2007). "Proposed minimum reporting standards for chemical analysis." *Metabolomics*, 3(3), 211–221. DOI: 10.1007/s11306-007-0082-2
- Hoffmann, N. et al. (2019). "mzTab-M: A Data Standard for Sharing Quantitative Results in Mass Spectrometry Metabolomics." *Analytical Chemistry*, 91(5), 3302–3310. DOI: 10.1021/acs.analchem.8b04310
- Rocca-Serra, P. et al. (2010). "ISA software suite: supporting standards-compliant experimental annotation and enabling curation at the community level." *Bioinformatics*, 26(18), 2354–2356. DOI: 10.1093/bioinformatics/btq415

**Repositories**

- Yurekten, O. et al. (2024). "MetaboLights: open data repository for metabolomics." *Nucleic Acids Research*, 52(D1), D640–D646. DOI: 10.1093/nar/gkad1045

**FAIR and open data principles**

- Wilkinson, M.D. et al. (2016). "The FAIR Guiding Principles for scientific data management and stewardship." *Scientific Data*, 3, 160018. DOI: 10.1038/sdata.2016.18

**Statistical methods**

- Benjamini, Y. and Hochberg, Y. (1995). "Controlling the False Discovery Rate: A Practical and Powerful Approach to Multiple Testing." *Journal of the Royal Statistical Society: Series B*, 57(1), 289–300. DOI: 10.1111/j.2517-6161.1995.tb02031.x

**Upstream analysis tools**

- Pang, Z. et al. (2024). "MetaboAnalyst 6.0: towards a unified platform for metabolomics data processing, analysis and interpretation." *Nucleic Acids Research*, 52(W1), W398–W406. DOI: 10.1093/nar/gkae253
- Smith, C.A. et al. (2006). "XCMS: Processing Mass Spectrometry Data for Metabolite Profiling Using Nonlinear Peak Alignment, Matching, and Identification." *Analytical Chemistry*, 78(3), 779–787. DOI: 10.1021/ac051437y
- Tsugawa, H. et al. (2015). "MS-DIAL: data-independent MS/MS deconvolution for comprehensive metabolome analysis." *Nature Methods*, 12(6), 523–526. DOI: 10.1038/nmeth.3393
- Schmid, R. et al. (2023). "Integrative analysis of multimodal mass spectrometry data in MZmine 3." *Nature Biotechnology*. DOI: 10.1038/s41587-023-01690-2
- Röst, H.L. et al. (2016). "OpenMS: a flexible open-source software platform for mass spectrometry data analysis." *Nature Methods*, 13, 741–748. DOI: 10.1038/nmeth.3959

---

## 6. Current Evidence Level

The current validation evidence for Validex is:

1. Unit tests for schema detection logic (`tests/test_schema_mapper.py`) covering false positive prevention and valid alias coverage.
2. Unit tests for audit engine behavior (`tests/test_audit.py`) covering missing field detection, value-level validation, ambiguity handling, and confidence labels.
3. A 14-fixture synthetic benchmark suite (`benchmarks/`) covering standard tables, missing statistical fields, invalid statistical values, ambiguous aliases, adversarial headers, and common export-style headers (MetaboAnalyst-like, MS-DIAL-like, XCMS-like, mixed case, punctuation variants).
4. On the included synthetic benchmark suite, Validex currently achieves **100% field-level schema detection precision and recall**.

This is **not** external validation. Specifically:

- The benchmark fixtures are synthetic and purpose-built. They are not drawn from published supplementary metabolomics tables.
- No expert-labeled external dataset has been used.
- No comparison against published metabolomics repository submissions has been performed.
- Performance on real-world tables with novel export formats, unusual column names, or platform-specific conventions is unknown.

---

## 7. Claims That Are Allowed

The following claims are supported by the current evidence:

1. Validex is a prototype reporting-completeness auditor for metabolomics result tables.
2. Validex uses strict alias-based schema detection with header normalization.
3. Validex flags missing raw p-values, missing FDR or adjusted p-values, invalid probability values, and ambiguous schema fields.
4. Validex includes regression tests and a synthetic benchmark suite.
5. On the included synthetic benchmark suite, Validex currently achieves 100% field-level precision and recall.
6. Validex is designed to complement, not replace, expert review.
7. Validex is a local, privacy-first tool — datasets are not sent to external services.

---

## 8. Claims That Are Not Allowed

The following claims are **not** supported and must not appear in any description of Validex:

1. "Validex validates metabolomics studies."
2. "Validex proves biological findings."
3. "Validex guarantees reproducibility."
4. "Validex is clinically validated."
5. "Validex is publication-ready as a validated methods tool."
6. "Validex replaces MetaboAnalyst, XCMS, MS-DIAL, MZmine, or expert curation."
7. "Validex detects all possible reporting problems."
8. "Validex guarantees correct metabolite identification."
9. Any claim citing specific journals, authors, DOIs, or benchmark datasets that have not been verified.

---

## 9. Next Validation Steps

To move Validex beyond a prototype with synthetic benchmarks, the following steps are needed:

1. Collect real published supplementary metabolomics result tables from journals or repositories (with appropriate use permissions).
2. Label expected canonical fields manually or with expert review.
3. Include tables from multiple platforms and export styles not already in the synthetic benchmark.
4. Measure schema detection precision and recall on this external dataset.
5. Measure agreement between Validex findings and expert reviewer judgments.
6. Document common failure cases and false positives or negatives.
7. Update alias sets based on observed gaps, using predefined normalization rules only (no substring matching regressions).
8. Keep external validation data strictly separate from the synthetic benchmark fixtures.
9. Report external validation results honestly, including limitations, before making any stronger claims.
