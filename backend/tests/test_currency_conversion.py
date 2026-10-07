"""
tests/test_currency_conversion.py — Unit tests for interactive safe currency conversion in ProofAI.
"""

import sys
import os
import asyncio
import pandas as pd
import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from core.analyst import DataAnalyst
from core.local_fallback import run_local_fallback


def test_mixed_currency_refusal_with_conversion_options():
    df = pd.DataFrame({
        "Paid_Amount": [100.0, 8350.0],
        "Currency": ["USD", "INR"]
    })
    analyst = DataAnalyst()
    res = asyncio.run(analyst.analyze(
        question="What is the total Paid_Amount?",
        df=df,
        filename="payments.csv"
    ))
    assert res["status"] == "refused"
    assert res["verification"] == "REFUSED"
    assert "contains INR and USD" in res["verification_detail"]
    assert res.get("currency_conversion_options") is not None
    assert res["currency_conversion_options"]["available"] is True
    assert res["currency_conversion_options"]["rate"] == 83.50


def test_currency_conversion_to_inr():
    df = pd.DataFrame({
        "Paid_Amount": [100.0, 8350.0],
        "Currency": ["USD", "INR"]
    })
    analyst = DataAnalyst()
    res = asyncio.run(analyst.analyze(
        question="What is the total Paid_Amount?",
        df=df,
        filename="payments.csv",
        target_currency="INR"
    ))
    assert res["status"] == "success"
    assert res["verification"] == "VERIFIED"
    assert "₹" in str(res["answer"]) or "16,700" in str(res["answer"]) or "16700" in str(res["answer"])
    assert "USD_TO_INR = 83.50" in res["generated_code"]


def test_currency_conversion_to_usd():
    df = pd.DataFrame({
        "Paid_Amount": [100.0, 8350.0],
        "Currency": ["USD", "INR"]
    })
    analyst = DataAnalyst()
    res = asyncio.run(analyst.analyze(
        question="What is the total Paid_Amount?",
        df=df,
        filename="payments.csv",
        target_currency="USD"
    ))
    assert res["status"] == "success"
    assert res["verification"] == "VERIFIED"
    assert "$" in str(res["answer"]) or "200" in str(res["answer"])
    assert "USD_TO_INR = 83.50" in res["generated_code"]


def test_unsupported_currency_pair_refusal():
    df = pd.DataFrame({
        "Paid_Amount": [100.0, 200.0],
        "Currency": ["EUR", "GBP"]
    })
    analyst = DataAnalyst()
    res = asyncio.run(analyst.analyze(
        question="What is the total Paid_Amount?",
        df=df,
        filename="payments.csv"
    ))
    assert res["status"] == "refused"
    opts = res.get("currency_conversion_options")
    assert opts is None or opts.get("available") is False
