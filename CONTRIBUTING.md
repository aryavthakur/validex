# Contributing to Validex

Thank you for your interest in contributing to Validex.

## Getting Started

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Run the test suite: `python -m pytest tests/ -v`
5. Submit a pull request

## Development Setup

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
```

## Code Quality

- Run tests: `python -m pytest tests/ -v`
- Run linting: `ruff check .`
- Run type checking: `mypy validex/`

## Guidelines

- All audit behavior must be deterministic
- New aliases must include rationale and risk level
- Probability-field changes must preserve the two-phase design (structural detection + usability gating)
- New features require accompanying tests
- Documentation should be updated alongside code changes

## Reporting Issues

Please use the GitHub issue tracker. Include:
- Validex version
- Python version
- Input file format (CSV/TSV/XLSX)
- Expected behavior
- Actual behavior
- Steps to reproduce

## Code of Conduct

Please follow our [Code of Conduct](CODE_OF_CONDUCT.md).

## Research-Preview Status

Validex is in research-preview status. Contributions that affect audit behavior should consider the implications for the frozen benchmark and existing validation evidence.
