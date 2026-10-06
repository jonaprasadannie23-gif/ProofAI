from fastapi import APIRouter, UploadFile, File, Form, HTTPException
from fastapi.responses import JSONResponse
import pandas as pd
import io
from core.analyst import DataAnalyst

router = APIRouter()
analyst = DataAnalyst()


@router.post("/upload")
async def upload_csv(file: UploadFile = File(...)):
    """Upload a CSV file and return a preview of the data."""
    if not file.filename.endswith(".csv"):
        raise HTTPException(status_code=400, detail="Only CSV files are supported.")

    contents = await file.read()
    try:
        df = pd.read_csv(io.BytesIO(contents))
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Failed to parse CSV: {str(e)}")

    preview = {
        "filename": file.filename,
        "rows": len(df),
        "columns": list(df.columns),
        "shape": list(df.shape),
        "preview": df.head(10).to_dict(orient="records"),
        "dtypes": {col: str(dtype) for col, dtype in df.dtypes.items()},
        "missing_values": df.isnull().sum().to_dict(),
        "csv_content": contents.decode("utf-8", errors="replace"),
    }
    return JSONResponse(content=preview)


@router.post("/analyze")
async def analyze(
    question: str = Form(...),
    file: UploadFile = File(...),
):
    """Analyze the uploaded dataset with a natural-language question."""
    if not file.filename.endswith(".csv"):
        raise HTTPException(status_code=400, detail="Only CSV files are supported.")

    contents = await file.read()
    try:
        df = pd.read_csv(io.BytesIO(contents))
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Failed to parse dataset: {str(e)}")

    result = await analyst.analyze(question=question, df=df, filename=file.filename)
    return JSONResponse(content=result)
