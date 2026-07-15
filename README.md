# Validex

Validex is a local-first metabolomics result-table auditing app. It runs from the terminal, opens in your browser, audits CSV datasets with deterministic checks, and can use Ollama for optional supplemental explanations.

Release status: **Research preview**. Validex has deterministic regression tests and a synthetic benchmark suite, but this repository does not currently contain a legally redistributable independent external-validation dataset. Do not treat Validex as clinically validated, publication-ready, or generally validated across all metabolomics platforms.

## Key Features

- Local web app served by FastAPI.
- Deterministic auditing that works without AI.
- Local Ollama AI with `llama3.2:3b` by default for optional explanations.
- No cloud AI by default.
- CSV audit workflow for metabolomics result tables.
- Installable `validex` command.

## Privacy Boundary

Validex is designed to run locally by default:

- Uploaded CSV files are processed by the local Validex application by default.
- The browser frontend talks to the local FastAPI backend.
- The backend talks only to local Ollama by default.
- No OpenAI, Groq, OpenRouter, Anthropic, or hosted backend is used by default.
- The server binds to `127.0.0.1` by default, not `0.0.0.0`.
- No telemetry, analytics, external tracking, remote logging, or remote crash reporting is included.

Uploaded CSV files are written only to a temporary local directory during audit processing and deleted after the request finishes. Deterministic audit does not require AI. When optional AI analysis is explicitly used, Validex sends a capped structured summary to Ollama: detected schema names, aggregate shape, deterministic score/confidence, bounded findings, bounded user context, and the user question. Validex does not send full raw CSV rows to AI by default.

Local execution does not eliminate every privacy risk. Validex cannot guarantee Ollama logging, retention, model behavior, operating-system behavior, or isolation from other local processes. If `ollama_url` is configured to a non-loopback host, structured summaries and user context may leave this device and the session is not local-only.

## Requirements

- Python 3.10 or newer.
- `pip`, or `pipx` for isolated CLI installation.
- Ollama installed locally.
- Enough disk space for the default `llama3.2:3b` model.

## Quick Start

Install from this repository:

```bash
python -m pip install .
validex
```

For development:

```bash
python -m pip install -e .
validex
```

## Recommended Install With pipx

```bash
pipx install .
validex
```

## First Run

When you run `validex`, the CLI:

1. Loads or creates `~/.validex/config.json`.
2. Checks whether Ollama is installed.
3. On macOS, asks before installing Ollama with Homebrew when Homebrew is available.
4. Checks whether Ollama is running at `http://localhost:11434`.
5. Tries `ollama serve` if Ollama is installed but not running.
6. Checks whether `llama3.2:3b` is installed.
7. Asks before running `ollama pull llama3.2:3b`.
8. Runs a tiny local model test prompt.
9. Starts the local FastAPI app on `127.0.0.1`.
10. Opens the local web app in your browser.

Expected terminal output:

```text
Validex is running locally.
App: http://127.0.0.1:PORT
AI provider: Ollama
Model: llama3.2:3b
Privacy mode: Local only, no cloud AI when Ollama URL is loopback; remote Ollama is not local-only
```

## CLI Commands

```bash
validex
validex status
validex config show
validex model list
validex model pull MODEL
validex model set MODEL
```

`validex model pull MODEL` pulls the requested model immediately because the command itself is explicit. The normal first-run `validex` flow still asks before pulling the default model.

Config lives at `~/.validex/config.json`. Local privacy defaults are enforced when config is loaded:

```json
{
  "ai_provider": "ollama",
  "ollama_url": "http://localhost:11434",
  "model": "llama3.2:3b",
  "ai_enabled": true,
  "cloud_ai_enabled": false,
  "open_browser": true,
  "host": "127.0.0.1",
  "port": null,
  "max_upload_bytes": 52428800,
  "max_rows": 100000,
  "max_columns": 500,
  "max_total_cells": 5000000,
  "max_cell_length": 20000,
  "max_header_length": 300
}
```

Important defaults:

- Uploads over 50 MiB are rejected.
- CSVs over 100,000 rows, 500 columns, or 5,000,000 cells are rejected.
- Individual cells over 20,000 characters and headers over 300 characters are rejected.
- CSV preview rows and validated export size are capped.
- AI prompts and model responses have separate size, timeout, and concurrency limits.

## Troubleshooting

### Ollama not installed

Install Ollama from `https://ollama.com/download`, or on macOS with Homebrew:

```bash
brew install ollama
```

Then run:

```bash
validex status
```

### Ollama not running

Start Ollama:

```bash
ollama serve
```

Then run `validex` again.

### Model missing

Pull the configured model:

```bash
validex model pull llama3.2:3b
```

