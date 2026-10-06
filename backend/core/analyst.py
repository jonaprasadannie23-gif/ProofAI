import logging
import traceback
import pandas as pd
import numpy as np
from dotenv import load_dotenv
from core.code_executor import execute_code
from core.llm import generate_analysis_code, GeminiUnavailableError
from core.local_fallback import run_local_fallback

load_dotenv()

logger = logging.getLogger(__name__)


class DataAnalyst:
    """
    Proof-Carrying Data Analyst.
    Generates Python code to answer a question, executes it,
    verifies the result, and refuses when data is insufficient.
    """

    async def analyze(
        self,
        question: str,
        df: pd.DataFrame,
        filename: str,
        context_history: list | None = None,
    ) -> dict:
        warnings = []

        # --- Data quality checks ---
        quality = self._check_data_quality(df)
        warnings.extend(quality["warnings"])

        if quality["refuse"]:
            logger.info(
                "analysis_mode=refused reason=data_quality question=%r file=%s",
                question, filename,
            )
            return {
                "status": "refused",
                "answer": None,
                "verification": "REFUSED",
                "verification_detail": quality["refuse_reason"],
                "generated_code": None,
                "dataset_summary": self._dataset_summary(df, filename),
                "data_quality": self._data_quality_report(df),
                "warnings": warnings,
                "ai_answer": None,
                "code_result": None,
                "match": None,
                "analysis_mode": "refused",
            }

        # --- Generate code via LLM ---
        try:
            generated_code = await generate_analysis_code(
                question=question,
                df=df,
                filename=filename,
                context_history=context_history or [],
            )
            logger.info("analysis_mode=gemini question=%r file=%s", question, filename)

        except GeminiUnavailableError as e:
            # ── Local fallback path ───────────────────────────────────────────
            # Gemini exhausted all retries due to 503/429. Attempt deterministic
            # local analysis so a demo / live session is not blocked.
            logger.warning(
                "analysis_mode=local_fallback reason=%s question=%r file=%s",
                e, question, filename,
            )
            fallback = run_local_fallback(question, df)

            if fallback is not None:
                return {
                    "status": "success",
                    "answer": fallback.answer,
                    "verification": "VERIFIED",
                    "verification_detail": (
                        "Gemini temporarily unavailable. "
                        "ProofAI used verified local analysis."
                    ),
                    "generated_code": fallback.generated_code,
                    "dataset_summary": self._dataset_summary(df, filename),
                    "data_quality": self._data_quality_report(df),
                    "warnings": warnings + [
                        "Gemini temporarily unavailable — result produced by local fallback analyzer."
                    ],
                    "ai_answer": fallback.answer,
                    "code_result": fallback.answer,
                    "match": True,
                    "analysis_mode": "local_fallback",
                }
            else:
                # Question not handled by local fallback — safe refusal
                logger.info(
                    "analysis_mode=refused reason=fallback_no_match question=%r",
                    question,
                )
                return {
                    "status": "refused",
                    "answer": None,
                    "verification": "REFUSED",
                    "verification_detail": (
                        "Unable to verify this question automatically "
                        "because the AI service is unavailable."
                    ),
                    "generated_code": None,
                    "dataset_summary": self._dataset_summary(df, filename),
                    "data_quality": self._data_quality_report(df),
                    "warnings": warnings + [
                        "Gemini temporarily unavailable — question requires AI analysis."
                    ],
                    "ai_answer": None,
                    "code_result": None,
                    "match": None,
                    "analysis_mode": "refused",
                }

        except Exception as e:
            logger.error(
                "analysis_mode=error reason=%s question=%r file=%s",
                e, question, filename,
            )
            return {
                "status": "error",
                "answer": None,
                "verification": "ERROR",
                "verification_detail": f"Code generation failed: {str(e)}",
                "generated_code": None,
                "dataset_summary": self._dataset_summary(df, filename),
                "data_quality": self._data_quality_report(df),
                "warnings": warnings,
                "ai_answer": None,
                "code_result": None,
                "match": None,
                "analysis_mode": "error",
            }

        # --- Execute generated code ---
        exec_result = execute_code(generated_code, df)

        if exec_result["success"]:
            output_str = str(exec_result["output"])

            # Check for INSUFFICIENT_DATA signal from the LLM
            if output_str.startswith("INSUFFICIENT_DATA:"):
                reason = output_str.replace("INSUFFICIENT_DATA:", "").strip()
                logger.info(
                    "analysis_mode=refused reason=insufficient_data question=%r",
                    question,
                )
                return {
                    "status": "refused",
                    "answer": None,
                    "verification": "REFUSED",
                    "verification_detail": f"Unable to answer reliably: {reason}",
                    "generated_code": generated_code,
                    "dataset_summary": self._dataset_summary(df, filename),
                    "data_quality": self._data_quality_report(df),
                    "warnings": warnings,
                    "ai_answer": reason,
                    "code_result": output_str,
                    "match": False,
                    "analysis_mode": "gemini",
                }

            return {
                "status": "success",
                "answer": output_str,
                "verification": "VERIFIED",
                "verification_detail": "Answer produced by executing code against your data.",
                "generated_code": generated_code,
                "dataset_summary": self._dataset_summary(df, filename),
                "data_quality": self._data_quality_report(df),
                "warnings": warnings,
                "ai_answer": output_str,
                "code_result": output_str,
                "match": True,
                "analysis_mode": "gemini",
            }
        else:
            logger.warning(
                "analysis_mode=gemini exec_failed question=%r file=%s",
                question, filename,
            )
            return {
                "status": "error",
                "answer": None,
                "verification": "FAILED",
                "verification_detail": exec_result["error"],
                "generated_code": generated_code,
                "dataset_summary": self._dataset_summary(df, filename),
                "data_quality": self._data_quality_report(df),
                "warnings": warnings,
                "ai_answer": None,
                "code_result": exec_result["error"],
                "match": False,
                "analysis_mode": "gemini",
            }

    # ── Data quality ──────────────────────────────────────────────────────────

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
        missing_cells = int(df.isnull().sum().sum())
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

        dup_count = int(df.duplicated().sum())
        if dup_count > 0:
            warnings.append(f"Dataset contains {dup_count} duplicate rows.")

        if len(df) < 3:
            warnings.append(
                "Dataset has very few rows. Statistical conclusions may not be meaningful."
            )

        return {
            "refuse": refuse,
            "refuse_reason": refuse_reason,
            "warnings": warnings,
        }

    def _data_quality_report(self, df: pd.DataFrame) -> dict:
        """
        Returns a structured data quality report for display in the UI.
        Only reports issues that are actually detected.
        """
        issues = []

        if df.empty:
            return {"issues": [{"type": "empty", "description": "Dataset is empty.", "severity": "error"}]}

        # Missing values
        missing = df.isnull().sum()
        missing_cols = [(col, int(cnt)) for col, cnt in missing.items() if cnt > 0]
        for col, cnt in missing_cols:
            pct = round(cnt / len(df) * 100, 1)
            issues.append({
                "type": "missing_values",
                "description": f"Column '{col}' has {cnt} missing values ({pct}%)",
                "severity": "warning" if pct < 30 else "error",
                "column": col,
                "count": cnt,
            })

        # Duplicate rows
        dup_count = int(df.duplicated().sum())
        if dup_count > 0:
            issues.append({
                "type": "duplicate_rows",
                "description": f"{dup_count} duplicate rows detected",
                "severity": "warning",
                "count": dup_count,
            })

        # Empty columns (all null)
        empty_cols = [col for col in df.columns if df[col].isnull().all()]
        for col in empty_cols:
            issues.append({
                "type": "empty_column",
                "description": f"Column '{col}' is entirely empty",
                "severity": "error",
                "column": col,
            })

        # Constant columns (single unique value, non-null)
        for col in df.columns:
            if df[col].nunique(dropna=True) == 1 and not df[col].isnull().all():
                issues.append({
                    "type": "constant_column",
                    "description": f"Column '{col}' has only one unique value",
                    "severity": "info",
                    "column": col,
                })

        # Potential duplicate ID columns
        for col in df.columns:
            col_lower = col.lower()
            if any(kw in col_lower for kw in ["id", "key", "code", "uuid"]):
                if df[col].notna().sum() > 0:
                    dup_ids = int(df[col].dropna().duplicated().sum())
                    if dup_ids > 0:
                        issues.append({
                            "type": "duplicate_ids",
                            "description": f"Column '{col}' appears to be an ID column but has {dup_ids} duplicate values",
                            "severity": "warning",
                            "column": col,
                            "count": dup_ids,
                        })

        # Mixed/unexpected types — numeric stored as object
        for col in df.columns:
            if df[col].dtype == object:
                sample = df[col].dropna().head(100)
                try:
                    converted = pd.to_numeric(sample, errors="coerce")
                    non_null_rate = converted.notna().sum() / len(sample) if len(sample) > 0 else 0
                    if 0.3 < non_null_rate < 0.95:
                        issues.append({
                            "type": "mixed_types",
                            "description": f"Column '{col}' contains mixed numeric and non-numeric values",
                            "severity": "warning",
                            "column": col,
                        })
                except Exception:
                    pass

        return {
            "issues": issues,
            "total_issues": len(issues),
            "has_errors": any(i["severity"] == "error" for i in issues),
            "has_warnings": any(i["severity"] == "warning" for i in issues),
        }

    def _dataset_summary(self, df: pd.DataFrame, filename: str) -> dict:
        return {
            "filename": filename,
            "rows": len(df),
            "columns": list(df.columns),
            "dtypes": {col: str(dtype) for col, dtype in df.dtypes.items()},
            "missing_values": {col: int(v) for col, v in df.isnull().sum().items()},
        }
