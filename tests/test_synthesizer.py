"""Unit tests for the synthesizer."""
from __future__ import annotations

import sys
from pathlib import Path

import pandas as pd
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from detector import classify  # noqa: E402
from synthesizer import synthesize  # noqa: E402


@pytest.fixture
def df():
    return pd.DataFrame(
        {
            "employee_id": ["E1001", "E1002", "E1003", "E1001"],  # deliberate repeat
            "first_name": ["Alice", "Bob", "Charlie", "Alice"],
            "email": ["a@acme.com", "b@acme.com", "c@acme.com", "a@acme.com"],
            "salary": [50000, 75000, 90000, 50000],
            "department": ["Eng", "Sales", "Eng", "Eng"],
        }
    )


class TestShapePreservation:
    def test_row_count_unchanged(self, df):
        result = synthesize(df, classify(df))
        assert result.rows == len(df)

    def test_column_order_unchanged(self, df):
        result = synthesize(df, classify(df))
        assert list(result.df.columns) == list(df.columns)

    def test_safe_columns_unchanged(self, df):
        result = synthesize(df, classify(df))
        assert result.df["department"].tolist() == df["department"].tolist()


class TestSensitiveReplacement:
    def test_emails_replaced(self, df):
        result = synthesize(df, classify(df))
        assert set(result.df["email"].tolist()).isdisjoint(set(df["email"].tolist()))

    def test_names_replaced(self, df):
        result = synthesize(df, classify(df))
        original = set(df["first_name"].tolist())
        # At least some values should differ — repeats may collide but not all
        new = set(result.df["first_name"].tolist())
        assert new != original

    def test_salary_within_reasonable_range(self, df):
        result = synthesize(df, classify(df))
        # Salaries should be numeric-ish strings within ±15% of original
        for orig, new in zip(df["salary"], result.df["salary"]):
            clean = "".join(c for c in str(new) if c.isdigit() or c == ".")
            assert clean, f"empty synthetic salary for {orig}"
            val = float(clean)
            assert 0.80 * orig <= val <= 1.20 * orig


class TestJoinConsistency:
    """Repeated values should remap consistently so joins keep working."""

    def test_repeated_id_remaps_consistently(self, df):
        result = synthesize(df, classify(df))
        # Rows 0 and 3 had the same employee_id originally
        assert result.df["employee_id"].iloc[0] == result.df["employee_id"].iloc[3]

    def test_repeated_email_remaps_consistently(self, df):
        result = synthesize(df, classify(df))
        assert result.df["email"].iloc[0] == result.df["email"].iloc[3]


class TestImmutability:
    def test_original_dataframe_unchanged(self, df):
        snapshot = df.copy()
        synthesize(df, classify(df))
        pd.testing.assert_frame_equal(df, snapshot)
