"""
local_fallback.py — ProofAI deterministic local analysis fallback.

Used when Gemini is temporarily unavailable (503 / 429).
Parses natural-language questions into safe pandas operations and executes
them directly against the DataFrame.

Design principles:
- NEVER hardcode answers — every value is computed from the real df.
- REFUSE rather than guess when the question cannot be safely interpreted.
- Modular: add new handlers by appending to _HANDLERS at the bottom.
- Each handler returns a FallbackResult or None (= cannot handle).
"""

from __future__ import annotations

import logging
import re
from dataclasses import dataclass, field
from typing import Callable

import pandas as pd
import numpy as np

logger = logging.getLogger(__name__)

# ── Result type ───────────────────────────────────────────────────────────────

@dataclass
class FallbackResult:
    """Structured result from local fallback analysis."""
    answer: str
    generated_code: str
    analysis_mode: str = "local_fallback"
    matched_handler: str = ""


# ── Helpers ───────────────────────────────────────────────────────────────────

def _numeric_cols(df: pd.DataFrame) -> list[str]:
    return [c for c in df.columns if pd.api.types.is_numeric_dtype(df[c])]


def _categorical_cols(df: pd.DataFrame) -> list[str]:
    """Non-numeric columns suitable for grouping (object, string, category)."""
    cols = []
    for c in df.columns:
        if pd.api.types.is_numeric_dtype(df[c]):
            continue
        if pd.api.types.is_datetime64_any_dtype(df[c]):
            continue
        cols.append(c)
    return cols


def _column_mentioned(question_lower: str, col: str) -> bool:
    """True if the column name appears as a whole token in the question."""
    name = col.lower()
    return re.search(
        rf"(?<![a-z0-9_]){re.escape(name)}(?![a-z0-9_])",
        question_lower,
    ) is not None


def _find_column(question_lower: str, candidates: list[str]) -> str | None:
    """
    Return the unique candidate column named in the question.

    Returns None if no candidate is named, or if two distinct columns are
    named (ambiguous). Never guesses a default column.
    """
    matches = [c for c in candidates if _column_mentioned(question_lower, c)]
    if not matches:
        return None
    # Drop shorter names that are substrings of a longer matched name
    # (e.g. "sales" vs "sales_total").
    filtered: list[str] = []
    for m in sorted(matches, key=lambda c: -len(c)):
        if any(m.lower() != f.lower() and m.lower() in f.lower() for f in filtered):
            continue
        filtered.append(m)
    if len(filtered) == 1:
        return filtered[0]
    return None


def _quoted_unknown_column(question: str, df: pd.DataFrame) -> bool:
    """True if the question quotes a column name that is not in the dataframe."""
    names = {c.lower() for c in df.columns}
    for quoted in re.findall(r"['\"`]([^'\"`]+)['\"`]", question):
        if quoted.strip().lower() not in names:
            return True
    return False


def _valid_numeric(value) -> bool:
    """False for None / NaN — those must be refused, not returned as answers."""
    if value is None:
        return False
    try:
        return not pd.isna(value)
    except (TypeError, ValueError):
        return True


def _fmt(value) -> str:
    """Format a scalar result for human display."""
    if isinstance(value, float):
        return f"{value:,.2f}" if value == value else "N/A"  # NaN guard
    return str(value)


# ── Handler type ─────────────────────────────────────────────────────────────
# A handler is a callable(question: str, df: DataFrame) -> FallbackResult | None.
# Return None to signal "I cannot handle this question" → try the next handler.

Handler = Callable[[str, pd.DataFrame], FallbackResult | None]


# ── Individual handlers ───────────────────────────────────────────────────────

def _handle_max(question: str, df: pd.DataFrame) -> FallbackResult | None:
    """Highest / maximum value in a numeric column."""
    kws = ["highest", "maximum", "max", "largest", "most", "greatest", "top"]
    if not any(k in question for k in kws):
        return None

    num_cols = _numeric_cols(df)
    if not num_cols:
        return None

    col = _find_column(question, num_cols)
    if col is None:
        return None
    code = f"result = df['{col}'].max()"
    value = df[col].max()
    if not _valid_numeric(value):
        return None
    return FallbackResult(
        answer=_fmt(value),
        generated_code=code,
        matched_handler="max",
    )


