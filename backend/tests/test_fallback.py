"""
tests/test_fallback.py

Tests covering:
  A. Gemini success path           → analysis_mode == "gemini"
  B. Gemini 503 → local fallback   → analysis_mode == "local_fallback"
  C. Gemini 429 → local fallback   → analysis_mode == "local_fallback"
  D. Unsupported question          → status == "refused"
  E. Real df calculation           → answer derived from actual df values
  F. Retry constants preserved     → 503 server, 429 client

All tests are synchronous where possible (asyncio.run for async).
No real Gemini API calls are made — the Gemini layer is monkey-patched.
"""

import asyncio
import sys
import os
import types as builtin_types

import pandas as pd
import pytest

# ── path setup ────────────────────────────────────────────────────────────────
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from core.local_fallback import run_local_fallback, FallbackResult
from core.llm import (
    GeminiUnavailableError,
    _RETRYABLE_SERVER_CODES,
    _RETRYABLE_CLIENT_CODES,
)
from core.analyst import DataAnalyst
from google.genai import errors as genai_errors


# ── shared fixtures ───────────────────────────────────────────────────────────

def _sales_df() -> pd.DataFrame:
    """Small deterministic sales dataframe — mirrors sample_data/sales.csv shape."""
    return pd.DataFrame({
        "product":  ["Widget A", "Widget B", "Gadget X", "Chair Pro", "Desk Lite"],
        "category": ["Electronics", "Electronics", "Electronics", "Furniture", "Furniture"],
        "region":   ["North", "South", "East", "North", "West"],
        "sales":    [1200.50, 850.00, 2200.00, 450.75, 320.00],
        "units":    [10, 7, 15, 3, 2],
        "rating":   [4.2, 3.9, 4.8, 4.5, 4.1],
    })


def _run(coro):
    """Run an async coroutine synchronously."""
    return asyncio.run(coro)


def _make_server_error(code: int) -> genai_errors.ServerError:
    """Construct a ServerError without hitting the network."""
    return genai_errors.ServerError(
        code,
        {"error": {"code": code, "status": "UNAVAILABLE", "message": "test"}},
    )


def _make_client_error(code: int) -> genai_errors.ClientError:
    """Construct a ClientError without hitting the network."""
    return genai_errors.ClientError(
        code,
        {"error": {"code": code, "status": "RESOURCE_EXHAUSTED", "message": "test"}},
    )


# ═══════════════════════════════════════════════════════════════════════════════
# A. GEMINI SUCCESS PATH
# ═══════════════════════════════════════════════════════════════════════════════

def test_gemini_success_returns_gemini_mode(monkeypatch):
    """When Gemini succeeds, analysis_mode must be 'gemini'."""
    df = _sales_df()
    analyst = DataAnalyst()

    async def mock_generate(*args, **kwargs):
        return "result = df['sales'].max()"

    monkeypatch.setattr("core.analyst.generate_analysis_code", mock_generate)

    result = _run(analyst.analyze("What is the highest sales?", df, "test.csv"))

    assert result["status"] == "success"
    assert result["analysis_mode"] == "gemini"
    assert result["answer"] is not None
    # Gemini verification detail should NOT mention fallback
    assert "local" not in result["verification_detail"].lower()


def test_gemini_success_executes_real_code(monkeypatch):
    """The code returned by Gemini must actually be executed against df."""
    df = _sales_df()
    analyst = DataAnalyst()

    async def mock_generate(*args, **kwargs):
        return "result = int(df['units'].sum())"

    monkeypatch.setattr("core.analyst.generate_analysis_code", mock_generate)

    result = _run(analyst.analyze("Total units sold?", df, "test.csv"))

    assert result["status"] == "success"
    expected = str(int(df["units"].sum()))
    assert result["answer"] == expected


# ═══════════════════════════════════════════════════════════════════════════════
# B. GEMINI 503 → LOCAL FALLBACK
# ═══════════════════════════════════════════════════════════════════════════════

