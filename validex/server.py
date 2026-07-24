from __future__ import annotations

import base64
import asyncio
import json
import math
import os
import re
import tempfile
from pathlib import Path
from typing import Any

import anyio
import pandas as pd  # type: ignore[import-untyped]
from fastapi import FastAPI, File, Form, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles

from .ai.prompting import AiPromptLimits, build_ai_prompt, minimized_audit_payload
from .ai.ollama_client import OllamaClient, OllamaError
from .ai.response_schema import AiResponseValidationError, parse_ai_analysis
from .audit import run_audit
from . import __version__
from .config import (
    DEFAULT_CONFIG,
    classify_provider_host,
    load_config,
    validate_config,
)
from .ingestion import (
    IngestionError,
    IngestionErrorCode,
    ResourceLimits,
    ingest_csv_bytes,
    ingest_table_bytes,
)
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


async def _read_limited_upload(file: UploadFile, limits: ResourceLimits) -> bytes:
    contents = await file.read(limits.max_upload_bytes + 1)
    if len(contents) > limits.max_upload_bytes:
        raise IngestionError(
            code=IngestionErrorCode.RESOURCE_LIMIT_EXCEEDED,  # type: ignore[name-defined]
            message="CSV file exceeds the configured size limit.",
            filename=file.filename,
            details={
                "limit": "max_upload_bytes",
                "max": limits.max_upload_bytes,
                "actual": len(contents),
            },
        )
    return contents


def _safe_http_error(status_code: int, code: str, message: str) -> JSONResponse:
    return JSONResponse(
        status_code=status_code,
        content={"error_code": code, "message": message},
    )


def _context_from_form(context: str) -> dict[str, Any]:
    try:
        parsed = json.loads(context)
    except Exception:
        return {}
    return parsed if isinstance(parsed, dict) else {}


def _privacy_payload(app_config: dict[str, Any]) -> dict[str, Any]:
    classification = classify_provider_host(app_config["ollama_url"])
    return {
        "provider": "ollama",
        "ai_enabled": bool(app_config["ai_enabled"]),
        "provider_host_classification": classification,
        "local_only": classification == "loopback",
        "cloud_ai_enabled": False,
        "ollama_url": app_config["ollama_url"],
        "model": app_config["model"],
        "ai_receives_structured_audit_summaries": True,
        "user_context_sent_to_ai": True,
        "raw_rows_sent_to_ai": False,
        "validex_retains_uploads": False,
        "ollama_privacy_limitations": (
            "Validex cannot guarantee Ollama logging, retention, or isolation from "
            "other local processes. Remote Ollama hosts may receive data over the network."
        ),
    }


