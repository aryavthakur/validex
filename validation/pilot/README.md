# Validex Pilot Validation Workspace

**This pilot directory is for testing the external validation workflow on a small number of real candidate tables. A pilot run is not sufficient to claim external validation.**

---

## 1. Purpose of Pilot Validation

This workspace exists to:
- Test that the external validation runner (`validation/run_external_validation.py`) works correctly end-to-end.
- Practice the registry and labeling workflow before running a full external validation study.
- Identify gaps in Validex alias coverage on a small sample of real tables.
- Accumulate candidate metadata and labeling notes for future formal external validation.

A pilot run produces provisional, exploratory data about Validex behavior. It is a workflow test, not an external validation study.

---

## 2. Difference Between a Pilot Run and Completed External Validation

| Attribute | Pilot Run | Completed External Validation |
|-----------|-----------|-------------------------------|
| Number of tables | Up to 5 | ≥30 (recommended) |
| Reviewer count | 1 (minimum) | 2 per table, with resolved disagreements |
| Sampling strategy | Opportunistic | Systematic, documented |
| Results status | Provisional / exploratory | Reportable with protocol reference |
| Claims allowed | None — workflow test only | Specific, scoped, with N and protocol |
| Committed to repo | Templates + notes only | Full labeled dataset + results JSON |

---

## 3. How to Select Candidate Tables

A candidate table must meet all eligibility criteria in `docs/external_validation_protocol.md` Section 3:

1. Real published metabolomics study or official repository record.
2. Legally accessible for review.
3. Post-analysis result table (not raw instrument data).
4. At least 2 data rows and 3 columns.
5. License permits local storage (and redistribution if committing to repo).

For the pilot, prefer:
- Open-access supplementary tables with a Creative Commons license.
- Tables from MetaboLights or Metabolomics Workbench with CC BY or similar terms.
- Tables covering a range of platforms (MetaboAnalyst, XCMS, MS-DIAL, MZmine) and formats.

---

## 4. How to Record Candidates in the Registry

Copy `registry.pilot.template.csv` to `registry.pilot.csv` (do not overwrite the template).

Fill in one row per candidate:
- `dataset_id`: use `PILOT_001`, `PILOT_002`, etc.
- `source_url_or_doi`: the DOI or direct URL to the source.
- `license_or_access_note`: be specific — e.g. "CC BY 4.0" or "Open access, no redistribution license stated."
- `table_filename`: filename of the CSV in `validation/pilot/tables/`. Leave blank if you cannot redistribute.
- `included`: `yes` if eligible, `no` if excluded.
- `exclusion_reason`: required if `included = no`.

---

## 5. How to Manually Label Fields

Do not create `labels.pilot.csv` until at least one candidate has a local table
file in `validation/pilot/tables/` and the header row has been directly
inspected from that local file.

Use the local intake helper for CSV/TSV files:

```bash
python validation/pilot/inspect_table_headers.py validation/pilot/tables/PILOT_003.tsv
```

For XLSX files, first check whether the local environment has Excel support:

```bash
python validation/pilot/inspect_table_headers.py validation/pilot/tables/PILOT_001.xlsx
```

If `openpyxl` is not available, manually convert the selected sheet to CSV
outside the repository and place the CSV under `validation/pilot/tables/`. Do
not add new dependencies only for pilot intake. If Excel support is available,
convert a selected sheet explicitly:

```bash
python validation/pilot/inspect_table_headers.py \
    validation/pilot/tables/PILOT_001.xlsx \
    --sheet Sheet1 \
    --output validation/pilot/tables/PILOT_001.csv
```

The helper refuses to overwrite converted output unless `--force` is passed.

Once at least one local table is inspected, copy `labels.pilot.template.csv` to
`labels.pilot.csv` (do not overwrite the template).

For each included table, fill in one row:
- Each canonical field column (`compound_id`, `effect_size`, `p_value`, `fdr`, `annotation`): enter the exact original column name, leave blank if absent, or `AMBIGUOUS:col1|col2` if multiple columns match.
- `expected_findings`: pipe-separated list of finding codes (e.g. `missing_p_value|missing_fdr`).
- `reviewer_id`: your identifier.
- Include only candidates with directly inspected local table files. Do not add
  rows based only on metadata notes.

See `docs/external_validation_protocol.md` Section 6 for full labeling instructions.

