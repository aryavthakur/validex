import json
import subprocess
from pathlib import Path

import pytest

from validex import cli
from validex.config import load_config


# ---------------------------------------------------------------------------
# audit subcommand
# ---------------------------------------------------------------------------

class TestCliAudit:
    """The 'validex audit <csv>' command must print score and audit_confidence."""

    def _write_csv(self, tmp_path: Path, name: str, content: str) -> str:
        p = tmp_path / name
        p.write_text(content)
        return str(p)

    def test_audit_complete_standard_prints_score(self, tmp_path, capsys):
        csv = self._write_csv(tmp_path, "complete.csv",
            "compound_id,logFC,p_value,fdr,Annotation\n"
            "M1,1.5,0.01,0.05,confirmed\nM2,-0.3,0.20,0.40,putative\n")
        exit_code = cli.main(["audit", csv])
        assert exit_code == 0
        out = capsys.readouterr().out
        assert "Validex score:" in out

    def test_audit_complete_standard_prints_high_confidence(self, tmp_path, capsys):
        csv = self._write_csv(tmp_path, "complete.csv",
            "compound_id,logFC,p_value,fdr,Annotation\n"
            "M1,1.5,0.01,0.05,confirmed\nM2,-0.3,0.20,0.40,putative\n")
        cli.main(["audit", csv])
        out = capsys.readouterr().out
        assert "Audit confidence: high" in out

    def test_audit_dataset_c_prints_low_confidence(self, tmp_path, capsys):
        csv = self._write_csv(tmp_path, "dataset_c.csv",
            "compound_id,logFC,Mean_Control,Mean_Case,Annotation\n"
            "M1,1.5,10,15,confirmed\nM2,-0.3,5,4,putative\n")
        cli.main(["audit", csv])
        out = capsys.readouterr().out
        assert "Audit confidence: low" in out

    def test_audit_dataset_c_prints_score_40(self, tmp_path, capsys):
        csv = self._write_csv(tmp_path, "dataset_c.csv",
            "compound_id,logFC,Mean_Control,Mean_Case,Annotation\n"
            "M1,1.5,10,15,confirmed\nM2,-0.3,5,4,putative\n")
        cli.main(["audit", csv])
        out = capsys.readouterr().out
        assert "Validex score: 40/100" in out

    def test_audit_ambiguous_pvalue_prints_medium_confidence(self, tmp_path, capsys):
        csv = self._write_csv(tmp_path, "ambig.csv",
            "compound_id,logFC,p_value,pval,FDR,Annotation\n"
            "M1,1.5,0.01,0.01,0.05,confirmed\nM2,-0.3,0.20,0.20,0.40,putative\n")
        cli.main(["audit", csv])
        out = capsys.readouterr().out
        assert "Audit confidence: medium" in out

    def test_audit_complete_standard_prints_100(self, tmp_path, capsys):
        csv = self._write_csv(tmp_path, "complete.csv",
            "compound_id,logFC,p_value,fdr,Annotation\n"
            "M1,1.5,0.01,0.05,confirmed\nM2,-0.3,0.20,0.40,putative\n")
        cli.main(["audit", csv])
        out = capsys.readouterr().out
        assert "100/100" in out

    def test_audit_writes_report_file_when_output_given(self, tmp_path, capsys):
        csv = self._write_csv(tmp_path, "complete.csv",
            "compound_id,logFC,p_value,fdr,Annotation\n"
            "M1,1.5,0.01,0.05,confirmed\n")
        report = str(tmp_path / "report.md")
        exit_code = cli.main(["audit", csv, "--output", report])
        assert exit_code == 0
        out = capsys.readouterr().out
        assert "Report written to:" in out
        assert (tmp_path / "report.md").exists()

    def test_audit_missing_file_returns_nonzero(self, tmp_path, capsys):
        exit_code = cli.main(["audit", str(tmp_path / "nonexistent.csv")])
        assert exit_code != 0

    def test_audit_output_includes_findings_section(self, tmp_path, capsys):
        csv = self._write_csv(tmp_path, "dataset_c.csv",
            "compound_id,logFC,Mean_Control,Mean_Case,Annotation\n"
            "M1,1.5,10,15,confirmed\n")
        cli.main(["audit", csv])
        out = capsys.readouterr().out
        assert "Findings:" in out


