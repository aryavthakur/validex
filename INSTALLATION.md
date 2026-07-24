# Installation

## Research-Preview Warning

Validex 0.2.0 is a research-preview audit tool for downstream metabolomics result tables. It has not undergone independent scientific peer review or real-world expert validation. Do not use it for clinical decisions.

## Requirements

- Python 3.10 or later
- pip

## Quick Install

```bash
# Clone the repository
git clone <repository-url>
cd <repository-directory>

# Create a virtual environment (recommended)
python3 -m venv .venv
source .venv/bin/activate  # macOS/Linux
# .venv\Scripts\activate   # Windows

# Install Validex and dependencies
pip install -e validex_0_2_worktree/

# Verify installation
validex --help
```

## Dependencies

Validex requires the following Python packages (installed automatically):

| Package | Minimum Version | Purpose |
|---------|----------------|---------|
| fastapi | 0.111.0 | Local web API |
| uvicorn | 0.29.0 | ASGI server |
| python-multipart | 0.0.9 | File upload handling |
| pandas | 2.2.2 | Data frame operations |
| numpy | 1.26.4 | Numerical operations |
| httpx | 0.27.0 | HTTP client |
| openpyxl | 3.1.5 | XLSX file support |

## Development Dependencies

For running tests and linting:

```bash
pip install -e "validex_0_2_worktree/[dev]"
```

## Running Tests

```bash
cd validex_0_2_worktree
python -m pytest tests/ -v
```

The locked 0.2.0 release candidate has 350 tests.

## Running the Web Interface

```bash
cd validex_0_2_worktree
uvicorn validex.server:app --host 127.0.0.1 --port 8000
```

Then open `http://127.0.0.1:8000` in a browser.

## Running the CLI

```bash
validex audit path/to/your/table.csv
```

## Supported Input Formats

| Format | Extension | Notes |
|--------|-----------|-------|
| CSV | `.csv` | Comma-separated values |
| TSV | `.tsv` | Tab-separated values |
| XLSX | `.xlsx` | Excel workbook (specify sheet with `--sheet`) |

## Local-Only AI Feature

Validex includes an optional local AI analysis feature that requires a locally running Ollama instance. This feature is entirely optional — all deterministic audit functionality works without it. No data is sent to cloud AI services.

## Troubleshooting

**`ModuleNotFoundError: No module named 'validex'`**
Ensure you installed with `-e` flag from the correct directory.

**XLSX files not loading**
Ensure `openpyxl` is installed: `pip install openpyxl`

**Frontend not rendering**
The web frontend requires a built frontend bundle. If absent, the API endpoints still function at `/audit` and `/api/health`.
