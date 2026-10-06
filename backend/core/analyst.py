import os
import traceback
import pandas as pd
import numpy as np
from dotenv import load_dotenv
from core.code_executor import execute_code
from core.llm import generate_analysis_code

load_dotenv()


class DataAnalyst:
    """
    Proof-Carrying Data Analyst.
    Generates Python code to answer a question, executes it,
    verifies the result, and refuses when data is insufficient.
    """

    async def analyze(self, question: str, df: pd.DataFrame, filename: str) -> dict:
        warnings = []

        # --- Data quality checks ---
        quality = self._check_data_quality(df)
        warnings.extend(quality["warnings"])

        if quality["refuse"]:
            return {
                "status": "refused",
                "answer": None,
                "verification": "REFUSED",
                "verification_detail": quality["refuse_reason"],
                "generated_code": None,
                "dataset_summary": self._dataset_summary(df, filename),
                "warnings": warnings,
            }

        # --- Generate code via LLM ---
        try:
            generated_code = await generate_analysis_code(
                question=question,
                df=df,
                filename=filename,
            )
        except Exception as e:
            return {
                "status": "error",
                "answer": None,
                "verification": "ERROR",
                "verification_detail": f"Code generation failed: {str(e)}",
                "generated_code": None,
                "dataset_summary": self._dataset_summary(df, filename),
                "warnings": warnings,
            }

        # --- Execute generated code ---
        exec_result = execute_code(generated_code, df)

        if exec_result["success"]:
            return {
                "status": "success",
                "answer": str(exec_result["output"]),
                "verification": "VERIFIED",
                "verification_detail": "Code executed successfully and produced a result.",
                "generated_code": generated_code,
                "dataset_summary": self._dataset_summary(df, filename),
                "warnings": warnings,
            }
        else:
            return {
                "status": "error",
                "answer": None,
                "verification": "FAILED",
                "verification_detail": exec_result["error"],
                "generated_code": generated_code,
                "dataset_summary": self._dataset_summary(df, filename),
                "warnings": warnings,
            }

    def _check_data_quality(self, df: pd.DataFrame) -> dict:
        warnings = []
        refuse = False
        refuse_reason = ""

        if df.empty:
            return {
                "refuse": True,
                "refuse_reason": "Dataset is empty. Cannot analyze.",
                "warnings": ["Dataset has no rows."],
            }

        total_cells = df.size
        missing_cells = df.isnull().sum().sum()
        missing_pct = (missing_cells / total_cells) * 100 if total_cells > 0 else 0

        if missing_pct > 50:
            refuse = True
            refuse_reason = (
                f"Dataset has {missing_pct:.1f}% missing values — "
                "too unreliable to produce a trustworthy answer."
            )
        elif missing_pct > 20:
            warnings.append(
                f"Dataset has {missing_pct:.1f}% missing values. Results may be unreliable."
            )

        # Check for duplicate rows
        dup_count = df.duplicated().sum()
        if dup_count > 0:
            warnings.append(f"Dataset contains {dup_count} duplicate rows.")

        # Check for very small datasets
        if len(df) < 3:
            warnings.append(
                "Dataset has very few rows. Statistical conclusions may not be meaningful."
            )

        return {
            "refuse": refuse,
            "refuse_reason": refuse_reason,
            "warnings": warnings,
        }

    def _dataset_summary(self, df: pd.DataFrame, filename: str) -> dict:
        return {
            "filename": filename,
            "rows": len(df),
            "columns": list(df.columns),
            "dtypes": {col: str(dtype) for col, dtype in df.dtypes.items()},
            "missing_values": df.isnull().sum().to_dict(),
        }
