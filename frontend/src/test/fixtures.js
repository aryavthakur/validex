export const liveAuditResponse = {
  score: 100,
  audit_confidence: "high",
  overview: {
    n_rows: 2,
    n_cols: 5,
    missing_cells: 0,
    filename: "complete.csv",
    original_columns: ["compound_id", "logFC", "p_value", "fdr", "Annotation"],
  },
  schema: {
    canonical_to_original: {
      compound_id: "compound_id",
      effect_size: "logFC",
      p_value: "p_value",
      fdr: "fdr",
      annotation: "Annotation",
    },
    missing: [],
    ambiguities: {},
  },
  findings: [],
  preview: {
    columns: ["compound_id", "logFC", "p_value", "fdr", "Annotation"],
    rows: [
      ["M1", "1.5", "0.01", "0.05", "confirmed"],
      ["M2", "-0.2", "0.20", "0.30", "putative"],
    ],
  },
  report_md: "# Metabolomics Validity Report\n\n## Dataset Overview\n- Number of rows: 2\n\n<b>VALIDEX_MARKER</b>",
  report_json: {
    analysis: {
      confidence: 100,
      audit_confidence: "high",
      flags: [],
      detected: {
        compound_id: "compound_id",
        effect_size: "logFC",
        p_value: "p_value",
        fdr: "fdr",
        annotation: "Annotation",
      },
      statistical_validation: {
        p_value: { total_row_count: 2, valid_numeric_count: 2 },
        fdr: { total_row_count: 2, valid_numeric_count: 2 },
      },
    },
  },
  histogram: null,
  ai_score: null,
  ai_score_reason: null,
};

export const missingEffectAndAnnotationResponse = {
  ...liveAuditResponse,
  score: 70,
  audit_confidence: "medium",
  schema: {
    canonical_to_original: {
      compound_id: "compound_id",
      p_value: "p_value",
      fdr: "fdr",
    },
    missing: ["effect_size", "annotation"],
    ambiguities: {},
  },
  preview: {
    columns: ["compound_id", "p_value", "fdr"],
    rows: [["M1", "0.01", "0.05"]],
  },
  report_json: {
    analysis: {
      confidence: 70,
      audit_confidence: "medium",
      flags: [
        {
          severity: "low",
          title: "Missing annotation evidence",
          why: "No annotation column was detected.",
          fix: "Include metabolite annotation where available.",
        },
      ],
    },
  },
};

export const liveCleanDataResponse = {
  issues: [],
  summary: {
    original_rows: 2,
    rows_removed: 0,
    rows_kept: 2,
    original_columns: ["compound_id", "logFC", "p_value", "fdr", "Annotation"],
    filename: "complete.csv",
  },
  removed_preview: [],
  clean_csv_b64: "Y29tcG91bmRfaWQsbG9nRkMscF92YWx1ZSxmZHIsQW5ub3RhdGlvbgpNMSwxLjUsMC4wMSwwLjA1LGNvbmZpcm1lZAo=",
};
