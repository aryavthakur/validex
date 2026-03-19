export const DEMO_RESULTS = {
  overview: {
    filename: "HILIC_POS_results_example.csv",
    n_rows: 847,
    n_cols: 9,
    missing_cells: 12,
  },
  schema: {
    canonical_to_original: {
      feature: "Metabolite_ID",
      p_value: "P_Value_ttest",
      fdr: "adj.p.BH",
      fold_change: "FC_group1_vs_group2",
      log2fc: "log2FC",
    },
    missing: [],
    ambiguities: { fold_change: ["FC_group1_vs_group2", "FC_ratio"] },
  },
  report_md: `# Metabolomics Validity Report

## Dataset Overview
- Number of rows (features): 847
- Number of columns: 9

## Detected Statistical Columns (schema-mapped)
- Fold change: FC_group1_vs_group2
- p-value: P_Value_ttest
- FDR / q-value: adj.p.BH

## Schema Ambiguities
- **fold_change** matched multiple columns: FC_group1_vs_group2, FC_ratio

## Scientific Interpretation
- Both p-values and FDR/q-values were detected, indicating statistically interpretable results with multiple-testing control.
- Schema ambiguity was detected in the fold_change field — two columns matched equally. Validex selected the first candidate, but manual verification is recommended.
- The study context indicates untargeted metabolomics with an exploratory goal, which is consistent with the breadth of features detected.

## Recommendations
- Rename ambiguous columns to remove the fold_change conflict — keep only one FC column in the export.
- Consider adding a feature annotation column (e.g. compound name or HMDB ID) for improved auditability.

## Overall Confidence Score
**72 / 100**

## Flags
- **MED** — Schema ambiguity: Two columns matched fold_change with equal confidence.  
  _Fix_: Rename or remove FC_ratio to eliminate ambiguity.
- **LOW** — Missing feature annotation: No compound name or identifier column detected.  
  _Fix_: Include a metabolite name or HMDB ID column in your export.
`,
  report_json: {
    analysis: {
      confidence: 72,
      flags: [
        {
          severity: "med",
          title: "Schema ambiguity",
          why: "Two columns matched fold_change with equal confidence: FC_group1_vs_group2 and FC_ratio.",
          fix: "Rename or remove FC_ratio to eliminate ambiguity.",
        },
        {
          severity: "low",
          title: "Missing feature annotation",
          why: "No compound name or HMDB ID column was detected.",
          fix: "Include a metabolite name or identifier column in your export.",
        },
      ],
      interpretations: [
        "Both p-values and FDR/q-values were detected, indicating statistically interpretable results with multiple-testing control.",
        "Schema ambiguity was detected in the fold_change field — two columns matched equally. Validex selected the first candidate, but manual verification is recommended.",
        "The study context indicates untargeted metabolomics with an exploratory goal, consistent with the breadth of features detected.",
      ],
      recommendations: [
        "Rename ambiguous columns to remove the fold_change conflict — keep only one FC column in the export.",
        "Consider adding a feature annotation column (e.g. compound name or HMDB ID) for improved auditability.",
      ],
    },
  },
  histogram: {
    column: "log2FC",
    counts: [2, 5, 9, 14, 22, 38, 54, 72, 89, 101, 95, 87, 74, 58, 41, 28, 17, 11, 6, 3, 2, 4, 8, 14, 21, 32, 28, 19, 11, 5],
    bin_edges: [-4.0,-3.73,-3.47,-3.20,-2.93,-2.67,-2.40,-2.13,-1.87,-1.60,-1.33,-1.07,-0.80,-0.53,-0.27,0.0,0.27,0.53,0.80,1.07,1.33,1.60,1.87,2.13,2.40,2.67,2.93,3.20,3.47,3.73,4.0],
  },
  preview: {
    columns: ["Metabolite_ID", "P_Value_ttest", "adj.p.BH", "FC_group1_vs_group2", "log2FC", "FC_ratio", "mean_ctrl", "mean_disease", "annotation"],
    rows: [
      ["HMDB0000148", "0.0002", "0.0041", "2.14", "1.10", "2.14", "1.22", "2.61", "L-Glutamic acid"],
      ["HMDB0000162", "0.0011", "0.0098", "1.87", "0.90", "1.87", "0.88", "1.65", "L-Proline"],
      ["HMDB0000517", "0.0034", "0.0201", "0.61", "-0.71", "0.61", "3.41", "2.08", "Choline"],
      ["HMDB0000159", "0.0051", "0.0287", "1.55", "0.63", "1.55", "1.10", "1.71", "L-Phenylalanine"],
      ["HMDB0000042", "0.0089", "0.0412", "0.48", "-1.06", "0.48", "2.87", "1.38", "Arachidonic acid"],
      ["HMDB0000292", "0.0134", "0.0531", "2.31", "1.21", "2.31", "0.74", "1.71", "Succinic acid"],
      ["HMDB0000696", "0.0201", "0.0714", "1.29", "0.37", "1.29", "1.55", "2.00", "L-Methionine"],
      ["HMDB0001311", "0.0388", "0.1192", "0.72", "-0.47", "0.72", "2.11", "1.52", "Carnitine"],
    ],
  },
};
