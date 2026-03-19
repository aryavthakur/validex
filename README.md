# Metabolomics Auditor — React + FastAPI

Migrated from Streamlit. Same Python audit logic, much better UI.

## Structure

```
metabolomics-auditor/
├── backend/
│   ├── api.py              ← FastAPI app (new)
│   ├── requirements.txt    ← pip deps
│   ├── main.py             ← your existing audit logic (copy here)
│   ├── schema_mapper.py    ← your existing schema mapper (copy here)
│   └── context_engine.py   ← your existing context engine (copy here)
└── frontend/
    ├── src/
    │   ├── App.jsx
    │   ├── index.css
    │   ├── main.jsx
    │   └── components/
    │       ├── Header.jsx
    │       ├── UploadZone.jsx
    │       ├── DataPreview.jsx
    │       ├── ContextForm.jsx
    │       └── AuditResults.jsx
    ├── index.html
    ├── package.json
    └── vite.config.js
```

## Setup

### 1. Copy your Python files into backend/
```bash
cp main.py schema_mapper.py context_engine.py backend/
```

### 2. Start the backend
```bash
cd backend
pip install -r requirements.txt
uvicorn api:app --reload --port 8000
```

### 3. Start the frontend
```bash
cd frontend
npm install
npm run dev
# → http://localhost:5173
```

## What changed vs Streamlit

| Streamlit | React + FastAPI |
|-----------|-----------------|
| `app.py` UI | `frontend/src/` — React components |
| File saved to `inputs/` | Uploaded via multipart form to FastAPI |
| `run_audit()` called in-process | Called by FastAPI `/audit` endpoint |
| Report written to disk | Returned as JSON over HTTP |
| Streamlit download buttons | Browser `Blob` download, no temp files |

## API

`POST /audit`
- `file`: CSV file (multipart)
- `context`: JSON string with study context
- Returns: `{ overview, schema, preview, report_md, report_json, histogram }`

## Deployment

**Backend**: Deploy to Railway, Render, or any Python host.
Set CORS origins in `api.py` to match your frontend domain.

**Frontend**: Deploy to Vercel/Netlify.
Set `VITE_API_URL=https://your-backend.com` in env vars.
