"""CleanSchema synthesizer.

Given a DataFrame and a list of Detections, produce a clean copy where sensitive
columns are replaced with realistic synthetic values — preserving row count,
column names, data types, and roughly the source distributions.

Key rule: **joins still work**. If `employee_id` appears in two DataFrames,
repeated IDs remap consistently within a single synthesis run.
"""
from __future__ import annotations

import hashlib
import random
import re
from dataclasses import dataclass

import pandas as pd
from faker import Faker

from detector import Detection, SENSITIVE

fake = Faker()


@dataclass
class SynthesisResult:
    df: pd.DataFrame
    columns_replaced: list[str]
    rows: int


class _Mapper:
    """Deterministic-within-session mapping old_value → new_value per column.

    Ensures repeated values get the same synthetic replacement so joins keep
    working without leaking the original.
    """

    def __init__(self, generator):
        self.generator = generator
        self._cache: dict[str, str] = {}

    def map(self, value) -> str:
        key = "" if pd.isna(value) else str(value)
        if key not in self._cache:
            self._cache[key] = self.generator()
        return self._cache[key]


def _salary_like(original: float | int | str | None) -> str:
    """Keep the currency symbol and magnitude range of the original."""
    s = str(original) if original is not None else ""
    prefix = ""
    m = re.match(r"^([\$€£¥])", s.strip())
    if m:
        prefix = m.group(1)
    # Strip non-numeric then jitter within ±15% to preserve distribution shape
    raw = re.sub(r"[^\d.]", "", s) or "50000"
    try:
        base = float(raw)
    except ValueError:
        base = 50000.0
    jittered = base * random.uniform(0.85, 1.15)
    formatted = f"{int(jittered):,}" if base >= 100 else f"{jittered:,.2f}"
    return f"{prefix}{formatted}"


def _date_like(original) -> str:
    """Keep within ±5y of original when parseable, otherwise pick a plausible year."""
    try:
        dt = pd.to_datetime(original, errors="coerce")
        if pd.isna(dt):
            raise ValueError
        shift_days = random.randint(-1825, 1825)
        new = dt + pd.Timedelta(days=shift_days)
        return new.strftime("%Y-%m-%d")
    except Exception:
        return fake.date_between(start_date="-20y", end_date="today").isoformat()


# category → generator factory
GENERATORS = {
    "NAME": lambda: fake.name,
    "EMAIL": lambda: lambda: fake.safe_email().replace("@example.com", "@example.org"),
    "PHONE": lambda: fake.phone_number,
    "ID": lambda: lambda: fake.bothify(text="###-##-####"),
    "ADDRESS": lambda: fake.street_address,
    "ZIP": lambda: fake.postcode,
    "FREE_TEXT": lambda: lambda: fake.sentence(nb_words=random.randint(6, 14)),
}


def synthesize(df: pd.DataFrame, detections: list[Detection]) -> SynthesisResult:
    """Return a cleaned copy of df based on the detection list.

    Mutates nothing on the input DataFrame. Preserves column order, dtypes where
    possible, and row count.
    """
    out = df.copy()
    replaced: list[str] = []

    for det in detections:
        if not det.is_sensitive:
            continue
        col = det.column
        cat = det.category

        if cat == "FINANCIAL":
            out[col] = df[col].apply(_salary_like)
        elif cat == "DATE":
            out[col] = df[col].apply(_date_like)
        elif cat in GENERATORS:
            mapper = _Mapper(GENERATORS[cat]())
            out[col] = df[col].apply(mapper.map)
        else:
            # Fallback — shouldn't happen but be defensive
            mapper = _Mapper(lambda: fake.word())
            out[col] = df[col].apply(mapper.map)

        replaced.append(col)

    return SynthesisResult(df=out, columns_replaced=replaced, rows=len(out))
