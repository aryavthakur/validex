export const CANONICAL_FIELDS = [
  "compound_id",
  "effect_size",
  "p_value",
  "fdr",
  "annotation",
];

export const FIELD_LABELS = {
  compound_id: "Compound identifier",
  effect_size: "Effect size",
  p_value: "p-value",
  fdr: "FDR / q-value",
  annotation: "Annotation",
};

export const AUDIT_LOADING_MESSAGES = [
  "Reading CSV structure...",
  "Detecting supported columns...",
  "Validating statistical values...",
  "Checking schema ambiguity...",
  "Building audit findings...",
  "Preparing the report...",
];

function asArray(value) {
  return Array.isArray(value) ? value : [];
}

function asObject(value) {
  return value && typeof value === "object" && !Array.isArray(value) ? value : {};
}

function normalizeSchema(schema = {}) {
  const normalizedSchema = asObject(schema);
  const c2o = asObject(normalizedSchema.canonical_to_original);
  const missing = new Set(asArray(normalizedSchema.missing));
  const ambiguities = asObject(normalizedSchema.ambiguities);

  return CANONICAL_FIELDS.reduce((acc, field) => {
    const value = c2o[field] ?? null;
    const candidateColumns = asArray(ambiguities[field]);
    acc[field] = {
      key: field,
      label: FIELD_LABELS[field],
      value,
      status: value ? "detected" : "missing",
      displayValue: value || "Unavailable",
      missing: !value || missing.has(field),
      candidateColumns,
      ambiguous: candidateColumns.length > 0,
    };
    return acc;
  }, {});
}

function normalizePreview(preview = {}, detectedSchema) {
  const normalizedPreview = asObject(preview);
  const columns = asArray(normalizedPreview.columns);
  const rows = asArray(normalizedPreview.rows).map((row) => asArray(row));
  const canonicalColumns = CANONICAL_FIELDS.reduce((acc, field) => {
    const original = detectedSchema[field]?.value ?? null;
    acc[field] = original && columns.includes(original) ? original : null;
    return acc;
  }, {});

  return {
    columns,
    rows,
    empty: columns.length === 0 || rows.length === 0,
    canonicalColumns,
  };
}

function normalizeAi(raw) {
  const analysis = asObject(raw?.ai_analysis);
  const summary = typeof analysis.summary === "string" && analysis.summary.trim()
    ? analysis.summary.trim()
    : null;
  const legacyReason = typeof raw?.ai_score_reason === "string" && raw.ai_score_reason.trim()
    ? raw.ai_score_reason.trim()
    : null;
  const reason = summary || legacyReason;
  return {
    available: reason !== null,
    score: null,
    reason,
    label: "Optional local AI explanation",
  };
}

export function adaptAuditResponse(raw = {}) {
  const normalizedRaw = asObject(raw);
  const overview = asObject(normalizedRaw.overview);
  const reportJson = asObject(normalizedRaw.report_json);
  const analysis = asObject(reportJson.analysis);
  const detectedSchema = normalizeSchema(normalizedRaw.schema);
  const score = Number.isFinite(normalizedRaw.score)
    ? normalizedRaw.score
    : Number.isFinite(analysis.confidence)
      ? analysis.confidence
      : null;

  return {
    kind: "validex-audit-view-model",
    raw: normalizedRaw,
    summary: {
      filename: overview.filename ?? null,
      nRows: Number.isFinite(overview.n_rows) ? overview.n_rows : null,
      nCols: Number.isFinite(overview.n_cols) ? overview.n_cols : null,
      missingCells: Number.isFinite(overview.missing_cells) ? overview.missing_cells : null,
      originalColumns: asArray(overview.original_columns),
    },
    detectedSchema,
    findings: asArray(normalizedRaw.findings).length ? asArray(normalizedRaw.findings) : asArray(analysis.flags),
    preview: normalizePreview(normalizedRaw.preview, detectedSchema),
    score: {
      value: score,
      confidence: normalizedRaw.audit_confidence ?? analysis.audit_confidence ?? null,
    },
    statisticalValidation: asObject(analysis.statistical_validation),
    report: {
      markdown: typeof normalizedRaw.report_md === "string" ? normalizedRaw.report_md : "",
      json: reportJson,
    },
    histogram: {
      available: Boolean(normalizedRaw.histogram),
      data: normalizedRaw.histogram ?? null,
    },
    ai: normalizeAi(normalizedRaw),
    cleaning: {
      available: true,
      label: "Validated CSV export",
    },
    experimental: {
      publicationReadiness: {
        available: false,
        reason: "Validex audits selected CSV reporting fields and does not certify publication readiness.",
      },
      powerAnalysis: {
        available: false,
        reason: "The deterministic backend does not return validated power-analysis inputs.",
      },
    },
  };
}