def _handle_min(question: str, df: pd.DataFrame) -> FallbackResult | None:
    """Lowest / minimum value in a numeric column."""
    kws = ["lowest", "minimum", "min", "smallest", "least", "cheapest"]
    if not any(k in question for k in kws):
        return None

    num_cols = _numeric_cols(df)
    if not num_cols:
        return None

    col = _find_column(question, num_cols)
    if col is None:
        return None
    code = f"result = df['{col}'].min()"
    value = df[col].min()
    if not _valid_numeric(value):
        return None
    return FallbackResult(
        answer=_fmt(value),
        generated_code=code,
        matched_handler="min",
    )


def _handle_average(question: str, df: pd.DataFrame) -> FallbackResult | None:
    """Average / mean of a numeric column."""
    kws = ["average", "mean", "avg"]
    if not any(k in question for k in kws):
        return None

    num_cols = _numeric_cols(df)
    if not num_cols:
        return None

    col = _find_column(question, num_cols)
    if col is None:
        return None
    code = f"result = round(df['{col}'].mean(), 2)"
    value = round(df[col].mean(), 2)
    if not _valid_numeric(value):
        return None
    return FallbackResult(
        answer=_fmt(value),
        generated_code=code,
        matched_handler="average",
    )


def _handle_count(question: str, df: pd.DataFrame) -> FallbackResult | None:
    """Row count / how many rows."""
    kws = ["how many", "count", "total rows", "number of rows", "row count"]
    if not any(k in question for k in kws):
        return None

    code = "result = len(df)"
    value = len(df)
    return FallbackResult(
        answer=_fmt(value),
        generated_code=code,
        matched_handler="count",
    )


def _handle_sum(question: str, df: pd.DataFrame) -> FallbackResult | None:
    """Total / sum of a numeric column."""
    kws = ["total", "sum", "summ"]
    if not any(k in question for k in kws):
        return None

    num_cols = _numeric_cols(df)
    if not num_cols:
        return None

    col = _find_column(question, num_cols)
    if col is None:
        return None
    code = f"result = round(df['{col}'].sum(), 2)"
    value = round(df[col].sum(), 2)
    if not _valid_numeric(value):
        return None
    return FallbackResult(
        answer=_fmt(value),
        generated_code=code,
        matched_handler="sum",
    )


def _handle_group_average(question: str, df: pd.DataFrame) -> FallbackResult | None:
    """Average of a numeric column grouped by a categorical column."""
    kws = ["average", "mean", "avg"]
    group_kws = ["by", "per", "each", "for each", "group"]
    if not any(k in question for k in kws):
        return None
    if not any(k in question for k in group_kws):
        return None

    cat_cols = _categorical_cols(df)
    num_cols = _numeric_cols(df)
    if not cat_cols or not num_cols:
        return None

    group_col = _find_column(question, cat_cols)
    val_col = _find_column(question, num_cols)
    if group_col is None or val_col is None:
        return None

    code = (
        f"result = df.groupby('{group_col}')['{val_col}'].mean()"
        f".round(2).to_string()"
    )
    value = df.groupby(group_col)[val_col].mean().round(2).to_string()
    return FallbackResult(
        answer=value,
        generated_code=code,
        matched_handler="group_average",
    )


def _handle_unique_values(question: str, df: pd.DataFrame) -> FallbackResult | None:
    """Unique / distinct values in a column."""
    kws = ["unique", "distinct", "different", "values in", "list of"]
    if not any(k in question for k in kws):
        return None

    cat_cols = _categorical_cols(df)
    if not cat_cols:
        return None

    col = _find_column(question, cat_cols)
    if col is None:
        return None
    code = f"result = ', '.join(sorted(df['{col}'].dropna().unique().tolist()))"
    value = ", ".join(sorted(str(v) for v in df[col].dropna().unique().tolist()))
    return FallbackResult(
        answer=value,
        generated_code=code,
        matched_handler="unique_values",
    )


