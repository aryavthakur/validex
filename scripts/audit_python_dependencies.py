#!/usr/bin/env python
from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
POLICY_PATH = REPO_ROOT / "docs" / "dependency_audit_policy.json"


def _run(command: list[str], cwd: Path = REPO_ROOT) -> subprocess.CompletedProcess[str]:
    print(f"$ {' '.join(command)}")
    result = subprocess.run(command, cwd=cwd, text=True, capture_output=True, check=False)
    if result.stdout:
        print(result.stdout, end="" if result.stdout.endswith("\n") else "\n")
    if result.stderr:
        print(result.stderr, end="" if result.stderr.endswith("\n") else "\n", file=sys.stderr)
    return result


def _policy() -> dict[str, object]:
    if not POLICY_PATH.is_file():
        return {"ignored_advisories": []}
    return json.loads(POLICY_PATH.read_text(encoding="utf-8"))


def _validate_policy() -> None:
    policy = _policy()
    ignored = policy.get("ignored_advisories", [])
    if not isinstance(ignored, list):
        raise ValueError("ignored_advisories must be a list")
    required = {
        "id",
        "package",
        "version",
        "reason",
        "reachability",
        "expires",
        "owner",
        "classification",
    }
    for item in ignored:
        if not isinstance(item, dict):
            raise ValueError("Each ignored advisory must be an object")
        missing = sorted(required - set(item))
        if missing:
            raise ValueError(f"Ignored advisory is missing fields: {missing}")


def main() -> int:
    try:
        _validate_policy()
    except ValueError as exc:
        print(f"ERROR: invalid dependency audit policy: {exc}", file=sys.stderr)
        return 1

    with tempfile.TemporaryDirectory(prefix="validex-python-audit-") as tmp:
        venv = Path(tmp) / "venv"
        create = _run([sys.executable, "-m", "venv", str(venv)])
        if create.returncode:
            return create.returncode
        python = venv / ("Scripts/python.exe" if os.name == "nt" else "bin/python")
        upgrade_pip = _run([str(python), "-m", "pip", "install", "--upgrade", "pip==26.1.2"])
        if upgrade_pip.returncode:
            return upgrade_pip.returncode
        install = _run([str(python), "-m", "pip", "install", "-c", "requirements-dev.txt", ".[dev,audit]"])
        if install.returncode:
            return install.returncode
        check = _run([str(python), "-m", "pip", "check"])
        if check.returncode:
            return check.returncode
        output = Path(tmp) / "pip-audit.json"
        audit = _run([str(python), "-m", "pip_audit", "--format", "json", "--output", str(output)])
        if audit.returncode:
            if output.is_file():
                print(output.read_text(encoding="utf-8"))
            return audit.returncode
        data = json.loads(output.read_text(encoding="utf-8"))
        vulnerabilities = [
            vuln
            for dep in data.get("dependencies", [])
            for vuln in dep.get("vulns", [])
        ]
        if vulnerabilities:
            print(json.dumps(data, indent=2))
            return 1
        print("Python dependency audit passed with no vulnerabilities.")
        return 0


if __name__ == "__main__":
    raise SystemExit(main())
