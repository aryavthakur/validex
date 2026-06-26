# Candidate Note — PILOT_003

---

## 1. Dataset ID

PILOT_003

## 2. Source Title

Comprehensive evaluation of untargeted metabolomics data processing software in feature detection, quantification and discriminating marker selection

## 3. DOI or URL

https://doi.org/10.1016/j.aca.2018.05.001

MetaboLights study ID: MTBLS733
MetaboLights URL: https://www.ebi.ac.uk/metabolights/MTBLS733
FTP: ftp://ftp.ebi.ac.uk/pub/databases/metabolights/studies/public/MTBLS733/

## 4. Access Date

2026-06-25

## 5. License or Reuse Note

EMBL-EBI Terms of Use (https://www.ebi.ac.uk/about/terms-of-use/). The data files are freely downloadable from the EMBL-EBI FTP. Redistribution terms are not explicitly CC BY — EMBL-EBI data is available for research use but redistribution rights should be reviewed before committing to the repository.

The associated journal article (Analytica Chimica Acta) is not confirmed CC BY.

Licensing triage: `public_access_but_redistribution_unclear`

Do NOT commit the table file to the repository without confirming redistribution rights.

## 6. Why This Table Is Eligible

- Real published metabolomics benchmark study (Rafiei & Meier, Analytica Chimica Acta 2018, PMID 29907290).
- Freely downloadable from EMBL-EBI FTP/API.
- Post-analysis MAF TSV file containing fold changes and p-values.
- Distinct format: MetaboLights MAF format with ISA-Tab-style column naming.
- 35 confirmed columns including statistical result columns.
- Tests a real repository export format not covered by synthetic benchmark.

## 7. Why This Table Might Be Excluded

- Redistribution rights unclear (EMBL-EBI terms, not CC BY).
- "metabolite_identification" column will NOT be detected as compound_id (alias gap) — expected FN for compound_id field.
- No FDR/adjusted p-value column present — only raw p-value.
- This is a software benchmark study, not a biological case-control study — the "fold changes" are against known mixture concentration ratios, not biological groups. This is unusual for a result table but the statistical columns are present.
- Wide format with many sample columns (SA1-SA5, SB1-SB5) that Validex ignores.

## 8. Table Filename

NOT COMMITTED (redistribution rights unclear)

File: m_MTBLS733_mass_spectrometry_v2_maf.tsv (72 KB)
FTP path: ftp://ftp.ebi.ac.uk/pub/databases/metabolights/studies/public/MTBLS733/m_MTBLS733_mass_spectrometry_v2_maf.tsv

## 9. Header Row Notes

Confirmed column headers (fetched via MetaboLights API 2026-06-25):

All 35 columns in order:
database_identifier, chemical_formula, smiles, inchi, metabolite_identification, mass_to_charge, fragmentation, modifications, charge, retention_time, taxid, species, database, database_version, reliability, uri, search_engine, search_engine_score, smallmolecule_abundance_sub, smallmolecule_abundance_stdev_sub, smallmolecule_abundance_std_error_sub, Fold change, p-value, Compound concentration ratio, SA1, SA2, SA3, SA4, SA5, SB1, SB2, SB3, SB4, SB5

Single header row. TSV format.

## 10. Multi-Header or Merged-Cell Issues

None. Single header row. Standard TSV. Column names use mixed case ("Fold change", "p-value" with lowercase after the first word).

## 11. Manual Label Decisions

Header row inspected: yes, from previously fetched source metadata.

Local table filename: none. No local CSV/TSV is present in
`validation/pilot/tables/`.

Labeling deferred until the table is available locally and redistribution rights
are clarified. Based on confirmed headers:
- compound_id → "metabolite_identification" (reviewer ground truth; normalizes to "metabolite_identification" — NOT in Validex compound_id aliases — expected FN)
- effect_size → "Fold change" (normalizes to "fold_change" — IS in Validex effect_size aliases — DETECTED)
- p_value → "p-value" (normalizes to "p_value" — IS in Validex p_value aliases — DETECTED)
- fdr → absent (no FDR column — expected finding: missing_fdr)
- annotation → absent

Note: "Fold change" with capital F — normalize: "fold_change" — in aliases ✓
Note: "p-value" with hyphen — normalize: hyphen → underscore → "p_value" — in aliases ✓

## 12. Ambiguities

None. No duplicate alias matches among the 35 columns.

## 13. Expected Findings

missing_fdr

Provisional Validex behavior (current alias set):
- compound_id: NOT DETECTED ("metabolite_identification" not in aliases — FN)
- effect_size: DETECTED ("Fold change")
- p_value: DETECTED ("p-value")
- fdr: ABSENT → missing_fdr finding
- Expected score: 80/100 (−20 for missing fdr)
- Expected audit_confidence: medium

## 14. Reviewer Initials

AT

## 15. Second Reviewer Check

Not yet completed.

## 16. Final Inclusion Decision

pending — headers confirmed; redistribution rights must be clarified before
committing any table file. Labeling deferred until a local TSV/CSV is inspected.
