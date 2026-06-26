# Candidate Note — PILOT_004

---

## 1. Dataset ID

PILOT_004

## 2. Source Title

A comprehensive analysis of metabolomics and transcriptomics in non-small cell lung cancer

## 3. DOI or URL

https://doi.org/10.1371/journal.pone.0232272

## 4. Access Date

2026-06-25

## 5. License or Reuse Note

CC BY 4.0 — PLOS ONE standard license. Redistribution would be permitted.

However, supplementary files are in DOCX format, which is unsuitable for Validex input without manual reformatting.

Licensing triage: `excluded_due_to_unsuitable_format`

## 6. Why This Table Is Eligible (Considered)

- Real published metabolomics study (PLOS ONE 2020, NSCLC cohort).
- CC BY 4.0 license.
- Post-analysis result tables with metabolite names, fold change, p-value, FDR present in S2 and S3 supplementary tables.
- Includes pathway analysis with Holm and FDR corrections.

## 7. Why This Table Might Be Excluded

EXCLUDED: Supplementary tables S2 and S3 are in DOCX format. Machine-readable CSV ingestion requires manual copy-paste extraction of table data from the Word document. This violates the protocol requirement that tables be "usable as CSV input without reformatting."

Note for future: if the authors publish a CSV version or the table is extracted by a reviewer, it could become a valid candidate.

## 8. Table Filename

NOT COMMITTED — excluded due to format

S2 Table (DOCX): https://doi.org/10.1371/journal.pone.0232272.s005
S3 Table (DOCX): https://doi.org/10.1371/journal.pone.0232272.s006

## 9. Header Row Notes

Not directly inspected (DOCX). Per the paper methods, S2 contains: metabolite names, fold change, p-value. S3 contains: pathway names, total compounds, hits, raw p-value, Holm-adjusted p-value, FDR, impact values.

## 10. Multi-Header or Merged-Cell Issues

DOCX table structure — unknown. DOCX tables frequently have merged header cells that break CSV extraction.

## 11. Manual Label Decisions

N/A — excluded.

## 12. Ambiguities

N/A — excluded.

## 13. Expected Findings

N/A — excluded.

## 14. Reviewer Initials

AT

## 15. Second Reviewer Check

N/A — excluded.

## 16. Final Inclusion Decision

no — excluded due to DOCX format. Supplementary tables require manual extraction before machine-readable CSV ingestion is possible. Recheck if a CSV version becomes available.