def test_main_config_show_creates_private_config(tmp_path, monkeypatch, capsys):
    monkeypatch.setenv("VALIDEX_HOME", str(tmp_path))

    exit_code = cli.main(["config", "show"])

    assert exit_code == 0
    output = capsys.readouterr().out
    assert "ai_provider: ollama" in output
    assert "cloud_ai_enabled: False" in output
    saved = json.loads((tmp_path / "config.json").read_text())
    assert saved["model"] == "llama3.2:3b"
    assert saved["host"] == "127.0.0.1"


def test_status_handles_ollama_missing_without_network(monkeypatch, capsys):
    calls = {"health": 0}

    class FakeClient:
        def __init__(self, base_url):
            self.base_url = base_url

        def is_installed(self):
            return False

        def health(self):
            calls["health"] += 1
            return {"running": False, "error": "ollama command not found"}

    monkeypatch.setattr(cli, "OllamaClient", FakeClient)

    exit_code = cli.command_status(load_config())

    assert exit_code == 0
    assert calls["health"] == 0
    output = capsys.readouterr().out
    assert "Ollama installed: False" in output
    assert "Ollama running: False" in output
    assert "Privacy mode: Local only, no cloud AI" in output


def test_start_ollama_service_uses_ollama_serve(monkeypatch):
    calls = []

    class FakePopen:
        def __init__(self, cmd, stdout, stderr):
            calls.append((cmd, stdout, stderr))

    monkeypatch.setattr(subprocess, "Popen", FakePopen)

    cli._start_ollama_service()

    assert calls[0][0] == ["ollama", "serve"]
    assert calls[0][1] == subprocess.DEVNULL
    assert calls[0][2] == subprocess.DEVNULL


def test_ensure_local_ai_starts_service_when_installed_but_not_running(monkeypatch):
    events = []

    class FakeClient:
        def __init__(self, base_url):
            self.health_calls = 0

        def is_installed(self):
            return True

        def health(self):
            self.health_calls += 1
            if self.health_calls == 1:
                return {"running": False, "error": "connection refused"}
            return {"running": True, "error": None}

        def has_model(self, model):
            return True

        def generate(self, prompt, model, timeout):
            return "ok"

    monkeypatch.setattr(cli, "OllamaClient", FakeClient)
    monkeypatch.setattr(cli, "_start_ollama_service", lambda: events.append("started"))

    cli.ensure_local_ai(load_config())

    assert events == ["started"]


def test_ensure_local_ai_prompts_before_missing_model_pull(monkeypatch):
    events = []

    class FakeClient:
        def __init__(self, base_url):
            pass

        def is_installed(self):
            return True

        def health(self):
            return {"running": True, "error": None}

        def has_model(self, model):
            return False

        def pull_model(self, model):
            events.append(("pull", model))

        def generate(self, prompt, model, timeout):
            events.append(("generate", model))
            return "ok"

    monkeypatch.setattr(cli, "OllamaClient", FakeClient)
    monkeypatch.setattr(cli, "_confirm", lambda message: True)

    cli.ensure_local_ai(load_config())

    assert events == [("pull", "llama3.2:3b"), ("generate", "llama3.2:3b")]


def test_ensure_local_ai_aborts_when_missing_model_pull_declined(monkeypatch):
    class FakeClient:
        def __init__(self, base_url):
            pass

        def is_installed(self):
            return True

        def health(self):
            return {"running": True, "error": None}

        def has_model(self, model):
            return False

    monkeypatch.setattr(cli, "OllamaClient", FakeClient)
    monkeypatch.setattr(cli, "_confirm", lambda message: False)

    with pytest.raises(SystemExit):
        cli.ensure_local_ai(load_config())


def test_model_list_prints_clean_error_when_ollama_is_unavailable(monkeypatch, capsys):
    class FakeClient:
        def __init__(self, base_url):
            pass

        def list_models(self):
            raise cli.OllamaError("Ollama is not running at http://localhost:11434")

    args = type("Args", (), {"model_command": "list"})()
    monkeypatch.setattr(cli, "OllamaClient", FakeClient)

    exit_code = cli.command_model(args, load_config())

    assert exit_code == 1
    assert "Ollama is not running at http://localhost:11434" in capsys.readouterr().out
