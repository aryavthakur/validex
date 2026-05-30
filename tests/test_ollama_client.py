import subprocess

import pytest

from validex.ai.ollama_client import OllamaClient, OllamaError


def test_list_models_normalizes_ollama_tags_response():
    client = OllamaClient()
    payload = {"models": [{"name": "llama3.2:3b"}, {"model": "mistral:7b"}]}

    assert client.model_names_from_tags(payload) == ["llama3.2:3b", "mistral:7b"]


def test_pull_model_uses_ollama_cli_with_requested_model(monkeypatch):
    calls = []

    def fake_run(cmd, check):
        calls.append((cmd, check))
        return subprocess.CompletedProcess(cmd, 0)

    monkeypatch.setattr(subprocess, "run", fake_run)
    monkeypatch.setattr(OllamaClient, "is_installed", lambda self: True)

    OllamaClient().pull_model("llama3.2:3b")

    assert calls == [(["ollama", "pull", "llama3.2:3b"], True)]


def test_generate_posts_to_localhost_ollama(monkeypatch):
    calls = []

    class FakeResponse:
        def raise_for_status(self):
            return None

        def json(self):
            return {"response": "ok"}

    def fake_post(url, json, timeout):
        calls.append((url, json, timeout))
        return FakeResponse()

    monkeypatch.setattr("httpx.post", fake_post)

    result = OllamaClient("http://localhost:11434").generate("hello", model="llama3.2:3b", timeout=12.0)

    assert result == "ok"
    assert calls == [
        (
            "http://localhost:11434/api/generate",
            {"model": "llama3.2:3b", "prompt": "hello", "stream": False},
            12.0,
        )
    ]


def test_pull_model_reports_clear_failure(monkeypatch):
    def fake_run(cmd, check):
        raise subprocess.CalledProcessError(1, cmd)

    monkeypatch.setattr(subprocess, "run", fake_run)
    monkeypatch.setattr(OllamaClient, "is_installed", lambda self: True)

    with pytest.raises(OllamaError, match="Failed to pull Ollama model: llama3.2:3b"):
        OllamaClient().pull_model("llama3.2:3b")


def test_require_installed_reports_clear_error_when_ollama_missing(monkeypatch):
    monkeypatch.setattr("shutil.which", lambda command: None)

    with pytest.raises(OllamaError, match="Ollama is not installed. Install Ollama to use private local AI."):
        OllamaClient().require_installed()
