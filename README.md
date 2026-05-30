# Validex

Validex is a local, privacy-first AI data auditing app. It runs from the terminal, opens in your browser, analyzes CSV datasets on your device, and uses local Ollama AI for explanations and review support.

## Key Features

- Local web app served by FastAPI.
- Private dataset processing on your machine.
- Local Ollama AI with `llama3.2:3b` by default.
- No cloud AI by default.
- CSV audit workflow for metabolomics result tables.
- Installable `validex` command.

## Privacy Guarantee

Validex is designed to run locally by default:

- Datasets stay on your device.
- The browser frontend talks to the local FastAPI backend.
- The backend talks only to local Ollama by default.
- No OpenAI, Groq, OpenRouter, Anthropic, or hosted backend is used by default.
- The server binds to `127.0.0.1` by default, not `0.0.0.0`.
- No telemetry, analytics, external tracking, remote logging, or remote crash reporting is included.

Uploaded CSV files are written only to a temporary local directory during audit processing and deleted after the request finishes. AI prompts use structured summaries, schema, statistics, and audit flags rather than sending raw full datasets to a remote service.

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
Privacy mode: Local only, no cloud AI
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
  "cloud_ai_enabled": false,
  "open_browser": true,
  "host": "127.0.0.1",
  "port": null
}
```

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
python -m pip install -e .
python -m pytest tests -q
```

Frontend source lives in `frontend/`. The packaged app does not need Node, Vite, or frontend development tools at runtime because the built frontend is included in `validex/static`.

To rebuild the frontend during development:

```bash
cd frontend
npm install
npm run build
cd ..
```

For Vite development, point the frontend at a local backend:

```bash
cd frontend
VITE_API_URL=http://127.0.0.1:8000 npm run dev
```

## Release Notes

### 0.1.0

- Privacy-first local CLI release.
- Local FastAPI app served by `validex`.
- Local Ollama AI with `llama3.2:3b` by default.
- Same-origin packaged frontend.
- No hosted backend or cloud AI by default.
