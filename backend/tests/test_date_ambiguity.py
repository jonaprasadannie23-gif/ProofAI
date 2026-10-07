"""
tests/test_date_ambiguity.py

Focused tests for DataAnalyst._check_date_ambiguity().

Cases:
  A. 03/04/2026 in a date-intent question  → refused  (both parts ≤ 12)
  B. 13/04/2026 in a date-intent question  → not refused  (13 > 12, unambiguous)
  C. 04/13/2026 in a date-intent question  → not refused  (13 > 12, unambiguous)
  D. No date in question                   → not refused  (no date-intent match)
  E. ISO date 2026-04-03 in question       → not refused  (slash regex not matched)
  F. Refusal message content               → mentions both interpretations
  G. No date-intent keyword                → not refused  (gate fails)
"""

import sys
import os

import pandas as pd
import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from core.analyst import DataAnalyst

# A minimal DataFrame that satisfies the analyst's data-quality checks.
_DF = pd.DataFrame({
    "OrderID": [1, 2, 3, 4],
    "Amount":  [100.0, 200.0, 300.0, 400.0],
    "OrderDate": ["2026-03-04", "2026-04-13", "2026-01-01", "2026-06-15"],
})


@pytest.fixture
def analyst():
    return DataAnalyst()


# ── A. Ambiguous date → refused ───────────────────────────────────────────────

def test_ambiguous_date_refused(analyst):
    """03/04/2026 — both 3 and 4 are ≤ 12 → refused."""
    result = analyst._check_date_ambiguity(
        "How many orders were placed on 03/04/2026?", _DF
    )
    assert result is not None, "Expected a refusal message, got None"
    assert "03/04/2026" in result
    assert "ambiguous" in result.lower()


# ── B. Unambiguous date (left > 12) → not refused ────────────────────────────

def test_unambiguous_date_left_gt_12(analyst):
    """13/04/2026 — left part 13 > 12, cannot be a month → not refused."""
    result = analyst._check_date_ambiguity(
        "How many orders were placed on 13/04/2026?", _DF
    )
    assert result is None, f"Expected None, got: {result}"


# ── C. Unambiguous date (right > 12) → not refused ───────────────────────────

def test_unambiguous_date_right_gt_12(analyst):
    """04/13/2026 — right part 13 > 12, cannot be a month → not refused."""
    result = analyst._check_date_ambiguity(
        "How many orders were placed on 04/13/2026?", _DF
    )
    assert result is None, f"Expected None, got: {result}"


# ── D. No date in question → not refused ─────────────────────────────────────

def test_no_date_in_question(analyst):
    """Pure numeric question with no date intent → not refused."""
    result = analyst._check_date_ambiguity(
        "What is the total amount?", _DF
    )
    assert result is None, f"Expected None, got: {result}"


# ── E. ISO date format → not refused ─────────────────────────────────────────

def test_iso_date_not_refused(analyst):
    """2026-04-03 uses ISO format (YYYY-MM-DD), slash regex won't match → not refused."""
    result = analyst._check_date_ambiguity(
        "How many orders were placed on 2026-04-03?", _DF
    )
    assert result is None, f"Expected None, got: {result}"


# ── F. Refusal message content ────────────────────────────────────────────────

def test_refusal_message_mentions_both_interpretations(analyst):
    """The refusal message must name both possible interpretations."""
    result = analyst._check_date_ambiguity(
        "How many orders were placed on 03/04/2026?", _DF
    )
    assert result is not None
    # Must mention the DD/MM interpretation: 3 April 2026
    assert "April" in result
    # Must mention the MM/DD interpretation: 4 March 2026
    assert "March" in result
    # Must mention both format labels
    assert "DD/MM/YYYY" in result
    assert "MM/DD/YYYY" in result
    # Must ask user to specify
    assert "specify" in result.lower() or "format" in result.lower()


# ── G. Date in question but no date-intent keyword → not refused ──────────────

def test_slash_date_without_date_intent_keyword(analyst):
    """
    '3/4 of the orders' contains a slash-number pattern but no date-intent
    keyword — the gate must block the regex scan.
    """
    result = analyst._check_date_ambiguity(
        "What is 3/4 of the total revenue?", _DF
    )
    assert result is None, f"Expected None, got: {result}"


# ── H. Edge: both parts exactly 12 → still ambiguous ────────────────────────

def test_both_parts_12_is_ambiguous(analyst):
    """12/12/2026 — both parts are 12, both ≤ 12 → ambiguous."""
    result = analyst._check_date_ambiguity(
        "Show records from 12/12/2026", _DF
    )
    assert result is not None, "12/12 should be considered ambiguous"


# ── I. Both parts are 1 → ambiguous ──────────────────────────────────────────

def test_both_parts_1_is_ambiguous(analyst):
    """01/01/2026 — both parts are 1, both ≤ 12 → ambiguous."""
    result = analyst._check_date_ambiguity(
        "Orders placed on 01/01/2026", _DF
    )
    assert result is not None, "01/01 should be considered ambiguous"
