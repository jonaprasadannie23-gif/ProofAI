# ProofAI — Proof-Carrying Data Analyst

> HNX26PSI08 Hackathon Project

An Agentic AI Data Analyst that analyzes messy real-world data, generates executable Python code for numerical answers, executes and verifies that code, and **refuses to answer** when data is insufficient, ambiguous, or unreliable.

---

## Project Structure

```
ProofAI/
├── start_backend.sh   # One-shot backend setup + launch script
├── frontend/          # React + Vite
│   └── src/
│       ├── components/
│       │   ├── Header.jsx
│       │   ├── UploadPanel.jsx
│       │   ├── DatasetPreview.jsx
│       │   ├── QuestionPanel.jsx
│       │   └── ResultPanel.jsx
│       ├── App.jsx
│       └── index.css
└── backend/           # Python FastAPI
    ├── main.py
    ├── requirements.txt
    ├── .env.example
    ├── api/
    │   └── routes.py
    ├── core/
    │   ├── analyst.py       # Data quality checks + orchestration
    │   ├── code_executor.py # Safe Python code execution
    │   └── llm.py           # Gemini code generation
    └── sample_data/
        └── sales.csv
```

---

## Python Version Requirement

**Python 3.13 is required.**  
`pandas==2.2.2` and `numpy==2.0.2` (the original pins) have no pre-built wheels for
Python 3.13 on macOS Apple Silicon and would trigger a source build that fails.
The requirements have been bumped to `pandas==2.2.3` and `numpy==2.1.0`, which are
the earliest patch releases that ship `cp313` arm64 wheels on PyPI. All other pins
are unchanged.

---

## Local Setup

### 1. Obtain a Gemini API Key

ProofAI uses Google's Gemini API for code generation. You need a free API key:

1. Go to [Google AI Studio](https://aistudio.google.com/apikey)
2. Sign in with your Google account
3. Click **Get API key** or **Create API key**
4. Copy the API key (it will look like `AIzaSy...` and be ~39 characters)

**Important:** Keep this key private. Never commit it to git or share it publicly.

### 2. Configure the API Key

```zsh
# From the ProofAI/backend/ directory
cp .env.example .env
# Edit .env and replace 'your_gemini_api_key_here' with your actual key
```

The `.env` file should contain:
```
GEMINI_API_KEY=AIzaSy...your-actual-key-here
```

### 3. Backend (FastAPI on port 8000)

#### Option A — one-shot script (recommended)

```zsh
# From the ProofAI/ directory
zsh start_backend.sh
```

The script will:
1. Create a virtual environment at `ProofAI/.venv_backend/`
2. Install all dependencies from `backend/requirements.txt`
3. Copy `backend/.env.example` → `backend/.env` if no `.env` exists yet
4. Start `uvicorn` on `http://127.0.0.1:8000` with `--reload`

#### Option B — manual steps

```zsh
# 1. Create and activate a virtual environment (from ProofAI/)
python3 -m venv .venv_backend
source .venv_backend/bin/activate

# 2. Install dependencies
pip install --upgrade pip
pip install -r backend/requirements.txt

# 3. Start the server (make sure you've configured .env first — see step 2 above)
cd backend
uvicorn main:app --reload --host 127.0.0.1 --port 8000
```

**Verify the backend is alive:**

```zsh
curl http://127.0.0.1:8000/health
# → {"status":"ok","service":"ProofAI","version":"0.1.0"}
```

**Test Gemini API authentication:**

```zsh
cd backend
python test_gemini_auth.py
# Should show: ✓ All checks passed
```

Swagger UI is also available at: http://127.0.0.1:8000/docs

---

### Frontend (React + Vite on port 5173)

Open a **second terminal** (keep the backend running in the first):

```zsh
cd frontend
npm install        # first time only
npm run dev
```

UI will be available at: http://localhost:5173

Vite proxies all `/api/*` requests to `http://127.0.0.1:8000`, so no CORS
configuration is needed during development.

---

## Verifying CSV Upload Works

1. Start the backend (`zsh start_backend.sh` or manual steps above).
2. Confirm it's alive: `curl http://127.0.0.1:8000/health`
3. Test the upload endpoint directly with the bundled sample CSV:

```zsh
curl -s -X POST http://127.0.0.1:8000/api/upload \
  -F "file=@backend/sample_data/sales.csv" | python3 -m json.tool
```

Expected response shape:

```json
{
  "filename": "sales.csv",
  "rows": 20,
  "columns": ["..."],
  "shape": [20, 7],
  "preview": [...],
  "dtypes": {...},
  "missing_values": {...},
  "csv_content": "..."
}
```

4. Start the frontend (`npm run dev` in `frontend/`).
5. Open http://localhost:5173, drag-and-drop `backend/sample_data/sales.csv` onto
   the upload zone — the file pill and row/column stats should appear immediately.

---

## API Endpoints

| Method | Path | Description |
|--------|------|-------------|
| `GET` | `/` | Root — quick status check |
| `GET` | `/health` | Liveness check (returns `{"status":"ok"}`) |
| `GET` | `/docs` | Swagger UI |
| `POST` | `/api/upload` | Upload a CSV; returns preview + metadata |
| `POST` | `/api/analyze` | Ask a natural-language question about a CSV |

---

## How It Works

1. **Upload CSV** → backend parses and returns preview + quality stats
2. **Ask a question** in natural language
3. **ProofAI**:
   - Runs data quality checks (missing values, duplicates, empty data)
   - If data is too bad → **REFUSES** with reason
   - Otherwise → calls Gemini to generate Python code
   - **Executes** the code against the actual DataFrame
   - Returns: Answer · Verification status · Generated code · Dataset summary · Warnings

---

## Key Design Decisions

- **Proof-carrying**: every answer comes with the code that produced it
- **Refusal system**: refuses before wasting LLM calls on bad data
- **Code execution**: sandboxed Python exec with access to `df`, `pd`, `np`
- **No hallucinations on numbers**: code is run, not just generated

---

## Sample CSV

`backend/sample_data/sales.csv` — 20 rows of sales data across products, categories,
regions, and months.

Try asking:
- "What is the total sales revenue?"
- "Which product has the highest average sales?"
- "Which region had the most units sold?"
- "What is the average discount by category?"

---

## Troubleshooting

### "Code generation failed: API key not valid"

This means the Gemini API key is missing, incorrect, or invalid.

**Solution:**
1. Make sure you created `backend/.env` (copy from `.env.example`)
2. Get a valid API key from [Google AI Studio](https://aistudio.google.com/apikey)
3. Replace `your_gemini_api_key_here` in `backend/.env` with your actual key
4. Restart the backend server
5. Run `python backend/test_gemini_auth.py` to verify authentication

**Common issues:**
- Placeholder value still in `.env` (not replaced with real key)
- Extra spaces or quotes around the key in `.env`
- API key expired or revoked — get a new one
- Gemini API not enabled for your Google account

### CSV Upload Issues

If CSV upload fails, check:
- Backend is running on http://127.0.0.1:8000
- `curl http://127.0.0.1:8000/health` returns 200 OK
- Frontend proxy is configured (already set in `vite.config.js`)

### Backend Not Starting

If `uvicorn` fails to start:
- Check Python version: `python3 --version` (should be 3.13)
- Reinstall dependencies: `pip install -r backend/requirements.txt`
- Check for port conflicts: `lsof -i :8000`
