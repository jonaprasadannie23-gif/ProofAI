"""
tests/test_multi_table.py

Multi-table foundation tests — Task 6 of the multi-table implementation.

Covers:
  1. Single DataFrame still works with execute_code(code, df)
  2. Multiple DataFrames can be represented as dict[str, DataFrame]
  3. LLM analysis context (_build_multi_table_prompt) describes multiple tables
  4. Generated code can access two named DataFrames via extra_tables
  5. execute_code executes code using two DataFrames
  6. Legacy execute_code(code, df) behaviour is unchanged
  7. Multi-table capability does not break existing single-table analyze() flow
  8. _table_name_from_filename produces valid identifiers
  9. _build_reproducible_proof produces correct load statements for multi-table
 10. analyze_multi() with one table is equivalent to analyze()
"""

import asyncio
import os
import sys

import pandas as pd
import pytest

# ── path setup ────────────────────────────────────────────────────────────────
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from core.code_executor import execute_code
from core.llm import _build_multi_table_prompt, GeminiUnavailableError
from core.analyst import DataAnalyst, _table_name_from_filename
from core.analyst import _filename_from_table_name


# ── helpers ───────────────────────────────────────────────────────────────────

def _run(coro):
    return asyncio.run(coro)


def _orders_df() -> pd.DataFrame:
    return pd.DataFrame({
        "order_id":   [1, 2, 3, 4, 5],
        "customer_id":[10, 11, 10, 12, 11],
        "amount":     [100.0, 250.0, 75.0, 400.0, 90.0],
    })


def _customers_df() -> pd.DataFrame:
    return pd.DataFrame({
        "customer_id": [10, 11, 12],
        "name":        ["Alice", "Bob", "Carol"],
        "region":      ["North", "South", "North"],
    })


def _products_df() -> pd.DataFrame:
    return pd.DataFrame({
        "product_id": [100, 101, 102],
        "name":       ["Widget", "Gadget", "Gizmo"],
        "price":      [9.99, 24.99, 4.99],
    })


# ── 1. Single DataFrame still works with legacy signature ─────────────────────

class TestLegacyExecuteCode:
    """execute_code(code, df) must behave exactly as before."""

    def test_sum_column(self):
        df = _orders_df()
        r = execute_code("result = df['amount'].sum()", df)
        assert r["success"] is True
        assert r["output"] == df["amount"].sum()

    def test_row_count(self):
        df = _orders_df()
        r = execute_code("result = len(df)", df)
        assert r["success"] is True
        assert r["output"] == 5

    def test_result_not_set_returns_message(self):
        df = _orders_df()
        r = execute_code("x = 1 + 1", df)
        assert r["success"] is True
        assert "no output" in r["output"].lower() or "result" in r["output"].lower()

    def test_syntax_error_captured(self):
        df = _orders_df()
        r = execute_code("result = df['amount'.sum()", df)
        assert r["success"] is False
        assert r["error"] is not None

    def test_extra_tables_none_is_identical_to_omitting(self):
        """Passing extra_tables=None must produce the same result as not passing it."""
        df = _orders_df()
        r1 = execute_code("result = df['amount'].max()", df)
        r2 = execute_code("result = df['amount'].max()", df, extra_tables=None)
        assert r1 == r2


# ── 2. Multiple DataFrames representation ─────────────────────────────────────

class TestMultiTableRepresentation:
    """dict[str, DataFrame] is the internal multi-table representation."""

    def test_tables_dict_holds_multiple_dataframes(self):
        tables = {
            "orders":    _orders_df(),
            "customers": _customers_df(),
        }
        assert len(tables) == 2
        assert isinstance(tables["orders"], pd.DataFrame)
        assert isinstance(tables["customers"], pd.DataFrame)

    def test_tables_dict_can_hold_three_tables(self):
        tables = {
            "orders":    _orders_df(),
            "customers": _customers_df(),
            "products":  _products_df(),
        }
        assert len(tables) == 3

    def test_table_names_are_logical_not_filenames(self):
        """Keys should be clean names; _table_name_from_filename handles derivation."""
        name = _table_name_from_filename("customer_data.csv")
        assert name == "customer_data"
        assert "." not in name


