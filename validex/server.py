from __future__ import annotations

import base64
import json
import math
import os
import re
import tempfile
from pathlib import Path
from typing import Any

import pandas as pd  # type: ignore[import-untyped]
from fastapi import FastAPI, File, Form, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles

from .ai.ollama_client import OllamaClient, OllamaError
from .audit import run_audit
from .config import DEFAULT_CONFIG, load_config
from .ingestion import IngestionError, ingest_csv_bytes
from .schema_mapper import detect_schema


_HASHED_STATIC_RE = re.compile(r"^/assets/.+-[A-Za-z0-9_-]{8,}\.(?:js|css)$")


def _frontend_dist() -> Path:
    packaged = Path(__file__).resolve().parent / "static"
    if packaged.exists():
        return packaged
    return Path(__file__).resolve().parents[1] / "frontend" / "dist"


def _safe_filename(filename: str | None) -> str:
    name = os.path.basename(filename or "dataset.csv")
    return re.sub(r"[^A-Za-z0-9._-]+", "_", name) or "dataset.csv"


def _json_safe(value: Any) -> Any:
    if isinstance(value, dict):
        return {str(key): _json_safe(item) for key, item in value.items()}
    if isinstance(value, list | tuple):
        return [_json_safe(item) for item in value]
    if isinstance(value, float):
        return value if math.isfinite(value) else None
    if hasattr(value, "item"):
        try:
            return _json_safe(value.item())
        except Exception:
            return str(value)
    return value


def _ingestion_error_response(exc: IngestionError) -> JSONResponse:
    return JSONResponse(
        status_code=exc.http_status, content=_json_safe(exc.to_response())
    )


