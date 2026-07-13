# Candidate Note — PILOT_005

---

## 1. Dataset ID

PILOT_005

## 2. Source Title

Widely targeted metabolomics reveals differences in metabolites of Paeonia lactiflora cultivars

## 3. DOI or URL

https://doi.org/10.1371/journal.pone.0298194

## 4. Access Date

2026-06-25

## 5. License or Reuse Note

CC BY 4.0 — PLOS ONE standard license. Redistribution confirmed as permitted.

Licensing triage: `redistributable_confirmed`

Do not commit the XLSX file in this stage.

## 6. Why This Table Is Eligible (Tentative)

- Real published metabolomics study (PLOS ONE 2024, plant metabolomics).
- CC BY 4.0 — legally accessible and redistributable.
- Widely-targeted metabolomics platform (MRM-based) — distinct from LC-MS/XCMS/MetaboAnalyst studies, adds platform diversity.
- S1 Data and S2 Data described in methods as containing differential metabolite results with VIP ≥ 1 and fold change ≥ 2 or ≤ 0.5 filtering.
- Plant context is distinct from mammalian studies — tests domain breadth.

## 7. Why This Table Might Be Excluded

- S1 Data and S2 Data column headers have NOT yet been directly confirmed. S3 Data was confirmed as quantification (not results). If S1 and S2 don't contain fold change and p-value columns in their headers, the table may be excluded.
- Widely-targeted metabolomics (MRM) uses VIP score from OPLS-DA rather than t-test p-values in some workflows — if no p-value column is present, expected findings would change.
- RAR archive (S2 File) contains files that may require extraction.

## 8. Table Filename

NOT COMMITTED (redistribution confirmed but file not committed in this stage)

S1 Data: https://doi.org/10.1371/journal.pone.0298194.s001
S2 Data: https://doi.org/10.1371/journal.pone.0298194.s002

## 9. Header Row Notes

NOT YET CONFIRMED. S3 Data confirmed columns (quantification, not results):
Index, Formula, Compounds, Class I, Class II, CAS, cpd_ID, kegg_map, CK1, CK2, CK3, DFG1, DFG2, DFG3, HSML1, HSML2, HSML3

S1 Data and S2 Data headers to be confirmed by direct file inspection.

## 10. Multi-Header or Merged-Cell Issues

Unknown. XLSX format — possible merged cells in comparison result tables from widely-targeted platforms.

## 11. Manual Label Decisions

DEFERRED — S1 Data and S2 Data headers not yet confirmed.

Tentative if result table uses standard fold change and VIP:
- compound_id: likely "Compound" or "Metabolite" (if present)
- effect_size: likely "FC" or "Fold Change" (if present)
- p_value: may be absent if only VIP score is used (OPLS-DA approach)
- fdr: may be absent
- annotation: possibly "Class I" or "Class II"

## 12. Ambiguities

Unknown until headers are confirmed.

## 13. Expected Findings

DEFERRED — cannot determine expected findings without confirmed headers.

Possible: missing_p_value|missing_fdr if the table uses VIP and fold change only without t-test p-values.

## 14. Reviewer Initials

AT

## 15. Second Reviewer Check

Not yet completed.

## 16. Final Inclusion Decision

pending — S1 Data and S2 Data column headers must be directly confirmed before labeling or inclusion decision.

## 17. Evidence and Current Status

Expected finding before validation:
Deferred. `missing_p_value|missing_fdr` is only a tentative possibility if the
result table contains VIP and fold change without probability columns.

Observed local finding:
None recorded. No local label row or inspected result-table header is preserved
for this candidate.

Reproducibility:
The tracked repository contains candidate metadata only. A local source table
must be obtained and directly inspected before labels or Validex findings can be
evaluated.

Current evidence status: pending
