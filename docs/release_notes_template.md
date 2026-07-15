# Validex Release Notes Template

## Release

- Version:
- Commit:
- Release status: Research preview
- Release-candidate command: `python scripts/verify_release_candidate.py`

## Evidence

- Backend tests:
- Frontend tests:
- Static parity:
- Wheel inspection:
- Sdist inspection:
- Installed-wheel smoke:
- Python dependency audit:
- npm audit:
- External validation:

## Scientific Scope

Validex audits metabolomics result-table structure, statistical-cell validity, and reporting completeness. It does not validate biological conclusions, raw instrument data processing, clinical utility, or publication readiness.

## Known Limitations

- Independent external validation is incomplete unless a release report identifies processed public datasets and metrics.
- Synthetic benchmark fixtures are regression tests, not independent external validation.
- Optional AI explanations are excluded from release validation.