export function adaptDemoAuditResponse(raw = {}) {
  const normalizedRaw = asObject(raw);
  const canonicalToOriginal = asObject(normalizedRaw.schema?.canonical_to_original);
  const demoRaw = {
    ...normalizedRaw,
    schema: {
      canonical_to_original: {
        compound_id: canonicalToOriginal.compound_id ?? canonicalToOriginal.feature ?? null,
        effect_size: canonicalToOriginal.effect_size ?? canonicalToOriginal.log2fc ?? canonicalToOriginal.fold_change ?? null,
        p_value: canonicalToOriginal.p_value ?? null,
        fdr: canonicalToOriginal.fdr ?? null,
        annotation: canonicalToOriginal.annotation ?? null,
      },
      missing: asArray(normalizedRaw.schema?.missing)
        .map((field) => (
          field === "feature" ? "compound_id"
            : field === "fold_change" || field === "log2fc" ? "effect_size"
              : field
        ))
        .filter((field) => CANONICAL_FIELDS.includes(field)),
      ambiguities: {
        effect_size: normalizedRaw.schema?.ambiguities?.effect_size
          ?? normalizedRaw.schema?.ambiguities?.log2fc
          ?? normalizedRaw.schema?.ambiguities?.fold_change,
        p_value: normalizedRaw.schema?.ambiguities?.p_value,
        fdr: normalizedRaw.schema?.ambiguities?.fdr,
        annotation: normalizedRaw.schema?.ambiguities?.annotation,
        compound_id: normalizedRaw.schema?.ambiguities?.compound_id ?? normalizedRaw.schema?.ambiguities?.feature,
      },
    },
  };
  return adaptAuditResponse(demoRaw);
}

export function ensureAuditViewModel(value, { demo = false } = {}) {
  if (value?.kind === "validex-audit-view-model") return value;
  return demo ? adaptDemoAuditResponse(value) : adaptAuditResponse(value);
}

export function adaptCleanDataResponse(raw = {}) {
  const normalizedRaw = asObject(raw);
  const summary = asObject(normalizedRaw.summary);
  const filename = summary.filename ?? "validated.csv";
  return {
    available: Boolean(normalizedRaw.clean_csv_b64),
    issues: asArray(normalizedRaw.issues),
    removedPreview: asArray(normalizedRaw.removed_preview),
    cleanCsvBase64: normalizedRaw.clean_csv_b64 ?? null,
    hasDownload: Boolean(normalizedRaw.clean_csv_b64),
    summary: {
      filename,
      originalRows: Number.isFinite(summary.original_rows) ? summary.original_rows : null,
      rowsRemoved: Number.isFinite(summary.rows_removed) ? summary.rows_removed : null,
      rowsKept: Number.isFinite(summary.rows_kept) ? summary.rows_kept : null,
      originalColumns: asArray(summary.original_columns),
    },
    preview: {
      available: Boolean(normalizedRaw.preview?.columns?.length),
      columns: asArray(normalizedRaw.preview?.columns),
      rows: asArray(normalizedRaw.preview?.rows),
    },
    downloadFilename: filename.replace(/\.csv$/i, "") + ".validated.csv",
    message: "A validated CSV export is available. Validex preserved parsed rows and columns; no broad scientific cleaning was performed.",
  };
}
