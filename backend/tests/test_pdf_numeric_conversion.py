"""
tests/test_pdf_numeric_conversion.py

Regression tests for the pandas-3.0-compatible numeric conversion logic
in _parse_pdf (core/file_parser.py).

Covers:
  A. Pure-text column  → must stay as text, no NaN introduced
  B. Pure-numeric column → must be converted to numeric dtype
  C. Mixed / currency column ("INR 184,000") → must NOT become all-NaN;
     original string values must be preserved
  D. Empty-string cells → treated as null, must not affect non-null count
  E. Pandas >= 3.0 compatibility: errors="ignore" is gone; logic must not
     raise TypeError or produce silent data loss
"""

import sys
import os
import pandas as pd
import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))


# ── Re-implement the exact conversion logic from _parse_pdf so the test
#    exercises the real algorithm without needing a real PDF file. ────────────

def _safe_numeric_convert(df: pd.DataFrame) -> pd.DataFrame:
    """
    Mirror of the conversion loop in _parse_pdf.
    Only replaces a column when coercion loses no non-null values.
    """
    df = df.copy()
    for col in df.columns:
        converted = pd.to_numeric(df[col], errors="coerce")
        original_non_null = df[col].notna().sum()
        converted_non_null = converted.notna().sum()
        if converted_non_null == original_non_null:
            df[col] = converted
    return df


# ── A. Pure-text column must stay as text ─────────────────────────────────────

def test_text_column_preserved():
    """Region column with cardinal directions must not become NaN."""
    df = pd.DataFrame({
        "Region": ["South", "North", "West", "East"],
        "Units":  ["10", "20", "30", "40"],
    })
    result = _safe_numeric_convert(df)

    # Region must be unchanged
    assert list(result["Region"]) == ["South", "North", "West", "East"]
    assert result["Region"].notna().all(), "Region column must have no NaN"


# ── B. Pure-numeric column must be converted ─────────────────────────────────

def test_numeric_column_converted():
    """A column containing only numeric strings must become a numeric dtype."""
    df = pd.DataFrame({
        "Revenue": ["184000", "105000", "92000", "71000"],
    })
    result = _safe_numeric_convert(df)

    assert pd.api.types.is_numeric_dtype(result["Revenue"]), (
        "Pure-numeric string column should be converted to numeric dtype"
    )
    assert result["Revenue"].tolist() == [184000, 105000, 92000, 71000]


# ── C. Currency strings must NOT become NaN ──────────────────────────────────

def test_currency_string_column_preserved():
    """'INR 184,000'-style values must survive unchanged, not become NaN."""
    currency_values = ["INR 184,000", "INR 105,000", "INR 92,000", "INR 71,000"]
    df = pd.DataFrame({"Revenue": currency_values})
    result = _safe_numeric_convert(df)

    # No value should become NaN
    assert result["Revenue"].notna().all(), (
        "Currency strings must not be coerced to NaN"
    )
    # Original values must be intact
    assert list(result["Revenue"]) == currency_values


# ── D. Mixed column (some numeric, some text) must stay as-is ────────────────

def test_mixed_column_preserved():
    """A column with both numeric and text values must not lose the text values."""
    mixed = ["100", "N/A", "200", "unknown"]
    df = pd.DataFrame({"Value": mixed})
    result = _safe_numeric_convert(df)

    # The two numeric entries would survive coercion, but the two text entries
    # would not → converted_non_null (2) < original_non_null (4) → keep original
    assert list(result["Value"]) == mixed, (
        "Mixed column must be preserved when coercion would lose values"
    )


# ── E. Empty-string treated as null — pure-numeric column still converts ──────

# ── E. Empty-string behaviour in pandas 3 ────────────────────────────────────

def test_empty_string_treated_as_non_null_in_pandas3():
    """
    In pandas 3, empty strings '' are NOT null — notna() returns True for them.
    pd.to_numeric("", errors="coerce") → NaN, so the non-null counts diverge
    and the column is correctly kept as-is (no data loss).
    This test documents and pins that behaviour.
    """
    df = pd.DataFrame({"Score": ["95", "", "87", ""]})
    result = _safe_numeric_convert(df)

    # pandas 3: "" is not null, so original_non_null=4, converted_non_null=2
    # → counts differ → column kept unchanged (safe, no data loss)
    assert list(result["Score"]) == ["95", "", "87", ""], (
        "Column with empty strings must be preserved unchanged in pandas 3"
    )
    assert result["Score"].notna().all(), (
        "Empty strings are non-null in pandas 3"
    )


# ── F. Mixed table (Region + numeric Revenue) from a PDF-like extraction ──────

def test_pdf_like_table_preserves_text_and_converts_numeric():
    """
    Simulates the sales_report.pdf table:
      Region  | Revenue
      South   | 184000
      North   | 105000
    Region stays string; Revenue becomes numeric.
    """
    df = pd.DataFrame({
        "Region":  ["South", "North", "West", "East"],
        "Revenue": ["184000", "105000", "92000", "71000"],
    })
    result = _safe_numeric_convert(df)

    # Region: text → preserved
    assert list(result["Region"]) == ["South", "North", "West", "East"]
    assert result["Region"].notna().all()

    # Revenue: numeric strings → converted
    assert pd.api.types.is_numeric_dtype(result["Revenue"])
    assert result["Revenue"].tolist() == [184000, 105000, 92000, 71000]


# ── G. pandas >= 3.0 compatibility: errors="ignore" must not be used ─────────

def test_no_errors_ignore_in_file_parser():
    """
    Guard against future regressions: ensure file_parser.py does not use
    the removed errors='ignore' argument in actual code (comments are fine).
    """
    import re as _re

    parser_path = os.path.join(
        os.path.dirname(__file__), "..", "core", "file_parser.py"
    )
    with open(parser_path) as f:
        lines = f.readlines()

    # Check every non-comment, non-blank line for errors="ignore"
    violations = []
    for lineno, line in enumerate(lines, start=1):
        stripped = line.lstrip()
        if stripped.startswith("#"):
            continue   # skip comment lines
        if 'errors="ignore"' in line or "errors='ignore'" in line:
            violations.append((lineno, line.rstrip()))

    assert not violations, (
        f"file_parser.py must not use errors='ignore' in live code "
        f"(removed in pandas 3.0). Found at: {violations}"
    )
