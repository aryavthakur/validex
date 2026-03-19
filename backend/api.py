from __future__ import annotations
import io
import json
import os
import re
import tempfile
from typing import Any, Dict, Optional

import httpx
import pandas as pd
from fastapi import FastAPI, File, Form, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from main import run_audit
from schema_mapper import detect_schema

app = FastAPI(title="Metabolomics Auditor API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

OPENROUTER_API_KEY = os.environ.get("OPENROUTER_API_KEY", "")
GROQ_API_KEY = os.environ.get("GROQ_API_KEY", "")
OLLAMA_URL = "http://localhost:11434"
async def call_ai(prompt: str, timeout: float = 60.0) -> str:
    """
    Call AI provider in priority order:
    1. Groq (free, fast, reliable) — preferred for production
    2. OpenRouter free models — fallback if no Groq key
    3. Ollama — local development fallback
    """
    async with httpx.AsyncClient(timeout=timeout) as client:
        # --- Groq (best free option) ---
        if GROQ_API_KEY:
            response = await client.post(
                "https://api.groq.com/openai/v1/chat/completions",
                headers={
                    "Authorization": "Bearer " + GROQ_API_KEY,
                    "Content-Type": "application/json",
                },
                json={
                    "model": "llama-3.3-70b-versatile",
                    "messages": [{"role": "user", "content": prompt}],
                    "max_tokens": 2048,
                },
            )
            if response.status_code == 200:
                return response.json()["choices"][0]["message"]["content"]
            if response.status_code == 429:
                # Groq rate limited — fall through to OpenRouter
                pass
            else:
                raise HTTPException(502, "Groq error: " + response.text[:300])

        # --- OpenRouter free fallback ---
        if OPENROUTER_API_KEY:
            for model in [
                "meta-llama/llama-3.3-70b-instruct:free",
                "google/gemma-3-27b-it:free",
                "mistralai/mistral-small-3.1-24b-instruct:free",
            ]:
                response = await client.post(
                    "https://openrouter.ai/api/v1/chat/completions",
                    headers={
                        "Authorization": "Bearer " + OPENROUTER_API_KEY,
                        "Content-Type": "application/json",
                    },
                    json={
                        "model": model,
                        "messages": [{"role": "user", "content": prompt}],
                    },
                )
                if response.status_code == 200:
                    return response.json()["choices"][0]["message"]["content"]
                if response.status_code == 429:
                    continue
                raise HTTPException(502, "OpenRouter error: " + response.text[:300])

        # --- Ollama local fallback ---
        try:
            response = await client.post(
                OLLAMA_URL + "/api/generate",
                json={"model": "llama3.2", "prompt": prompt, "stream": False},
                timeout=180.0,
            )
            if response.status_code == 200:
                return response.json().get("response", "")
        except Exception:
            pass

        raise HTTPException(503, "No AI provider available. Add a GROQ_API_KEY to your environment.")


async def ai_confidence_score(
    baseline_score: int,
    notes: str,
    ctx: Dict[str, Any],
    df: pd.DataFrame,
    flags: list,
) -> Dict[str, Any]:
    """
    Use AI to adjust the confidence score based on user-provided notes
    and study context. Returns adjusted score + explanation.
    """
    if not notes or not notes.strip():
        return {"ai_score": None, "ai_score_reason": None}

    flag_summary = ""
    if flags:
        flag_summary = "Detected issues: " + "; ".join(
            f.get("title", "") for f in flags if f.get("title")
        )
    else:
        flag_summary = "No major issues detected by automated checks."

    prompt = (
        "You are an expert metabolomics data reviewer. "
        "Your job is to adjust a confidence score for a metabolomics dataset audit.\n\n"
        "BASELINE SCORE (from automated checks): " + str(baseline_score) + "/100\n\n"
        "AUTOMATED FLAGS: " + flag_summary + "\n\n"
        "STUDY CONTEXT:\n"
        "- Metabolomics type: " + ctx.get("metabolomics_type", "unknown") + "\n"
        "- Study goal: " + ctx.get("study_goal", "unknown") + "\n"
        "- Design type: " + ctx.get("design_type", "unknown") + "\n"
        "- Group count: " + ctx.get("group_count", "unknown") + "\n"
        "- Small sample size flag: " + str(ctx.get("small_n", False)) + "\n"
        "- Batch effects likely: " + str(ctx.get("has_batches", False)) + "\n"
        "- Alpha threshold: " + str(ctx.get("alpha", "0.05")) + "\n\n"
        "DATASET STATS:\n"
        "- Rows: " + str(df.shape[0]) + "\n"
        "- Columns: " + str(df.shape[1]) + "\n"
        "- Missing values: " + str(int(df.isna().sum().sum())) + "\n\n"
        "RESEARCHER NOTES (this is the key input — take it seriously):\n"
        + notes.strip() + "\n\n"
        "Based on all of the above, provide an adjusted confidence score from 0-100. "
        "Consider whether the notes reveal additional concerns (lower the score) "
        "or provide reassuring context (raise the score). "
        "Be precise and critical — notes like 'small n', 'no batch correction', "
        "'pilot study', 'no replicates' should meaningfully lower the score. "
        "Notes like 'validated by orthogonal method', 'large well-controlled cohort' should raise it.\n\n"
        "Respond in this exact format and nothing else:\n"
        "SCORE: <number>\n"
        "REASON: <one or two sentences explaining the adjustment>"
    )

    try:
        raw = await call_ai(prompt, timeout=45.0)
        score_match = re.search(r"SCORE:\s*(\d+)", raw)
        reason_match = re.search(r"REASON:\s*(.+)", raw, re.DOTALL)

        ai_score = int(score_match.group(1)) if score_match else None
        ai_reason = reason_match.group(1).strip() if reason_match else raw.strip()

        if ai_score is not None:
            ai_score = max(0, min(100, ai_score))

        return {"ai_score": ai_score, "ai_score_reason": ai_reason}
    except Exception:
        return {"ai_score": None, "ai_score_reason": None}


@app.get("/health")
def health():
    return {"status": "ok"}


@app.get("/lambda-health")
async def lambda_health():
    if GROQ_API_KEY:
        return {"status": "ok", "provider": "groq"}
    if OPENROUTER_API_KEY:
        return {"status": "ok", "provider": "openrouter"}
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            r = await client.get(f"{OLLAMA_URL}/api/tags")
            if r.status_code == 200:
                return {"status": "ok", "provider": "ollama"}
        return {"status": "unavailable"}
    except Exception as e:
        return {"status": "unavailable", "error": str(e)}


@app.post("/audit")
async def audit(
    file: UploadFile = File(...),
    context: str = Form("{}"),
):
    if not file.filename.endswith(".csv"):
        raise HTTPException(400, "Only .csv files are supported.")

    ctx: Dict[str, Any] = {}
    try:
        ctx = json.loads(context)
    except Exception:
        pass

    contents = await file.read()

    with tempfile.TemporaryDirectory() as tmpdir:
        csv_path = os.path.join(tmpdir, "results.csv")
        report_path = os.path.join(tmpdir, "validity_report.md")
        json_path = os.path.join(tmpdir, "validity_report.json")

        with open(csv_path, "wb") as f:
            f.write(contents)

        try:
            run_audit(csv_path=csv_path, report_path=report_path, json_path=json_path, context=ctx)
        except TypeError:
            run_audit(csv_path=csv_path, report_path=report_path, json_path=json_path)

        report_md = ""
        if os.path.exists(report_path):
            with open(report_path, "r", encoding="utf-8") as f:
                report_md = f.read()

        report_json: Dict[str, Any] = {}
        if os.path.exists(json_path):
            with open(json_path, "r", encoding="utf-8") as f:
                report_json = json.load(f)

    df = pd.read_csv(io.BytesIO(contents))
    sm = detect_schema(df)
    schema_info = {
        "canonical_to_original": sm.canonical_to_original,
        "missing": sm.missing,
        "ambiguities": sm.ambiguities,
    }

    preview_columns = list(df.columns)
    preview_rows = df.head(100).where(pd.notnull(df.head(100)), None).values.tolist()
    overview = {
        "n_rows": int(df.shape[0]),
        "n_cols": int(df.shape[1]),
        "missing_cells": int(df.isna().sum().sum()),
        "filename": file.filename,
    }

    effect_col = (
        sm.canonical_to_original.get("log2fc")
        or sm.canonical_to_original.get("fold_change")
    )
    histogram: Optional[Dict[str, Any]] = None
    if effect_col and effect_col in df.columns:
        import numpy as np
        series = pd.to_numeric(df[effect_col], errors="coerce").replace([np.inf, -np.inf], np.nan).dropna()
        if len(series) > 0:
            counts, bin_edges = np.histogram(series, bins=30)
            histogram = {
                "column": effect_col,
                "counts": counts.tolist(),
                "bin_edges": [round(float(x), 4) for x in bin_edges],
            }

    # Extract confidence score directly from markdown report
    baseline_score = None
    score_match = re.search(r"\*\*(\d+)\s*/\s*100\*\*", report_md)
    if score_match:
        baseline_score = int(score_match.group(1))

    # Inject score into report_json so frontend can use it
    if baseline_score is not None:
        if "analysis" not in report_json:
            report_json["analysis"] = {}
        report_json["analysis"]["confidence"] = baseline_score

    # AI confidence scoring — only runs if notes are provided
    notes = ctx.get("notes", "")
    flags = report_json.get("analysis", {}).get("flags", [])

    ai_score_data = {"ai_score": None, "ai_score_reason": None}
    if notes and notes.strip() and baseline_score is not None and (GROQ_API_KEY or OPENROUTER_API_KEY):
        ai_score_data = await ai_confidence_score(
            baseline_score=baseline_score,
            notes=notes,
            ctx=ctx,
            df=df,
            flags=flags,
        )

    return JSONResponse({
        "overview": overview,
        "schema": schema_info,
        "preview": {"columns": preview_columns, "rows": preview_rows},
        "report_md": report_md,
        "report_json": report_json,
        "histogram": histogram,
        "ai_score": ai_score_data["ai_score"],
        "ai_score_reason": ai_score_data["ai_score_reason"],
    })


@app.post("/lambda-analyze")
async def lambda_analyze(
    file: UploadFile = File(...),
    question: str = Form("Analyze this metabolite dataset. Summarize key patterns, identify statistical concerns, and suggest the most important metabolites to investigate further."),
    context: str = Form("{}"),
):
    contents = await file.read()
    df = pd.read_csv(io.BytesIO(contents))

    ctx: Dict[str, Any] = {}
    try:
        ctx = json.loads(context)
    except Exception:
        pass

    lines = [
        "Dataset: " + file.filename,
        "Shape: " + str(df.shape[0]) + " rows x " + str(df.shape[1]) + " columns",
        "Columns: " + ", ".join(df.columns.tolist()),
        "Missing values: " + str(int(df.isna().sum().sum())),
    ]
    if ctx.get("metabolomics_type"):
        lines.append("Metabolomics type: " + ctx["metabolomics_type"])
    if ctx.get("study_goal"):
        lines.append("Study goal: " + ctx["study_goal"])
    if ctx.get("comparison_label"):
        lines.append("Comparison: " + ctx["comparison_label"])

    preview_csv = df.head(20).to_csv(index=False)
    context_block = "\n".join(lines)

    prompt = (
        "You are a metabolomics data analysis expert.\n\n"
        + context_block
        + "\n\nFirst 20 rows of data:\n"
        + preview_csv
        + "\n\nUser question: "
        + question
        + "\n\nPlease provide:\n"
        + "1. Data quality assessment\n"
        + "2. Key patterns and trends\n"
        + "3. Notable metabolites\n"
        + "4. Statistical concerns\n"
        + "5. Suggested next steps"
    )

    try:
        analysis_text = await call_ai(prompt, timeout=60.0)
        return JSONResponse({"analysis": analysis_text, "status": "ok"})
    except httpx.ConnectError:
        raise HTTPException(503, "Cannot connect to AI service.")
    except httpx.TimeoutException:
        raise HTTPException(504, "AI request timed out. Try again.")
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(500, "Error: " + str(e))


@app.post("/clean-data")
async def clean_data(
    file: UploadFile = File(...),
    missing_threshold: float = Form(0.5),
    outlier_std: float = Form(3.0),
    remove_duplicates: bool = Form(True),
):
    """
    Analyze a CSV and return a cleaning report + cleaned CSV as base64.
    Returns a preview and summary for user approval before downloading.
    """
    contents = await file.read()
    df = pd.read_csv(io.BytesIO(contents))

    original_shape = df.shape
    log = []
    removed_rows = set()

    # 1. Duplicate rows
    if remove_duplicates:
        dup_mask = df.duplicated()
        dup_count = int(dup_mask.sum())
        if dup_count > 0:
            removed_rows.update(df[dup_mask].index.tolist())
            log.append({
                "type": "duplicates",
                "severity": "med",
                "title": str(dup_count) + " duplicate row" + ("s" if dup_count > 1 else "") + " found",
                "detail": "Rows that are exact copies of another row.",
                "rows_affected": dup_count,
                "action": "Remove duplicates",
            })

    # 2. Missing values per row
    numeric_cols = df.select_dtypes(include="number").columns.tolist()
    if numeric_cols:
        missing_frac = df[numeric_cols].isnull().mean(axis=1)
        high_missing = missing_frac[missing_frac > missing_threshold].index.tolist()
        new_high_missing = [i for i in high_missing if i not in removed_rows]
        if new_high_missing:
            removed_rows.update(new_high_missing)
            pct = int(missing_threshold * 100)
            log.append({
                "type": "missing_values",
                "severity": "high",
                "title": str(len(new_high_missing)) + " row" + ("s" if len(new_high_missing) > 1 else "") + " with >" + str(pct) + "% missing values",
                "detail": "These rows are missing more than " + str(pct) + "% of numeric measurements.",
                "rows_affected": len(new_high_missing),
                "action": "Remove rows with >" + str(pct) + "% missing",
            })

    # 3. Outliers per numeric column
    import numpy as np
    outlier_rows = set()
    outlier_details = []
    for col in numeric_cols:
        series = pd.to_numeric(df[col], errors="coerce")
        mean = series.mean()
        std = series.std()
        if std == 0 or std != std:
            continue
        outlier_mask = (series - mean).abs() > outlier_std * std
        col_outliers = df[outlier_mask].index.tolist()
        new_outliers = [i for i in col_outliers if i not in removed_rows]
        if new_outliers:
            outlier_rows.update(new_outliers)
            outlier_details.append(col + ": " + str(len(new_outliers)) + " outlier" + ("s" if len(new_outliers) > 1 else ""))

    if outlier_rows:
        removed_rows.update(outlier_rows)
        log.append({
            "type": "outliers",
            "severity": "med",
            "title": str(len(outlier_rows)) + " row" + ("s" if len(outlier_rows) > 1 else "") + " with statistical outliers (>" + str(outlier_std) + "σ)",
            "detail": "Affected columns: " + "; ".join(outlier_details[:5]) + ("..." if len(outlier_details) > 5 else ""),
            "rows_affected": len(outlier_rows),
            "action": "Remove rows with values >" + str(outlier_std) + " standard deviations from mean",
        })

    # 4. Column-level missing value summary
    col_missing = {}
    for col in numeric_cols:
        n_missing = int(df[col].isnull().sum())
        if n_missing > 0:
            col_missing[col] = n_missing

    if col_missing:
        log.append({
            "type": "column_missing",
            "severity": "low",
            "title": str(len(col_missing)) + " column" + ("s" if len(col_missing) > 1 else "") + " with missing values",
            "detail": "Missing counts: " + ", ".join(k + ": " + str(v) for k, v in list(col_missing.items())[:5]),
            "rows_affected": 0,
            "action": "Consider imputation (mean/median) for missing values",
        })

    # Build cleaned dataframe
    removed_list = sorted(removed_rows)
    df_clean = df.drop(index=removed_list).reset_index(drop=True)

    # Build before/after preview (first 5 removed rows)
    removed_preview = []
    for idx in removed_list[:5]:
        row = df.iloc[idx].where(pd.notnull(df.iloc[idx]), None).to_dict()
        removed_preview.append({"original_index": int(idx), "data": row})

    # Encode cleaned CSV as base64
    import base64
    clean_csv_bytes = df_clean.to_csv(index=False).encode("utf-8")
    clean_csv_b64 = base64.b64encode(clean_csv_bytes).decode("utf-8")

    summary = {
        "original_rows": original_shape[0],
        "original_cols": original_shape[1],
        "rows_removed": len(removed_list),
        "rows_kept": len(df_clean),
        "clean_filename": file.filename.replace(".csv", "_clean.csv"),
    }

    return JSONResponse({
        "summary": summary,
        "issues": log,
        "removed_preview": removed_preview,
        "clean_csv_b64": clean_csv_b64,
        "preview": {
            "columns": list(df_clean.columns),
            "rows": df_clean.head(20).where(pd.notnull(df_clean.head(20)), None).values.tolist(),
        },
    })
