from __future__ import annotations

import shutil
import subprocess
from typing import Any

import httpx

from ..config import validate_ollama_url


class OllamaError(RuntimeError):
    pass


class OllamaClient:
    def __init__(
        self,
        base_url: str = "http://localhost:11434",
        timeout: float = 60.0,
        *,
        connect_timeout: float = 5.0,
        read_timeout: float | None = None,
        max_response_bytes: int = 64 * 1024,
    ):
        self.base_url = validate_ollama_url(base_url)
        self.timeout = timeout
        self.connect_timeout = connect_timeout
        self.read_timeout = read_timeout or timeout
        self.max_response_bytes = max_response_bytes

    def _timeout(self, timeout: float | None = None) -> httpx.Timeout:
        read_timeout = timeout or self.read_timeout
        return httpx.Timeout(
            timeout=read_timeout,
            connect=self.connect_timeout,
            read=read_timeout,
            write=min(10.0, read_timeout),
            pool=self.connect_timeout,
        )

    def is_installed(self) -> bool:
        return shutil.which("ollama") is not None

    def require_installed(self) -> None:
        if not self.is_installed():
            raise OllamaError("Ollama is not installed. Install Ollama to use private local AI.")

    def health(self) -> dict[str, Any]:
        try:
            response = httpx.get(f"{self.base_url}/api/tags", timeout=self._timeout(5.0))
            response.raise_for_status()
            return {"running": True, "error": None}
        except Exception as exc:
            return {"running": False, "error": self._safe_error(exc)}

    def tags(self) -> dict[str, Any]:
        try:
            response = httpx.get(f"{self.base_url}/api/tags", timeout=self._timeout(10.0))
            response.raise_for_status()
            self._check_response_size(response)
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
                timeout=self._timeout(timeout or self.timeout),
            )
            response.raise_for_status()
            self._check_response_size(response)
            model_payload = response.json()
            if not isinstance(model_payload, dict):
                raise OllamaError("Local Ollama returned an invalid response.")
            result = model_payload.get("response", "")
            if not isinstance(result, str):
                raise OllamaError("Local Ollama returned a non-text response.")
            return result
        except httpx.TimeoutException as exc:
            raise OllamaError("Local Ollama model timed out.") from exc
        except httpx.HTTPStatusError as exc:
            status_code = exc.response.status_code
            if status_code == 404:
                raise OllamaError("Configured Ollama model is unavailable.") from exc
            if 400 <= status_code < 500:
                raise OllamaError("Ollama rejected the model request.") from exc
            raise OllamaError("Ollama model server failed.") from exc
        except Exception as exc:
            if isinstance(exc, OllamaError):
                raise
            raise OllamaError("Could not generate with local Ollama model.") from exc

    def _check_response_size(self, response: httpx.Response) -> None:
        content = getattr(response, "content", b"")
        if content and len(content) > self.max_response_bytes:
            raise OllamaError("Local Ollama response exceeded the configured size limit.")

    def _safe_error(self, exc: Exception) -> str:
        if isinstance(exc, httpx.TimeoutException):
            return "Ollama request timed out."
        if isinstance(exc, httpx.ConnectError):
            return "Ollama is not reachable."
        if isinstance(exc, httpx.HTTPStatusError):
            return f"Ollama returned HTTP {exc.response.status_code}."
        return "Ollama is unavailable."
