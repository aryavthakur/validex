from __future__ import annotations

import base64
import io
import json
import os
import re
import tempfile
from pathlib import Path
from typing import Any

import pandas as pd
from fastapi import FastAPI, File, Form, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles

from .ai.ollama_client import OllamaClient, OllamaError
from .audit import run_audit
from .config import DEFAULT_CONFIG, load_config
from .schema_mapper import detect_schema


def _frontend_dist() -> Path:
    packaged = Path(__file__).resolve().parent / "static"
    if packaged.exists():
        return packaged
    return Path(__file__).resolve().parents[1] / "frontend" / "dist"


def _safe_filename(filename: str | None) -> str:
    name = os.path.basename(filename or "dataset.csv")
    return re.sub(r"[^A-Za-z0-9._-]+", "_", name) or "dataset.csv"


def _dataset_summary(df: pd.DataFrame, flags: list[dict[str, Any]], context: dict[str, Any]) -> str:
    numeric = df.select_dtypes(include="number")
    stats = numeric.describe().round(4).to_dict() if not numeric.empty else {}
    summary = {
        "shape": {"rows": int(df.shape[0]), "columns": int(df.shape[1])},
        "columns": [str(column) for column in df.columns],
        "missing_values": int(df.isna().sum().sum()),
        "numeric_summary": stats,
        "audit_flags": flags,
        "study_context": context,
    }
    return json.dumps(summary, default=str)[:16000]


