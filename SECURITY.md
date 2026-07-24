# Security Policy

## Supported Versions

| Version | Supported |
|---------|-----------|
| 0.2.x   | Yes       |
| < 0.2   | No        |

## Reporting a Vulnerability

Please report security vulnerabilities by emailing aryav.thakur@gmail.com.

Do not open a public issue for security vulnerabilities.

## Scope

Validex processes user-supplied table files locally. Security considerations include:
- File parsing (CSV, TSV, XLSX)
- Local web server (FastAPI/Uvicorn on localhost)
- Optional local AI integration (Ollama on localhost)
- No cloud services or external network calls during auditing
