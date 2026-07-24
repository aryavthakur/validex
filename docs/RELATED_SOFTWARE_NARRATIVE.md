# Related Software and Positioning of Validex

**Date:** 2026-07-24
**Scope:** Software tools, formats, and standards related to Validex's function: auditing downstream metabolomics result tables for reporting completeness and internal consistency.

---

## 1. What Validex does

Validex 0.1.0 is a local-first, deterministic auditor for CSV tables that are intended to contain downstream metabolomics comparison results. It maps a finite set of exact normalized header aliases to five canonical reporting fields (compound/metabolite identifier, p-value, FDR/adjusted p-value, fold change, annotation), checks usability of recognized probability columns, reports missing/ambiguous/invalid/duplicate conditions and FDR-versus-p-value consistency, and calculates a heuristic score plus an interpretability confidence label. It does not process raw spectra, recompute statistics, verify metabolite identity, or certify publication readiness.

---

## 2. Tool landscape categories

### 2.1 Direct alternatives (result-table auditing)

**No direct alternative was identified.** No existing open-source or commercial tool was found that specifically audits downstream metabolomics result tables (CSV/TSV) for field completeness, header alias normalization, probability-column validity, FDR-versus-p-value consistency, and ambiguity reporting.

The closest conceptual analogue is **statcheck**, which automatically detects statistical reporting inconsistencies in psychology articles. However, statcheck operates on APA-formatted prose in PDFs/HTML (extracting test statistics and recomputing p-values), not on structured CSV tables. It also does not perform schema detection, alias normalization, or metabolomics-specific checks.

**Gap assessment:** Validex addresses an unoccupied niche. The metabolomics software ecosystem has extensive coverage of upstream processing (raw data to feature tables), analytical QC (instrument monitoring), and statistical analysis, but lacks automated tools that audit the structure and internal consistency of the result tables that these pipelines produce.

### 2.2 Adjacent tools (related but different function)

| Tool | Relationship to Validex |
|---|---|
| **MetaboReport** | Generates new comprehensive HTML reports from metabolomics data. Validex audits existing result tables without generating new analyses. MetaboReport is a report *producer*; Validex is a report *auditor*. |
| **mzQuality** | Performs batch correction and outlier detection on peak area tables from targeted MS. Operates on processed tables (like Validex) but modifies data rather than auditing reporting completeness. |
| **MetaboAnalyst QC module** | Checks input data quality (CV filtering, outlier detection, PCA clustering of QC samples) before statistical analysis. This is pre-analysis QC, not post-analysis result-table auditing. |
| **QCScreen** | Checks analytical signal quality parameters from LC-HRMS. Instrument-level QC, not result-table auditing. |

### 2.3 Upstream tools (raw data processing)

These tools produce the feature tables and statistical results that Validex would subsequently audit:

| Tool | What it produces |
|---|---|
| **XCMS** | Feature detection, alignment, and grouping from LC-MS/GC-MS raw data. Output feature tables could become Validex input after statistical analysis. |
| **MZmine** | Similar to XCMS; exports feature lists as CSV/MGF. |
| **DIAMetAlyzer** | FDR-controlled metabolite identification from DIA-MS data. Computes FDR during spectral analysis (upstream), while Validex checks whether reported FDR values in result tables are valid (downstream). |
| **asari** | Trackable LC-MS data processing. Produces feature tables. |

None of these tools audit the structure or reporting completeness of their own output tables or of result tables produced by downstream statistical analysis.

### 2.4 General tabular data validation frameworks

| Tool | Overlap | Key difference |
|---|---|---|
| **Great Expectations** | Both validate tabular data structure. Moderate overlap in concept. | Great Expectations is a general-purpose data pipeline validation framework requiring user-defined expectations (rules). It has no metabolomics-specific logic, no header alias detection, no built-in p-value/FDR rules. A user could theoretically configure GX to perform similar checks, but this would require writing all domain logic from scratch. |
| **pandera** | Both validate tabular data schemas. Moderate overlap in concept. | pandera validates pandas DataFrames against user-defined schemas programmatically. Validex auto-detects schemas from header aliases without requiring user schema definition. pandera has no metabolomics-specific logic. |
| **Frictionless Data (goodtables)** | Both validate CSV structural conformance. Low overlap. | Frictionless checks general CSV structure (types, constraints, encoding). No domain-specific logic. |
| **CSVLint** | Both validate CSV files. Low overlap. | CSVLint checks CSV structural conformance (headers, types, encoding). No domain-specific logic. |
| **ydata-profiling** | Both generate data quality reports. Low overlap. | ydata-profiling generates comprehensive EDA reports (distributions, correlations, missing values) on any DataFrame. It describes data; Validex audits data against domain-specific expectations with pass/fail findings. |
| **Cerberus** | None meaningful. | Validates Python dictionaries, not tabular data. |

