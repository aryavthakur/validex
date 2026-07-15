from __future__ import annotations

import json
import os
import re
import shutil
import subprocess
import sys
import tarfile
import tempfile
import zipfile
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, Sequence


REPO_ROOT = Path(__file__).resolve().parents[1]
MAX_ARCHIVE_MEMBER_BYTES = 50 * 1024 * 1024
FORBIDDEN_ARCHIVE_PARTS = {
    ".cache",
    ".git",
    ".mypy_cache",
    ".playwright-cli",
    ".pytest_cache",
    ".ruff_cache",
    ".tox",
    "__pycache__",
    "coverage",
    "dist",
    "node_modules",
}
FORBIDDEN_ARCHIVE_SUFFIXES = {
    ".env",
    ".env.local",
    ".key",
    ".pem",
    ".pyc",
    ".pyo",
    ".swp",
    ".tmp",
}
FORBIDDEN_ARCHIVE_PATTERNS = (
    re.compile(r"(^|/)(pilot|private)(/|$)", re.IGNORECASE),
    re.compile(r"(^|/).*coverage.*", re.IGNORECASE),
)
TEXT_SUFFIXES = {
    ".cfg",
    ".css",
    ".csv",
    ".html",
    ".ini",
    ".js",
    ".json",
    ".md",
    ".py",
    ".toml",
    ".txt",
    ".yaml",
    ".yml",
}
DEVELOPER_PATH_PATTERNS = (
    re.compile(r"/Users/[A-Za-z0-9_.-]+"),
    re.compile(r"/home/[A-Za-z0-9_.-]+"),
    re.compile(r"[A-Za-z]:\\Users\\[A-Za-z0-9_.-]+"),
    re.compile(r"/private/var/folders/"),
    re.compile(r"http://localhost:5173"),
    re.compile(r"http://127\.0\.0\.1:5173"),
)
SECRET_PATTERNS = (
    re.compile(r"sk-[A-Za-z0-9_-]{20,}"),
    re.compile(r"(?i)(api[_-]?key|secret|token)\s*[:=]\s*['\"][A-Za-z0-9_./+=-]{16,}"),
)


class ReleaseCheckError(RuntimeError):
    pass


@dataclass(frozen=True)
class CommandResult:
    name: str
    command: list[str]
    cwd: Path
    returncode: int
    stdout: str
    stderr: str
    required: bool = True

    @property
    def passed(self) -> bool:
        return self.returncode == 0


@dataclass(frozen=True)
class ArchiveInspection:
    path: Path
    files: list[str]
    forbidden_files: list[str]
    text_findings: list[str]

    @property
    def passed(self) -> bool:
        return not self.forbidden_files and not self.text_findings


def run_command(
    name: str,
    command: Sequence[str],
    cwd: Path = REPO_ROOT,
    *,
    required: bool = True,
    env: dict[str, str] | None = None,
) -> CommandResult:
    print(f"\n$ {' '.join(command)}")
    completed = subprocess.run(
        list(command),
        cwd=cwd,
        text=True,
        capture_output=True,
        check=False,
        env={**os.environ, **(env or {})},
    )
    if completed.stdout:
        print(completed.stdout, end="" if completed.stdout.endswith("\n") else "\n")
    if completed.stderr:
        print(completed.stderr, end="" if completed.stderr.endswith("\n") else "\n", file=sys.stderr)
    status = "PASS" if completed.returncode == 0 else ("FAIL" if required else "WARN")
    print(f"[{status}] {name} exited {completed.returncode}")
    return CommandResult(
        name=name,
        command=list(command),
        cwd=cwd,
        returncode=completed.returncode,
        stdout=completed.stdout,
        stderr=completed.stderr,
        required=required,
    )


def assert_required_results(results: Iterable[CommandResult]) -> None:
    failed = [result for result in results if result.required and not result.passed]
    if failed:
        names = ", ".join(result.name for result in failed)
        raise ReleaseCheckError(f"Required release gate(s) failed: {names}")


@dataclass(frozen=True)
class ArchiveMember:
    name: str
    size: int
    is_file: bool
    is_symlink: bool


def _archive_members(path: Path) -> list[ArchiveMember]:
    if path.suffix == ".whl" or path.suffix == ".zip":
        with zipfile.ZipFile(path) as archive:
            members = []
            for info in archive.infolist():
                mode = (info.external_attr >> 16) & 0o170000
                members.append(
                    ArchiveMember(
                        name=info.filename,
                        size=info.file_size,
                        is_file=not info.is_dir(),
                        is_symlink=mode == 0o120000,
                    )
                )
            return members
    if path.name.endswith((".tar.gz", ".tgz")):
        with tarfile.open(path, "r:gz") as archive:
            return [
                ArchiveMember(
                    name=member.name,
                    size=member.size,
                    is_file=member.isfile(),
                    is_symlink=member.issym() or member.islnk(),
                )
                for member in archive.getmembers()
            ]
    raise ReleaseCheckError(f"Unsupported archive type: {path}")


