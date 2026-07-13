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
        files={
            "file": (
                "dataset.csv",
                b"metabolite,p_value,log2fc\nA,0.01,1.5\nB,0.20,-0.2\n",
            )
        },
        data={"question": "What should I check?", "context": "{}"},
    )

    assert response.status_code == 200
    assert response.json() == {
        "analysis": "local analysis",
        "status": "ok",
        "provider": "ollama",
    }
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


def test_ai_status_does_not_probe_ollama_when_cli_missing(monkeypatch):
    calls = []

    class FakeOllama:
        def __init__(self, base_url):
            calls.append(("init", base_url))

        def is_installed(self):
            calls.append(("is_installed",))
            return False

        def health(self):
            calls.append(("health",))
            raise AssertionError(
                "health should not be called when Ollama is not installed"
            )

        def list_models(self):
            calls.append(("list_models",))
            raise AssertionError(
                "list_models should not be called when Ollama is not installed"
            )

    monkeypatch.setattr("validex.server.OllamaClient", FakeOllama)
    app = create_app(config=DEFAULT_CONFIG)
    client = TestClient(app)

    response = client.get("/api/ai/status")

    assert response.status_code == 200
    assert response.json() == {
        "provider": "ollama",
        "installed": False,
        "running": False,
        "model": "llama3.2:3b",
        "model_installed": False,
        "models": [],
        "local_only": True,
        "cloud_ai_enabled": False,
        "error": "Ollama is not installed.",
    }
    assert calls == [
        ("init", "http://localhost:11434"),
        ("is_installed",),
    ]


class TestPhase1ApiIngestionErrors:
    def _post_file(self, payload: bytes, filename: str):
        app = create_app(config=DEFAULT_CONFIG)
        client = TestClient(app)
        return client.post(
            "/audit",
            files={"file": (filename, payload, "text/csv")},
            data={"context": "{}"},
        )

    def test_empty_csv_returns_controlled_error(self):
        response = self._post_file(b"", "empty.csv")

        assert response.status_code == 400
        assert response.json()["error_code"] == "EMPTY_FILE"
        assert "traceback" not in response.text.lower()

    def test_duplicate_headers_return_controlled_error(self):
        response = self._post_file(
            b"compound_id,p_value,p_value\nA,0.01,0.02\n", "duplicate.csv"
        )

        assert response.status_code == 422
        assert response.json()["error_code"] == "DUPLICATE_HEADERS"
        assert response.json()["filename"] == "duplicate.csv"

    def test_blank_headers_return_controlled_error(self):
        response = self._post_file(b"compound_id, ,fdr\nA,0.01,0.02\n", "blank.csv")

        assert response.status_code == 422
        assert response.json()["error_code"] == "BLANK_HEADERS"

    def test_malformed_csv_returns_controlled_error(self):
        response = self._post_file(
            b"compound_id,p_value,fdr\nA,0.01,0.02\nB,0.03\n", "malformed.csv"
        )

        assert response.status_code == 400
        assert response.json()["error_code"] == "MALFORMED_CSV"

    def test_invalid_encoding_returns_controlled_error(self):
        response = self._post_file(b"compound_id,p_value\nA,\xff\n", "encoding.csv")

        assert response.status_code == 400
        assert response.json()["error_code"] == "INVALID_ENCODING"

    def test_unsupported_format_returns_controlled_error(self):
        response = self._post_file(b"compound_id,p_value\nA,0.01\n", "study.tsv")

        assert response.status_code == 415
        assert response.json()["error_code"] == "UNSUPPORTED_FORMAT"

    def test_api_response_contains_strict_json_for_nonfinite_input(self):
        response = self._post_file(
            b"compound_id,logFC,p_value,fdr,Annotation\nA,1.0,inf,0.02,confirmed\nB,2.0,0.03,-inf,putative\n",
            "nonfinite.csv",
        )

        assert response.status_code == 200
        response.json()
        assert "Infinity" not in response.text
        assert "NaN" not in response.text

    def test_clean_data_uses_same_ingestion_errors(self):
        app = create_app(config=DEFAULT_CONFIG)
        client = TestClient(app)

        response = client.post(
            "/clean-data",
            files={
                "file": (
                    "duplicate.csv",
                    b"compound_id,p_value,p_value\nA,0.01,0.02\n",
                    "text/csv",
                )
            },
        )

        assert response.status_code == 422
        assert response.json()["error_code"] == "DUPLICATE_HEADERS"


# ---------------------------------------------------------------------------
# /audit endpoint — top-level response shape
# ---------------------------------------------------------------------------