The first-run `validex` command will also ask before pulling the missing default model.

### Port already in use

Validex chooses an available local port by default. To pin a port, edit `~/.validex/config.json`:

```json
{
  "port": 8787
}
```

### Browser did not open

Copy the `App:` URL printed by `validex` and open it in your browser. You can also set `"open_browser": false` in `~/.validex/config.json`.

### pipx command not found

Use pip instead:

```bash
python -m pip install .
validex
```

Or install pipx using the official instructions for your operating system.

### Permission issues

Use a virtual environment or pipx instead of installing into a system Python:

```bash
python -m venv .venv
source .venv/bin/activate
python -m pip install .
validex
```

## Developer Setup

```bash
python -m pip install -c requirements-dev.txt -e '.[dev,audit]'
python -m pytest tests -q
```

Frontend source lives in `frontend/`. The packaged app does not need Node, Vite, or frontend development tools at runtime because the built frontend is included in `validex/static`.

The authoritative release workflow builds the reviewed frontend source in a temporary clean copy, installs dependencies with `npm ci` from `frontend/package-lock.json`, excludes `.env.local`, and synchronizes only the production Vite output into `validex/static`:

```bash
python scripts/build_frontend.py
python scripts/verify_frontend_assets.py
```

The final local release-candidate gate is:

```bash
python scripts/verify_release_candidate.py
```

This command runs backend tests, Ruff, mypy, the scientific benchmark, frontend lint/tests/build, static parity, wheel and source distribution builds, artifact inspection, installed-wheel smoke checks, dependency audits, external-validation manifest checks, and repeated-build content comparison. It uses temporary directories and does not require Playwright.

Requirements:

- Python 3.10 or newer.
- Node 20.19.0 or newer.
- npm with lockfile v3 support.

Frontend development commands:

```bash
cd frontend
npm ci
npm run lint
npm test
npm run build -- --outDir /private/tmp/validex-phase3-source-build --emptyOutDir
```

For Vite development, point the frontend at a local backend:

```bash
VITE_API_URL=http://127.0.0.1:8000 npm run dev
```

Do not manually copy frontend build output into `validex/static`; use `python scripts/build_frontend.py` so stale hashed assets are removed and package static assets stay reproducible.

## Benchmark Suite

Validex includes a reproducible benchmark suite that evaluates schema detection accuracy and audit behavior across 14 synthetic fixture tables covering standard tables, missing statistical fields, invalid statistical values, ambiguous aliases, adversarial headers, and common export-style headers. On this included benchmark suite, Validex currently achieves 100% field-level schema detection precision and recall.

This benchmark is synthetic regression evidence. It is not independent external validation and should not be described as proof of scientific validity.

This benchmark is a regression and behavior suite, not a real-world validation study. It does not establish performance across published metabolomics supplements or expert-labeled external datasets.

```bash
python benchmarks/run_benchmark.py
```

The benchmark reports per-fixture pass/fail status, audit score, confidence label (`high` / `medium` / `low`), and schema detection precision and recall. It also runs as part of the standard test suite:

```bash
pytest
```

See `benchmarks/README.md` for fixture descriptions, score semantics, confidence label rules, how to add new fixtures, and known limitations.

## External Validation Scaffold

Validex includes an external validation scaffold for future evaluation on legally accessible, real published metabolomics result tables. This scaffold defines a registry format, manual labeling format, metric calculation, and a validation runner. No external validation results are claimed unless a completed labeled external dataset and results file are provided.

- Protocol: [`docs/external_validation_protocol.md`](docs/external_validation_protocol.md)
- Scaffold: [`validation/README.md`](validation/README.md)

A pilot validation workspace is available under `validation/pilot/` for manually recording candidate external tables, licensing notes, labels, and dry-run results. Pilot runs are workflow tests and are not external validation claims. See [`validation/pilot/README.md`](validation/pilot/README.md).

## Scope and Claims

Validex audits post-analysis result tables for reporting completeness. It does not process raw instrument data, perform statistical testing, validate biological findings, certify publication readiness, or replace expert review. AI explanations are supplemental, non-deterministic, and not scientifically verified by Validex.

See [`docs/scope_and_prior_art.md`](docs/scope_and_prior_art.md) for a full description of what Validex does and does not do, where it sits in the metabolomics workflow, adjacent tool categories, prior-art citation placeholders, current evidence level, and allowed versus disallowed claims.

## Release Notes

### 0.1.0

- Privacy-first local CLI release.
- Local FastAPI app served by `validex`.
- Local Ollama AI with `llama3.2:3b` by default.
- Same-origin packaged frontend.
- No hosted backend or cloud AI by default.
