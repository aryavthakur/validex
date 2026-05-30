from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any

DEFAULT_CONFIG: dict[str, Any] = {
    "ai_provider": "ollama",
    "ollama_url": "http://localhost:11434",
    "model": "llama3.2:3b",
    "cloud_ai_enabled": False,
    "open_browser": True,
    "host": "127.0.0.1",
    "port": None,
}


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

    config = {**DEFAULT_CONFIG, **existing}
    # Privacy boundary: cloud AI must never be enabled by implicit/default config.
    config["ai_provider"] = "ollama"
    config["cloud_ai_enabled"] = False
    config["host"] = "127.0.0.1"

    path.write_text(json.dumps(config, indent=2) + "\n", encoding="utf-8")
    return config


def save_config(config: dict[str, Any]) -> dict[str, Any]:
    merged = {**DEFAULT_CONFIG, **config}
    merged["ai_provider"] = "ollama"
    merged["cloud_ai_enabled"] = False
    merged["host"] = "127.0.0.1"
    config_path().parent.mkdir(parents=True, exist_ok=True)
    config_path().write_text(json.dumps(merged, indent=2) + "\n", encoding="utf-8")
    return merged
