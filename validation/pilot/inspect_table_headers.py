#!/usr/bin/env python
"""Inspect table headers for pilot validation candidates.

Prints the header row and a truncated preview of the first rows of a CSV,
TSV, or XLSX file without modifying the source. Optionally converts a
selected XLSX sheet to CSV for local inspection.

Usage:
    python validation/pilot/inspect_table_headers.py path/to/table.csv
    python validation/pilot/inspect_table_headers.py path/to/table.tsv
    python validation/pilot/inspect_table_headers.py path/to/table.xlsx
    python validation/pilot/inspect_table_headers.py path/to/table.xlsx --sheet Sheet1
    python validation/pilot/inspect_table_headers.py path/to/table.xlsx --sheet Sheet1 \\
        --output validation/pilot/tables/PILOT_001.csv

IMPORTANT: This script does not download files or write extracted data unless
--output is explicitly provided. Source files are never modified.

Dependencies:
    - pandas (in pyproject.toml) — required for all formats
    - openpyxl — required for XLSX files only; NOT in pyproject.toml.
      Install manually: pip install openpyxl
      CSV and TSV files work without openpyxl.
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

import pandas as pd


_PREVIEW_ROWS = 5
_MAX_CELL_WIDTH = 80


def detect_format(path: Path) -> str:
    """Return 'csv', 'tsv', or 'xlsx' based on file extension."""
    suffix = path.suffix.lower()
    if suffix == ".csv":
        return "csv"
    if suffix in (".tsv", ".txt"):
        return "tsv"
    if suffix in (".xlsx", ".xls"):
        return "xlsx"
    # Default: attempt CSV
    return "csv"


def _require_openpyxl() -> None:
    """Exit with a clear message if openpyxl is not installed."""
    try:
        import openpyxl  # noqa: F401
    except ImportError:
        print(
            "ERROR: openpyxl is required to read XLSX files.\n"
            "Install it with: pip install openpyxl\n"
            "(openpyxl is not in pyproject.toml — install it manually in your environment.)",
            file=sys.stderr,
        )
        sys.exit(1)


def _read_xlsx(path: Path, sheet: str | None) -> tuple[pd.DataFrame, str]:
    """Read a sheet from an XLSX file. Returns (DataFrame, sheet_name_used)."""
    _require_openpyxl()
    xl = pd.ExcelFile(path)
    available = xl.sheet_names
    if sheet is None:
        if len(available) > 1:
            print(f"INFO: XLSX contains {len(available)} sheets:")
            for s in available:
                print(f"  {s!r}")
            print("Use --sheet <name> to select one. Showing first sheet by default.")
        sheet = available[0]
    elif sheet not in available:
        print(
            f"ERROR: Sheet {sheet!r} not found in {path}.\n"
            f"Available sheets: {available}",
            file=sys.stderr,
        )
        sys.exit(1)
    df = pd.read_excel(path, sheet_name=sheet)
    return df, sheet


def read_table(path: Path, sheet: str | None = None) -> tuple[pd.DataFrame, str | None]:
    """Read a CSV, TSV, or XLSX file.

    Returns:
        (DataFrame, sheet_used) where sheet_used is None for CSV/TSV.

    Raises:
        FileNotFoundError: if path does not exist.
    """
    if not path.exists():
        raise FileNotFoundError(f"File not found: {path}")

    fmt = detect_format(path)
    if fmt == "csv":
        return pd.read_csv(path), None
    if fmt == "tsv":
        return pd.read_csv(path, sep="\t"), None
    # xlsx
    df, sheet_used = _read_xlsx(path, sheet)
    return df, sheet_used


def print_table_info(
    df: pd.DataFrame,
    path: Path,
    sheet_used: str | None = None,
) -> None:
    """Print header row and truncated preview rows to stdout."""
    print(f"File:  {path}")
    if sheet_used is not None:
        print(f"Sheet: {sheet_used}")
    print(f"Shape: {len(df)} rows x {len(df.columns)} columns")
    print()
    print("--- Column headers ---")
    for i, col in enumerate(df.columns):
        print(f"  [{i:>3}] {col!r}")
    print()
    n = min(_PREVIEW_ROWS, len(df))
    print(f"--- First {n} row(s) (values truncated to {_MAX_CELL_WIDTH} chars) ---")
    for row_idx in range(n):
        vals = []
        for col in df.columns:
            raw = str(df.iloc[row_idx][col])
            if len(raw) > _MAX_CELL_WIDTH:
                raw = raw[: _MAX_CELL_WIDTH - 3] + "..."
            vals.append(raw)
        print(f"  [{row_idx}] {vals}")


def write_csv(df: pd.DataFrame, output_path: Path, force: bool = False) -> None:
    """Write DataFrame as CSV.

    Raises:
        FileExistsError: if output_path exists and force is False.
    """
    if output_path.exists() and not force:
        raise FileExistsError(
            f"Output file already exists: {output_path}\n"
            "Use --force to overwrite."
        )
    output_path.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(output_path, index=False)
    print(f"Converted CSV written to: {output_path}")


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="inspect_table_headers",
        description=(
            "Print headers and a preview of a metabolomics result table "
            "(CSV, TSV, or XLSX) without modifying the source. "
            "Optionally convert a selected XLSX sheet to CSV."
        ),
    )
    p.add_argument("path", help="Path to the table file (CSV, TSV, or XLSX).")
    p.add_argument(
        "--sheet",
        default=None,
        metavar="SHEET",
        help="XLSX sheet name. If omitted, uses the first sheet and lists all available sheets.",
    )
    p.add_argument(
        "--output",
        default=None,
        metavar="OUTPUT_CSV",
        help="If given, write a CSV of the selected sheet to this path.",
    )
    p.add_argument(
        "--force",
        action="store_true",
        help="Allow overwriting an existing --output file.",
    )
    return p


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    path = Path(args.path)

    try:
        df, sheet_used = read_table(path, sheet=args.sheet)
    except FileNotFoundError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1

    print_table_info(df, path, sheet_used)

    if args.output:
        output_path = Path(args.output)
        try:
            write_csv(df, output_path, force=args.force)
        except FileExistsError as exc:
            print(f"ERROR: {exc}", file=sys.stderr)
            return 1

    return 0


if __name__ == "__main__":
    sys.exit(main())
