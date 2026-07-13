# Historical local pilot table header inspection

This note preserves non-sensitive mapping observations previously recorded from
a local pilot inspection. The source tables are local-only and untracked, so the
observations cannot be independently reproduced from the public repository and
must not be treated as evidence of current Validex output.

## Files previously recorded

1. `PILOT_001_ST000915.csv`
2. `PILOT_002_ST002843.csv`
3. `PILOT_003_ST002334.csv`
4. `PILOT_004_ST000164_cleaned.csv`

The tracked repository does not establish the identity or provenance linkage
between these ST filenames and the original publication candidates documented
in `PILOT_001_notes.md` through `PILOT_004_notes.md`.

For `PILOT_004_ST000164_cleaned.csv`, a prior record says that a blank first row
was removed. No source file, conversion recipe, or evidence connecting that CSV
to PILOT_004's DOCX supplementary tables is tracked. The cleanup is therefore an
unverified local action, not a verified DOCX-to-CSV conversion.

## Previously recorded headers

The historical record gave the same headers for all four ST files:

* `Metabolite`
* `F value`
* `P-value`
* `FDR adjusted P-value`
* `Main class`
* `Sub class`

Because the source files are untracked and absent from a clean clone, this list
records a prior manual observation rather than a header inspection reproducible
from the repository. Ignored local copies do not establish provenance.

## Previously recorded label mapping

The populated local label rows recorded:

* `Metabolite` as `compound_id`.
* A blank `effect_size`, because `F value` was treated as a test statistic rather
  than a fold-change or effect-size field.
* `P-value` as `p_value`.
* `FDR adjusted P-value` as `fdr`.
* `AMBIGUOUS:Main class|Sub class` as the serialized `annotation` mapping.
* `ambiguous_schema_field` as the expected finding for the ambiguous annotation
  mapping.

These are historical reviewer decisions. They do not prove that the current
schema mapper selects the same fields or that a current audit produces the same
finding.

## Alias follow-up

The pilot work recorded exact normalized aliases for `fdr_adjusted_p_value`,
`main_class`, and `sub_class`. The rationale was that the first names an adjusted
probability column and the latter two name compound-classification fields.
`F value` remained excluded from `effect_size` because it is a test statistic.
Current alias behavior is covered by the schema-mapper tests; this historical
note is not a substitute for those reproducible fixtures.