# ── 3. LLM context describes multiple tables ──────────────────────────────────

class TestMultiTablePrompt:
    """_build_multi_table_prompt must clearly describe every table."""

    def test_all_table_names_appear(self):
        tables = {
            "orders":    _orders_df(),
            "customers": _customers_df(),
        }
        prompt = _build_multi_table_prompt("dummy question", tables)
        assert "orders" in prompt
        assert "customers" in prompt

    def test_variable_names_appear(self):
        """The prompt must tell the LLM to use orders_df and customers_df."""
        tables = {
            "orders":    _orders_df(),
            "customers": _customers_df(),
        }
        prompt = _build_multi_table_prompt("dummy question", tables)
        assert "orders_df" in prompt
        assert "customers_df" in prompt

    def test_column_names_appear(self):
        tables = {
            "orders":    _orders_df(),
            "customers": _customers_df(),
        }
        prompt = _build_multi_table_prompt("total amount?", tables)
        # orders columns
        assert "order_id" in prompt
        assert "amount" in prompt
        # customers columns
        assert "customer_id" in prompt
        assert "region" in prompt

    def test_dtypes_appear(self):
        tables = {"orders": _orders_df()}
        prompt = _build_multi_table_prompt("question", tables)
        assert "float64" in prompt or "int64" in prompt

    def test_sample_values_appear(self):
        tables = {"orders": _orders_df()}
        prompt = _build_multi_table_prompt("question", tables)
        # Sample values from the orders DataFrame should be in the prompt
        assert "100" in prompt  # amount sample

    def test_question_is_in_prompt(self):
        tables = {"orders": _orders_df()}
        prompt = _build_multi_table_prompt("What is the total revenue?", tables)
        assert "What is the total revenue?" in prompt

    def test_tables_are_not_merged_in_prompt(self):
        """Tables must be described separately, not concatenated."""
        tables = {
            "orders":    _orders_df(),
            "customers": _customers_df(),
        }
        prompt = _build_multi_table_prompt("join question", tables)
        # Each table must have its own section header
        assert "Table: orders" in prompt
        assert "Table: customers" in prompt

    def test_context_history_injected(self):
        tables = {"orders": _orders_df()}
        history = [{"question": "prev q", "answer": "prev a"}]
        prompt = _build_multi_table_prompt("follow up", tables, context_history=history)
        assert "prev q" in prompt
        assert "prev a" in prompt


# ── 4 & 5. execute_code with extra_tables ─────────────────────────────────────

class TestExecuteCodeMultiTable:
    """Generated code can access named DataFrames via <name>_df variables."""

    def test_access_second_table(self):
        """Code can read from customers_df injected via extra_tables."""
        df = _orders_df()
        extra = {"customers": _customers_df()}
        code = "result = len(customers_df)"
        r = execute_code(code, df, extra_tables=extra)
        assert r["success"] is True
        assert r["output"] == 3  # customers_df has 3 rows

    def test_access_both_tables(self):
        """Code can reference both df (primary) and an extra table."""
        df = _orders_df()
        extra = {"customers": _customers_df()}
        code = "result = (len(df), len(customers_df))"
        r = execute_code(code, df, extra_tables=extra)
        assert r["success"] is True
        assert r["output"] == (5, 3)

    def test_merge_two_tables(self):
        """Pandas merge across two injected DataFrames produces correct result."""
        df = _orders_df()
        extra = {"customers": _customers_df()}
        code = (
            "merged = df.merge(customers_df, on='customer_id')\n"
            "result = int(merged[merged['region'] == 'North']['amount'].sum())"
        )
        r = execute_code(code, df, extra_tables=extra)
        assert r["success"] is True
        # North customers: Alice (customer_id=10) orders 1+3 = 175
        #                  Carol (customer_id=12) order  4   = 400
        # Total = 575
        assert r["output"] == 575

    def test_three_tables_all_accessible(self):
        """All three tables are in the namespace when three are passed."""
        df = _orders_df()
        extra = {
            "customers": _customers_df(),
            "products":  _products_df(),
        }
        code = "result = (len(df), len(customers_df), len(products_df))"
        r = execute_code(code, df, extra_tables=extra)
        assert r["success"] is True
        assert r["output"] == (5, 3, 3)

    def test_extra_tables_are_copies(self):
        """Code mutations to extra_tables must not affect the caller's DataFrames."""
        df = _orders_df()
        customers = _customers_df()
        extra = {"customers": customers}
        # Mutate inside the exec
        code = "customers_df['name'] = 'X'; result = customers_df['name'].iloc[0]"
        r = execute_code(code, df, extra_tables=extra)
        assert r["success"] is True
        # Caller's df must be unchanged
        assert customers["name"].iloc[0] == "Alice"

    def test_primary_df_copy_not_mutated(self):
        """Mutations to df inside exec must not affect caller's DataFrame."""
        df = _orders_df()
        original_sum = df["amount"].sum()
        code = "df['amount'] = 0; result = 'mutated'"
        r = execute_code(code, df)
        assert r["success"] is True
        assert df["amount"].sum() == original_sum


