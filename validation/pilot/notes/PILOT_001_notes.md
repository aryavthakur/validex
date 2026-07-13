# Candidate Note — PILOT_001

---

## 1. Dataset ID

PILOT_001

## 2. Source Title

Metabolomic profiling of rare cell populations isolated by flow cytometry from tissues

## 3. DOI or URL

https://doi.org/10.7554/eLife.61980

## 4. Access Date

2026-06-25

## 5. License or Reuse Note

CC BY 4.0 — eLife standard license. Redistribution confirmed as permitted under Creative Commons Attribution 4.0 International. Attribution required.

Licensing triage: `redistributable_confirmed`

Do not commit the XLSX table file in this stage. Redistribution is confirmed for future stages if needed.

## 6. Why This Table Is Eligible

- Real published metabolomics study (eLife 2021).
- Legally accessible and redistributable under CC BY 4.0.
- Post-analysis result table: differential metabolites from flow-sorted cell populations.
- Contains metabolite identifiers, fold change, and FDR — confirmed post-statistical output.
- XLSX format convertible to CSV.
- Distinct format variant: FC column name includes comparison label in parentheses — novel to synthetic benchmark.

## 7. Why This Table Might Be Excluded

- XLSX has multiple sheets, each a different pairwise comparison. A single sheet must be selected.
- FC column name "FC (1x PBS / 0.5x PBS)" includes a contextual label preventing Validex effect_size detection (alias gap, not file quality problem).
- No raw p-value column — FDR only. Validex will flag missing_p_value.
- If sheet selection is ambiguous the table may be excluded as requiring excessive manual preparation.

## 8. Table Filename

NOT COMMITTED (redistribution confirmed but file not committed in this stage)

Supplementary data URL pattern:
https://cdn.elifesciences.org/articles/61980/elife-61980-fig1-data2-v2.xlsx

Data2 through data8 are separate pairwise comparison tables.

## 9. Header Row Notes

The tracked 2026-06-25 triage note records these headers as fetched from
elife-61980-fig1-data2-v2.xlsx, primary comparison sheet:

- Metabolite
- FC (1x PBS / 0.5x PBS)
- FDR

Single header row. Three columns only.

## 10. Multi-Header or Merged-Cell Issues

None observed. Single header row. Sheet name encodes the comparison context.

## 11. Manual Label Decisions

The tracked triage note records direct header inspection from fetched source
metadata. The source workbook itself is not tracked.

No local file is provenance-linked to this eLife candidate. An ignored
ST000915-named CSV may exist in a developer workspace, but the tracked
repository does not establish that it is the source described above.

Labeling deferred — a specific XLSX sheet must be selected and saved as CSV
locally before `labels.pilot.csv` can include this candidate.

Tentative label decisions based on confirmed headers:
- compound_id → "Metabolite" (normalizes to "metabolite" which is in compound_id aliases)
- effect_size → "FC (1x PBS / 0.5x PBS)" (reviewer ground truth; normalizes to "fc_1x_pbs_0_5x_pbs" which is NOT in Validex effect_size aliases — expected FN for this field)
- p_value → absent
- fdr → "FDR" (normalizes to "fdr" which is in fdr aliases)
- annotation → absent

## 12. Ambiguities

None. Only three columns; no overlap across canonical field aliases.

## 13. Expected Findings

missing_p_value

Provisional Validex behavior (current alias set):
- compound_id: DETECTED
- effect_size: NOT DETECTED (alias gap)
- fdr: DETECTED
- Expected score: 60/100
- Expected audit_confidence: low

## 14. Reviewer Initials

AT

## 15. Second Reviewer Check

Not yet completed. Two-reviewer agreement required before formal external validation.

## 16. Final Inclusion Decision

pending — headers confirmed; labeling deferred until a single-sheet local CSV is
prepared and inspected.

## 17. Evidence and Current Status

Expected finding before validation:
`missing_p_value`, with a likely effect-size alias gap, was the tentative
prediction for the eLife candidate described above.

Observed local finding:
A prior local labels row recorded a separate file named
`PILOT_001_ST000915.csv`, the shared ST header mapping documented in
`uploaded_table_header_inspection.md`, and `ambiguous_schema_field`. The tracked
repository does not establish that ST000915 is the eLife candidate identified
in Sections 2–3.

Reproducibility:
The ST source table is local-only and untracked. The recorded mapping is a
historical manual observation, not evidence that the current code produces the
same output, and its identity/provenance linkage to PILOT_001 cannot be verified
from the tracked repository.

Current evidence status: locally_inspected
