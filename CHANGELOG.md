# Changelog

All notable changes to Validex will be documented in this file.

## [0.2.0] - 2026-07-24

### Added
- CSV, TSV, and XLSX ingestion with explicit sheet selection
- Governed alias registry for metabolomics field recognition
- Structured candidate and ambiguity handling
- Probability-field usability gating (80% valid-fraction threshold)
- FDR comparable-row consistency checking
- Audit confidence labels (high/medium/low)
- Output provenance tracking
- Local web interface
- Optional local AI analysis (Ollama)
- 350 automated tests

### Changed
- Redesigned from 0.1.0 based on diagnostic benchmark findings
- Replaced overly strict aliases with governed registry
- Improved annotation detection to eliminate false negatives

### Fixed
- CSV-only ingestion limitation
- Ambiguity-contract mismatches
- Audit-expectation defects

## [0.1.0] - Initial Release

- CSV-focused audit tool
- Diagnostic benchmark: 30/100 exact-table agreement