def test_503_triggers_local_fallback(monkeypatch):
    """GeminiUnavailableError (from 503) must route to local fallback."""
    df = _sales_df()
    analyst = DataAnalyst()

    async def mock_generate(*args, **kwargs):
        raise GeminiUnavailableError("503 simulated")

    monkeypatch.setattr("core.analyst.generate_analysis_code", mock_generate)

    result = _run(analyst.analyze("What is the highest sales value?", df, "test.csv"))

    assert result["status"] == "success"
    assert result["analysis_mode"] == "local_fallback"
    assert "gemini temporarily unavailable" in result["verification_detail"].lower()
    assert result["answer"] is not None
    # Answer must be derived from real data, not hardcoded
    assert result["answer"] == "2,200.00"   # max(sales) in fixture


def test_503_fallback_includes_generated_code(monkeypatch):
    """Fallback results must include the generated Python code."""
    df = _sales_df()
    analyst = DataAnalyst()

    async def mock_generate(*args, **kwargs):
        raise GeminiUnavailableError("503 simulated")

    monkeypatch.setattr("core.analyst.generate_analysis_code", mock_generate)

    result = _run(analyst.analyze("What is the highest sales value?", df, "test.csv"))

    assert result["generated_code"] is not None
    assert "df[" in result["generated_code"]   # real pandas code, not a placeholder


def test_503_fallback_warning_included(monkeypatch):
    """A warning about Gemini being unavailable must appear in warnings."""
    df = _sales_df()
    analyst = DataAnalyst()

    async def mock_generate(*args, **kwargs):
        raise GeminiUnavailableError("503 simulated")

    monkeypatch.setattr("core.analyst.generate_analysis_code", mock_generate)

    result = _run(analyst.analyze("What is the highest sales value?", df, "test.csv"))

    assert any("gemini" in w.lower() for w in result["warnings"])


# ═══════════════════════════════════════════════════════════════════════════════
# C. GEMINI 429 → LOCAL FALLBACK
# ═══════════════════════════════════════════════════════════════════════════════

def test_429_triggers_local_fallback(monkeypatch):
    """GeminiUnavailableError (from 429) must also route to local fallback."""
    df = _sales_df()
    analyst = DataAnalyst()

    async def mock_generate(*args, **kwargs):
        # analyst.py catches GeminiUnavailableError regardless of the HTTP code
        # that caused it; _call_with_retry raises this after exhausting 429 retries
        raise GeminiUnavailableError("429 rate limit simulated")

    monkeypatch.setattr("core.analyst.generate_analysis_code", mock_generate)

    result = _run(analyst.analyze("How many rows are in this dataset?", df, "test.csv"))

    assert result["status"] == "success"
    assert result["analysis_mode"] == "local_fallback"
    assert result["answer"] == str(len(df))   # real count from fixture


def test_429_is_in_retryable_client_codes():
    """The retry layer must list 429 as a retryable client error code."""
    assert 429 in _RETRYABLE_CLIENT_CODES


def test_503_is_in_retryable_server_codes():
    """The retry layer must list 503 as a retryable server error code."""
    assert 503 in _RETRYABLE_SERVER_CODES


# ═══════════════════════════════════════════════════════════════════════════════
# D. UNSUPPORTED QUESTION → SAFE REFUSAL
# ═══════════════════════════════════════════════════════════════════════════════

def test_unsupported_question_refused_when_gemini_down(monkeypatch):
    """If Gemini is unavailable and fallback can't handle the question → refused."""
    df = _sales_df()
    analyst = DataAnalyst()

    async def mock_generate(*args, **kwargs):
        raise GeminiUnavailableError("503 simulated")

    monkeypatch.setattr("core.analyst.generate_analysis_code", mock_generate)

    # "Predict" requires complex reasoning that local fallback cannot handle
    result = _run(analyst.analyze(
        "Predict next month revenue based on trend analysis",
        df, "test.csv"
    ))

    assert result["status"] == "refused"
    assert result["analysis_mode"] == "refused"
    assert "unable to verify" in result["verification_detail"].lower()
    assert result["answer"] is None
    assert result["generated_code"] is None


