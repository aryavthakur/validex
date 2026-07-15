from __future__ import annotations

import json
import os
import ipaddress
from pathlib import Path
from typing import Any
from urllib.parse import urlparse


DEFAULT_CONFIG: dict[str, Any] = {
    "ai_provider": "ollama",
    "ollama_url": "http://localhost:11434",
    "model": "llama3.2:3b",
    "ai_enabled": True,
    "cloud_ai_enabled": False,
    "open_browser": True,
    "host": "127.0.0.1",
    "port": None,
    "cors_origins": ["http://127.0.0.1:*", "http://localhost:*"],
    "max_upload_bytes": 50 * 1024 * 1024,
    "max_rows": 100_000,
    "max_columns": 500,
    "max_total_cells": 5_000_000,
    "max_cell_length": 20_000,
    "max_header_length": 300,
    "preview_rows": 100,
    "max_report_chars": 250_000,
    "max_clean_export_bytes": 20 * 1024 * 1024,
    "ai_max_columns": 80,
    "ai_max_findings": 30,
    "ai_max_examples": 0,
    "ai_max_column_name_length": 120,
    "ai_max_context_chars": 2000,
    "ai_max_question_chars": 1000,
    "ai_max_prompt_chars": 16000,
    "ai_timeout_seconds": 60.0,
    "ai_connect_timeout_seconds": 5.0,
    "ai_read_timeout_seconds": 60.0,
    "ai_max_response_bytes": 64 * 1024,
    "ai_max_concurrent_requests": 2,
}


def _as_int(config: dict[str, Any], key: str, minimum: int, maximum: int) -> int:
    value = config.get(key, DEFAULT_CONFIG[key])
    if isinstance(value, bool):
        raise ValueError(f"{key} must be an integer.")
    try:
        parsed = int(value)
    except (TypeError, ValueError) as exc:
        raise ValueError(f"{key} must be an integer.") from exc
    if parsed < minimum or parsed > maximum:
        raise ValueError(f"{key} must be between {minimum} and {maximum}.")
    return parsed


def _as_float(config: dict[str, Any], key: str, minimum: float, maximum: float) -> float:
    value = config.get(key, DEFAULT_CONFIG[key])
    if isinstance(value, bool):
        raise ValueError(f"{key} must be a number.")
    try:
        parsed = float(value)
    except (TypeError, ValueError) as exc:
        raise ValueError(f"{key} must be a number.") from exc
    if parsed < minimum or parsed > maximum:
        raise ValueError(f"{key} must be between {minimum} and {maximum}.")
    return parsed


def classify_provider_host(url: str) -> str:
    parsed = urlparse(url)
    host = (parsed.hostname or "").lower()
    if host == "localhost":
        return "loopback"
    try:
        address = ipaddress.ip_address(host)
    except ValueError:
        return "remote"
    if address.is_loopback:
        return "loopback"
    if address.is_private:
        return "private-network"
    return "remote"


def validate_ollama_url(url: str) -> str:
    parsed = urlparse(str(url))
    if parsed.scheme not in {"http", "https"}:
        raise ValueError("ollama_url must use http or https.")
    if not parsed.hostname:
        raise ValueError("ollama_url must include a host.")
    if parsed.username or parsed.password:
        raise ValueError("ollama_url must not include credentials.")
    if parsed.hostname in {"169.254.169.254", "metadata.google.internal"}:
        raise ValueError("ollama_url must not target metadata services.")
    if parsed.path not in {"", "/"} or parsed.query or parsed.fragment:
        raise ValueError("ollama_url must be an origin URL without path, query, or fragment.")
    return url.rstrip("/")


def validate_config(config: dict[str, Any]) -> dict[str, Any]:
    merged = {**DEFAULT_CONFIG, **config}
    merged["ai_provider"] = "ollama"
    merged["cloud_ai_enabled"] = False
    merged["ollama_url"] = validate_ollama_url(str(merged["ollama_url"]))
    merged["model"] = str(merged["model"]).strip()
    if not merged["model"] or len(merged["model"]) > 120:
        raise ValueError("model must be a non-empty string up to 120 characters.")
    merged["host"] = str(merged.get("host") or "127.0.0.1")
    if merged["host"] != "127.0.0.1":
        raise ValueError("host must remain 127.0.0.1 unless remote exposure is explicitly implemented.")
    port = merged.get("port")
    merged["port"] = None if port in {None, ""} else _as_int(merged, "port", 1, 65535)
    for key, minimum, maximum in [
        ("max_upload_bytes", 1, 500 * 1024 * 1024),
        ("max_rows", 1, 2_000_000),
        ("max_columns", 1, 10_000),
        ("max_total_cells", 1, 20_000_000),
        ("max_cell_length", 1, 1_000_000),
        ("max_header_length", 1, 10_000),
        ("preview_rows", 0, 1000),
        ("max_report_chars", 1000, 5_000_000),
        ("max_clean_export_bytes", 1, 200 * 1024 * 1024),
        ("ai_max_columns", 1, 1000),
        ("ai_max_findings", 0, 500),
        ("ai_max_examples", 0, 10),
        ("ai_max_column_name_length", 1, 1000),
        ("ai_max_context_chars", 0, 20_000),
        ("ai_max_question_chars", 1, 10_000),
        ("ai_max_prompt_chars", 1000, 200_000),
        ("ai_max_response_bytes", 1000, 5 * 1024 * 1024),
        ("ai_max_concurrent_requests", 1, 16),
    ]:
        merged[key] = _as_int(merged, key, minimum, maximum)
    for key in [
        "ai_timeout_seconds",
        "ai_connect_timeout_seconds",
        "ai_read_timeout_seconds",
    ]:
        merged[key] = _as_float(merged, key, 0.1, 600.0)
    merged["ai_enabled"] = bool(merged.get("ai_enabled", True))
    merged["open_browser"] = bool(merged.get("open_browser", True))
    return merged


def config_dir() -> Path:
    override = os.environ.get("VALIDEX_HOME")
    if override:
        return Path(override).expanduser()
    return Path.home() / ".validex"


def config_path() -> Path:
    return config_dir() / "config.json"


def load_config() -> dict[str, Any]:
    path = config_path()
    path.parent.mkdir(parents=True, exist_ok=True)

    if path.exists():
        try:
            existing = json.loads(path.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            existing = {}
    else:
        existing = {}

    existing["host"] = "127.0.0.1"
    config = validate_config(existing)

    path.write_text(json.dumps(config, indent=2) + "\n", encoding="utf-8")
    return config


def save_config(config: dict[str, Any]) -> dict[str, Any]:
    merged = validate_config(config)
    config_path().parent.mkdir(parents=True, exist_ok=True)
    config_path().write_text(json.dumps(merged, indent=2) + "\n", encoding="utf-8")
    return merged
