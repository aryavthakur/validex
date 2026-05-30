# Validex

Validex is a privacy-first local web app for auditing metabolomics result tables. It runs from the terminal, opens in your browser, processes CSV files on your device, and uses a local Ollama model for AI-assisted interpretation.

## Install

From this repository:

```bash
pipx install .
validex
```

For development:

```bash
python -m pip install -e ".[dev]"
validex
```

## Run

```bash
validex
```

Validex will:

1. Load or create `~/.validex/config.json`.
2. Check whether Ollama is installed.
3. Check whether Ollama is running at `http://localhost:11434`.
4. Check whether `llama3.2:3b` is installed.
5. Ask before installing/pulling anything large.
6. Start FastAPI on `127.0.0.1` using an available port.
7. Open the local web app in your browser.

Expected terminal output:

```text
Validex is running locally.
App: http://127.0.0.1:PORT
AI provider: Ollama
Model: llama3.2:3b
Privacy mode: Local only, no cloud AI
```

## First-Run Ollama Setup

Validex uses `llama3.2:3b` by default because it is small enough for typical laptops.

If Ollama is missing on macOS and Homebrew is installed, Validex asks before running:

```bash
brew install ollama
```

If Homebrew is missing, Validex prints manual installation instructions. It does not install Homebrew for you.

If Ollama is installed but not running, `validex` attempts to start it locally with:

```bash
ollama serve
```

If that fails, start Ollama manually with the same command and run `validex` again.

Pull the default model manually if needed:

```bash
ollama pull llama3.2:3b
```

## Privacy Guarantee

Default Validex behavior is local only:

- AI provider: Ollama.
- AI endpoint: `http://localhost:11434`.
- Server bind address: `127.0.0.1`.
- Cloud AI: disabled.
- Telemetry: none.
- Remote logging or crash reporting: none.

Uploaded datasets are written only to a temporary local directory during an audit and deleted when processing finishes. Validex sends structured summaries, schema, statistics, and audit flags to the local model instead of sending raw full datasets to any remote provider.

The app does not include telemetry, analytics, external tracking, remote logging, or remote crash reporting. The only first-run network fetch Validex initiates is `ollama pull MODEL`, and only after you confirm it in the terminal.

## CLI Commands

```bash
validex
validex status
validex model list
validex model pull llama3.2:3b
validex model set mistral:7b
validex config show
```

Config lives at:

```text
~/.validex/config.json
```

Default config:

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

## API

- `GET /api/health`
- `GET /api/ai/status`
- `GET /api/privacy/status`
- `POST /api/ai/analyze`
- `POST /audit`
- `POST /lambda-analyze` compatibility route, backed by local Ollama
- `POST /clean-data`

Privacy status returns:

```json
{
  "provider": "ollama",
  "local_only": true,
  "cloud_ai_enabled": false,
  "ollama_url": "http://localhost:11434",
  "model": "llama3.2:3b"
}
```

## Troubleshooting

### Ollama Not Installed

Install Ollama from `https://ollama.com/download`, or on macOS:

```bash
brew install ollama
```

### Ollama Not Running

Start Ollama:

```bash
ollama serve
```

Then check:

```bash
validex status
```

### Model Not Found

Pull the configured model:

```bash
validex model pull llama3.2:3b
```

### Port Already In Use

By default, Validex chooses an available local port. To pin a port, edit `~/.validex/config.json`:

```json
{
  "port": 8787
}
```

### Frontend Static Files Missing

Build the frontend:

```bash
cd frontend
npm install
npm run build
```

## Developer Setup

```bash
python -m pip install -e ".[dev]"
cd frontend
npm install
npm run build
cd ..
python -m pytest tests -q
validex status
```

For frontend development, run Vite separately and point it at a local backend if desired:

```bash
cd frontend
VITE_API_URL=http://127.0.0.1:8000 npm run dev
```