### 2.5 Repository and metadata validation

| Tool | What it validates | Relationship to Validex |
|---|---|---|
| **MetaboLights validation (mtbls-validation)** | ISA-Tab metadata completeness for repository submission. Uses Open Policy Agent rules to check study metadata structure. | Validates metadata about experiments, not the content of result tables. Complementary but non-overlapping. |
| **ISA-Tab tools (ISAvalidator)** | ISA-Tab metadata file structure and compliance. | Validates experimental metadata schemas. Does not inspect result table content. |
| **mzQC format** | Standardized JSON format for MS run quality metrics. | A data exchange format for acquisition-level QC metrics, not a validation tool for result tables. |

### 2.6 Reporting standards and guidelines (not software)

| Standard | Relationship to Validex |
|---|---|
| **MSI reporting guidelines** (Sumner et al. 2007) | Foundational community checklist for minimum information in metabolomics studies. Covers experimental design, chemical analysis, data processing, and annotation confidence levels. Validex checks a narrow subset of table-level reporting completeness but does not implement or claim MSI compliance checking. |
| **QComics guidelines** (Broadhurst et al. 2024) | Recommendations for robust, implementable QC of metabolomics data. Human-readable guidelines, not software. |
| **mQACC consensus** (Metabolomics 2023 workshop) | Community-driven guidance document for QA/QC best practices in LC-MS untargeted metabolomics. Living document, not software. |

### 2.7 Instrument and acquisition QC tools

| Tool | What it monitors |
|---|---|
| **QC4Metabolomics** | Real-time and retrospective monitoring of LC-MS acquisition quality: m/z drift, retention time stability, contaminant levels. Web dashboard. Does not audit result tables. |
| **mzQuality** | QC monitoring and batch correction for targeted MS. Operates on peak areas, not result tables. |

---

## 3. Summary: does Validex address a gap?

**Yes.** The research identified no existing tool that performs automated, deterministic auditing of downstream metabolomics result tables for:

1. **Header alias detection and schema normalization** -- mapping diverse column naming conventions to canonical fields
2. **Probability-column validity checking** -- verifying that p-value and FDR columns contain parseable, in-range numeric values
3. **FDR-versus-p-value consistency** -- flagging cases where FDR values are smaller than corresponding p-values
4. **Ambiguity reporting** -- detecting headers that could map to multiple canonical fields
5. **Reporting completeness scoring** -- producing a structured assessment of whether a result table contains the fields needed for interpretability

The metabolomics software ecosystem is mature for upstream processing (XCMS, MZmine), instrument QC (QC4Metabolomics), statistical analysis (MetaboAnalyst), metadata validation (MetaboLights, ISA-Tab), and reporting guidelines (MSI). However, the specific step of auditing the CSV/TSV result tables that emerge from these workflows -- checking whether they are structurally complete, internally consistent, and interpretable -- is not addressed by any identified tool.

General tabular validation frameworks (Great Expectations, pandera, Frictionless) could theoretically be configured to perform similar checks, but they require users to write all domain-specific logic from scratch and provide no metabolomics-aware defaults.

The closest conceptual peer is statcheck (psychology), which audits statistical reporting in published articles, but it operates on prose text rather than structured tables and targets a different domain.

---

## 4. Limitations of this survey

- This survey was conducted via web search on 2026-07-24 and may not capture tools published after this date or tools not indexed by search engines.
- Commercial/proprietary tools with limited web presence may be underrepresented.
- The absence of a tool from search results does not guarantee it does not exist.
- Tool capabilities were assessed from documentation, publications, and repository descriptions, not from hands-on testing.
- Validex itself has not completed independent external validation; the gap identified here is a gap in available tooling, not a validated claim about Validex's effectiveness.