def _archive_names(path: Path) -> list[str]:
    return sorted(member.name for member in _archive_members(path) if member.is_file)


def _read_archive_text(path: Path, name: str) -> str | None:
    if Path(name).suffix not in TEXT_SUFFIXES:
        return None
    try:
        if path.suffix == ".whl" or path.suffix == ".zip":
            with zipfile.ZipFile(path) as archive:
                return archive.read(name).decode("utf-8", errors="ignore")
        with tarfile.open(path, "r:gz") as archive:
            member = archive.extractfile(name)
            if member is None:
                return None
            return member.read().decode("utf-8", errors="ignore")
    except Exception as exc:
        return f"<unreadable text member: {exc}>"


def _is_allowed_text_finding(name: str) -> bool:
    rel = "/".join(Path(name).parts[1:])
    return (
        rel.startswith("tests/")
        or rel in {"scripts/release_checks.py", "scripts/frontend_assets.py"}
    )


def inspect_archive(path: Path) -> ArchiveInspection:
    path = path.resolve()
    members = _archive_members(path)
    names = sorted(member.name for member in members if member.is_file)
    forbidden: list[str] = []
    text_findings: list[str] = []
    seen_names: set[str] = set()
    for member in members:
        if member.name in seen_names:
            forbidden.append(member.name)
        seen_names.add(member.name)
        member_path = Path(member.name)
        if member_path.is_absolute() or any(part == ".." for part in member_path.parts):
            forbidden.append(member.name)
        if member.is_symlink:
            forbidden.append(member.name)
        if member.size > MAX_ARCHIVE_MEMBER_BYTES:
            forbidden.append(member.name)
    for name in names:
        parts = set(Path(name).parts)
        if parts & FORBIDDEN_ARCHIVE_PARTS:
            forbidden.append(name)
        if any(name.endswith(suffix) for suffix in FORBIDDEN_ARCHIVE_SUFFIXES):
            forbidden.append(name)
        if any(pattern.search(name) for pattern in FORBIDDEN_ARCHIVE_PATTERNS):
            forbidden.append(name)
        text = _read_archive_text(path, name)
        if text is None:
            continue
        for pattern in (*DEVELOPER_PATH_PATTERNS, *SECRET_PATTERNS):
            if pattern.search(text) and not _is_allowed_text_finding(name):
                text_findings.append(f"{name}: {pattern.pattern}")
    static_indexes = [
        name for name in names if name.endswith("validex/static/index.html")
    ]
    for index_name in static_indexes:
        index_text = _read_archive_text(path, index_name) or ""
        prefix = index_name.removesuffix("index.html")
        referenced_assets = set(re.findall(r"/assets/(index-[A-Za-z0-9_-]+\.(?:js|css))", index_text))
        packaged_assets = {
            Path(name).name
            for name in names
            if name.startswith(prefix + "assets/index-")
            and name.endswith((".js", ".css"))
        }
        stale_assets = packaged_assets - referenced_assets
        missing_assets = referenced_assets - packaged_assets
        for stale in sorted(stale_assets):
            forbidden.append(prefix + "assets/" + stale)
        for missing in sorted(missing_assets):
            forbidden.append(index_name + f": missing referenced asset {missing}")
    return ArchiveInspection(
        path=path,
        files=names,
        forbidden_files=sorted(set(forbidden)),
        text_findings=sorted(set(text_findings)),
    )


def assert_archive_clean(path: Path) -> ArchiveInspection:
    report = inspect_archive(path)
    print(f"Archive inspection: {path.name} ({len(report.files)} files)")
    if report.forbidden_files:
        print("Forbidden archive entries:")
        for item in report.forbidden_files:
            print(f"  - {item}")
    if report.text_findings:
        print("Forbidden text findings:")
        for item in report.text_findings:
            print(f"  - {item}")
    if not report.passed:
        raise ReleaseCheckError(f"Archive inspection failed for {path}")
    return report


def project_version() -> str:
    import validex

    return validex.__version__


def assert_version_consistency() -> str:
    version = project_version()
    pyproject_text = (REPO_ROOT / "pyproject.toml").read_text(encoding="utf-8")
    if 'version = "0.1.0"' in pyproject_text:
        raise ReleaseCheckError("pyproject.toml still contains a duplicated static version.")
    package_json = json.loads((REPO_ROOT / "frontend" / "package.json").read_text(encoding="utf-8"))
    if package_json.get("version") != version:
        raise ReleaseCheckError(
            f"frontend/package.json version {package_json.get('version')} does not match {version}"
        )
    return version


