"""Unit tests for the detection engine.

Run with:  python -m pytest -v
"""
from __future__ import annotations

import sys
from pathlib import Path

import pandas as pd
import pytest

# Make parent importable when running pytest from the repo root
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from detector import SENSITIVE, SAFE, classify  # noqa: E402


def _frame(**cols) -> pd.DataFrame:
    return pd.DataFrame(cols)


class TestColumnNameHints:
    """Name-based detection should fire regardless of values."""

    def test_email_column(self):
        df = _frame(email=["a@b.com", "c@d.io"])
        det = classify(df)[0]
        assert det.category == "EMAIL"
        assert det.tier == SENSITIVE

    def test_name_column(self):
        df = _frame(first_name=["Alice", "Bob"], last_name=["X", "Y"])
        out = {d.column: d for d in classify(df)}
        assert out["first_name"].category == "NAME"
        assert out["last_name"].category == "NAME"
        assert all(d.tier == SENSITIVE for d in out.values())

    def test_ssn_column(self):
        df = _frame(ssn=["123-45-6789", "234-56-7890"])
        det = classify(df)[0]
        assert det.category == "ID"
        assert det.tier == SENSITIVE

    def test_salary_column(self):
        df = _frame(salary=[50000, 75000, 90000])
        det = classify(df)[0]
        assert det.category == "FINANCIAL"
        assert det.tier == SENSITIVE

    def test_department_is_safe(self):
        df = _frame(department=["Eng", "Sales", "Eng"])
        det = classify(df)[0]
        assert det.tier == SAFE

    def test_boolean_is_safe(self):
        df = _frame(is_admin=[True, False, True])
        det = classify(df)[0]
        assert det.tier == SAFE


class TestValuePatternFallback:
    """When column name is unhelpful, value shape should classify."""

    def test_email_values_without_name(self):
        df = _frame(contact=["a@b.com", "c@d.io", "e@f.net"])
        det = classify(df)[0]
        # 'contact' matches "EMAIL" hint by substring, so this tests hint-first
        assert det.tier == SENSITIVE

    def test_phone_values_without_name(self):
        df = _frame(reachout=["(415) 555-1234", "(212) 555-6789", "(310) 555-0001"])
        det = classify(df)[0]
        # value pattern forces PHONE classification
        assert det.category == "PHONE"
        assert det.tier == SENSITIVE


class TestParanoidDefault:
    """When nothing matches, high-cardinality columns default to FREE_TEXT."""

    def test_high_cardinality_unknown_column(self):
        df = _frame(xyz=[f"unique_val_{i}" for i in range(20)])
        det = classify(df)[0]
        assert det.tier == SENSITIVE
        assert det.category == "FREE_TEXT"

    def test_low_cardinality_unknown_column(self):
        df = _frame(xyz=["A", "B", "A", "A", "B", "A"])
        det = classify(df)[0]
        assert det.tier == SAFE
        assert det.category == "CATEGORICAL"


class TestEdgeCases:
    def test_empty_dataframe(self):
        df = pd.DataFrame()
        assert classify(df) == []

    def test_all_null_column(self):
        df = _frame(salary=[None, None, None])
        det = classify(df)[0]
        # Name hint wins even when all values are null
        assert det.category == "FINANCIAL"

    def test_case_insensitive_column_names(self):
        df = _frame(EMAIL=["x@y.com"], Phone=["(415) 555-0001"])
        out = {d.column: d for d in classify(df)}
        assert out["EMAIL"].category == "EMAIL"
        assert out["Phone"].category == "PHONE"