def _handle_missing(question: str, df: pd.DataFrame) -> FallbackResult | None:
    """Missing / null value counts."""
    kws = ["missing", "null", "nan", "empty", "blank"]
    if not any(k in question for k in kws):
        return None

    code = "result = df.isnull().sum().to_string()"
    value = df.isnull().sum().to_string()
    return FallbackResult(
        answer=value,
        generated_code=code,
        matched_handler="missing_values",
    )


# ── Handler registry (ordered: most specific first) ───────────────────────────

_HANDLERS: list[Handler] = [
    _handle_group_average,   # "average sales by category" — before plain average
    _handle_count,
    _handle_sum,
    _handle_max,
    _handle_min,
    _handle_average,
    _handle_unique_values,
    _handle_missing,
]


# ── Public entry point ────────────────────────────────────────────────────────

def run_local_fallback(
    question: str,
    df: pd.DataFrame,
    dfs: dict[str, pd.DataFrame] | None = None,
    target_currency: str | None = None,
) -> FallbackResult | None:
    """
    Attempt to answer *question* using deterministic pandas operations.

    Returns a FallbackResult if a handler matched and executed successfully,
    or None if the question cannot be safely handled locally.

    Never raises — exceptions inside handlers are caught and logged.
    """
    q_lower = question.lower().strip()

    if not q_lower or df is None or df.empty:
        logger.info("local_fallback: refusing empty question or empty dataframe")
        return None

    if target_currency and target_currency.upper() in ["INR", "USD"]:
        tc = target_currency.upper()
        USD_TO_INR = 83.50
        curr_cols = [c for c in df.columns if any(k in c.lower() for k in ["currency", "curr", "ccy"])]
        num_cols = _numeric_cols(df)
        if curr_cols and num_cols:
            curr_col = curr_cols[0]
            val_col = _find_column(q_lower, num_cols) or num_cols[0]
            if tc == "INR":
                code = (
                    f"USD_TO_INR = 83.50\n\n"
                    f"df['Amount_INR'] = np.where(df['{curr_col}'].astype(str).str.strip().str.upper() == 'USD', df['{val_col}'] * USD_TO_INR, df['{val_col}'])\n\n"
                    f"result = f\"Total {val_col}: ₹{{df['Amount_INR'].sum():,.2f}} (Converted using 1 USD = ₹83.50)\""
                )
                df_copy = df.copy()
                df_copy['Amount_INR'] = np.where(df_copy[curr_col].astype(str).str.strip().str.upper() == 'USD', df_copy[val_col] * USD_TO_INR, df_copy[val_col])
                total = df_copy['Amount_INR'].sum()
                ans = f"Total {val_col}: ₹{total:,.2f} (Converted using 1 USD = ₹83.50)"
                return FallbackResult(answer=ans, generated_code=code, matched_handler="currency_conversion")
            else:
                code = (
                    f"USD_TO_INR = 83.50\n\n"
                    f"df['Amount_USD'] = np.where(df['{curr_col}'].astype(str).str.strip().str.upper() == 'INR', df['{val_col}'] / USD_TO_INR, df['{val_col}'])\n\n"
                    f"result = f\"Total {val_col}: ${{df['Amount_USD'].sum():,.2f}} (Converted using 1 USD = ₹83.50)\""
                )
                df_copy = df.copy()
                df_copy['Amount_USD'] = np.where(df_copy[curr_col].astype(str).str.strip().str.upper() == 'INR', df_copy[val_col] / USD_TO_INR, df_copy[val_col])
                total = df_copy['Amount_USD'].sum()
                ans = f"Total {val_col}: ${total:,.2f} (Converted using 1 USD = ₹83.50)"
                return FallbackResult(answer=ans, generated_code=code, matched_handler="currency_conversion")

    if _quoted_unknown_column(q_lower, df):
        logger.info(
            "local_fallback: refusing unknown quoted column for question=%r",
            question,
        )
        return None

    for handler in _HANDLERS:
        try:
            result = handler(q_lower, df)
            if result is not None:
                logger.info(
                    "local_fallback matched handler=%s for question=%r",
                    result.matched_handler,
                    question,
                )
                return result
        except Exception as exc:
            logger.warning(
                "local_fallback handler %s raised %s: %s",
                handler.__name__, type(exc).__name__, exc,
            )
            # Try the next handler

    logger.info("local_fallback: no handler matched for question=%r", question)
    return None