def _dataset_summary(
    df: pd.DataFrame, flags: list[dict[str, Any]], context: dict[str, Any]
) -> str:
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
    return json.dumps(_json_safe(summary), allow_nan=False, default=str)[:16000]


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

    @app.middleware("http")
    async def frontend_cache_headers(request, call_next):
        response = await call_next(request)
        path = request.url.path
        if path in {"/", "/index.html"} and "text/html" in response.headers.get(
            "content-type", ""
        ):
            response.headers["Cache-Control"] = "no-cache"
        elif response.status_code == 200 and _HASHED_STATIC_RE.match(path):
            response.headers["Cache-Control"] = "public, max-age=31536000, immutable"
        elif response.status_code == 200 and path.startswith(
            ("/assets/", "/fonts/", "/mobile/")
        ):
            response.headers.setdefault("Cache-Control", "public, max-age=3600")
        elif response.status_code == 404 and path.startswith(
            ("/assets/", "/fonts/", "/mobile/")
        ):
            response.headers["Cache-Control"] = "no-cache"
        return response

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
        health = (
            ollama.health()
            if installed
            else {"running": False, "error": "Ollama is not installed."}
        )
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
        return {
            "status": "ok"
            if status["running"] and status["model_installed"]
            else "unavailable",
            "provider": "ollama",
        }

    @app.post("/api/ai/analyze")
    async def ai_analyze(
        file: UploadFile = File(...),
        question: str = Form(
            "Analyze this metabolite dataset summary and identify data quality concerns."
        ),
        context: str = Form("{}"),
    ):
        contents = await file.read()
        try:
            df = ingest_csv_bytes(contents, filename=file.filename).dataframe
        except IngestionError as exc:
            return _ingestion_error_response(exc)
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
            return JSONResponse(
                {"analysis": analysis, "status": "ok", "provider": "ollama"}
            )
        except OllamaError as exc:
            raise HTTPException(503, str(exc))

    @app.post("/lambda-analyze")
    async def legacy_lambda_analyze(
        file: UploadFile = File(...),
        question: str = Form(
            "Analyze this metabolite dataset. Summarize key patterns, identify statistical concerns, and suggest the most important metabolites to investigate further."
        ),
        context: str = Form("{}"),
    ):
        return await ai_analyze(file=file, question=question, context=context)

    @app.post("/audit")
    async def audit(file: UploadFile = File(...), context: str = Form("{}")):
        try:
            ctx = json.loads(context)
        except Exception:
            ctx = {}

        contents = await file.read()
        try:
            ingested = ingest_csv_bytes(contents, filename=file.filename)
        except IngestionError as exc:
            return _ingestion_error_response(exc)

        with tempfile.TemporaryDirectory(prefix="validex-") as tmpdir:
            csv_path = os.path.join(tmpdir, _safe_filename(file.filename))
            report_path = os.path.join(tmpdir, "validity_report.md")
            json_path = os.path.join(tmpdir, "validity_report.json")
            with open(csv_path, "wb") as handle:
                handle.write(contents)
            try:
                report_md = run_audit(
                    csv_path=csv_path,
                    report_path=report_path,
                    json_path=json_path,
                    context=ctx,
                )
            except IngestionError as exc:
                return _ingestion_error_response(exc)
            report_json = (
                json.loads(Path(json_path).read_text(encoding="utf-8"))
                if os.path.exists(json_path)
                else {}
            )

        df = ingested.dataframe
        sm = detect_schema(df.columns)
        overview = {
            "n_rows": int(df.shape[0]),
            "n_cols": int(df.shape[1]),
            "missing_cells": int(df.isna().sum().sum()),
            "filename": ingested.metadata.filename,
            "original_columns": ingested.metadata.original_columns,
        }
        preview_rows = _json_safe(
            df.head(100).where(pd.notnull(df.head(100)), None).values.tolist()
        )

        ai_score_data: dict[str, int | str | None] = {
            "ai_score": None,
            "ai_score_reason": None,
        }
        notes = str(ctx.get("notes", "")).strip()
        baseline_score = report_json.get("analysis", {}).get("confidence")
        if notes and baseline_score is not None:
            prompt = (
                "You are a local metabolomics reviewer. Adjust this confidence score using the context. "
                "Respond exactly as SCORE: <number> and REASON: <one sentence>.\n"
                + _dataset_summary(
                    df, report_json.get("analysis", {}).get("flags", []), ctx
                )
                + f"\nBASELINE SCORE: {baseline_score}/100\nNOTES: {notes}"
            )
            try:
                raw = ollama.generate(prompt, model=app_config["model"], timeout=60.0)
                score_match = re.search(r"SCORE:\s*(\d+)", raw)
                reason_match = re.search(r"REASON:\s*(.+)", raw, re.DOTALL)
                if score_match:
                    ai_score_data["ai_score"] = max(
                        0, min(100, int(score_match.group(1)))
                    )
                ai_score_data["ai_score_reason"] = (
                    reason_match.group(1).strip() if reason_match else raw.strip()
                )
            except OllamaError:
                ai_score_data = {"ai_score": None, "ai_score_reason": None}

        audit_analysis = report_json.get("analysis", {})
        audit_confidence = audit_analysis.get("audit_confidence", "low")
        audit_score = audit_analysis.get("confidence", 0)

        return JSONResponse(
            _json_safe(
                {
                    "score": audit_score,
                    "audit_confidence": audit_confidence,
                    "overview": overview,
                    "schema": {
                        "canonical_to_original": sm.canonical_to_original,
                        "missing": sm.missing,
                        "ambiguities": sm.ambiguities,
                    },
                    "findings": audit_analysis.get("flags", []),
                    "preview": {"columns": list(df.columns), "rows": preview_rows},
                    "report_md": report_md,
                    "report_json": report_json,
                    "histogram": None,
                    "ai_score": ai_score_data["ai_score"],
                    "ai_score_reason": ai_score_data["ai_score_reason"],
                }
            )
        )

    @app.post("/clean-data")
    async def clean_data(file: UploadFile = File(...)):
        contents = await file.read()
        try:
            ingested = ingest_csv_bytes(contents, filename=file.filename)
        except IngestionError as exc:
            return _ingestion_error_response(exc)
        df = ingested.dataframe
        clean_csv_b64 = base64.b64encode(df.to_csv(index=False).encode("utf-8")).decode(
            "utf-8"
        )
        return JSONResponse(
            _json_safe(
                {
                    "issues": [],
                    "summary": {
                        "original_rows": int(df.shape[0]),
                        "rows_removed": 0,
                        "rows_kept": int(df.shape[0]),
                        "original_columns": ingested.metadata.original_columns,
                        "filename": ingested.metadata.filename,
                    },
                    "removed_preview": [],
                    "clean_csv_b64": clean_csv_b64,
                }
            )
        )

    dist = _frontend_dist()
    if dist.exists():
        app.mount("/", StaticFiles(directory=dist, html=True), name="frontend")

    return app


app = create_app()