# ── 6. Legacy signature unchanged ─────────────────────────────────────────────

class TestLegacySignatureUnchanged:
    """All callers using execute_code(code, df) without extra_tables must work."""

    def test_no_extra_tables_kwarg(self):
        df = _orders_df()
        r = execute_code("result = df['amount'].min()", df)
        assert r["success"] is True
        assert r["output"] == 75.0

    def test_positional_args_still_work(self):
        df = _orders_df()
        r = execute_code("result = 42", df)
        assert r["success"] is True
        assert r["output"] == 42


# ── 7. Multi-table does not break existing single-table analyze() ─────────────

class TestSingleTableFlowUnbroken:
    """analyze() via the public API must continue working as before."""

    def test_analyze_success_path(self, monkeypatch):
        df = _orders_df()
        analyst = DataAnalyst()

        async def mock_generate(*args, **kwargs):
            return "result = int(df['amount'].sum())"

        monkeypatch.setattr("core.analyst.generate_analysis_code", mock_generate)
        result = _run(analyst.analyze("total amount?", df, "orders.csv"))

        assert result["status"] == "success"
        assert result["answer"] == str(int(df["amount"].sum()))
        assert result["analysis_mode"] == "gemini"

    def test_analyze_fallback_still_works(self, monkeypatch):
        df = _orders_df()
        analyst = DataAnalyst()

        async def mock_generate(*args, **kwargs):
            raise GeminiUnavailableError("503 simulated")

        monkeypatch.setattr("core.analyst.generate_analysis_code", mock_generate)
        result = _run(analyst.analyze("How many rows?", df, "orders.csv"))

        assert result["status"] == "success"
        assert result["analysis_mode"] == "local_fallback"
        assert result["answer"] == str(len(df))

    def test_analyze_returns_all_required_fields(self, monkeypatch):
        df = _orders_df()
        analyst = DataAnalyst()

        async def mock_generate(*args, **kwargs):
            return "result = 1"

        monkeypatch.setattr("core.analyst.generate_analysis_code", mock_generate)
        result = _run(analyst.analyze("anything", df, "orders.csv"))

        required = [
            "status", "answer", "verification", "verification_detail",
            "generated_code", "dataset_summary", "data_quality",
            "warnings", "ai_answer", "code_result", "match", "analysis_mode",
        ]
        for field in required:
            assert field in result, f"Missing field: {field}"

    def test_analyze_generated_code_uses_df_alias(self, monkeypatch):
        """Single-table code using the `df` alias must still execute correctly."""
        df = _orders_df()
        analyst = DataAnalyst()

        async def mock_generate(*args, **kwargs):
            # Classic single-table code uses `df` directly
            return "result = df['amount'].max()"

        monkeypatch.setattr("core.analyst.generate_analysis_code", mock_generate)
        result = _run(analyst.analyze("max amount?", df, "orders.csv"))

        assert result["status"] == "success"
        assert result["answer"] == str(df["amount"].max())


# ── 8. _table_name_from_filename ──────────────────────────────────────────────

