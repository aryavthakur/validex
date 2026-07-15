from __future__ import annotations

import argparse
import filecmp
import hashlib
import os
import uuid
import shutil
import subprocess
import sys
import tempfile
import zipfile
from dataclasses import dataclass
from html.parser import HTMLParser
from pathlib import Path
from typing import Iterable


REPO_ROOT = Path(__file__).resolve().parents[1]
FRONTEND_DIR = REPO_ROOT / "frontend"
STATIC_DIR = REPO_ROOT / "validex" / "static"
FRONTEND_EXCLUDES = {
    "node_modules",
    "dist",
    "coverage",
    ".vite",
    ".cache",
    ".env.local",
    ".DS_Store",
}
FORBIDDEN_STATIC_PARTS = {
    "node_modules",
    "coverage",
    ".vite",
    ".cache",
    "__tests__",
    ".env.local",
}
FORBIDDEN_STATIC_SUFFIXES = {
    ".map",
    ".test.js",
    ".test.jsx",
    ".spec.js",
    ".spec.jsx",
}
PRESERVED_STATIC_FILES: frozenset[str] = frozenset()


class FrontendAssetError(RuntimeError):
    pass


@dataclass(frozen=True)
class TreeComparison:
    missing: list[str]
    extra: list[str]
    changed: list[str]

    @property
    def matches(self) -> bool:
        return not self.missing and not self.extra and not self.changed

    def format(self) -> str:
        if self.matches:
            return "validex/static matches the current frontend production build."
        lines = ["validex/static does not match the current frontend production build."]
        if self.missing:
            lines.append("Missing from validex/static:")
            lines.extend(f"  - {item}" for item in self.missing)
        if self.extra:
            lines.append("Extra in validex/static:")
            lines.extend(f"  - {item}" for item in self.extra)
        if self.changed:
            lines.append("Changed content:")
            lines.extend(f"  - {item}" for item in self.changed)
        return "\n".join(lines)


@dataclass(frozen=True)
class WheelStaticReport:
    static_files: list[str]
    forbidden: list[str]


class _AssetReferenceParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.references: list[str] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        attr_map = dict(attrs)
        for name in ("src", "href"):
            value = attr_map.get(name)
            if value and value.startswith("/"):
                self.references.append(value.lstrip("/"))


def _relative_files(root: Path) -> list[str]:
    if not root.is_dir():
        raise FrontendAssetError(f"Directory does not exist: {root}")
    paths: list[str] = []
    for path in root.rglob("*"):
        if path.is_symlink():
            raise FrontendAssetError(f"Refusing to process symlink: {path}")
        if path.is_file():
            paths.append(path.relative_to(root).as_posix())
    return sorted(paths)


def _ensure_inside(path: Path, expected_parent: Path) -> Path:
    resolved = path.resolve()
    parent = expected_parent.resolve()
    if resolved != parent and parent not in resolved.parents:
        raise FrontendAssetError(f"Refusing path outside {parent}: {resolved}")
    return resolved


def referenced_assets(index_html: Path) -> list[str]:
    if not index_html.is_file():
        raise FrontendAssetError(f"Missing index.html: {index_html}")
    parser = _AssetReferenceParser()
    parser.feed(index_html.read_text(encoding="utf-8"))
    refs = [
        ref
        for ref in parser.references
        if not ref.startswith(("http://", "https://", "data:"))
    ]
    return sorted(dict.fromkeys(refs))


def validate_build_output(build_dir: Path) -> None:
    build_dir = build_dir.resolve()
    index = build_dir / "index.html"
    if not index.is_file():
        raise FrontendAssetError(f"Frontend build output is missing index.html: {index}")
    refs = referenced_assets(index)
    if not refs:
        raise FrontendAssetError(
            "Frontend build index.html does not reference any /assets/ files."
        )
    if not any(ref.startswith("assets/") and ref.endswith(".js") for ref in refs):
        raise FrontendAssetError("Frontend build index.html is missing a /assets/ JavaScript reference.")
    if not any(ref.startswith("assets/") and ref.endswith(".css") for ref in refs):
        raise FrontendAssetError("Frontend build index.html is missing a /assets/ CSS reference.")
    for rel in refs:
        if rel.startswith("/"):
            raise FrontendAssetError(f"Unexpected absolute relative asset path: {rel}")
        asset = build_dir / rel
        if not asset.is_file():
            raise FrontendAssetError(f"Frontend build references missing asset: {rel}")
    for rel in _relative_files(build_dir):
        path = Path(rel)
        if any(part in FORBIDDEN_STATIC_PARTS for part in path.parts):
            raise FrontendAssetError(f"Forbidden development artifact in build output: {rel}")
        if any(rel.endswith(suffix) for suffix in FORBIDDEN_STATIC_SUFFIXES):
            raise FrontendAssetError(f"Forbidden source map or test artifact in build output: {rel}")
    text = "\n".join(
        (build_dir / rel).read_text(encoding="utf-8", errors="ignore")
        for rel in _relative_files(build_dir)
        if Path(rel).suffix in {".html", ".js", ".css"}
    )
    forbidden_text = [str(REPO_ROOT), str(Path.home()), "http://localhost:5173", "http://127.0.0.1:5173"]
    for item in forbidden_text:
        if item and item in text:
            raise FrontendAssetError(f"Forbidden local path or development URL found in build output: {item}")


def compare_trees(expected: Path, actual: Path, preserve: Iterable[str] = PRESERVED_STATIC_FILES) -> TreeComparison:
    expected = expected.resolve()
    actual = actual.resolve()
    preserve_set = {Path(item).as_posix() for item in preserve}
    expected_files = set(_relative_files(expected))
    actual_files = set(_relative_files(actual)) - preserve_set
    missing = sorted(expected_files - actual_files)
    extra = sorted(actual_files - expected_files)
    changed = sorted(
        rel
        for rel in expected_files & actual_files
        if not filecmp.cmp(expected / rel, actual / rel, shallow=False)
    )
    return TreeComparison(missing=missing, extra=extra, changed=changed)


