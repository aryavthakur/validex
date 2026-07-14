import { describe, expect, it } from "vitest";
import { DEMO_RESULTS } from "../demoData";
import {
  liveAuditResponse,
  liveCleanDataResponse,
  missingEffectAndAnnotationResponse,
} from "../test/fixtures";
import {
  adaptAuditResponse,
  adaptCleanDataResponse,
  adaptDemoAuditResponse,
  AUDIT_LOADING_MESSAGES,
} from "./auditViewModel";

describe("audit response adapter", () => {
  it("maps live backend fields into the canonical view model", () => {
    const vm = adaptAuditResponse(liveAuditResponse);

    expect(vm.summary.filename).toBe("complete.csv");
    expect(vm.detectedSchema.compound_id.value).toBe("compound_id");
    expect(vm.detectedSchema.effect_size.value).toBe("logFC");
    expect(vm.detectedSchema.p_value.value).toBe("p_value");
    expect(vm.detectedSchema.fdr.value).toBe("fdr");
    expect(vm.detectedSchema.annotation.value).toBe("Annotation");
    expect(vm.score.value).toBe(100);
    expect(vm.score.confidence).toBe("high");
    expect(vm.preview.columns).toEqual(["compound_id", "logFC", "p_value", "fdr", "Annotation"]);
    expect(vm.histogram.available).toBe(false);
    expect(vm.ai.available).toBe(false);
  });

  it("renders missing optional fields as unavailable without fabricated values", () => {
    const vm = adaptAuditResponse(missingEffectAndAnnotationResponse);

    expect(vm.detectedSchema.effect_size.status).toBe("missing");
    expect(vm.detectedSchema.effect_size.value).toBeNull();
    expect(vm.detectedSchema.annotation.status).toBe("missing");
    expect(vm.detectedSchema.annotation.value).toBeNull();
    expect(vm.preview.canonicalColumns.effect_size).toBeNull();
    expect(vm.preview.canonicalColumns.annotation).toBeNull();
  });

  it("uses actual clean-data response keys", () => {
    const vm = adaptCleanDataResponse(liveCleanDataResponse);

    expect(vm.available).toBe(true);
    expect(vm.summary.filename).toBe("complete.csv");
    expect(vm.summary.originalColumns).toEqual(["compound_id", "logFC", "p_value", "fdr", "Annotation"]);
    expect(vm.hasDownload).toBe(true);
    expect(vm.preview.available).toBe(false);
    expect(vm.message).toContain("validated CSV export");
  });

  it("keeps demo data on the same canonical view model as live data", () => {
    const liveVm = adaptAuditResponse(liveAuditResponse);
    const demoVm = adaptDemoAuditResponse(DEMO_RESULTS);

    expect(Object.keys(demoVm.detectedSchema)).toEqual(Object.keys(liveVm.detectedSchema));
    expect(demoVm.preview.canonicalColumns.p_value).not.toBeNull();
    expect(demoVm.experimental.publicationReadiness.available).toBe(false);
    expect(demoVm.experimental.powerAnalysis.available).toBe(false);
  });

  it("does not expose old live fallback keys", () => {
    const vm = adaptAuditResponse(liveAuditResponse);

    expect(vm.detectedSchema.feature).toBeUndefined();
    expect(vm.detectedSchema.fold_change).toBeUndefined();
    expect(vm.detectedSchema.log2fc).toBeUndefined();
  });

  it("handles null top-level optional fields without crashing or fabricating values", () => {
    const vm = adaptAuditResponse({
      overview: null,
      schema: null,
      preview: null,
      report_json: null,
      report_md: null,
      histogram: null,
      ai_score: null,
      ai_score_reason: null,
    });

    expect(vm.score.value).toBeNull();
    expect(vm.score.confidence).toBeNull();
    expect(vm.summary.filename).toBeNull();
    expect(vm.preview.empty).toBe(true);
    expect(vm.report.markdown).toBe("");
    expect(vm.histogram.available).toBe(false);
    expect(vm.ai.available).toBe(false);
    expect(vm.detectedSchema.effect_size.value).toBeNull();
  });
});

describe("loading messages", () => {
  it("contains only supported audit operations", () => {
    const unsupported = /batch|normalization|publication|power|biological|journal|cleaning/i;

    expect(AUDIT_LOADING_MESSAGES).toHaveLength(6);
    expect(AUDIT_LOADING_MESSAGES.join(" ")).not.toMatch(unsupported);
    expect(AUDIT_LOADING_MESSAGES).toContain("Validating statistical values...");
  });
});
