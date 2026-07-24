# Benchmark Reference Correction Note

## Summary

This note documents a benchmark-reference defect identified through post hoc adjudication of the Validex 0.2.0 frozen held-out evaluation. The defect affected 13 of 160 held-out cases. No product defect was identified. The frozen primary metric of 147/160 exact-table agreement is preserved without recalculation.

## Affected Benchmark Family

`invalid_probability_cells`

## Affected Case IDs

SYNV2_0045, SYNV2_0057, SYNV2_0069, SYNV2_0081, SYNV2_0093, SYNV2_0105, SYNV2_0117, SYNV2_0129, SYNV2_0141, SYNV2_0153, SYNV2_0165, SYNV2_0177, SYNV2_0189

## Number of Cases Affected

13 of 160 held-out cases (8.1%).

## Original Expected Behavior

The benchmark ground truth (`expected_columns`) specified the structurally identified column names `p_value` and `fdr` as the expected values for `detected.p_value` and `detected.fdr`, respectively. The benchmark generator did not modify `expected_columns` for the `invalid_probability_cells` family despite these cases containing injected invalid cell values.

## Actual Product Behavior

The product correctly:
1. Identified the `p_value` and `fdr` columns structurally (recorded in `ambiguity.selected_column`).
2. Validated cell values and found valid fractions below the 80% threshold.
3. Set `detected.p_value` and `detected.fdr` to null per its usability gate.
4. Emitted high-severity "Invalid p-value column" and "Invalid FDR column" findings.
5. Set audit confidence to "low" and minimum auditability to false.

This behavior is explicitly tested by `test_invalid_p_value_rejected` and `test_invalid_fdr_rejected` in the product test suite.

## Prospective Product Contract

The product specification (01_CURRENT_VALIDEX_TECHNICAL_SPECIFICATION.md, line 215) states:

> "If a detected p/FDR column is below 80% valid, the recognized header remains in raw schema metadata but the active detected field becomes `None`."

This specification was written before the benchmark was generated. The product's two-phase design — structural detection in `ambiguity` records, usability-gated values in `detected` — is a documented, prospective design decision.

## Benchmark Generator Defect

The benchmark generator (`generate_benchmark_v2.py`, lines 148–149) handles the `invalid_probability_cells` family by setting `invalid = True` but does not modify `expected_columns`. The default `expected_columns` retains structural column names. The generator therefore expected the structurally identified column names in a field that the product defines as usability-gated.

The analysis script (`analyze_validex_0_2_results.py`) compares `detected` (usability-gated) against `expected_columns` (structural), producing false negatives for all 13 cases.

## Why the Primary Metric Remains Unchanged

The frozen primary result of **147/160** exact-table agreement was computed once from frozen outputs and is preserved as the historical prospective evaluation result. The adjudication is a post hoc interpretive correction explaining the source of the 13 disagreements. It does not recalculate, replace, or reinterpret the prospective metric as 160/160.

## Implications for Interpretation

- The 13 false negatives in p-value F1 (0.958) and FDR F1 (0.954) are attributable to the benchmark-reference defect, not to product failure.
- Structural field recognition succeeded in all 160 held-out cases.
- The product's user-facing audit output (low confidence, explicit invalidity warnings, preserved structural selection) is correct and user-protective in these cases.
- The disagreement affected only the benchmark comparison metric, not the user-facing audit interpretation.

## Corrective Action for Future Benchmark Versions

Future benchmark versions should set `expected_columns.p_value = ""` and `expected_columns.fdr = ""` (empty/null) for the `invalid_probability_cells` family, matching the product's documented usability-gate contract. This correction applies only to future benchmark generations and does not alter any frozen artifact.

## Confirmations

- **Frozen artifacts were not edited.** All original synthesis artifacts, benchmark inputs, expected outputs, actual outputs, and analysis results remain at their frozen hashes.
- **No product defect was identified.** Product behavior is consistent with its prospective specification, test suite, and user-facing messages.
- **No substantive audit difference occurred.** The user-facing audit interpretation is identical regardless of the `detected` serialization for these cases.
- **Both locked product worktrees remained clean** throughout the adjudication.