def _remove_path(path: Path) -> None:
    if path.is_symlink():
        raise FrontendAssetError(f"Refusing to remove symlink: {path}")
    if path.is_dir():
        for child in path.iterdir():
            _remove_path(child)
        path.rmdir()
    else:
        path.unlink()


def sync_static_assets(
    source: Path,
    target: Path,
    preserve: Iterable[str] = PRESERVED_STATIC_FILES,
    protected_parent: Path | None = None,
) -> None:
    source = source.resolve()
    if target.is_symlink():
        raise FrontendAssetError(f"Refusing to replace symlinked static target: {target}")
    target = (
        _ensure_inside(target, protected_parent)
        if protected_parent is not None
        else target.resolve()
    )
    validate_build_output(source)
    target.parent.mkdir(parents=True, exist_ok=True)
    preserve_set = {Path(item).as_posix() for item in preserve}
    source_files = set(_relative_files(source))
    target_files = set(_relative_files(target)) if target.exists() else set()
    stage = target.parent / f".{target.name}.stage-{uuid.uuid4().hex}"
    backup = target.parent / f".{target.name}.backup-{uuid.uuid4().hex}"
    try:
        stage.mkdir()
        for rel in sorted(source_files):
            src = source / rel
            dest = stage / rel
            dest.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(src, dest)
        for rel in sorted(preserve_set & target_files):
            src = target / rel
            dest = stage / rel
            dest.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(src, dest)
        validate_build_output(stage)
        if target.exists():
            target.rename(backup)
        try:
            stage.rename(target)
        except Exception:
            if backup.exists() and not target.exists():
                backup.rename(target)
            raise
    finally:
        for leftover in (stage, backup):
            if leftover.exists():
                _remove_path(leftover)

    for rel in sorted(set(_relative_files(target)) - source_files - preserve_set):
        path = target / rel
        if path.exists():
            _remove_path(path)

    for directory in sorted((path for path in target.rglob("*") if path.is_dir()), reverse=True):
        if not any(directory.iterdir()):
            directory.rmdir()

def _ignore_frontend_copy(directory: str, names: list[str]) -> set[str]:
    return {name for name in names if name in FRONTEND_EXCLUDES}


def _assert_no_source_symlinks(root: Path) -> None:
    for current, dirs, files in os.walk(root):
        dirs[:] = [name for name in dirs if name not in FRONTEND_EXCLUDES]
        for name in dirs + files:
            path = Path(current) / name
            if path.is_symlink():
                raise FrontendAssetError(f"Refusing to copy frontend symlink: {path}")


def build_frontend_in_workspace(workspace: Path, repo_root: Path = REPO_ROOT) -> Path:
    frontend_dir = repo_root / "frontend"
    lockfile = frontend_dir / "package-lock.json"
    if not lockfile.is_file():
        raise FrontendAssetError("frontend/package-lock.json is required for reproducible npm ci builds.")
    _assert_no_source_symlinks(frontend_dir)
    workspace.mkdir(parents=True, exist_ok=True)
    frontend_copy = workspace / "frontend"
    output_dir = workspace / "dist"
    shutil.copytree(frontend_dir, frontend_copy, ignore=_ignore_frontend_copy)
    install_env = {**os.environ, "NODE_ENV": "development"}
    build_env = {**os.environ, "NODE_ENV": "production"}
    subprocess.run(["npm", "ci"], cwd=frontend_copy, check=True, env=install_env)
    subprocess.run(
        ["npm", "run", "build", "--", "--outDir", str(output_dir), "--emptyOutDir"],
        cwd=frontend_copy,
        check=True,
        env=build_env,
    )
    validate_build_output(output_dir)
    return output_dir


def build_and_sync() -> None:
    with tempfile.TemporaryDirectory(prefix="validex-frontend-build-") as tmp:
        build_dir = build_frontend_in_workspace(Path(tmp), REPO_ROOT)
        sync_static_assets(build_dir, STATIC_DIR, protected_parent=REPO_ROOT / "validex")


def verify_static_matches_build() -> TreeComparison:
    with tempfile.TemporaryDirectory(prefix="validex-frontend-build-") as tmp:
        build_dir = build_frontend_in_workspace(Path(tmp), REPO_ROOT)
        result = compare_trees(build_dir, STATIC_DIR)
        if not result.matches:
            raise FrontendAssetError(result.format())
        return result


def inspect_wheel_static_files(wheel_path: Path) -> WheelStaticReport:
    forbidden: list[str] = []
    static_files: list[str] = []
    with zipfile.ZipFile(wheel_path) as archive:
        for name in sorted(archive.namelist()):
            if not name.startswith("validex/static/") or name.endswith("/"):
                continue
            static_files.append(name)
            rel = name.removeprefix("validex/static/")
            path = Path(rel)
            if any(part in FORBIDDEN_STATIC_PARTS for part in path.parts):
                forbidden.append(name)
            if any(rel.endswith(suffix) for suffix in FORBIDDEN_STATIC_SUFFIXES):
                forbidden.append(name)
    return WheelStaticReport(static_files=static_files, forbidden=sorted(set(forbidden)))


def file_sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Build or verify packaged Validex frontend assets.")
    parser.add_argument("command", choices=["build", "verify"])
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        if args.command == "build":
            build_and_sync()
            print("Built frontend with npm ci and synchronized validex/static.")
        else:
            result = verify_static_matches_build()
            print(result.format())
        return 0
    except (FrontendAssetError, subprocess.CalledProcessError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
