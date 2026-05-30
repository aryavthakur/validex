from fastapi.testclient import TestClient

from validex.config import DEFAULT_CONFIG
from validex.server import create_app


def test_privacy_status_reports_local_only_ollama():
    app = create_app(config={**DEFAULT_CONFIG, "model": "llama3.2:3b"})
    client = TestClient(app)

    response = client.get("/api/privacy/status")

    assert response.status_code == 200
    assert response.json() == {
        "provider": "ollama",
        "local_only": True,
        "cloud_ai_enabled": False,
        "ollama_url": "http://localhost:11434",
        "model": "llama3.2:3b",
    }


def test_health_route_is_namespaced_and_legacy_compatible():
    app = create_app(config=DEFAULT_CONFIG)
    client = TestClient(app)

    assert client.get("/api/health").json() == {"status": "ok"}
    assert client.get("/health").json() == {"status": "ok"}


def test_packaged_frontend_is_served_when_built():
    app = create_app(config=DEFAULT_CONFIG)
    client = TestClient(app)

    response = client.get("/")

    assert response.status_code == 200
    assert "text/html" in response.headers["content-type"]


def test_ai_analyze_uses_local_ollama_with_structured_summary(monkeypatch):
    prompts = []

    class FakeOllama:
        def __init__(self, base_url):
            self.base_url = base_url

        def generate(self, prompt, model, timeout):
            prompts.append((prompt, model, timeout))
            return "local analysis"

    monkeypatch.setattr("validex.server.OllamaClient", FakeOllama)
    app = create_app(config=DEFAULT_CONFIG)
    client = TestClient(app)

    response = client.post(
        "/api/ai/analyze",
        files={"file": ("dataset.csv", b"metabolite,p_value,log2fc\nA,0.01,1.5\nB,0.20,-0.2\n")},
        data={"question": "What should I check?", "context": "{}"},
    )

    assert response.status_code == 200
    assert response.json() == {"analysis": "local analysis", "status": "ok", "provider": "ollama"}
    prompt, model, timeout = prompts[0]
    assert "DATASET SUMMARY" in prompt
    assert '"columns": ["metabolite", "p_value", "log2fc"]' in prompt
    assert "A,0.01,1.5" not in prompt
    assert model == "llama3.2:3b"
    assert timeout == 90.0


def test_ai_status_reports_local_ollama_without_cloud_calls(monkeypatch):
    calls = []

    class FakeOllama:
        def __init__(self, base_url):
            calls.append(("init", base_url))

        def is_installed(self):
            calls.append(("is_installed",))
            return True

        def health(self):
            calls.append(("health",))
            return {"running": True, "error": None}

        def list_models(self):
            calls.append(("list_models",))
            return ["llama3.2:3b"]

    monkeypatch.setattr("validex.server.OllamaClient", FakeOllama)
    app = create_app(config=DEFAULT_CONFIG)
    client = TestClient(app)

    response = client.get("/api/ai/status")

    assert response.status_code == 200
    assert response.json() == {
        "provider": "ollama",
        "installed": True,
        "running": True,
        "model": "llama3.2:3b",
        "model_installed": True,
        "models": ["llama3.2:3b"],
        "local_only": True,
        "cloud_ai_enabled": False,
        "error": None,
    }
    assert calls == [
        ("init", "http://localhost:11434"),
        ("is_installed",),
        ("health",),
        ("list_models",),
    ]
