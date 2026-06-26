from __future__ import annotations

import argparse
import os
import socket
import subprocess
import sys
import time
import webbrowser
from typing import Any

import uvicorn

from .ai.ollama_client import OllamaClient, OllamaError
from .audit import audit_dataframe
from .config import config_path, load_config, save_config
from .server import create_app


def _free_port(host: str) -> int:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.bind((host, 0))
        return int(sock.getsockname()[1])


def _confirm(message: str) -> bool:
    answer = input(message + " [Y/n] ").strip().lower()
    return answer in {"", "y", "yes"}


def _install_ollama_guided() -> bool:
    if sys.platform == "darwin":
        if subprocess.run(["which", "brew"], capture_output=True).returncode == 0:
            if _confirm("Ollama is required for private local AI. Install it with Homebrew now?"):
                subprocess.run(["brew", "install", "ollama"], check=True)
                return True
        print("Install Ollama from https://ollama.com/download or with: brew install ollama")
        return False
    print("Install Ollama from https://ollama.com/download, then run validex again.")
    return False


def _start_ollama_service() -> None:
    subprocess.Popen(["ollama", "serve"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)


def _wait_for_ollama(client: OllamaClient, timeout_seconds: float = 10.0) -> bool:
    deadline = time.monotonic() + timeout_seconds
    while time.monotonic() < deadline:
        if client.health()["running"]:
            return True
        time.sleep(0.5)
    return False


def ensure_local_ai(config: dict[str, Any]) -> None:
    client = OllamaClient(config["ollama_url"])
    if not client.is_installed():
        if not _install_ollama_guided():
            raise SystemExit(1)

    health = client.health()
    if not health["running"]:
        print("Ollama is installed but not running.")
        print("Starting Ollama locally with: ollama serve")
        _start_ollama_service()
        if not _wait_for_ollama(client):
            print("Could not confirm Ollama is running at " + config["ollama_url"])
            print("Start it manually with: ollama serve")
            raise SystemExit(1)

    model = config["model"]
    if not client.has_model(model):
        if not _confirm(f"Validex needs local model {model}. This may be a large download. Pull it now?"):
            raise SystemExit(1)
        client.pull_model(model)

    try:
        client.generate("Reply with: ok", model=model, timeout=30.0)
    except OllamaError as exc:
        print("Ollama model check failed: " + str(exc))
        raise SystemExit(1)


def command_status(config: dict[str, Any]) -> int:
    client = OllamaClient(config["ollama_url"])
    installed = client.is_installed()
    health = client.health() if installed else {"running": False, "error": "Ollama is not installed."}
    models = []
    if health["running"]:
        try:
            models = client.list_models()
        except OllamaError:
            models = []
    print("Validex status")
    print(f"Ollama installed: {installed}")
    print(f"Ollama running: {health['running']}")
    print(f"AI provider: Ollama")
    print(f"Model: {config['model']}")
    print(f"Model installed: {config['model'] in models}")
    print("Privacy mode: Local only, no cloud AI")
    return 0


def command_model(args: argparse.Namespace, config: dict[str, Any]) -> int:
    client = OllamaClient(config["ollama_url"])
    try:
        if args.model_command == "list":
            for model in client.list_models():
                print(model)
            return 0
        if args.model_command == "pull":
            client.pull_model(args.model)
            return 0
    except OllamaError as exc:
        print(str(exc))
        return 1
    if args.model_command == "set":
        config["model"] = args.model
        save_config(config)
        print("Selected model: " + args.model)
        return 0
    return 2


def command_config(args: argparse.Namespace, config: dict[str, Any]) -> int:
    if args.config_command == "show":
        print(f"Config: {config_path()}")
        for key in ["ai_provider", "ollama_url", "model", "cloud_ai_enabled", "open_browser", "host", "port"]:
            print(f"{key}: {config.get(key)}")
        return 0
    return 2


def command_audit(args: argparse.Namespace) -> int:
    """Run a schema audit on a CSV file and print results to the terminal."""
    import pandas as pd

    csv_path: str = args.input
    report_path: str | None = getattr(args, "output", None)

    if not os.path.exists(csv_path):
        print(f"Error: file not found: {csv_path}")
        return 1

    df = pd.read_csv(csv_path)
    result = audit_dataframe(df)

    score = result["confidence"]
    confidence = result["audit_confidence"]
    flags = result["flags"]
    detected = result["detected"]

    print(f"Validex score: {score}/100")
    print(f"Audit confidence: {confidence}")
    print()

    # Detected schema
    print("Detected schema:")
    for field, col in detected.items():
        if col is not None:
            print(f"  {field}: {col}")
    missing = [f for f, c in detected.items() if c is None]
    if missing:
        print(f"  Missing: {', '.join(missing)}")
    print()

    # Findings summary
    if flags:
        print("Findings:")
        for flag in flags:
            sev = flag.get("severity", "")
            title = flag.get("title", "")
            print(f"  [{sev}] {title}")
        print()
    else:
        print("Findings: none")
        print()

    # Optionally write report
    if report_path:
        from .audit import run_audit
        report_dir = os.path.dirname(report_path)
        if report_dir:
            os.makedirs(report_dir, exist_ok=True)
        # Derive json path alongside report
        json_path = os.path.splitext(report_path)[0] + ".json"
        run_audit(csv_path=csv_path, report_path=report_path, json_path=json_path)
        print(f"Report written to: {report_path}")

    return 0


def command_run(config: dict[str, Any]) -> int:
    ensure_local_ai(config)
    host = config.get("host") or "127.0.0.1"
    port = int(config["port"] or _free_port(host))
    url = f"http://{host}:{port}"
    app = create_app(config)
    if config.get("open_browser", True):
        webbrowser.open(url)
    print("Validex is running locally.")
    print("App: " + url)
    print("AI provider: Ollama")
    print("Model: " + config["model"])
    print("Privacy mode: Local only, no cloud AI")
    uvicorn.run(app, host=host, port=port, log_level="info")
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="validex", description="Run Validex locally with private Ollama AI.")
    subparsers = parser.add_subparsers(dest="command")
    subparsers.add_parser("status")
    model = subparsers.add_parser("model")
    model_sub = model.add_subparsers(dest="model_command", required=True)
    model_sub.add_parser("list")
    pull = model_sub.add_parser("pull")
    pull.add_argument("model")
    set_model = model_sub.add_parser("set")
    set_model.add_argument("model")
    config = subparsers.add_parser("config")
    config_sub = config.add_subparsers(dest="config_command", required=True)
    config_sub.add_parser("show")
    audit = subparsers.add_parser("audit", help="Audit a metabolomics result CSV.")
    audit.add_argument("input", help="Path to the CSV file to audit.")
    audit.add_argument("--output", "-o", default=None, help="Optional path to write the Markdown report.")
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    config = load_config()
    if args.command == "status":
        return command_status(config)
    if args.command == "model":
        return command_model(args, config)
    if args.command == "config":
        return command_config(args, config)
    if args.command == "audit":
        return command_audit(args)
    return command_run(config)


if __name__ == "__main__":
    raise SystemExit(main())
