# Uploaded pilot table header inspection

This file records header inspection for the local pilot dry run. It is not an external validation result.

## Files inspected

1. PILOT_001_ST000915.csv
2. PILOT_002_ST002843.csv
3. PILOT_003_ST002334.csv
4. PILOT_004_ST000164_cleaned.csv

## Shared inspected headers

The four inspected ST result tables use the same core headers:

* Metabolite
* F value
* P-value
* FDR adjusted P-value
* Main class
* Sub class

## Label policy

* Metabolite is labeled as compound_id.
* F value is not labeled as effect_size because it is a test statistic, not a fold-change or effect-size field.
* P-value is labeled as p_value.
* FDR adjusted P-value is labeled as fdr.
* Main class and Sub class are labeled as ambiguous annotation candidates.
* No missing p-value or missing FDR finding is expected for these four pilot files.

## Claim boundary

This is a local pilot dry run only. It is not external validation and should not be described as validation evidence.

## Pilot alias follow-up

Targeted exact aliases were added after the local pilot dry run exposed schema
coverage gaps:

* `fdr_adjusted_p_value` maps to `fdr`.
* `main_class` maps to `annotation`.
* `sub_class` maps to `annotation`.

These aliases are scientifically defensible for these tables because
`FDR adjusted P-value` is an adjusted probability column, and `Main class` /
`Sub class` are metabolite classification fields that describe compound
annotation. The aliases are exact normalized aliases, not substring matches.

`F value` remains excluded from `effect_size` because it is a test statistic,
not a fold-change or effect-size field.

The pilot dry run no longer reports schema mismatches for these four local
tables after targeted alias updates. This remains a pilot-only workflow check,
not external validation.
