from __future__ import annotations

import json
import tarfile
import zipfile
from pathlib import Path

import pytest

from scripts.release_checks import (
    CommandResult,
    ReleaseCheckError,
    assert_archive_clean,
    assert_required_results,
    assert_version_consistency,
    compare_wheel_contents,
    inspect_archive,
    smoke_installed_wheel,
)
from validation.run_external_validation import load_manifest, run_manifest_validation


def test_release_command_failure_propagates():
    results = [
        CommandResult("ok", ["true"], Path.cwd(), 0, "", ""),
        CommandResult("bad", ["false"], Path.cwd(), 1, "", ""),
    ]

    with pytest.raises(ReleaseCheckError, match="bad"):
        assert_required_results(results)


def test_release_command_ignores_warning_failures():
    results = [CommandResult("warn", ["false"], Path.cwd(), 1, "", "", required=False)]

    assert_required_results(results)


def test_wheel_inspection_rejects_forbidden_artifact(tmp_path):
    wheel = tmp_path / "validex-0.1.0-py3-none-any.whl"
    with zipfile.ZipFile(wheel, "w") as archive:
        archive.writestr("validex/__init__.py", "__version__ = '0.1.0'\n")
        archive.writestr("validex/static/node_modules/bad.js", "bad")

    report = inspect_archive(wheel)

    assert "validex/static/node_modules/bad.js" in report.forbidden_files
    with pytest.raises(ReleaseCheckError):
        assert_archive_clean(wheel)


def test_sdist_inspection_rejects_developer_path(tmp_path):
    sdist = tmp_path / "validex-0.1.0.tar.gz"
    payload = tmp_path / "README.md"
    payload.write_text("built from /Users/example/validex\n", encoding="utf-8")
    with tarfile.open(sdist, "w:gz") as archive:
        archive.add(payload, arcname="validex-0.1.0/README.md")

    report = inspect_archive(sdist)

    assert report.text_findings


def test_repeated_build_content_comparison_detects_changed_member(tmp_path):
    first = tmp_path / "first.whl"
    second = tmp_path / "second.whl"
    with zipfile.ZipFile(first, "w") as archive:
        archive.writestr("validex/static/index.html", "one")
    with zipfile.ZipFile(second, "w") as archive:
        archive.writestr("validex/static/index.html", "two")

    assert compare_wheel_contents(first, second) == ["validex/static/index.html"]


def test_archive_inspection_rejects_stale_hashed_asset(tmp_path):
    wheel = tmp_path / "validex-0.1.0-py3-none-any.whl"
    with zipfile.ZipFile(wheel, "w") as archive:
        archive.writestr(
            "validex/static/index.html",
            '<script src="/assets/index-current123.js"></script>',
        )
        archive.writestr("validex/static/assets/index-current123.js", "ok")
        archive.writestr("validex/static/assets/index-stale999.js", "stale")

    report = inspect_archive(wheel)

    assert "validex/static/assets/index-stale999.js" in report.forbidden_files


def test_archive_inspection_rejects_missing_referenced_asset(tmp_path):
    wheel = tmp_path / "validex-0.1.0-py3-none-any.whl"
    with zipfile.ZipFile(wheel, "w") as archive:
        archive.writestr(
            "validex/static/index.html",
            '<script src="/assets/index-missing1.js"></script>',
        )

    report = inspect_archive(wheel)

    assert any("missing referenced asset index-missing1.js" in item for item in report.forbidden_files)


def test_archive_inspection_rejects_unsafe_archive_members(tmp_path):
    sdist = tmp_path / "validex-0.1.0.tar.gz"
    payload = tmp_path / "payload.txt"
    payload.write_text("payload", encoding="utf-8")
    with tarfile.open(sdist, "w:gz") as archive:
        archive.add(payload, arcname="validex-0.1.0/ok.txt")
        archive.add(payload, arcname="../escape.txt")
        info = tarfile.TarInfo("validex-0.1.0/link")
        info.type = tarfile.SYMTYPE
        info.linkname = "ok.txt"
        archive.addfile(info)

    report = inspect_archive(sdist)

    assert "../escape.txt" in report.forbidden_files
    assert "validex-0.1.0/link" in report.forbidden_files


def test_archive_inspection_rejects_duplicate_member(tmp_path):
    wheel = tmp_path / "validex-0.1.0-py3-none-any.whl"
    with zipfile.ZipFile(wheel, "w") as archive:
        archive.writestr("validex/__init__.py", "one")
        archive.writestr("validex/__init__.py", "two")

    report = inspect_archive(wheel)

    assert "validex/__init__.py" in report.forbidden_files


