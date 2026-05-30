from __future__ import annotations

import json
import os
from typing import Any

import pandas as pd


def run_audit(csv_path: str, report_path: str, json_path: str | None = None, context: dict[str, Any] | None = None) -> str:
    if not os.path.exists(csv_path):
        raise FileNotFoundError("Input CSV not found: " + csv_path)

    df = pd.read_csv(csv_path)
    n_rows, n_cols = df.shape

    def find_col(keywords: list[str]) -> str | None:
        for keyword in keywords:
            for column in df.columns:
                if keyword in str(column).lower():
                    return str(column)
        return None

    p_col = find_col(["p", "pvalue"])
    fdr_col = find_col(["fdr", "q", "adj"])
    fc_col = find_col(["log2fc", "logfc", "fold"])

    confidence = 100
    interpretations: list[str] = []
    recommendations: list[str] = []
    flags: list[dict[str, Any]] = []

    if fc_col and not p_col:
        confidence -= 40
        message = "Fold-change values are present without corresponding p-values. Statistical significance cannot be assessed."
        interpretations.append(message)
        recommendations.append("Run a statistical test (e.g., t-test or ANOVA) to obtain p-values.")
        flags.append({"severity": "high", "title": "Missing p-values", "why": message, "fix": recommendations[-1]})

    if p_col and not fdr_col:
        confidence -= 20
        message = "P-values are present without FDR/q-values. This increases false positive risk in high-dimensional data."
        interpretations.append(message)
        recommendations.append("Apply FDR correction (e.g., Benjamini-Hochberg) to control multiple comparisons.")
        flags.append({"severity": "med", "title": "No multiple-testing correction", "why": message, "fix": recommendations[-1]})

    if p_col and fdr_col:
        interpretations.append("Both p-values and FDR-adjusted q-values are present, indicating statistically interpretable results.")

    confidence = max(confidence, 0)

    md = [
        "# Metabolomics Validity Report\n",
        "## Dataset Overview",
        f"- Number of features (rows): {n_rows}",
        f"- Number of columns: {n_cols}\n",
        "## Detected Statistical Columns",
        f"- Fold change: {fc_col}",
        f"- p-value: {p_col}",
        f"- FDR / q-value: {fdr_col}\n",
        "## Scientific Interpretation",
    ]
    md.extend([f"- {item}" for item in interpretations] or ["- No major statistical issues detected."])
    md.append("\n## Recommendations")
    md.extend([f"- {item}" for item in recommendations] or ["- No immediate corrective actions required."])
    md.extend(["\n## Overall Confidence Score", f"**{confidence} / 100**\n"])
    report_text = "\n".join(md)

    os.makedirs(os.path.dirname(report_path), exist_ok=True)
    with open(report_path, "w", encoding="utf-8") as handle:
        handle.write(report_text)

    if json_path:
        os.makedirs(os.path.dirname(json_path), exist_ok=True)
        with open(json_path, "w", encoding="utf-8") as handle:
            json.dump({"analysis": {"confidence": confidence, "flags": flags, "interpretations": interpretations, "recommendations": recommendations}}, handle)

    return report_text
