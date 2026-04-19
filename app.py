"""CleanSchema — Streamlit app entrypoint.

    $ streamlit run app.py

Or double-click `run.command` on macOS / `run.bat` on Windows / `run.sh` on Linux.

Philosophy: no network, no telemetry, no login. The file enters memory, leaves
as a clean copy. Every rule lives in detector.py — read it.
"""
from __future__ import annotations

import time
from pathlib import Path

import pandas as pd
import streamlit as st

from detector import CATEGORIES, SENSITIVE, Detection, classify
from io_utils import read_any, to_csv_bytes, to_xlsx_bytes
from synthesizer import synthesize

# ---------------------------------------------------------------------------
# Theme + page config
# ---------------------------------------------------------------------------
st.set_page_config(
    page_title="CleanSchema · Strip the secrets. Keep the structure.",
    page_icon="🧼",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# Brand color from cleanschema.app
ACCENT = "#E63946"

st.markdown(
    f"""
    <style>
        :root {{ --accent: {ACCENT}; }}
        .stApp {{ background: #0a0a0a; color: #e0e0e0; }}
        .cs-hero {{ padding: 1rem 0 2rem 0; border-bottom: 1px solid #222; }}
        .cs-hero h1 {{ font-size: 2.6rem; font-weight: 900; margin: 0; color: #fff; }}
        .cs-hero p  {{ color: #888; margin-top: 0.5rem; font-size: 1.05rem; }}
        .cs-badge   {{ display:inline-block; padding:2px 10px; border-radius:999px;
                        font-size:0.72rem; letter-spacing:0.05em; font-weight:700;
                        margin-right:0.4rem; vertical-align: middle; }}
        .cs-badge.sens {{ background: rgba(230,57,70,0.12); color: var(--accent); border: 1px solid rgba(230,57,70,0.35); }}
        .cs-badge.safe {{ background: rgba(20, 180, 120, 0.12); color: #36d399; border: 1px solid rgba(20,180,120,0.35); }}
        .cs-promise {{ color:#888; font-size:0.8rem; margin-top:0.4rem; }}
        .stDataFrame {{ border: 1px solid #222; border-radius: 8px; }}
        .stButton>button {{ background: var(--accent); color: #fff; font-weight: 700;
                              border: none; padding: 0.6rem 1.4rem; border-radius: 8px; }}
        .stDownloadButton>button {{ background: var(--accent); color: #fff; font-weight: 700;
                                      border: none; padding: 0.6rem 1.4rem; border-radius: 8px; }}
        section[data-testid="stSidebar"] {{ display: none; }}
        footer {{ visibility: hidden; }}
    </style>
    <div class="cs-hero">
      <h1>🧼 CleanSchema</h1>
      <p>Strip the secrets. Keep the structure. <span class="cs-promise">
      100% local · no upload · no telemetry · open source</span></p>
    </div>
    """,
    unsafe_allow_html=True,
)

# ---------------------------------------------------------------------------
# Step 01 — Drop your file
# ---------------------------------------------------------------------------
st.subheader("01 — Drop your file")
st.caption("CSV, TSV, or Excel. Any size, any structure. Everything stays on this machine.")

uploaded = st.file_uploader(
    label="Drop your file",
    type=["csv", "tsv", "xlsx", "xls", "xlsm"],
    label_visibility="collapsed",
)

if not uploaded:
    st.info("Drop a `.csv`, `.tsv`, or `.xlsx` above to get started.")
    with st.expander("No data handy? Use the sample file"):
        sample_path = Path(__file__).parent / "examples" / "employees_sample.csv"
        if sample_path.exists():
            st.download_button(
                "Download sample employees CSV",
                data=sample_path.read_bytes(),
                file_name="employees_sample.csv",
                mime="text/csv",
            )
        else:
            st.caption("(sample file not installed)")
    st.stop()

# ---------------------------------------------------------------------------
# Load + classify
# ---------------------------------------------------------------------------
with st.spinner("Reading file locally…"):
    try:
        df = read_any(uploaded)
    except Exception as e:
        st.error(f"Couldn't read that file: {e}")
        st.stop()

rows, cols = df.shape
st.success(f"Loaded **{uploaded.name}** — {rows:,} rows · {cols} columns")

with st.spinner("Classifying columns…"):
    detections: list[Detection] = classify(df)

sens_count = sum(1 for d in detections if d.is_sensitive)
safe_count = len(detections) - sens_count

# ---------------------------------------------------------------------------
# Step 02 — Review what was detected
# ---------------------------------------------------------------------------
st.subheader("02 — Review what was detected")
st.caption(
    f"**{sens_count} sensitive · {safe_count} safe.** Uncheck any column you want left alone."
)

# Build a review table with override checkboxes
overrides: dict[str, bool] = {}
# 4 columns per row for a tight grid
GRID = 4
for i in range(0, len(detections), GRID):
    row_cols = st.columns(GRID)
    for slot, det in enumerate(detections[i : i + GRID]):
        with row_cols[slot]:
            badge_class = "sens" if det.is_sensitive else "safe"
            badge_label = "SENSITIVE" if det.is_sensitive else "SAFE"
            st.markdown(
                f'<div style="margin-bottom:0.3rem;">'
                f'<span class="cs-badge {badge_class}">{badge_label}</span>'
                f'<strong>{det.column}</strong></div>',
                unsafe_allow_html=True,
            )
            st.caption(f"{det.category} · {det.reason}")
            overrides[det.column] = st.checkbox(
                f"Replace {det.column}",
                value=det.is_sensitive,
                key=f"override-{det.column}",
                label_visibility="collapsed",
            )

# Apply overrides
effective_detections: list[Detection] = []
for det in detections:
    replace = overrides.get(det.column, det.is_sensitive)
    tier = SENSITIVE if replace else "safe"
    effective_detections.append(
        Detection(column=det.column, category=det.category, tier=tier, reason=det.reason)
    )

st.markdown("---")

# ---------------------------------------------------------------------------
# Before preview
# ---------------------------------------------------------------------------
with st.expander("Preview your file (first 5 rows, original — do not share)", expanded=False):
    st.dataframe(df.head(5), use_container_width=True)

# ---------------------------------------------------------------------------
# Step 03 — Clean + download
# ---------------------------------------------------------------------------
st.subheader("03 — Download the clean copy")
st.caption("Sensitive values become realistic synthetics. Joins still work: repeated values remap consistently within a single run.")

if st.button("Clean it ✂️", type="primary"):
    t0 = time.time()
    with st.spinner("Synthesizing…"):
        result = synthesize(df, effective_detections)
    elapsed = time.time() - t0
    st.success(
        f"Replaced {len(result.columns_replaced)} sensitive columns across {result.rows:,} rows in {elapsed:.2f}s"
    )

    st.markdown("**Preview (first 5 rows of clean copy — safe to share):**")
    st.dataframe(result.df.head(5), use_container_width=True)

    src = Path(uploaded.name).stem
    csv_bytes = to_csv_bytes(result.df)
    dl_col1, dl_col2 = st.columns(2)
    with dl_col1:
        st.download_button(
            "⬇ Download CSV",
            data=csv_bytes,
            file_name=f"{src}_clean.csv",
            mime="text/csv",
            use_container_width=True,
        )
    with dl_col2:
        st.download_button(
            "⬇ Download XLSX",
            data=to_xlsx_bytes(result.df),
            file_name=f"{src}_clean.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            use_container_width=True,
        )

    st.caption(
        "Your original file is untouched. The clean copy is built in memory and lives "
        "only in this browser tab until you download it."
    )

# ---------------------------------------------------------------------------
# Footer — the detection taxonomy so people can audit
# ---------------------------------------------------------------------------
st.markdown("---")
with st.expander("Detection taxonomy — every rule, visible"):
    st.caption(
        "CleanSchema ships with 13 built-in classifiers. Column-name hints win, "
        "then a value-shape regex falls back, then a paranoid default. "
        "See `detector.py` to read or extend."
    )
    for cat in CATEGORIES:
        tier_label = "🔴 SENSITIVE" if cat["tier"] == SENSITIVE else "🟢 SAFE"
        hints = ", ".join(cat["hints"][:6])
        more = "…" if len(cat["hints"]) > 6 else ""
        st.markdown(f"**{cat['name']}** — {tier_label}  \n`{hints}{more}`")

st.caption(
    "CleanSchema · open source · built by Dr. Jonesy · "
    "[cleanschema.app](https://cleanschema.app) · "
    "[github.com/rjboogey/cleanschema](https://github.com/rjboogey/cleanschema)"
)