def assert_git_clean(allow_untracked: set[str] | None = None) -> None:
    allow_untracked = allow_untracked or {".playwright-cli/"}
    result = subprocess.run(
        ["git", "status", "--short"],
        cwd=REPO_ROOT,
        text=True,
        capture_output=True,
        check=False,
    )
    if result.returncode != 0:
        raise ReleaseCheckError(result.stderr.strip() or "git status failed")
    dirty: list[str] = []
    for line in result.stdout.splitlines():
        if line.startswith("?? ") and line[3:] in allow_untracked:
            continue
        dirty.append(line)
    if dirty:
        raise ReleaseCheckError("Worktree has release-relevant changes:\n" + "\n".join(dirty))


def assert_no_forbidden_worktree_artifacts() -> None:
    forbidden_roots = [
        REPO_ROOT / "node_modules",
        REPO_ROOT / "frontend" / "dist",
        REPO_ROOT / "frontend" / "coverage",
    ]
    existing = [str(path.relative_to(REPO_ROOT)) for path in forbidden_roots if path.exists()]
    if existing:
        raise ReleaseCheckError("Forbidden generated worktree artifact(s): " + ", ".join(existing))


def build_artifacts(outdir: Path) -> tuple[Path, Path]:
    outdir.mkdir(parents=True, exist_ok=True)
    result = run_command(
        "build wheel and sdist",
        [sys.executable, "-m", "build", "--wheel", "--sdist", "--outdir", str(outdir)],
    )
    if not result.passed:
        raise ReleaseCheckError("Artifact build failed")
    wheels = sorted(outdir.glob("*.whl"))
    sdists = sorted(outdir.glob("*.tar.gz"))
    if len(wheels) != 1 or len(sdists) != 1:
        raise ReleaseCheckError(f"Expected one wheel and one sdist in {outdir}")
    return wheels[0], sdists[0]


def build_wheel_from_sdist(sdist: Path, outdir: Path) -> Path:
    outdir.mkdir(parents=True, exist_ok=True)
    result = run_command(
        "build wheel from sdist",
        [sys.executable, "-m", "pip", "wheel", str(sdist), "--no-deps", "-w", str(outdir)],
    )
    if not result.passed:
        raise ReleaseCheckError("Building wheel from sdist failed")
    wheels = sorted(outdir.glob("*.whl"))
    if len(wheels) != 1:
        raise ReleaseCheckError(f"Expected one sdist-built wheel in {outdir}")
    return wheels[0]


def wheel_file_hashes(wheel: Path) -> dict[str, str]:
    import hashlib

    hashes: dict[str, str] = {}
    with zipfile.ZipFile(wheel) as archive:
        for name in sorted(n for n in archive.namelist() if not n.endswith("/")):
            hashes[name] = hashlib.sha256(archive.read(name)).hexdigest()
    return hashes


def compare_wheel_contents(first: Path, second: Path) -> list[str]:
    left = wheel_file_hashes(first)
    right = wheel_file_hashes(second)
    differences: list[str] = []
    for name in sorted(set(left) | set(right)):
        if left.get(name) != right.get(name):
            differences.append(name)
    return differences