class TestAuditEndpointResponseShape:
    """The /audit endpoint must expose audit_confidence, score, and findings top-level."""

    def _post_csv(self, client, csv_content: str, filename: str = "test.csv"):
        return client.post(
            "/audit",
            files={"file": (filename, csv_content.encode(), "text/csv")},
            data={"context": "{}"},
        )

    def test_audit_response_includes_top_level_audit_confidence(self):
        app = create_app(config=DEFAULT_CONFIG)
        client = TestClient(app)
        csv = "compound_id,logFC,p_value,fdr,Annotation\nM1,1.5,0.01,0.05,confirmed\n"
        response = self._post_csv(client, csv, "complete.csv")
        assert response.status_code == 200
        data = response.json()
        assert "audit_confidence" in data, (
            f"audit_confidence missing from top-level response: {list(data.keys())}"
        )

    def test_audit_response_includes_top_level_score(self):
        app = create_app(config=DEFAULT_CONFIG)
        client = TestClient(app)
        csv = "compound_id,logFC,p_value,fdr,Annotation\nM1,1.5,0.01,0.05,confirmed\n"
        response = self._post_csv(client, csv, "complete.csv")
        assert response.status_code == 200
        data = response.json()
        assert "score" in data, (
            f"score missing from top-level response: {list(data.keys())}"
        )

    def test_audit_response_includes_top_level_findings(self):
        app = create_app(config=DEFAULT_CONFIG)
        client = TestClient(app)
        csv = "compound_id,logFC,p_value,fdr,Annotation\nM1,1.5,0.01,0.05,confirmed\n"
        response = self._post_csv(client, csv, "complete.csv")
        assert response.status_code == 200
        data = response.json()
        assert "findings" in data, (
            f"findings missing from top-level response: {list(data.keys())}"
        )
        assert isinstance(data["findings"], list)

    def test_complete_standard_returns_high_confidence(self):
        app = create_app(config=DEFAULT_CONFIG)
        client = TestClient(app)
        csv = (
            "compound_id,logFC,p_value,fdr,Annotation\n"
            "M1,1.5,0.01,0.05,confirmed\n"
            "M2,-0.3,0.20,0.40,putative\n"
        )
        response = self._post_csv(client, csv, "complete.csv")
        assert response.status_code == 200
        data = response.json()
        assert data["audit_confidence"] == "high", (
            f"Expected 'high' for complete standard input, got {data['audit_confidence']!r}"
        )
        assert data["score"] == 100

    def test_dataset_c_returns_low_confidence(self):
        """Dataset C has no p-value or FDR — must return low confidence."""
        app = create_app(config=DEFAULT_CONFIG)
        client = TestClient(app)
        csv = (
            "compound_id,logFC,Mean_Control,Mean_Case,Annotation\n"
            "M1,1.5,10,15,confirmed\n"
            "M2,-0.3,5,4,putative\n"
        )
        response = self._post_csv(client, csv, "dataset_c.csv")
        assert response.status_code == 200
        data = response.json()
        assert data["audit_confidence"] == "low", (
            f"Expected 'low' for Dataset C input, got {data['audit_confidence']!r}"
        )
        assert data["score"] == 40

    def test_ambiguous_pvalue_returns_medium_confidence(self):
        """Two columns both matching p_value aliases — must return medium confidence."""
        app = create_app(config=DEFAULT_CONFIG)
        client = TestClient(app)
        csv = (
            "compound_id,logFC,p_value,pval,FDR,Annotation\n"
            "M1,1.5,0.01,0.01,0.05,confirmed\n"
            "M2,-0.3,0.20,0.20,0.40,putative\n"
        )
        response = self._post_csv(client, csv, "ambiguous.csv")
        assert response.status_code == 200
        data = response.json()
        assert data["audit_confidence"] == "medium", (
            f"Expected 'medium' for ambiguous p_value input, got {data['audit_confidence']!r}"
        )

    def test_top_level_audit_confidence_matches_report_json(self):
        """Top-level audit_confidence must equal report_json.analysis.audit_confidence."""
        app = create_app(config=DEFAULT_CONFIG)
        client = TestClient(app)
        csv = "compound_id,logFC,p_value,fdr,Annotation\nM1,1.5,0.01,0.05,confirmed\n"
        response = self._post_csv(client, csv, "complete.csv")
        assert response.status_code == 200
        data = response.json()
        report_json_confidence = (
            data.get("report_json", {}).get("analysis", {}).get("audit_confidence")
        )
        assert data["audit_confidence"] == report_json_confidence, (
            f"Top-level audit_confidence {data['audit_confidence']!r} != "
            f"report_json value {report_json_confidence!r}"
        )

    def test_audit_response_still_includes_schema(self):
        app = create_app(config=DEFAULT_CONFIG)
        client = TestClient(app)
        csv = "compound_id,logFC,p_value,fdr,Annotation\nM1,1.5,0.01,0.05,confirmed\n"
        response = self._post_csv(client, csv, "complete.csv")
        assert response.status_code == 200
        data = response.json()
        assert "schema" in data
        assert "canonical_to_original" in data["schema"]

    def test_audit_response_still_includes_report_json(self):
        app = create_app(config=DEFAULT_CONFIG)
        client = TestClient(app)
        csv = "compound_id,logFC,p_value,fdr,Annotation\nM1,1.5,0.01,0.05,confirmed\n"
        response = self._post_csv(client, csv, "complete.csv")
        assert response.status_code == 200
        data = response.json()
        assert "report_json" in data
        assert "analysis" in data["report_json"]
