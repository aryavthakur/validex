import { fireEvent, render, screen, waitFor, within } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";
import AuditResults, { ReportMarkdown, CleanData } from "./AuditResults";
import { liveAuditResponse, liveCleanDataResponse, missingEffectAndAnnotationResponse } from "../test/fixtures";

function renderResults(results = liveAuditResponse) {
  return render(
    <AuditResults
      results={results}
      file={new File(["compound_id,p_value\nM1,0.01\n"], "complete.csv", { type: "text/csv" })}
      onReset={() => {}}
      isDemo={false}
      context={{}}
    />
  );
}

describe("AuditResults", () => {
  it("renders report HTML-looking text without interpreting it as elements", () => {
    const { container } = render(<ReportMarkdown md={"# Report\n\n<b>VALIDEX_MARKER</b>\n<div>REPORT_MARKER</div>"} />);

    expect(screen.getByText("<b>VALIDEX_MARKER</b>")).toBeInTheDocument();
    expect(screen.getByText("<div>REPORT_MARKER</div>")).toBeInTheDocument();
    expect(container.querySelector("b")).toBeNull();
    expect(container.querySelector(".report-md div")).toBeNull();
  });

  it("renders an unavailable state for missing report content", () => {
    render(<ReportMarkdown md="" />);

    expect(screen.getByText("Report unavailable")).toBeInTheDocument();
    expect(screen.getByText(/did not include report content/i)).toBeInTheDocument();
  });

  it("renders p-value and FDR preview values from the canonical view model", () => {
    renderResults();
    fireEvent.click(screen.getByRole("button", { name: /data/i }));

    expect(screen.getByRole("columnheader", { name: "p_value" })).toBeInTheDocument();
    expect(screen.getByRole("columnheader", { name: "fdr" })).toBeInTheDocument();
    expect(screen.getByText("0.01")).toBeInTheDocument();
    expect(screen.getByText("0.05")).toBeInTheDocument();
  });

  it("shows unavailable state for missing effect size and annotation", () => {
    renderResults(missingEffectAndAnnotationResponse);
    fireEvent.click(screen.getByRole("button", { name: /schema map/i }));

    const effectRow = screen.getByTestId("schema-effect_size");
    const annotationRow = screen.getByTestId("schema-annotation");
    expect(within(effectRow).getByText("Unavailable")).toBeInTheDocument();
    expect(within(annotationRow).getByText("Unavailable")).toBeInTheDocument();
  });

  it("does not display live power analysis when histogram is missing", () => {
    renderResults();

    expect(screen.queryByRole("button", { name: /power/i })).not.toBeInTheDocument();
    expect(screen.queryByText(/adequately powered|underpowered/i)).not.toBeInTheDocument();
  });

  it("does not display publication-readiness panels in ordinary audit results", () => {
    renderResults();

    expect(screen.queryByRole("button", { name: /pub|publication|checklist/i })).not.toBeInTheDocument();
    expect(screen.queryByText(/publication ready|msi compliant|journal accepted/i)).not.toBeInTheDocument();
    expect(screen.getByText(/does not certify biological validity, publication readiness/i)).toBeInTheDocument();
  });

  it("keeps deterministic results visible when Ollama output is unavailable", () => {
    renderResults({ ...liveAuditResponse, ai_score: null, ai_score_reason: null });

    expect(screen.getByText("Deterministic audit score")).toBeInTheDocument();
    expect(screen.getByText("100")).toBeInTheDocument();
    expect(screen.getByText(/local ai explanation unavailable/i)).toBeInTheDocument();
  });

  it("renders a valid live audit response without crashing", () => {
    renderResults();

    expect(screen.getByRole("heading", { name: "CSV Audit Report" })).toBeInTheDocument();
    expect(screen.getByText("complete.csv")).toBeInTheDocument();
  });
});

describe("CleanData", () => {
  it("uses actual clean-data response keys and avoids broad cleaning claims", async () => {
    vi.stubGlobal("fetch", vi.fn(async () => ({
      ok: true,
      json: async () => liveCleanDataResponse,
    })));

    render(<CleanData file={new File(["x"], "complete.csv", { type: "text/csv" })} />);
    fireEvent.click(screen.getByRole("button", { name: /prepare validated csv export/i }));

    expect(await screen.findByText(/validated CSV export is available/i)).toBeInTheDocument();
    expect(screen.getByText("complete.csv")).toBeInTheDocument();
    expect(screen.queryByText(/detects outliers|removes outliers|batch effect detection|normalization validation/i)).not.toBeInTheDocument();
  });

  it("shows clean-data endpoint errors", async () => {
    vi.stubGlobal("fetch", vi.fn(async () => ({
      ok: false,
      json: async () => ({ detail: "CSV parse failed" }),
    })));

    render(<CleanData file={new File(["x"], "bad.csv", { type: "text/csv" })} />);
    fireEvent.click(screen.getByRole("button", { name: /prepare validated csv export/i }));

    expect(await screen.findByRole("alert")).toHaveTextContent("CSV parse failed");
  });

  it("announces loading status", async () => {
    let resolveResponse;
    vi.stubGlobal("fetch", vi.fn(() => new Promise((resolve) => { resolveResponse = resolve; })));

    render(<CleanData file={new File(["x"], "complete.csv", { type: "text/csv" })} />);
    fireEvent.click(screen.getByRole("button", { name: /prepare validated csv export/i }));

    expect(screen.getByRole("status")).toHaveTextContent(/preparing validated csv export/i);
    resolveResponse({ ok: true, json: async () => liveCleanDataResponse });
    await waitFor(() => expect(screen.queryByRole("status")).not.toBeInTheDocument());
  });

  it("shows an error when the clean export payload cannot be decoded", async () => {
    vi.stubGlobal("fetch", vi.fn(async () => ({
      ok: true,
      json: async () => ({ ...liveCleanDataResponse, clean_csv_b64: "not valid base64!" }),
    })));

    render(<CleanData file={new File(["x"], "complete.csv", { type: "text/csv" })} />);
    fireEvent.click(screen.getByRole("button", { name: /prepare validated csv export/i }));
    fireEvent.click(await screen.findByRole("button", { name: /download validated csv/i }));

    expect(await screen.findByRole("alert")).toHaveTextContent("could not be decoded");
  });
});
