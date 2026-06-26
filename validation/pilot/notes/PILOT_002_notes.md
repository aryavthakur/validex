# Candidate Note — PILOT_002

---

## 1. Dataset ID

PILOT_002

## 2. Source Title

Metabolomic profiling identifies complex lipid species and amino acid analogues associated with response to weight loss interventions

## 3. DOI or URL

https://doi.org/10.1371/journal.pone.0240764

## 4. Access Date

2026-06-25

## 5. License or Reuse Note

CC BY 4.0 — PLOS ONE standard license. Redistribution confirmed as permitted under Creative Commons Attribution 4.0 International.

Licensing triage: `redistributable_confirmed`

Do not commit the XLSX file in this stage.

## 6. Why This Table Is Eligible

- Real published metabolomics study (PLOS ONE 2020).
- CC BY 4.0 — legally accessible and redistributable.
- Post-analysis result table: mixed-effects regression outputs from a dietary intervention cohort.
- Contains metabolite identifiers (Metabolite), effect sizes (Beta_Random), p-values (Pvalue_Random), adjusted p-values (Pvalue_Adj_Random), HMDB IDs, and lipid class annotations.
- XLSX format convertible to CSV.
- Non-standard column naming convention for p-value and FDR — valuable test of alias coverage gaps.

## 7. Why This Table Might Be Excluded

- Non-standard column names (Pvalue_Random, Pvalue_Adj_Random, Beta_Random) will not be detected by current Validex aliases — this reflects a genuine alias gap, not a file quality issue.
- Effect size is reported as beta coefficient / percent change, not as a traditional log fold change or fold change ratio.
- If too many critical aliases fail, the table tests Validex limitations rather than correct behavior.

## 8. Table Filename

NOT COMMITTED (redistribution confirmed but file not committed in this stage)

S1 Table at: https://doi.org/10.1371/journal.pone.0240764.s001

## 9. Header Row Notes

Confirmed column headers (fetched from S1 Table XLSX):

- Metabolite
- Beta_Random
- Pvalue_Random
- Pvalue_Adj_Random
- HMDB.ID
- super_class
- class
- sub_class
- CV
- missingness

Single header row.

## 10. Multi-Header or Merged-Cell Issues

None observed. Single header row.

## 11. Manual Label Decisions

Header row inspected: yes, from previously fetched source metadata.

Local table filename: none. No local CSV/TSV/XLSX is present in
`validation/pilot/tables/`.

Labeling deferred — XLSX must be available locally and converted to CSV before
formal labeling.

Tentative label decisions based on confirmed headers:
- compound_id → "Metabolite" (normalizes to "metabolite" — in compound_id aliases)
- effect_size → "Beta_Random" (reviewer ground truth; normalizes to "beta_random" — NOT in Validex effect_size aliases — expected FN)
- p_value → "Pvalue_Random" (reviewer ground truth; normalizes to "pvalue_random" — NOT in Validex p_value aliases which has "pvalue" but not "pvalue_random" — expected FN)
- fdr → "Pvalue_Adj_Random" (reviewer ground truth; normalizes to "pvalue_adj_random" — NOT in Validex fdr aliases — expected FN)
- annotation → "super_class" or "class" — neither in annotation aliases; labeled absent

## 12. Ambiguities

Open decision: Should Validex support suffix-qualified statistical columns?

`Pvalue_Random` and `Pvalue_Adj_Random` are semantically plausible p-value and
adjusted p-value fields, but they are suffix-qualified by the model/output
context and are not currently in the Validex alias policy. This candidate is
therefore deferred rather than labeled in `labels.pilot.csv`.

If Validex should support suffix-qualified statistical columns, this is a schema
alias limitation rather than a missing-field table. If Validex should not support
them, the expected findings can remain `missing_p_value|missing_fdr` after local
CSV inspection documents the decision.

## 13. Expected Findings

DEFERRED — likely `missing_p_value|missing_fdr` only if suffix-qualified
statistics remain intentionally unsupported.

Provisional Validex behavior (current alias set):
- compound_id: DETECTED ("Metabolite")
- effect_size: NOT DETECTED (alias gap: "Beta_Random")
- p_value: NOT DETECTED (alias gap: "Pvalue_Random") → missing_p_value finding
- fdr: NOT DETECTED (alias gap: "Pvalue_Adj_Random") → missing_fdr finding
- Expected score: 40/100
- Expected audit_confidence: low

This is a valuable test case for identifying the alias gap for non-standard statistical output column names from mixed-effects regression tools.

## 14. Reviewer Initials

AT

## 15. Second Reviewer Check

Not yet completed.

## 16. Final Inclusion Decision

pending — headers confirmed; labeling deferred until CSV prepared and the
suffix-qualified p-value policy is explicitly resolved.

## 17. Local Pilot Dry Run Decision

Header row inspected: yes

Local table filename: PILOT_002_ST002843.csv

Exact inspected headers: Metabolite, F value, P-value, FDR adjusted P-value, Main class, Sub class

Manual label decisions:
- compound_id = Metabolite
- effect_size = empty
- p_value = P-value
- fdr = FDR adjusted P-value
- annotation = AMBIGUOUS:Main class|Sub class

Expected findings: empty

Ambiguities: annotation has Main class and Sub class

Final inclusion decision: included for pilot dry run only