def create_app(config: dict[str, Any] | None = None) -> FastAPI:
    app_config = {**DEFAULT_CONFIG, **(config or load_config())}
    # Privacy boundary: runtime routes only expose/use local Ollama.
    app_config["ai_provider"] = "ollama"
    app_config["cloud_ai_enabled"] = False
    ollama = OllamaClient(app_config["ollama_url"])

    app = FastAPI(title="Validex Local API", version="0.1.0")
    app.add_middleware(
        CORSMiddleware,
        allow_origin_regex=r"^http://(127\.0\.0\.1|localhost)(:\d+)?$",
        allow_credentials=False,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    @app.get("/api/health")
    def api_health():
        return {"status": "ok"}

    @app.get("/health")
    def legacy_health():
        return {"status": "ok"}

    @app.get("/api/privacy/status")
    def privacy_status():
        return {
            "provider": "ollama",
            "local_only": True,
            "cloud_ai_enabled": False,
            "ollama_url": app_config["ollama_url"],
            "model": app_config["model"],
        }

    @app.get("/api/ai/status")
    def ai_status():
        installed = ollama.is_installed()
        health = ollama.health()
        models: list[str] = []
        model_installed = False
        if health["running"]:
            try:
                models = ollama.list_models()
                model_installed = app_config["model"] in models
            except OllamaError:
                models = []
        return {
            "provider": "ollama",
            "installed": installed,
            "running": health["running"],
            "model": app_config["model"],
            "model_installed": model_installed,
            "models": models,
            "local_only": True,
            "cloud_ai_enabled": False,
            "error": health["error"],
        }

    @app.get("/lambda-health")
    async def legacy_lambda_health():
        status = ai_status()
        return {"status": "ok" if status["running"] and status["model_installed"] else "unavailable", "provider": "ollama"}

    @app.post("/api/ai/analyze")
    async def ai_analyze(
        file: UploadFile = File(...),
        question: str = Form("Analyze this metabolite dataset summary and identify data quality concerns."),
        context: str = Form("{}"),
    ):
        contents = await file.read()
        df = pd.read_csv(io.BytesIO(contents))
        try:
            ctx = json.loads(context)
        except Exception:
            ctx = {}

        flags: list[dict[str, Any]] = []
        prompt = (
            "You are a metabolomics data reviewer running locally inside Validex. "
            "Use only this structured summary; do not assume access to raw files.\n\n"
            "DATASET SUMMARY:\n"
            + _dataset_summary(df, flags, ctx)
            + "\n\nQUESTION:\n"
            + question
            + "\n\nRespond with data quality concerns, interpretation risks, and concrete next steps."
        )
        try:
            analysis = ollama.generate(prompt, model=app_config["model"], timeout=90.0)
            return JSONResponse({"analysis": analysis, "status": "ok", "provider": "ollama"})
        except OllamaError as exc:
            raise HTTPException(503, str(exc))

    @app.post("/lambda-analyze")
    async def legacy_lambda_analyze(
        file: UploadFile = File(...),
        question: str = Form("Analyze this metabolite dataset. Summarize key patterns, identify statistical concerns, and suggest the most important metabolites to investigate further."),
        context: str = Form("{}"),
    ):
        return await ai_analyze(file=file, question=question, context=context)

    @app.post("/audit")
    async def audit(file: UploadFile = File(...), context: str = Form("{}")):
        if not (file.filename or "").lower().endswith(".csv"):
            raise HTTPException(400, "Only .csv files are supported.")
        try:
            ctx = json.loads(context)
        except Exception:
            ctx = {}

        contents = await file.read()
        with tempfile.TemporaryDirectory(prefix="validex-") as tmpdir:
            csv_path = os.path.join(tmpdir, _safe_filename(file.filename))
            report_path = os.path.join(tmpdir, "validity_report.md")
            json_path = os.path.join(tmpdir, "validity_report.json")
            with open(csv_path, "wb") as handle:
                handle.write(contents)
            report_md = run_audit(csv_path=csv_path, report_path=report_path, json_path=json_path, context=ctx)
            report_json = json.loads(Path(json_path).read_text(encoding="utf-8")) if os.path.exists(json_path) else {}

        df = pd.read_csv(io.BytesIO(contents))
        sm = detect_schema(df)
        overview = {
            "n_rows": int(df.shape[0]),
            "n_cols": int(df.shape[1]),
            "missing_cells": int(df.isna().sum().sum()),
            "filename": _safe_filename(file.filename),
        }
        preview_rows = df.head(100).where(pd.notnull(df.head(100)), None).values.tolist()

        ai_score_data = {"ai_score": None, "ai_score_reason": None}
        notes = str(ctx.get("notes", "")).strip()
        baseline_score = report_json.get("analysis", {}).get("confidence")
        if notes and baseline_score is not None:
            prompt = (
                "You are a local metabolomics reviewer. Adjust this confidence score using the context. "
                "Respond exactly as SCORE: <number> and REASON: <one sentence>.\n"
                + _dataset_summary(df, report_json.get("analysis", {}).get("flags", []), ctx)
                + f"\nBASELINE SCORE: {baseline_score}/100\nNOTES: {notes}"
            )
            try:
                raw = ollama.generate(prompt, model=app_config["model"], timeout=60.0)
                score_match = re.search(r"SCORE:\s*(\d+)", raw)
                reason_match = re.search(r"REASON:\s*(.+)", raw, re.DOTALL)
                if score_match:
                    ai_score_data["ai_score"] = max(0, min(100, int(score_match.group(1))))
                ai_score_data["ai_score_reason"] = reason_match.group(1).strip() if reason_match else raw.strip()
            except OllamaError:
                ai_score_data = {"ai_score": None, "ai_score_reason": None}

        return JSONResponse({
            "overview": overview,
            "schema": {
                "canonical_to_original": sm.canonical_to_original,
                "missing": sm.missing,
                "ambiguities": sm.ambiguities,
            },
            "preview": {"columns": list(df.columns), "rows": preview_rows},
            "report_md": report_md,
            "report_json": report_json,
            "histogram": None,
            "ai_score": ai_score_data["ai_score"],
            "ai_score_reason": ai_score_data["ai_score_reason"],
        })

    @app.post("/clean-data")
    async def clean_data(file: UploadFile = File(...)):
        contents = await file.read()
        df = pd.read_csv(io.BytesIO(contents))
        clean_csv_b64 = base64.b64encode(df.to_csv(index=False).encode("utf-8")).decode("utf-8")
        return JSONResponse({
            "issues": [],
            "summary": {"original_rows": int(df.shape[0]), "rows_removed": 0, "rows_kept": int(df.shape[0])},
            "removed_preview": [],
            "clean_csv_b64": clean_csv_b64,
        })

    dist = _frontend_dist()
    if dist.exists():
        app.mount("/", StaticFiles(directory=dist, html=True), name="frontend")

    return app


app = create_app()
