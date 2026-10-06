import os
import pandas as pd
import google.generativeai as genai
from dotenv import load_dotenv

load_dotenv()

# Configure the Gemini client once at import time
genai.configure(api_key=os.getenv("GEMINI_API_KEY", ""))

# gemini-2.0-flash: fast, capable, optimised for code generation
_MODEL_NAME = "gemini-3.8-flash"

SYSTEM_PROMPT = """You are ProofAI, a Proof-Carrying Data Analyst.
Your job is to write clean, executable Python code that answers a user's question about a dataset.

Rules:
1. You have access to a pandas DataFrame called `df`.
2. You also have access to `pd` (pandas) and `np` (numpy).
3. Your answer MUST be assigned to a variable called `result`.
4. Do NOT use print() — assign the final answer to `result`.
5. Write only the Python code — no markdown fences, no explanation.
6. If the question cannot be answered with the available data, set result = "INSUFFICIENT_DATA: <reason>"
7. Keep the code concise and correct.

Example:
result = df['sales'].sum()
"""


def _build_prompt(question: str, df: pd.DataFrame, filename: str) -> str:
    """Build the full prompt string that is sent to Gemini."""
    col_info = []
    for col in df.columns:
        dtype = str(df[col].dtype)
        sample = df[col].dropna().head(3).tolist()
        col_info.append(f"  - {col} ({dtype}): sample values = {sample}")

    data_description = (
        f"File: {filename}\n"
        f"Shape: {df.shape[0]} rows × {df.shape[1]} columns\n"
        f"Columns:\n" + "\n".join(col_info)
    )

    return (
        f"{SYSTEM_PROMPT}\n\n"
        f"Dataset description:\n{data_description}\n\n"
        f"Question: {question}\n\n"
        "Write Python code to answer this question. Assign the answer to `result`."
    )


def _strip_fences(code: str) -> str:
    """Remove markdown code fences if the model wrapped the response in them."""
    if code.startswith("```"):
        lines = code.splitlines()
        code = "\n".join(
            line for line in lines if not line.startswith("```")
        ).strip()
    return code


async def generate_analysis_code(
    question: str,
    df: pd.DataFrame,
    filename: str,
) -> str:
    """Call Gemini to generate Python code that answers the question."""
    prompt = _build_prompt(question, df, filename)

    model = genai.GenerativeModel(
        model_name=_MODEL_NAME,
        generation_config=genai.types.GenerationConfig(
            temperature=0.0,
            max_output_tokens=512,
        ),
    )

    # GenerativeModel.generate_content_async is the async entry point
    response = await model.generate_content_async(prompt)
    code = response.text.strip()
    return _strip_fences(code)
