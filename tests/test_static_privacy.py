from pathlib import Path


def _join(parts: list[str]) -> str:
    return "".join(parts)


FORBIDDEN_BUNDLE_STRINGS = [
    ["validex-6zfp.on", "ren", "der.com"],
    ["ren", "der", ".com"],
    ["api.", "op", "enai"],
    ["api.", "gr", "oq"],
    ["open", "router.ai"],
    ["anth", "ropic.com"],
]


def _static_text() -> str:
    static_dir = Path(__file__).resolve().parents[1] / "validex" / "static"
    chunks: list[str] = []
    for path in static_dir.rglob("*"):
        if path.suffix in {".js", ".html", ".css"}:
            chunks.append(path.read_text(encoding="utf-8"))
    return "\n".join(chunks)


def test_packaged_frontend_bundle_has_no_hosted_backend_url():
    text = _static_text()

    assert _join(["validex-6zfp.on", "ren", "der.com"]) not in text


def test_packaged_frontend_bundle_has_no_remote_ai_provider_urls():
    text = _static_text().lower()

    for forbidden in FORBIDDEN_BUNDLE_STRINGS:
        assert _join(forbidden) not in text


def test_packaged_frontend_uses_same_origin_api_paths():
    text = _static_text()

    assert "/api/privacy/status" in text
    assert "/api/ai/status" in text
    assert "/audit" in text
