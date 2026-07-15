#!/usr/bin/env python
from __future__ import annotations

import json
import sys
import tempfile
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[1]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from scripts.release_checks import (  # noqa: E402
    REPO_ROOT,
    ReleaseCheckError,
    assert_archive_clean,
    assert_no_forbidden_worktree_artifacts,
    assert_required_results,
    assert_version_consistency,
    build_artifacts,
    build_wheel_from_sdist,
    clean_temp_frontend_checks,
    compare_wheel_contents,
    isolated_python_audit,
    run_command,
    smoke_installed_wheel,
)


def main() -> int:
    if Path.cwd().resolve() != REPO_ROOT:
        print(f"ERROR: run from repository root: {REPO_ROOT}", file=sys.stderr)
        return 1

    required_results = []
    warnings: list[str] = []
    try:
        print("Validex release-candidate verification")
        print(f"Repository: {REPO_ROOT}")
        print(f"Version: {assert_version_consistency()}")
        assert_no_forbidden_worktree_artifacts()

        required_results.append(run_command("git diff whitespace", ["git", "diff", "--check"]))
        required_results.append(run_command("backend tests", [sys.executable, "-m", "pytest", "-q"]))
        required_results.append(run_command("ruff", ["ruff", "check", "."]))
        required_results.append(run_command("mypy", ["mypy", "validex"]))
        required_results.append(run_command("scientific benchmark", [sys.executable, "benchmarks/run_benchmark.py"]))
        required_results.extend(clean_temp_frontend_checks())
        required_results.append(run_command("frontend static parity", [sys.executable, "scripts/verify_frontend_assets.py"]))
        required_results.append(run_command("performance and limit smoke", [sys.executable, "scripts/performance_smoke.py"]))
        required_results.append(isolated_python_audit())
        required_results.append(
            run_command(
                "external validation",
                [
                    sys.executable,
                    "validation/run_external_validation.py",
                    "--manifest",
                    "validation/manifest.json",
                    "--output",
                    str(Path(tempfile.gettempdir()) / "validex-external-validation.json"),
                ],
            )
        )
        assert_required_results(required_results)

        with tempfile.TemporaryDirectory(prefix="validex-rc-artifacts-") as tmp:
            outdir = Path(tmp) / "dist"
            wheel, sdist = build_artifacts(outdir)
            assert_archive_clean(wheel)
            assert_archive_clean(sdist)
            sdist_wheel = build_wheel_from_sdist(sdist, Path(tmp) / "sdist-wheel")
            assert_archive_clean(sdist_wheel)
            smoke_installed_wheel(wheel, "wheel")
            smoke_installed_wheel(sdist_wheel, "sdist-wheel")

            second_wheel, _ = build_artifacts(Path(tmp) / "dist-second")
            differences = compare_wheel_contents(wheel, second_wheel)
            if differences:
                warnings.append(
                    "Repeated wheel content differs in files: " + ", ".join(differences)
                )
            else:
                print("Repeated wheel content comparison passed.")

        validation_status_path = Path(tempfile.gettempdir()) / "validex-external-validation.json"
        if validation_status_path.is_file():
            data = json.loads(validation_status_path.read_text(encoding="utf-8"))
            if data.get("status") == "EXTERNAL_VALIDATION_INCOMPLETE":
                warnings.append(
                    "External validation is incomplete; Validex remains a research preview."
                )

        if warnings:
            print("\nDocumented warnings:")
            for warning in warnings:
                print(f"WARNING: {warning}")

        if warnings:
            print("Release-candidate verification passed with documented warnings.")
        else:
            print("Release-candidate verification passed.")
        return 0
    except ReleaseCheckError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