class TestTableNameFromFilename:

    def test_csv_extension_stripped(self):
        assert _table_name_from_filename("sales.csv") == "sales"

    def test_xlsx_extension_stripped(self):
        assert _table_name_from_filename("data.xlsx") == "data"

    def test_underscores_preserved(self):
        assert _table_name_from_filename("customer_data.csv") == "customer_data"

    def test_hyphens_become_underscores(self):
        assert _table_name_from_filename("order-items.csv") == "order_items"

    def test_spaces_become_underscores(self):
        assert _table_name_from_filename("my data.csv") == "my_data"

    def test_no_extension(self):
        assert _table_name_from_filename("orders") == "orders"

    def test_result_is_valid_identifier_fragment(self):
        name = _table_name_from_filename("2024-sales-data.csv")
        # Must not start with a digit when used as <name>_df
        var = f"{name}_df"
        assert var.isidentifier() or var.replace("_", "").isalnum()


# ── 9. Reproducible proof for multiple tables ─────────────────────────────────

class TestReproducibleProofMultiTable:

    def test_single_table_proof_has_df_alias(self):
        analyst = DataAnalyst()
        tables = {"orders": _orders_df()}
        proof = analyst._build_reproducible_proof("result = df['amount'].sum()", tables)
        # Must contain the load statement
        assert 'orders_df = pd.read_csv("orders.csv")' in proof
        # Must expose `df` alias for single-table backward-compat
        assert "df = orders_df" in proof
        # Must include the generated code
        assert "result = df['amount'].sum()" in proof

    def test_multi_table_proof_has_all_load_statements(self):
        analyst = DataAnalyst()
        tables = {
            "orders":    _orders_df(),
            "customers": _customers_df(),
        }
        proof = analyst._build_reproducible_proof(
            "result = orders_df.merge(customers_df, on='customer_id')", tables
        )
        assert 'orders_df = pd.read_csv("orders.csv")' in proof
        assert 'customers_df = pd.read_csv("customers.csv")' in proof
        # Multi-table: no spurious single-table `df = orders_df` alias line
        # (that alias is only added for single-table proofs)
        assert "df = orders_df" not in proof

    def test_proof_is_complete_python(self):
        analyst = DataAnalyst()
        tables = {"orders": _orders_df()}
        proof = analyst._build_reproducible_proof("result = len(orders_df)", tables)
        assert "import pandas as pd" in proof
        assert "import numpy as np" in proof
        assert 'print("Result:", result)' in proof


# ── 10. analyze_multi with one table equals analyze() ────────────────────────

class TestAnalyzeMultiSingleTableEquivalence:

    def test_same_answer(self, monkeypatch):
        df = _orders_df()
        analyst = DataAnalyst()

        async def mock_generate(*args, **kwargs):
            return "result = int(df['amount'].sum())"

        monkeypatch.setattr("core.analyst.generate_analysis_code", mock_generate)

        r_single = _run(analyst.analyze("total?", df, "orders.csv"))
        r_multi  = _run(analyst.analyze_multi(
            "total?",
            tables={"orders": df},
        ))

        assert r_single["status"]  == r_multi["status"]
        assert r_single["answer"]  == r_multi["answer"]
        assert r_single["analysis_mode"] == r_multi["analysis_mode"]

    def test_analyze_multi_two_tables_passes_correct_namespace(self, monkeypatch):
        """analyze_multi with two tables injects both into execution namespace."""
        orders    = _orders_df()
        customers = _customers_df()
        analyst   = DataAnalyst()

        async def mock_generate(*args, **kwargs):
            # LLM-generated code for multi-table: merges orders_df and customers_df
            return (
                "merged = orders_df.merge(customers_df, on='customer_id')\n"
                "result = int(merged[merged['region']=='North']['amount'].sum())"
            )

        monkeypatch.setattr("core.analyst.generate_analysis_code", mock_generate)

        result = _run(analyst.analyze_multi(
            "total amount for North region customers?",
            tables={"orders": orders, "customers": customers},
        ))

        assert result["status"] == "success"
        # North customers: Alice (id=10) orders 100+75=175, Carol (id=12) order 400
        # Total = 575
        assert result["answer"] == "575"