def test_unsupported_question_analysis_mode_is_refused(monkeypatch):
    """analysis_mode must be 'refused' when fallback cannot answer."""
    df = _sales_df()
    analyst = DataAnalyst()

    async def mock_generate(*args, **kwargs):
        raise GeminiUnavailableError("503 simulated")

    monkeypatch.setattr("core.analyst.generate_analysis_code", mock_generate)

    result = _run(analyst.analyze(
        "Cluster the products using k-means and explain the results",
        df, "test.csv"
    ))

    assert result["analysis_mode"] == "refused"


# ═══════════════════════════════════════════════════════════════════════════════
# E. REAL DATAFRAME CALCULATION (values must come from actual df)
# ═══════════════════════════════════════════════════════════════════════════════

class TestFallbackCalculations:
    """Verify every handler computes from actual df values, never hardcodes."""

    def setup_method(self):
        self.df = _sales_df()

    def test_max_sales(self):
        r = run_local_fallback("What is the highest sales value?", self.df)
        assert r is not None
        assert r.matched_handler == "max"
        expected = f"{self.df['sales'].max():,.2f}"
        assert r.answer == expected

    def test_min_sales(self):
        r = run_local_fallback("What is the lowest sales value?", self.df)
        assert r is not None
        assert r.matched_handler == "min"
        expected = f"{self.df['sales'].min():,.2f}"
        assert r.answer == expected

    def test_average_rating(self):
        r = run_local_fallback("What is the average rating?", self.df)
        assert r is not None
        assert r.matched_handler == "average"
        expected = f"{round(self.df['rating'].mean(), 2):,.2f}"
        assert r.answer == expected

    def test_count_rows(self):
        r = run_local_fallback("How many rows are in this dataset?", self.df)
        assert r is not None
        assert r.matched_handler == "count"
        assert r.answer == str(len(self.df))

    def test_total_sales(self):
        r = run_local_fallback("What is the total sales?", self.df)
        assert r is not None
        assert r.matched_handler == "sum"
        expected = f"{round(self.df['sales'].sum(), 2):,.2f}"
        assert r.answer == expected

    def test_group_average_sales_by_category(self):
        r = run_local_fallback("What is the average sales by category?", self.df)
        assert r is not None
        assert r.matched_handler == "group_average"
        # Answer must contain real category names
        assert "Electronics" in r.answer
        assert "Furniture" in r.answer
        # Values must be computable from df, not hardcoded
        elec_avg = round(
            self.df[self.df["category"] == "Electronics"]["sales"].mean(), 2
        )
        assert str(elec_avg) in r.answer.replace(",", "")

    def test_answer_changes_with_different_df(self):
        """If the df changes, the answer must change — proving no hardcoding."""
        df_modified = self.df.copy()
        df_modified.loc[0, "sales"] = 99999.0   # inflate one value

        r_original = run_local_fallback("What is the highest sales value?", self.df)
        r_modified = run_local_fallback("What is the highest sales value?", df_modified)

        assert r_original is not None
        assert r_modified is not None
        # Modified df must produce a different answer
        assert r_original.answer != r_modified.answer
        assert "99,999.00" in r_modified.answer

    def test_fallback_result_includes_code(self):
        """Every FallbackResult must include valid Python code."""
        r = run_local_fallback("What is the total sales?", self.df)
        assert r is not None
        assert "result" in r.generated_code
        assert "df[" in r.generated_code

    def test_fallback_returns_none_for_unknown_question(self):
        """run_local_fallback must return None for questions it cannot handle."""
        r = run_local_fallback(
            "What is the eigenvalue decomposition of the covariance matrix?",
            self.df,
        )
        assert r is None

    def test_fallback_returns_none_for_vague_question(self):
        """Vague questions with no matching keyword must return None."""
        r = run_local_fallback("Tell me something interesting.", self.df)
        assert r is None


# ═══════════════════════════════════════════════════════════════════════════════
# F. RETRY BEHAVIOR UNIT TESTS
# ═══════════════════════════════════════════════════════════════════════════════

