"""I/O helpers — robust CSV/XLSX reading and writing.

Avoids surprises with encodings, delimiters, and the occasional Excel file
with merged cells or multiple sheets.
"""
from __future__ import annotations

import io
from pathlib import Path

import pandas as pd


SUPPORTED_SUFFIXES = {".csv", ".tsv", ".xlsx", ".xls", ".xlsm"}


def read_any(file_or_path, sheet_name: str | int | None = 0) -> pd.DataFrame:
    """Read a CSV/TSV/XLSX into a DataFrame.

    Accepts either a filesystem path, an open file-like object (Streamlit's
    UploadedFile), or bytes. Tries UTF-8 then falls back to latin-1.
    """
    if isinstance(file_or_path, (str, Path)):
        suffix = Path(str(file_or_path)).suffix.lower()
        data = Path(file_or_path).read_bytes()
    else:
        # Streamlit UploadedFile has .name and .getvalue()
        name = getattr(file_or_path, "name", "upload.csv")
        suffix = Path(name).suffix.lower()
        data = file_or_path.getvalue() if hasattr(file_or_path, "getvalue") else file_or_path.read()

    if suffix in {".xlsx", ".xls", ".xlsm"}:
        return pd.read_excel(io.BytesIO(data), sheet_name=sheet_name, engine="openpyxl" if suffix != ".xls" else None)

    # CSV / TSV path
    sep = "\t" if suffix == ".tsv" else ","
    for encoding in ("utf-8", "utf-8-sig", "latin-1"):
        try:
            return pd.read_csv(io.BytesIO(data), sep=sep, encoding=encoding)
        except UnicodeDecodeError:
            continue
    raise ValueError("Could not decode file with utf-8, utf-8-sig, or latin-1.")


def to_csv_bytes(df: pd.DataFrame) -> bytes:
    """Serialize a DataFrame to CSV bytes (UTF-8, no BOM)."""
    return df.to_csv(index=False).encode("utf-8")


def to_xlsx_bytes(df: pd.DataFrame) -> bytes:
    """Serialize a DataFrame to XLSX bytes."""
    buf = io.BytesIO()
    df.to_excel(buf, index=False, engine="openpyxl")
    return buf.getvalue()
