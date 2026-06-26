#!/usr/bin/env python
"""Create a candidate note file for a pilot validation dataset.

Usage:
    python validation/pilot/create_candidate_note.py \\
        --dataset-id PILOT_001 \\
        --output-dir validation/pilot/notes

Creates a note file named PILOT_001_notes.md from the candidate_notes_template.md.
Refuses to overwrite an existing file unless --force is passed.
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

_TEMPLATE_NAME = "candidate_notes_template.md"
_NOTES_DIR = Path(__file__).resolve().parent / "notes"


def create_candidate_note(
    dataset_id: str,
    output_dir: Path,
    force: bool = False,
) -> Path:
    """Create a candidate note file for dataset_id in output_dir.

    Returns the path of the created file.
    Raises FileExistsError if the file already exists and force is False.
    Raises FileNotFoundError if the template is missing.
    """
    template_path = _NOTES_DIR / _TEMPLATE_NAME
    if not template_path.exists():
        raise FileNotFoundError(f"Template not found: {template_path}")

    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    note_filename = f"{dataset_id}_notes.md"
    output_path = output_dir / note_filename

    if output_path.exists() and not force:
        raise FileExistsError(
            f"Note file already exists: {output_path}\n"
            "Pass --force to overwrite."
        )

    template_text = template_path.read_text(encoding="utf-8")
    # Replace the placeholder [DATASET_ID] in the template title
    note_text = template_text.replace("[DATASET_ID]", dataset_id, 1)

    output_path.write_text(note_text, encoding="utf-8")
    return output_path


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="create_candidate_note",
        description="Create a candidate note file from the pilot template.",
    )
    p.add_argument(
        "--dataset-id",
        required=True,
        help="Dataset ID for the candidate note (e.g. PILOT_001).",
    )
    p.add_argument(
        "--output-dir",
        default=str(_NOTES_DIR),
        help=(
            "Directory to write the note file. "
            f"Defaults to {_NOTES_DIR}."
        ),
    )
    p.add_argument(
        "--force",
        action="store_true",
        help="Overwrite an existing note file.",
    )
    return p


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    try:
        output_path = create_candidate_note(
            dataset_id=args.dataset_id,
            output_dir=Path(args.output_dir),
            force=args.force,
        )
    except FileNotFoundError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1
    except FileExistsError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1

    print(f"Created: {output_path}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
