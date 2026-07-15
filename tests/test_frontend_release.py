from __future__ import annotations

import zipfile
import subprocess
import sys
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from validex.config import DEFAULT_CONFIG
from validex.server import create_app


def _write_build_output(root: Path, js: str = "new", css: str = "body{}") -> None:
    (root / "assets").mkdir(parents=True)
    (root / "assets" / "index-new.js").write_text(js, encoding="utf-8")
    (root / "assets" / "index-new.css").write_text(css, encoding="utf-8")
    (root / "index.html").write_text(
        '<script type="module" src="/assets/index-new.js"></script>'
        '<link rel="stylesheet" href="/assets/index-new.css">',
        encoding="utf-8",
    )


def test_validate_build_output_requires_index_and_assets(tmp_path):
    from scripts.frontend_assets import FrontendAssetError, validate_build_output

    build_dir = tmp_path / "dist"
    build_dir.mkdir()

    with pytest.raises(FrontendAssetError, match="index.html"):
        validate_build_output(build_dir)

    (build_dir / "index.html").write_text("<div></div>", encoding="utf-8")
    with pytest.raises(FrontendAssetError, match="/assets/"):
        validate_build_output(build_dir)


def test_sync_static_assets_replaces_stale_files_and_preserves_declared_files(tmp_path):
    from scripts.frontend_assets import sync_static_assets

    source = tmp_path / "dist"
    target = tmp_path / "static"
    _write_build_output(source)
    (target / "assets").mkdir(parents=True)
    (target / "assets" / "index-old.js").write_text("old", encoding="utf-8")
    (target / "package-only.txt").write_text("keep", encoding="utf-8")

    sync_static_assets(source, target, preserve={"package-only.txt"})

    assert (target / "assets" / "index-new.js").read_text(encoding="utf-8") == "new"
    assert not (target / "assets" / "index-old.js").exists()
    assert (target / "package-only.txt").read_text(encoding="utf-8") == "keep"


def test_sync_static_assets_leaves_existing_bundle_intact_when_copy_fails(tmp_path, monkeypatch):
    from scripts import frontend_assets

    source = tmp_path / "dist"
    target = tmp_path / "static"
    _write_build_output(source)
    (target / "assets").mkdir(parents=True)
    (target / "assets" / "index-old.js").write_text("old", encoding="utf-8")
    (target / "index.html").write_text(
        '<script type="module" src="/assets/index-old.js"></script>',
        encoding="utf-8",
    )

    def fail_copy(src, dest, *args, **kwargs):
        raise OSError("simulated copy failure")

    monkeypatch.setattr(frontend_assets.shutil, "copy2", fail_copy)

    with pytest.raises(OSError, match="simulated copy failure"):
        frontend_assets.sync_static_assets(source, target)

    assert (target / "assets" / "index-old.js").read_text(encoding="utf-8") == "old"
    assert not (target / "assets" / "index-new.js").exists()


def test_sync_static_assets_refuses_symlinked_target(tmp_path):
    from scripts.frontend_assets import FrontendAssetError, sync_static_assets

    source = tmp_path / "dist"
    real_target = tmp_path / "real-static"
    symlink_target = tmp_path / "static-link"
    _write_build_output(source)
    real_target.mkdir()
    symlink_target.symlink_to(real_target, target_is_directory=True)

    with pytest.raises(FrontendAssetError, match="symlinked static target"):
        sync_static_assets(source, symlink_target)


def test_sync_static_assets_enforces_protected_parent(tmp_path):
    from scripts.frontend_assets import FrontendAssetError, sync_static_assets

    source = tmp_path / "dist"
    target = tmp_path / "outside" / "static"
    _write_build_output(source)

    with pytest.raises(FrontendAssetError, match="outside"):
        sync_static_assets(source, target, protected_parent=tmp_path / "allowed")


def test_compare_static_trees_reports_changed_extra_and_missing_files(tmp_path):
    from scripts.frontend_assets import compare_trees

    expected = tmp_path / "expected"
    actual = tmp_path / "actual"
    expected.mkdir()
    actual.mkdir()
    (expected / "same.txt").write_text("same", encoding="utf-8")
    (actual / "same.txt").write_text("same", encoding="utf-8")
    (expected / "changed.txt").write_text("expected", encoding="utf-8")
    (actual / "changed.txt").write_text("actual", encoding="utf-8")
    (expected / "missing.txt").write_text("missing", encoding="utf-8")
    (actual / "extra.txt").write_text("extra", encoding="utf-8")

    result = compare_trees(expected, actual)

    assert result.matches is False
    assert result.changed == ["changed.txt"]
    assert result.missing == ["missing.txt"]
    assert result.extra == ["extra.txt"]


def test_compare_static_trees_refuses_symlinks(tmp_path):
    from scripts.frontend_assets import FrontendAssetError, compare_trees

    expected = tmp_path / "expected"
    actual = tmp_path / "actual"
    expected.mkdir()
    actual.mkdir()
    (expected / "target.txt").write_text("target", encoding="utf-8")
    (expected / "link.txt").symlink_to(expected / "target.txt")

    with pytest.raises(FrontendAssetError, match="symlink"):
        compare_trees(expected, actual)


def test_packaged_static_index_references_existing_assets():
    from scripts.frontend_assets import referenced_assets

    static_dir = Path(__file__).resolve().parents[1] / "validex" / "static"
    refs = referenced_assets(static_dir / "index.html")

    assert any(ref.endswith(".js") for ref in refs)
    assert any(ref.endswith(".css") for ref in refs)
    for ref in refs:
        assert (static_dir / ref).is_file(), ref


def test_server_serves_static_with_cache_headers_and_keeps_api_routes_reachable():
    from scripts.frontend_assets import referenced_assets

    app = create_app(config=DEFAULT_CONFIG)
    client = TestClient(app)

    index_response = client.get("/")
    assert index_response.status_code == 200
    assert "text/html" in index_response.headers["content-type"]
    assert "no-cache" in index_response.headers["cache-control"]

    refs = referenced_assets(
        Path(__file__).resolve().parents[1] / "validex" / "static" / "index.html"
    )
    asset_response = client.get("/" + refs[0])
    assert asset_response.status_code == 200
    assert "immutable" in asset_response.headers["cache-control"]

    missing_response = client.get("/assets/does-not-exist.js")
    assert missing_response.status_code == 404
    assert client.get("/api/health").json() == {"status": "ok"}


def test_wheel_static_file_filter_rejects_frontend_development_artifacts(tmp_path):
    from scripts.frontend_assets import inspect_wheel_static_files

    wheel = tmp_path / "validex-0.1.0-py3-none-any.whl"
    with zipfile.ZipFile(wheel, "w") as archive:
        archive.writestr("validex/static/index.html", "<html></html>")
        archive.writestr("validex/static/assets/index-ok.js", "ok")
        archive.writestr("validex/static/node_modules/bad.js", "bad")

    report = inspect_wheel_static_files(wheel)

    assert "validex/static/node_modules/bad.js" in report.forbidden


def test_setup_build_hook_refuses_to_remove_source_static_directory():
    result = subprocess.run(
        [sys.executable, "setup.py", "build_py", "--build-lib", "."],
        cwd=Path(__file__).resolve().parents[1],
        text=True,
        capture_output=True,
        check=False,
    )

    assert result.returncode != 0
    assert "source package static directory" in result.stderr
