import json
from fastapi import APIRouter, UploadFile, File, Form, HTTPException
from fastapi.responses import JSONResponse
from core.analyst import DataAnalyst
from core.file_parser import parse_file, get_file_type
from core.llm import generate_question_suggestions

router = APIRouter()
analyst = DataAnalyst()


# ── /upload ──────────────────────────────────────────────────────────────────

@router.post("/upload")
async def upload_file(file: UploadFile = File(...)):
    """
    Upload a data file and return a structured preview.
    Supports: .csv, .xlsx, .xls, .json, .html, .htm, .txt, .pdf
    """
    file_type = get_file_type(file.filename or "")
    if file_type is None:
        raise HTTPException(
            status_code=400,
            detail=(
                f"Unsupported file type '{file.filename}'. "
                "Supported formats: .csv, .xlsx, .xls, .json, .html, .txt, .pdf"
            ),
        )

    contents = await file.read()
    parsed = parse_file(contents, file.filename)

    if parsed["parse_error"] and not parsed["is_tabular"]:
        # Non-tabular result with a parse error — still return it,
        # the frontend will show the appropriate message
        return JSONResponse(content=_serialisable(parsed))

    if parsed["parse_error"] and not parsed["df"] is not None:
        raise HTTPException(status_code=400, detail=parsed["parse_error"])

    response = _serialisable(parsed)

    # Generate smart question suggestions if tabular
    if parsed["is_tabular"] and parsed["df"] is not None:
        df = parsed["df"]
        try:
            suggestions = await generate_question_suggestions(df, file.filename)
            response["suggestions"] = suggestions
        except Exception:
            response["suggestions"] = []
        # Include raw CSV-like content for /analyze to work
        # We store the file bytes as base64 — but we'll just re-parse server-side
        # The frontend will re-send the original file on /analyze
    else:
        response["suggestions"] = []

    return JSONResponse(content=response)


# ── /analyze ─────────────────────────────────────────────────────────────────

@router.post("/analyze")
async def analyze(
    question: str = Form(...),
    file: UploadFile = File(...),
    context_history: str = Form(default="[]"),
):
    """
    Analyze the uploaded dataset with a natural-language question.
    context_history: JSON-encoded list of {question, answer} dicts for follow-up support.
    """
    file_type = get_file_type(file.filename or "")
    if file_type is None:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported file type '{file.filename}'.",
        )

    contents = await file.read()
    parsed = parse_file(contents, file.filename)

    if not parsed["is_tabular"] or parsed["df"] is None:
        error_msg = parsed["parse_error"] or "File could not be parsed into structured data."
        return JSONResponse(content={
            "status": "refused",
            "answer": None,
            "verification": "REFUSED",
            "verification_detail": (
                f"Unable to answer reliably: {error_msg}"
            ),
            "generated_code": None,
            "dataset_summary": {
                "filename": file.filename,
                "rows": 0,
                "columns": [],
                "dtypes": {},
                "missing_values": {},
            },
            "data_quality": {"issues": [], "total_issues": 0},
            "warnings": [error_msg] if error_msg else [],
            "ai_answer": None,
            "code_result": None,
            "match": None,
        })

    df = parsed["df"]

    # Parse context history
    try:
        history = json.loads(context_history)
        if not isinstance(history, list):
            history = []
    except Exception:
        history = []

    result = await analyst.analyze(
        question=question,
        df=df,
        filename=file.filename,
        context_history=history,
    )
    return JSONResponse(content=_serialisable(result))


# ── /suggestions ─────────────────────────────────────────────────────────────

@router.post("/suggestions")
async def get_suggestions(file: UploadFile = File(...)):
    """Return schema-aware question suggestions for an uploaded file."""
    contents = await file.read()
    parsed = parse_file(contents, file.filename)

    if not parsed["is_tabular"] or parsed["df"] is None:
        return JSONResponse(content={"suggestions": []})

    try:
        suggestions = await generate_question_suggestions(parsed["df"], file.filename)
    except Exception:
        suggestions = []

    return JSONResponse(content={"suggestions": suggestions})


# ── helpers ──────────────────────────────────────────────────────────────────

def _serialisable(obj):
    """Recursively make a dict JSON-serialisable (drop DataFrames, convert numpy types)."""
    import numpy as np
    import pandas as pd

    if isinstance(obj, dict):
        result = {}
        for k, v in obj.items():
            if k == "df":
                continue  # never send DataFrame to frontend
            result[k] = _serialisable(v)
        return result
    elif isinstance(obj, list):
        return [_serialisable(i) for i in obj]
    elif isinstance(obj, (np.integer,)):
        return int(obj)
    elif isinstance(obj, (np.floating,)):
        return float(obj)
    elif isinstance(obj, (np.ndarray,)):
        return obj.tolist()
    elif isinstance(obj, pd.Timestamp):
        return str(obj)
    elif obj is None or isinstance(obj, (str, int, float, bool)):
        return obj
    else:
        return str(obj)
