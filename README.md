# ProofAI — Proof-Carrying Data Analyst

> HNX26PSI08 Hackathon Project

An Agentic AI Data Analyst that analyzes messy real-world data, generates executable Python code for numerical answers, executes and verifies that code, and **refuses to answer** when data is insufficient, ambiguous, or unreliable.

---

## Project Structure

```
ProofAI/
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
    ├── api/
    │   └── routes.py
    ├── core/
    │   ├── analyst.py       # Data quality checks + orchestration
    │   ├── code_executor.py # Safe Python code execution
    │   └── llm.py           # OpenAI code generation
    ├── sample_data/
    │   └── sales.csv
    └── requirements.txt
```

---

## Setup & Running

### Backend

```bash
cd backend

# 1. Install dependencies
pip install -r requirements.txt

# 2. Set your OpenAI API key
copy .env.example .env
# Edit .env and add your OPENAI_API_KEY

# 3. Start the server
uvicorn main:app --reload --port 8000
```

API will be available at: http://localhost:8000  
Swagger docs: http://localhost:8000/docs

### Frontend

```bash
cd frontend

# 1. Install dependencies (already done during scaffold)
npm install

# 2. Start dev server
npm run dev
```

UI will be available at: http://localhost:5173

---

## How It Works

1. **Upload CSV** → backend parses and returns preview + quality stats
2. **Ask a question** in natural language
3. **ProofAI**:
   - Runs data quality checks (missing values, duplicates, empty data)
   - If data is too bad → **REFUSES** with reason
   - Otherwise → calls OpenAI to generate Python code
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

`backend/sample_data/sales.csv` — 20 rows of sales data across products, categories, regions, and months.

Try asking:
- "What is the total sales revenue?"
- "Which product has the highest average sales?"
- "Which region had the most units sold?"
- "What is the average discount by category?"
