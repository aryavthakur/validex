from __future__ import annotations
import io
import json
import os
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
OLLAMA_URL = "http://localhost:11434"


@app.get("/health")
def health():
    return {"status": "ok"}


@app.get("/lambda-health")
async def lambda_health():
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

    return JSONResponse({
        "overview": overview,
        "schema": schema_info,
        "preview": {"columns": preview_columns, "rows": preview_rows},
        "report_md": report_md,
        "report_json": report_json,
        "histogram": histogram,
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
        async with httpx.AsyncClient(timeout=60.0) as client:
            if OPENROUTER_API_KEY:
                # Production: use OpenRouter (free)
                response = await client.post(
                    "https://openrouter.ai/api/v1/chat/completions",
                    headers={
                        "Authorization": "Bearer " + OPENROUTER_API_KEY,
                        "Content-Type": "application/json",
                    },
                    json={
                        "model": "google/gemma-3-4b-it:free",
                        "messages": [{"role": "user", "content": prompt}],
                    },
                )
                if response.status_code != 200:
                    raise HTTPException(502, "OpenRouter error: " + response.text[:300])
                result = response.json()
                analysis_text = result["choices"][0]["message"]["content"]
            else:
                # Local: use Ollama
                response = await client.post(
                    OLLAMA_URL + "/api/generate",
                    json={"model": "llama3.2", "prompt": prompt, "stream": False},
                    timeout=180.0,
                )
                if response.status_code != 200:
                    raise HTTPException(502, "Ollama error: " + response.text[:300])
                result = response.json()
                analysis_text = result.get("response", "No response from model.")

            return JSONResponse({"analysis": analysis_text, "status": "ok"})

    except httpx.ConnectError:
        raise HTTPException(503, "Cannot connect to AI service.")
    except httpx.TimeoutException:
        raise HTTPException(504, "AI request timed out. Try again.")
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(500, "Error: " + str(e))
