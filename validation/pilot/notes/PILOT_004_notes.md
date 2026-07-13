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

Licensing triage: `redistributable_confirmed`

## 6. Why This Table Is Eligible (Considered)

- Real published metabolomics study (PLOS ONE 2020, NSCLC cohort).
- CC BY 4.0 license.
- Post-analysis result tables with metabolite names, fold change, p-value, FDR present in S2 and S3 supplementary tables.
- Includes pathway analysis with Holm and FDR corrections.

## 7. Why This Table Might Be Excluded

Supplementary tables S2 and S3 are in DOCX format. Validex cannot ingest them
directly, and converting them to machine-readable CSV requires a documented
preparation step. The candidate remains excluded under the current protocol;
reconsider it only if the authors publish a machine-readable version or a
reviewer documents and verifies an eligible conversion.

## 8. Table Filename

NOT COMMITTED — public supplementary tables are DOCX

S2 Table (DOCX): https://doi.org/10.1371/journal.pone.0232272.s005
S3 Table (DOCX): https://doi.org/10.1371/journal.pone.0232272.s006

## 9. Header Row Notes

Not directly inspected (DOCX). Per the paper methods, S2 contains: metabolite names, fold change, p-value. S3 contains: pathway names, total compounds, hits, raw p-value, Holm-adjusted p-value, FDR, impact values.

## 10. Multi-Header or Merged-Cell Issues

DOCX table structure — unknown. DOCX tables frequently have merged header cells that break CSV extraction.

## 11. Manual Label Decisions

Deferred. The original DOCX tables have not been directly inspected in the
tracked repository.

## 12. Ambiguities

The tracked repository cannot verify how DOCX headers or merged cells should be
converted to CSV fields.

## 13. Expected Findings

Not established. The original DOCX table structure and resulting CSV headers
must be inspected before predicting Validex findings.

## 14. Reviewer Initials

AT

## 15. Second Reviewer Check

Not yet completed.

## 16. Final Inclusion Decision

no — excluded because the original candidate is distributed as DOCX and no
verified, documented conversion is attributable to it.

## 17. Evidence and Current Status

Expected finding before validation:
No finding prediction was established because the original DOCX tables were not
directly inspected.

Observed local finding:
A prior local record names `PILOT_004_ST000164_cleaned.csv`, states that a blank
first row was removed, and records the shared ST header mapping and
`ambiguous_schema_field` documented in `uploaded_table_header_inspection.md`.
The record does not include the source table, a conversion recipe, or evidence
connecting ST000164 to the DOCX candidate in Sections 2–3. It is therefore an
unverified local action, not a verified conversion of either DOCX supplement.

Reproducibility:
The local CSV and original working files are untracked. Neither the cleanup nor
the code output can be reproduced from the tracked repository. The
identity/provenance linkage to PILOT_004 cannot be verified from the tracked
repository, and the recorded mapping is not evidence that the current code
produces the same output.

Current evidence status: excluded
