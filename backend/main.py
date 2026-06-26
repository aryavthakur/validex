# Thin script entry point for direct file-based audit.
# Canonical audit logic lives in validex/audit.py.
#
# Hardcoded paths:
#   inputs/results.csv       — input CSV to audit (must exist before running)
#   outputs/validity_report.md — Markdown report written by run_audit
#
# The outputs/ directory is git-ignored. Create it locally before running:
#   mkdir -p inputs outputs
#   python backend/main.py
from validex.audit import run_audit


def main():
    run_audit(
        csv_path="inputs/results.csv",
        report_path="outputs/validity_report.md",
    )


if __name__ == "__main__":
    main()
