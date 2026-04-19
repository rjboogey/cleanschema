"""CleanSchema detection engine.

Classifies each column of a DataFrame into one of 13 sensitive types based on
column name hints + sampled value patterns. Column name matching is the primary
signal because it's deterministic and fast; value regex is a fallback.

No network calls. No telemetry. Every rule is visible below.
"""
from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Iterable

import pandas as pd

# ---------------------------------------------------------------------------
# Sensitivity tiers
# ---------------------------------------------------------------------------

SENSITIVE = "sensitive"  # value should be replaced with synthetic
SAFE = "safe"            # value can pass through

# ---------------------------------------------------------------------------
# Category definitions — the 13 types promised on cleanschema.app
# ---------------------------------------------------------------------------
# Each category has:
#   name     — display label
#   tier     — SENSITIVE or SAFE
#   hints    — substrings matched against lowercased column names
#   pattern  — optional regex matched against values; a high match rate on
#              sampled non-null values confirms the category when name hints
#              are ambiguous.

CATEGORIES: list[dict] = [
    {
        "name": "EMAIL",
        "tier": SENSITIVE,
        "hints": ("email", "mail", "contact_email", "e_mail"),
        "pattern": re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$"),
    },
    {
        "name": "PHONE",
        "tier": SENSITIVE,
        "hints": ("phone", "mobile", "cell", "tel", "telephone", "fax"),
        "pattern": re.compile(r"^[\+\(]?[\d][\d\s\-\(\)\.]{6,}\d$"),
    },
    {
        "name": "ID",
        "tier": SENSITIVE,
        "hints": (
            "ssn", "social_security", "taxid", "tax_id", "ein",
            "employee_id", "emp_id", "account_no", "account_num",
            "customer_id", "user_id", "member_id", "license", "passport",
        ),
        "pattern": re.compile(r"^\d{3}[- ]?\d{2}[- ]?\d{4}$"),  # SSN shape
    },
    {
        "name": "NAME",
        "tier": SENSITIVE,
        "hints": (
            "first_name", "last_name", "full_name", "firstname", "lastname",
            "fullname", "customer_name", "user_name", "employee_name",
            "contact_name", "given_name", "family_name", "surname",
        ),
        "pattern": None,
    },
    {
        "name": "ADDRESS",
        "tier": SENSITIVE,
        "hints": (
            "address", "street", "street1", "street2", "addr", "line1", "line2",
            "city", "state", "country", "region_name",
        ),
        "pattern": None,
    },
    {
        "name": "ZIP",
        "tier": SENSITIVE,
        "hints": ("zip", "zipcode", "zip_code", "postal", "postal_code", "postcode"),
        "pattern": re.compile(r"^\d{5}(-\d{4})?$|^[A-Z]\d[A-Z][ -]?\d[A-Z]\d$"),
    },
    {
        "name": "FINANCIAL",
        "tier": SENSITIVE,
        "hints": (
            "salary", "wage", "compensation", "income", "revenue",
            "amount", "price", "cost", "balance", "total_paid",
        ),
        # Money strings like "$87,500" or "87500.00"
        "pattern": re.compile(r"^[\$€£¥]?\s*-?[\d,]+(\.\d+)?$"),
    },
    {
        "name": "DATE",
        "tier": SENSITIVE,
        "hints": (
            "dob", "birth", "birthdate", "date_of_birth", "hire_date",
            "created_at", "updated_at", "start_date", "end_date",
            "joined", "signup_date",
        ),
        "pattern": re.compile(
            r"^\d{4}[-/]\d{1,2}[-/]\d{1,2}"
            r"|\d{1,2}[-/]\d{1,2}[-/]\d{2,4}$"
        ),
    },
    {
        "name": "FREE_TEXT",
        "tier": SENSITIVE,
        # Free-text fields can leak PII in unpredictable ways — strip them.
        "hints": ("notes", "note", "description", "comments", "comment", "feedback", "reason"),
        "pattern": None,
    },
    # -- safe categories below --
    {
        "name": "CATEGORICAL",
        "tier": SAFE,
        "hints": (
            "department", "dept", "status", "region", "type", "category",
            "tier", "plan", "role", "level", "group",
        ),
        "pattern": None,
    },
    {
        "name": "NUMERIC",
        "tier": SAFE,
        "hints": ("count", "units", "quantity", "qty", "volume", "orders", "rows", "visits"),
        "pattern": re.compile(r"^-?\d+(\.\d+)?$"),
    },
    {
        "name": "PERCENTAGE",
        "tier": SAFE,
        "hints": ("rate", "pct", "percent", "completion", "ratio"),
        "pattern": re.compile(r"^-?(100|\d{1,2})(\.\d+)?%?$"),
    },
    {
        "name": "BOOLEAN",
        "tier": SAFE,
        "hints": ("active", "is_", "has_", "enabled", "admin", "deleted", "archived"),
        "pattern": re.compile(r"^(true|false|yes|no|y|n|1|0|t|f)$", re.IGNORECASE),
    },
]


@dataclass
class Detection:
    column: str
    category: str
    tier: str
    reason: str  # human-readable explanation

    @property
    def is_sensitive(self) -> bool:
        return self.tier == SENSITIVE


def _name_match(col: str, hints: Iterable[str]) -> str | None:
    """Return the matching hint substring, or None."""
    lo = col.lower().strip()
    for h in hints:
        if h in lo:
            return h
    return None


def _value_match_rate(series: pd.Series, pattern: re.Pattern, sample: int = 50) -> float:
    """Fraction of sampled non-null values that match the regex."""
    if pattern is None:
        return 0.0
    non_null = series.dropna().astype(str).head(sample)
    if len(non_null) == 0:
        return 0.0
    hits = sum(1 for v in non_null if pattern.match(v.strip()))
    return hits / len(non_null)


def classify(df: pd.DataFrame) -> list[Detection]:
    """Classify every column in the DataFrame.

    Column-name match wins. Falls back to a value-shape check at >=70% hit rate.
    If nothing matches, default to CATEGORICAL (safe) when cardinality is low
    vs FREE_TEXT (sensitive) when cardinality is high — a paranoid default.
    """
    out: list[Detection] = []
    for col in df.columns:
        series = df[col]
        matched = None

        # Pass 1: column name hints (most reliable)
        for cat in CATEGORIES:
            hint = _name_match(col, cat["hints"])
            if hint:
                matched = (cat, f"column name contains '{hint}'")
                break

        # Pass 2: value shape regex
        if not matched:
            for cat in CATEGORIES:
                if cat["pattern"] is None:
                    continue
                rate = _value_match_rate(series, cat["pattern"])
                if rate >= 0.7:
                    matched = (cat, f"{int(rate * 100)}% of values match {cat['name']} shape")
                    break

        # Pass 3: paranoid default
        if not matched:
            nunique = series.nunique(dropna=True)
            total = len(series.dropna())
            if total > 0 and nunique / total > 0.5:
                # high cardinality = probably not a bucket — treat as free text
                matched = (
                    next(c for c in CATEGORIES if c["name"] == "FREE_TEXT"),
                    "high-cardinality text — defaulting to FREE_TEXT (paranoid)",
                )
            else:
                matched = (
                    next(c for c in CATEGORIES if c["name"] == "CATEGORICAL"),
                    "no match — low-cardinality values pass through as CATEGORICAL",
                )

        cat, reason = matched
        out.append(Detection(column=col, category=cat["name"], tier=cat["tier"], reason=reason))

    return out