def test_retry_exhausts_four_attempts_on_503(monkeypatch):
    """_call_with_retry must try exactly 4 times before raising GeminiUnavailableError."""
    import core.llm as llm_mod

    call_count = 0

    async def always_503():
        nonlocal call_count
        call_count += 1
        raise _make_server_error(503)

    # Patch sleep to avoid real waiting
    async def fast_sleep(s):
        pass

    monkeypatch.setattr(llm_mod.asyncio, "sleep", fast_sleep)

    with pytest.raises(GeminiUnavailableError):
        _run(llm_mod._call_with_retry(always_503))

    assert call_count == 4  # 1 immediate + 3 retries


def test_retry_exhausts_four_attempts_on_429(monkeypatch):
    """_call_with_retry must try exactly 4 times before raising GeminiUnavailableError."""
    import core.llm as llm_mod

    call_count = 0

    async def always_429():
        nonlocal call_count
        call_count += 1
        raise _make_client_error(429)

    async def fast_sleep(s):
        pass

    monkeypatch.setattr(llm_mod.asyncio, "sleep", fast_sleep)

    with pytest.raises(GeminiUnavailableError):
        _run(llm_mod._call_with_retry(always_429))

    assert call_count == 4


def test_401_is_not_retried(monkeypatch):
    """A 401 ClientError (bad API key) must propagate immediately, no retries."""
    import core.llm as llm_mod

    call_count = 0

    async def bad_key():
        nonlocal call_count
        call_count += 1
        raise _make_client_error(401)

    async def fast_sleep(s):
        pass

    monkeypatch.setattr(llm_mod.asyncio, "sleep", fast_sleep)

    with pytest.raises(genai_errors.ClientError):
        _run(llm_mod._call_with_retry(bad_key))

    assert call_count == 1  # must NOT retry


def test_500_server_error_not_retried(monkeypatch):
    """A 500 internal server error must propagate immediately, no retries."""
    import core.llm as llm_mod

    call_count = 0

    async def server_crash():
        nonlocal call_count
        call_count += 1
        raise _make_server_error(500)

    async def fast_sleep(s):
        pass

    monkeypatch.setattr(llm_mod.asyncio, "sleep", fast_sleep)

    with pytest.raises(genai_errors.ServerError):
        _run(llm_mod._call_with_retry(server_crash))

    assert call_count == 1


def test_retry_succeeds_on_third_attempt(monkeypatch):
    """If the API recovers on the 3rd attempt, the result must be returned."""
    import core.llm as llm_mod

    call_count = 0

    async def flaky():
        nonlocal call_count
        call_count += 1
        if call_count < 3:
            raise _make_server_error(503)
        return "recovered"

    async def fast_sleep(s):
        pass

    monkeypatch.setattr(llm_mod.asyncio, "sleep", fast_sleep)

    result = _run(llm_mod._call_with_retry(flaky))

    assert result == "recovered"
    assert call_count == 3


# ═══════════════════════════════════════════════════════════════════════════════
# G. API RESPONSE COMPATIBILITY
# ═══════════════════════════════════════════════════════════════════════════════

def test_fallback_response_has_all_required_fields(monkeypatch):
    """Fallback response must include all fields the frontend expects."""
    df = _sales_df()
    analyst = DataAnalyst()

    async def mock_generate(*args, **kwargs):
        raise GeminiUnavailableError("503 simulated")

    monkeypatch.setattr("core.analyst.generate_analysis_code", mock_generate)

    result = _run(analyst.analyze("What is the highest sales value?", df, "test.csv"))

    required_fields = [
        "status", "answer", "verification", "verification_detail",
        "generated_code", "dataset_summary", "data_quality",
        "warnings", "ai_answer", "code_result", "match", "analysis_mode",
    ]
    for field in required_fields:
        assert field in result, f"Missing field: {field}"


