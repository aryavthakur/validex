import json

from validex.config import DEFAULT_CONFIG, load_config


def test_load_config_creates_private_local_defaults(tmp_path, monkeypatch):
    monkeypatch.setenv("VALIDEX_HOME", str(tmp_path))

    config = load_config()

    assert config["ai_provider"] == "ollama"
    assert config["ollama_url"] == "http://localhost:11434"
    assert config["model"] == "llama3.2:3b"
    assert config["cloud_ai_enabled"] is False
    assert config["host"] == "127.0.0.1"
    assert config["port"] is None

    config_path = tmp_path / "config.json"
    assert config_path.exists()
    saved = json.loads(config_path.read_text())
    assert saved == DEFAULT_CONFIG


def test_load_config_merges_existing_values_without_enabling_cloud(tmp_path, monkeypatch):
    monkeypatch.setenv("VALIDEX_HOME", str(tmp_path))
    (tmp_path / "config.json").write_text(json.dumps({"model": "mistral:7b"}))

    config = load_config()

    assert config["model"] == "mistral:7b"
    assert config["ai_provider"] == "ollama"
    assert config["cloud_ai_enabled"] is False