---

## 6. How to Run the Validation Runner

Once tables (in `validation/pilot/tables/`) and label files are ready:

```bash
python validation/run_external_validation.py \
    --registry validation/pilot/registry.pilot.csv \
    --labels   validation/pilot/labels.pilot.csv \
    --tables-dir validation/pilot/tables \
    --output   validation/pilot/results/pilot_results.json
```

The output JSON will be written to `validation/pilot/results/`. Generated
results are git-ignored by default and are local dry-run outputs only. Commit
results only if they are part of a formal external validation study.

---

## 7. What Can and Cannot Be Claimed from a Pilot Run

### Can be claimed (internally, not in published descriptions)
- "The external validation runner executed without errors on N candidate tables."
- "Validex detected [or failed to detect] the following fields in the pilot tables."
- "The following alias gaps were identified: [list]."

### Cannot be claimed
- "Validex has been externally validated."
- "Validex achieves X% precision on real-world tables."
- Any performance claim based solely on pilot data.

See `docs/external_validation_protocol.md` Section 12 for evidence-level language rules.

---

## 8. Licensing and Redistribution Warning

**Do not commit supplementary tables unless the license clearly permits redistribution. If licensing is unclear, record the source metadata in the registry and keep the file outside the repository.**

- `validation/pilot/tables/*.csv` is git-ignored by default. Remove an entry from `.gitignore` only after confirming the license.
- If a table cannot be committed, note in the registry that it must be downloaded separately.
- Never commit patient-identifiable data or raw instrument files.

---

## 9. Reviewer Checklist

Before marking a pilot candidate as `included = yes`:

- [ ] I have read the full eligibility criteria in `docs/external_validation_protocol.md` Section 3.
- [ ] I have confirmed the table is a post-analysis result table, not raw data.
- [ ] I have confirmed the license permits local review.
- [ ] I have recorded the license or access note in the registry.
- [ ] I have created a candidate note file using `create_candidate_note.py`.
- [ ] If committing the table CSV, I have confirmed redistribution is permitted.
- [ ] I have completed a label row in `labels.pilot.csv`.
- [ ] I have run the validation runner and reviewed the output in `validation/pilot/results/`.
- [ ] I have not used pilot results to make external validation claims.

---

## 10. Candidate Sourcing Status

Candidate metadata may be stored in `registry.pilot.csv`. Table files are not committed unless redistribution is clearly permitted. Labels are only filled after direct header inspection. Pilot candidate metadata is not external validation evidence.

Current status (as of 2026-06-25):

| ID | Source | License Triage | Headers Confirmed | Labeling Status | Inclusion |
|----|--------|---------------|-------------------|-----------------|-----------|
| PILOT_001 | eLife 61980 — flow cytometry metabolomics | redistributable_confirmed (CC BY 4.0) | Yes (Metabolite, FC (...), FDR) | Deferred — XLSX sheet selection needed | pending |
| PILOT_002 | PLOS ONE 0240764 — weight loss metabolomics | redistributable_confirmed (CC BY 4.0) | Yes (Metabolite, Beta_Random, Pvalue_Random, Pvalue_Adj_Random) | Deferred — XLSX conversion needed | pending |
| PILOT_003 | MTBLS733 (MetaboLights) — software benchmark | public_access_but_redistribution_unclear | Yes (metabolite_identification, Fold change, p-value — no FDR) | Deferred — redistribution rights to confirm | pending |
| PILOT_004 | PLOS ONE 0232272 — NSCLC metabolomics | redistributable_confirmed (CC BY 4.0) | No — DOCX format | N/A | excluded (DOCX format) |
| PILOT_005 | PLOS ONE 0298194 — Paeonia lactiflora | redistributable_confirmed (CC BY 4.0) | Partial (S3 only — quantification, not results) | Deferred — S1/S2 headers to confirm | pending |

See `notes/PILOT_NNN_notes.md` for full details on each candidate.

**No table files are committed.** The `validation/pilot/tables/` directory is git-ignored for CSV files.

**No labels have been committed.** `labels.pilot.csv` has not been created — no
local pilot table files are currently present. Labeling is deferred until each
candidate table is available locally, converted to CSV if needed, and directly
inspected.

**No external validation is claimed.** This metadata is exploratory. A pilot run using these candidates would be a workflow test, not an external validation result.