def test_refused_response_has_all_required_fields(monkeypatch):
    """Refusal response (unsupported question) must include all frontend fields."""
    df = _sales_df()
    analyst = DataAnalyst()

    async def mock_generate(*args, **kwargs):
        raise GeminiUnavailableError("503 simulated")

    monkeypatch.setattr("core.analyst.generate_analysis_code", mock_generate)

    result = _run(analyst.analyze(
        "Run a neural network forecast on next year sales",
        df, "test.csv"
    ))

    required_fields = [
        "status", "answer", "verification", "verification_detail",
        "generated_code", "dataset_summary", "data_quality",
        "warnings", "ai_answer", "code_result", "match", "analysis_mode",
    ]
    for field in required_fields:
        assert field in result, f"Missing field: {field}"

    assert result["status"] == "refused"


# ═══════════════════════════════════════════════════════════════════════════════
# E. MISSING COLUMN → SAFE REFUSAL
# ═══════════════════════════════════════════════════════════════════════════════

def test_missing_column_refused_when_gemini_down(monkeypatch):
    """If the requested column does not exist, fallback must refuse (no guess)."""
    df = _sales_df()
    analyst = DataAnalyst()

    async def mock_generate(*args, **kwargs):
        raise GeminiUnavailableError("503 simulated")

    monkeypatch.setattr("core.analyst.generate_analysis_code", mock_generate)

    result = _run(analyst.analyze(
        "What is the highest revenue?",
        df, "test.csv",
    ))

    assert result["status"] == "refused"
    assert result["analysis_mode"] == "refused"
    assert result["answer"] is None
    assert result["generated_code"] is None


def test_fallback_returns_none_for_missing_column():
    """run_local_fallback must not invent a column when the named one is absent."""
    df = _sales_df()
    r = run_local_fallback("What is the highest revenue?", df)
    assert r is None


def test_fallback_returns_none_for_quoted_missing_column():
    df = _sales_df()
    r = run_local_fallback("What is the average of 'profit_margin'?", df)
    assert r is None


def test_fallback_does_not_guess_first_numeric_column():
    """A max/min/avg question with no column name must refuse, not pick col 0."""
    df = _sales_df()
    r = run_local_fallback("What is the highest value?", df)
    assert r is None


# ═══════════════════════════════════════════════════════════════════════════════
# G. EXISTING BACKEND IMPORTS
# ═══════════════════════════════════════════════════════════════════════════════

def test_existing_backend_imports():
    import core.local_fallback as lf
    import core.llm as llm
    import core.analyst as analyst_mod
    import core.code_executor as executor
    import api.routes as routes
    import main as app_main

    assert lf.run_local_fallback is not None
    assert llm.generate_analysis_code is not None
    assert analyst_mod.DataAnalyst is not None
    assert executor.execute_code is not None
    assert routes.router is not None
    assert app_main.app is not None


# ═══════════════════════════════════════════════════════════════════════════════
# H. SYNTAX COMPILATION + NO HARDCODED DATASET ANSWERS
# ═══════════════════════════════════════════════════════════════════════════════

def test_changed_backend_files_compile():
    import py_compile

    backend_root = os.path.join(os.path.dirname(__file__), "..")
    files = [
        os.path.join(backend_root, "core", "local_fallback.py"),
        os.path.join(backend_root, "core", "llm.py"),
        os.path.join(backend_root, "core", "analyst.py"),
        os.path.join(backend_root, "api", "routes.py"),
        os.path.join(backend_root, "tests", "test_fallback.py"),
    ]
    for path in files:
        py_compile.compile(path, doraise=True)


def test_production_fallback_has_no_hardcoded_dataset_answers():
    """local_fallback.py must compute from df — no baked-in sample-data numbers."""
    src_path = os.path.join(
        os.path.dirname(__file__), "..", "core", "local_fallback.py"
    )
    with open(src_path, encoding="utf-8") as f:
        src = f.read()
    forbidden = ["2200", "1200.50", "850.00", "450.75", "320.00", "Widget A"]
    for token in forbidden:
        assert token not in src, f"Hardcoded dataset token found: {token}"