def create_app(config: dict[str, Any] | None = None) -> FastAPI:
    app_config = validate_config({**DEFAULT_CONFIG, **(config or load_config())})
    limits = ResourceLimits.from_config(app_config)
    prompt_limits = AiPromptLimits.from_config(app_config)
    ai_semaphore = asyncio.Semaphore(int(app_config["ai_max_concurrent_requests"]))
    try:
        ollama = OllamaClient(
            app_config["ollama_url"],
            timeout=float(app_config["ai_timeout_seconds"]),
            connect_timeout=float(app_config["ai_connect_timeout_seconds"]),
            read_timeout=float(app_config["ai_read_timeout_seconds"]),
            max_response_bytes=int(app_config["ai_max_response_bytes"]),
        )
    except TypeError:
        ollama = OllamaClient(app_config["ollama_url"])

    app = FastAPI(title="Validex Local API", version=__version__)
    app.add_middleware(
        CORSMiddleware,
        allow_origin_regex=r"^http://(127\.0\.0\.1|localhost)(:\d+)?$",
        allow_credentials=False,
        allow_methods=["GET", "POST", "OPTIONS"],
        allow_headers=["content-type", "accept"],
    )

    @app.middleware("http")
    async def security_and_cache_headers(request, call_next):
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
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["Referrer-Policy"] = "no-referrer"
        response.headers["Permissions-Policy"] = "camera=(), microphone=(), geolocation=()"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["Content-Security-Policy"] = (
            "default-src 'self'; "
            "script-src 'self'; "
            "style-src 'self' 'unsafe-inline'; "
            "img-src 'self' data: blob:; "
            "font-src 'self'; "
            "media-src 'self'; "
            "connect-src 'self' http://127.0.0.1:* http://localhost:*; "
            "frame-ancestors 'none'; "
            "base-uri 'self'; "
            "form-action 'self'"
        )
        return response

    @app.get("/api/health")
    def api_health():
        return {"status": "ok", "version": __version__}

    @app.get("/health")
    def legacy_health():
        return {"status": "ok", "version": __version__}

    @app.get("/api/privacy/status")
    def privacy_status():
        return _privacy_payload(app_config)

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
            "local_only": classify_provider_host(app_config["ollama_url"]) == "loopback",
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
        if not app_config["ai_enabled"]:
            return _safe_http_error(503, "AI_DISABLED", "AI analysis is disabled.")
        try:
            contents = await _read_limited_upload(file, limits)
        except IngestionError as exc:
            return _ingestion_error_response(exc)
        try:
            ingested = ingest_table_bytes(contents, filename=file.filename, limits=limits)
        except IngestionError as exc:
            return _ingestion_error_response(exc)
        ctx = _context_from_form(context)
        with tempfile.TemporaryDirectory(prefix="validex-") as tmpdir:
            csv_path = os.path.join(tmpdir, _safe_filename(file.filename))
            report_path = os.path.join(tmpdir, "validity_report.md")
            json_path = os.path.join(tmpdir, "validity_report.json")
            with open(csv_path, "wb") as handle:
                handle.write(contents)
            try:
                await anyio.to_thread.run_sync(
                    run_audit,
                    csv_path,
                    report_path,
                    json_path,
                    ctx,
                    limits,
                )
            except IngestionError as exc:
                return _ingestion_error_response(exc)
            report_json = json.loads(Path(json_path).read_text(encoding="utf-8"))
        df = ingested.dataframe
        input_summary = minimized_audit_payload(df, report_json, ctx, prompt_limits)
        prompt = build_ai_prompt(df, report_json, question, ctx, prompt_limits)
        try:
            async with ai_semaphore:
                raw = await anyio.to_thread.run_sync(
                    ollama.generate,
                    prompt,
                    app_config["model"],
                    float(app_config["ai_timeout_seconds"]),
                )
            analysis = parse_ai_analysis(
                raw,
                provider="ollama",
                model_name=app_config["model"],
                input_summary={
                    "rows": int(df.shape[0]),
                    "columns": int(df.shape[1]),
                    "raw_rows_sent": False,
                    "findings_sent": len(input_summary["findings"]),
                },
                report_json=report_json,
                known_columns=set(map(str, df.columns)),
            )
            return JSONResponse(
                {"analysis": analysis.as_dict(), "status": "ok", "provider": "ollama"}
            )
        except AiResponseValidationError:
            return _safe_http_error(
                502,
                "AI_INVALID_RESPONSE",
                "AI response could not be validated. Deterministic audit results are unchanged.",
            )
        except OllamaError as exc:
            return _safe_http_error(503, "AI_UNAVAILABLE", str(exc))

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
        ctx = _context_from_form(context)

        try:
            contents = await _read_limited_upload(file, limits)
        except IngestionError as exc:
            return _ingestion_error_response(exc)
        try:
            ingested = ingest_table_bytes(contents, filename=file.filename, limits=limits)
        except IngestionError as exc:
            return _ingestion_error_response(exc)

        with tempfile.TemporaryDirectory(prefix="validex-") as tmpdir:
            csv_path = os.path.join(tmpdir, _safe_filename(file.filename))
            report_path = os.path.join(tmpdir, "validity_report.md")
            json_path = os.path.join(tmpdir, "validity_report.json")
            with open(csv_path, "wb") as handle:
                handle.write(contents)
            try:
                report_md = await anyio.to_thread.run_sync(
                    run_audit,
                    csv_path,
                    report_path,
                    json_path,
                    ctx,
                    limits,
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
            df.head(int(app_config["preview_rows"]))
            .where(pd.notnull(df.head(int(app_config["preview_rows"]))), None)
            .values.tolist()
        )

        ai_score_data: dict[str, int | str | None] = {
            "ai_score": None,
            "ai_score_reason": None,
        }

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
        try:
            contents = await _read_limited_upload(file, limits)
        except IngestionError as exc:
            return _ingestion_error_response(exc)
        try:
            ingested = ingest_table_bytes(contents, filename=file.filename, limits=limits)
        except IngestionError as exc:
            return _ingestion_error_response(exc)
        df = ingested.dataframe
        clean_csv = df.to_csv(index=False).encode("utf-8")
        if len(clean_csv) > int(app_config["max_clean_export_bytes"]):
            return _safe_http_error(
                413,
                "CLEAN_EXPORT_TOO_LARGE",
                "Validated CSV export exceeds the configured size limit.",
            )
        clean_csv_b64 = base64.b64encode(clean_csv).decode("utf-8")
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
