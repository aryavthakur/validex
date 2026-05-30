from __future__ import annotations

import shutil
import subprocess
from typing import Any

import httpx


class OllamaError(RuntimeError):
    pass


class OllamaClient:
    def __init__(self, base_url: str = "http://localhost:11434", timeout: float = 60.0):
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout

    def is_installed(self) -> bool:
        return shutil.which("ollama") is not None

    def require_installed(self) -> None:
        if not self.is_installed():
            raise OllamaError("Ollama is not installed. Install Ollama to use private local AI.")

    def health(self) -> dict[str, Any]:
        try:
            response = httpx.get(f"{self.base_url}/api/tags", timeout=5.0)
            response.raise_for_status()
            return {"running": True, "error": None}
        except Exception as exc:
            return {"running": False, "error": str(exc)}

    def tags(self) -> dict[str, Any]:
        try:
            response = httpx.get(f"{self.base_url}/api/tags", timeout=10.0)
            response.raise_for_status()
            return response.json()
        except Exception as exc:
            raise OllamaError("Ollama is not running at " + self.base_url) from exc

    def model_names_from_tags(self, payload: dict[str, Any]) -> list[str]:
        names: list[str] = []
        for item in payload.get("models", []):
            name = item.get("name") or item.get("model")
            if name:
                names.append(name)
        return names

    def list_models(self) -> list[str]:
        return self.model_names_from_tags(self.tags())

    def has_model(self, model: str) -> bool:
        return model in self.list_models()

    def pull_model(self, model: str) -> None:
        self.require_installed()
        try:
            subprocess.run(["ollama", "pull", model], check=True)
        except subprocess.CalledProcessError as exc:
            raise OllamaError("Failed to pull Ollama model: " + model) from exc

    def generate(self, prompt: str, model: str, timeout: float | None = None) -> str:
        payload = {"model": model, "prompt": prompt, "stream": False}
        try:
            response = httpx.post(
                f"{self.base_url}/api/generate",
                json=payload,
                timeout=timeout or self.timeout,
            )
            response.raise_for_status()
            return response.json().get("response", "")
        except httpx.TimeoutException as exc:
            raise OllamaError("Local Ollama model timed out.") from exc
        except Exception as exc:
            raise OllamaError("Could not generate with local Ollama model.") from exc