def test_validation_manifest_rejects_required_dataset_without_checksum(tmp_path):
    manifest = tmp_path / "manifest.json"
    manifest.write_text(
        json.dumps(
            {
                "datasets": [
                    {
                        "dataset_id": "BAD",
                        "title": "Bad",
                        "source": "fixture",
                        "version": "1",
                        "license": "MIT",
                        "redistribution_allowed": True,
                        "local_path": "table.csv",
                        "sha256": None,
                        "data_category": "fixture",
                        "expected_schema": {},
                        "ground_truth_source": "test",
                        "preprocessing": [],
                        "enabled_by_default": True,
                        "required_for_release": True,
                        "notes": "",
                    }
                ]
            }
        ),
        encoding="utf-8",
    )

    with pytest.raises(ValueError, match="needs sha256"):
        load_manifest(manifest)


def test_validation_manifest_rejects_path_traversal(tmp_path):
    manifest = tmp_path / "manifest.json"
    manifest.write_text(
        json.dumps(
            {
                "datasets": [
                    {
                        "dataset_id": "BAD",
                        "title": "Bad",
                        "source": "fixture",
                        "version": "1",
                        "license": "not redistributed",
                        "redistribution_allowed": False,
                        "local_path": "../table.csv",
                        "sha256": None,
                        "data_category": "fixture",
                        "expected_schema": {},
                        "ground_truth_source": "test",
                        "preprocessing": [],
                        "enabled_by_default": False,
                        "required_for_release": False,
                        "notes": "",
                    }
                ]
            }
        ),
        encoding="utf-8",
    )

    with pytest.raises(ValueError, match="escapes"):
        load_manifest(manifest)


def test_validation_manifest_rejects_duplicate_dataset_ids(tmp_path):
    manifest = tmp_path / "manifest.json"
    dataset = {
        "dataset_id": "DUPLICATE",
        "title": "Duplicate",
        "source": "fixture",
        "version": "1",
        "license": "not redistributed",
        "redistribution_allowed": False,
        "local_path": None,
        "sha256": None,
        "data_category": "fixture",
        "expected_schema": {},
        "ground_truth_source": "test",
        "preprocessing": [],
        "enabled_by_default": False,
        "required_for_release": False,
        "notes": "",
    }
    manifest.write_text(json.dumps({"datasets": [dataset, dataset]}), encoding="utf-8")

    with pytest.raises(ValueError, match="duplicate dataset_id"):
        load_manifest(manifest)


def test_external_validation_incomplete_status(tmp_path):
    manifest = tmp_path / "manifest.json"
    manifest.write_text(
        json.dumps(
            {
                "datasets": [
                    {
                        "dataset_id": "MISSING_OPTIONAL",
                        "title": "Missing optional",
                        "source": "fixture",
                        "version": "1",
                        "license": "not redistributed",
                        "redistribution_allowed": False,
                        "local_path": None,
                        "sha256": None,
                        "data_category": "independent_external_candidate_unavailable",
                        "expected_schema": {},
                        "ground_truth_source": "none",
                        "preprocessing": [],
                        "enabled_by_default": False,
                        "required_for_release": False,
                        "notes": "",
                    }
                ]
            }
        ),
        encoding="utf-8",
    )

    output = run_manifest_validation(manifest)

    assert output["status"] == "EXTERNAL_VALIDATION_INCOMPLETE"
    assert output["metrics"]["independent_external_dataset_performance"] is None


def test_version_consistency():
    assert assert_version_consistency() == "0.2.0"


def test_installed_wheel_smoke_rejects_missing_static_package(tmp_path):
    wheel = tmp_path / "validex-0.1.0-py3-none-any.whl"
    with zipfile.ZipFile(wheel, "w") as archive:
        archive.writestr("validex/__init__.py", "__version__ = '0.1.0'\n")
        archive.writestr(
            "validex-0.1.0.dist-info/METADATA",
            "Metadata-Version: 2.1\nName: validex\nVersion: 0.1.0\n",
        )
        archive.writestr(
            "validex-0.1.0.dist-info/WHEEL",
            "Wheel-Version: 1.0\nGenerator: test\nRoot-Is-Purelib: true\nTag: py3-none-any\n",
        )
        archive.writestr(
            "validex-0.1.0.dist-info/entry_points.txt",
            "[console_scripts]\nvalidex=validex.cli:main\n",
        )
        archive.writestr("validex-0.1.0.dist-info/RECORD", "")

    with pytest.raises(ReleaseCheckError):
        smoke_installed_wheel(wheel, "missing-static")