def smoke_installed_wheel(wheel: Path, label: str) -> None:
    with tempfile.TemporaryDirectory(prefix=f"validex-smoke-{label}-") as tmp:
        tmp_path = Path(tmp)
        venv = tmp_path / "venv"
        run_command(f"{label} create venv", [sys.executable, "-m", "venv", str(venv)])
        python = venv / ("Scripts/python.exe" if os.name == "nt" else "bin/python")
        valid_csv = tmp_path / "valid.csv"
        invalid_csv = tmp_path / "invalid.csv"
        valid_csv.write_text(
            "compound_id,logFC,p_value,FDR,Annotation\nA,1.2,0.01,0.02,Known\n",
            encoding="utf-8",
        )
        invalid_csv.write_text("compound_id,p_value\nA,not-a-number\n", encoding="utf-8")
        commands = [
            [str(python), "-m", "pip", "install", str(wheel)],
            [str(python), "-m", "pip", "check"],
            [
                str(python),
                "-c",
                (
                    "import pathlib,sys,validex;"
                    "root=pathlib.Path(sys.prefix).resolve();"
                    "module=pathlib.Path(validex.__file__).resolve();"
                    "print(validex.__version__); print(module);"
                    "assert root == module or root in module.parents"
                ),
            ],
            [str(python), "-m", "validex.cli", "--help"],
            [str(python), "-m", "validex.cli", "--version"],
            [str(python), "-m", "validex.cli", "audit", str(valid_csv)],
            [str(python), "-m", "validex.cli", "audit", str(invalid_csv)],
            [
                str(python),
                "-c",
                (
                    "import re;"
                    "from fastapi.testclient import TestClient;"
                    "from validex.config import DEFAULT_CONFIG;"
                    "from validex.server import create_app;"
                    "c=TestClient(create_app({**DEFAULT_CONFIG,'ai_enabled':False}));"
                    "index=c.get('/');"
                    "assert index.status_code==200;"
                    "assert c.get('/index.html').status_code==200;"
                    "assert index.headers['Cache-Control']=='no-cache';"
                    "assert index.headers['X-Content-Type-Options']=='nosniff';"
                    "assert '/Users/' not in index.text and 'Traceback' not in index.text;"
                    "assets=re.findall(r'/(assets/[^\"\\']+\\.(?:js|css))', index.text);"
                    "assert any(a.endswith('.js') for a in assets), assets;"
                    "assert any(a.endswith('.css') for a in assets), assets;"
                    "asset_responses=[(asset,c.get('/'+asset)) for asset in assets];"
                    "assert all(r.status_code==200 for _,r in asset_responses), asset_responses;"
                    "assert all('immutable' in r.headers.get('Cache-Control','') for _,r in asset_responses), asset_responses;"
                    "font=c.get('/assets/fonts/subset-PPFraktionMono-Regular.woff2');"
                    "assert font.status_code==200;"
                    "assert font.headers.get('Cache-Control','').startswith('public');"
                    "image=c.get('/assets/images/helix@2x.png');"
                    "assert image.status_code==200;"
                    "assert image.headers.get('Cache-Control','').startswith('public');"
                    "health=c.get('/api/health');"
                    "assert health.json()['status']=='ok' and health.json()['version'];"
                    "assert c.get('/api/privacy/status').status_code==200;"
                    "valid={'file':('valid.csv',b'compound_id,logFC,p_value,FDR,Annotation\\nA,1.2,0.01,0.02,Known\\n','text/csv')};"
                    "invalid={'file':('invalid.csv',b'compound_id,p_value\\nA,not-a-number\\n','text/csv')};"
                    "assert c.post('/audit',files=valid,data={'context':'{}'}).status_code==200;"
                    "bad=c.post('/audit',files=invalid,data={'context':'{}'});"
                    "assert bad.status_code in {200,400,422};"
                    "ai=c.post('/api/ai/analyze',files=valid,data={'context':'{}','question':'x'});"
                    "assert ai.status_code==503 and ai.json()['error_code']=='AI_DISABLED';"
                    "print('installed runtime smoke ok')"
                ),
            ],
        ]
        results = [
            run_command(f"{label} smoke", command, cwd=tmp_path)
            for command in commands
        ]
        assert_required_results(results)


def isolated_python_audit() -> CommandResult:
    return run_command(
        "python dependency audit",
        [sys.executable, "scripts/audit_python_dependencies.py"],
    )


def clean_temp_frontend_checks() -> list[CommandResult]:
    with tempfile.TemporaryDirectory(prefix="validex-clean-frontend-") as tmp:
        frontend_copy = Path(tmp) / "frontend"
        shutil.copytree(
            REPO_ROOT / "frontend",
            frontend_copy,
            ignore=shutil.ignore_patterns("node_modules", "dist", "coverage", ".vite", ".cache"),
        )
        results: list[CommandResult] = []
        install = run_command("clean frontend npm ci", ["npm", "ci"], cwd=frontend_copy)
        results.append(install)
        if not install.passed:
            return results
        lint = run_command("clean frontend lint", ["npm", "run", "lint"], cwd=frontend_copy)
        results.append(lint)
        if not lint.passed:
            return results
        test = run_command("clean frontend tests", ["npm", "test"], cwd=frontend_copy)
        results.append(test)
        if not test.passed:
            return results
        build = run_command(
            "clean frontend build",
            [
                "npm",
                "run",
                "build",
                "--",
                "--outDir",
                str(Path(tmp) / "dist"),
                "--emptyOutDir",
            ],
            cwd=frontend_copy,
        )
        results.append(build)
        if not build.passed:
            return results
        results.append(
            run_command("npm audit", ["npm", "audit", "--audit-level=moderate"], cwd=frontend_copy)
        )
        results.append(
            run_command(
                "npm dependency tree",
                ["npm", "ls", "vite", "esbuild", "@vitejs/plugin-react", "vitest"],
                cwd=frontend_copy,
            )
        )
        return results
