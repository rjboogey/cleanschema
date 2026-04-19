# 🧼 CleanSchema

> Strip the secrets. Keep the structure.

CleanSchema detects PII and sensitive values in your CSV and Excel files and replaces them with realistic synthetic data — same column names, same data types, same row count, **zero real values**. Runs entirely on your machine. No upload. No telemetry. No account.

[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](https://opensource.org/licenses/MIT)
[![Python 3.9+](https://img.shields.io/badge/Python-3.9+-blue.svg)](https://www.python.org/downloads/)
[![Local-first](https://img.shields.io/badge/local-first-success.svg)](#privacy)
[![Cross-platform](https://img.shields.io/badge/macOS%20·%20Linux%20·%20Windows-supported-blue.svg)](#install)

---

## Why CleanSchema

You need to share data with a contractor, a colleague on a different team, an LLM, an AI demo, or a stakeholder — but the file is full of names, emails, salaries, SSNs, and other things that should never leave your machine.

You could:
- Manually scrub every column (slow, error-prone)
- Use a SaaS tool (your data gets uploaded — defeats the point)
- Build something one-off in pandas (you'll do it differently every time)

Or you can drop the file into CleanSchema. **Same shape. Different values. Joins still work. Done in seconds.**

---

## Install

CleanSchema is a Python app that runs locally. You need **Python 3.9 or newer**. That's it.

```bash
git clone https://github.com/rjboogey/cleanschema
cd cleanschema
pip install -r requirements.txt
streamlit run app.py
```

### Even easier: one-click launcher

| Platform | Just double-click |
|---|---|
| **macOS** | `run.command` |
| **Windows** | `run.bat` |
| **Linux** | `run.sh` (or `bash run.sh`) |

The launcher creates an isolated `.venv/` so it never touches your system Python, installs dependencies the first time only, then opens CleanSchema in your default browser at `http://localhost:8501`.

---

## How it works

```
┌────────────────────┐    ┌───────────────────┐    ┌────────────────────┐
│  01 — Drop file    │ →  │ 02 — Review +      │ →  │ 03 — Download     │
│  CSV / TSV / XLSX  │    │     override       │    │     clean copy    │
└────────────────────┘    └───────────────────┘    └────────────────────┘
```

1. **Drop your file.** CleanSchema reads it locally — nothing transmitted, nothing logged.
2. **Review what was detected.** 13 sensitive-data classifiers run against column names and value patterns. You see every detection — and can override any of them — before anything is replaced.
3. **Download the clean copy.** Sensitive values become realistic synthetics. Names look like names. Salaries fall in the same range. Joins still work because IDs replace **consistently within a single run**.

---

## What it detects

| Category | Tier | Example column names |
|---|---|---|
| `EMAIL` | 🔴 sensitive | `email`, `mail`, `contact_email` |
| `PHONE` | 🔴 sensitive | `phone`, `mobile`, `cell` |
| `ID` | 🔴 sensitive | `ssn`, `employee_id`, `account_no`, `passport` |
| `NAME` | 🔴 sensitive | `first_name`, `last_name`, `full_name`, `customer_name` |
| `ADDRESS` | 🔴 sensitive | `address`, `street`, `city`, `state` |
| `ZIP` | 🔴 sensitive | `zip`, `zipcode`, `postal_code` |
| `FINANCIAL` | 🔴 sensitive | `salary`, `revenue`, `amount`, `balance` |
| `DATE` | 🔴 sensitive | `dob`, `hire_date`, `created_at` |
| `FREE_TEXT` | 🔴 sensitive | `notes`, `description`, `comments` |
| `CATEGORICAL` | 🟢 safe | `department`, `status`, `region`, `category` |
| `NUMERIC` | 🟢 safe | `count`, `quantity`, `units` |
| `PERCENTAGE` | 🟢 safe | `rate`, `pct`, `completion` |
| `BOOLEAN` | 🟢 safe | `is_admin`, `enabled`, `active` |

When the column name doesn't match a hint, CleanSchema falls back to a value-shape regex check (e.g. `(415) 555-1234` → `PHONE`). When that also doesn't match, the **paranoid default** kicks in: high-cardinality unknowns are treated as `FREE_TEXT` (replaced) — low-cardinality unknowns pass through as `CATEGORICAL`.

Every rule is in [`detector.py`](./detector.py). Read it. Fork it. Trust it on inspection, not on faith.

---

## What gets preserved

CleanSchema is built so that the cleaned output is statistically and structurally indistinguishable from the original:

- **Column names** — unchanged
- **Column order** — unchanged
- **Row count** — unchanged
- **Data types** — preserved when possible (numeric stays numeric, etc.)
- **Categorical distributions** — passed through untouched
- **Joins** — repeated IDs/emails/etc. remap *consistently* within a single run, so a join on `employee_id` between two cleaned tables still works
- **Salary ranges** — replaced values stay within ±15% of the original to preserve descriptive stats
- **Date ranges** — shifted by a random ±5 years rather than randomized to a new century

---

## Privacy

CleanSchema is built around one promise: **your data never leaves this machine.**

- **No internet connection required.** Works on a plane. Works air-gapped.
- **No account, no login, no email** — you've already given enough of that away.
- **No analytics, no telemetry, no logs** — the app doesn't even know you used it.
- **Open source** — every line is in this repo. Audit before you trust.

Streamlit binds to `localhost` only. The file enters memory when you upload, leaves your browser as a clean copy when you click download. We never built a pipe to phone home.

---

## Use cases

- **Sharing with contractors** — give them realistic-looking data without leaking anything real
- **AI / LLM demos** — paste a sample table into ChatGPT, Claude, Copilot without compliance drama
- **Conference talks / blog posts** — show your real workflow on fake data
- **Bug reports** — attach a representative dataset to an issue without redacting cells by hand
- **Onboarding & tutorials** — train new team members on safe data
- **Compliance prep** — meet GDPR / HIPAA / SOC 2 data-minimization requirements when prepping samples

---

## Examples

A sample employees CSV ships in [`examples/employees_sample.csv`](./examples/employees_sample.csv) — 20 rows × 10 columns covering the most common sensitive types. Drop it into the app to see how detection and replacement work end to end.

---

## Develop / contribute

```bash
# Run tests
python -m pytest -v

# Run the app
streamlit run app.py
```

Pull requests very welcome. Especially:
- New detection rules (add to `CATEGORIES` in `detector.py` + a test in `tests/`)
- Locale-specific generators (Spanish names, UK postcodes, etc.)
- Bigger / weirder file format support (Parquet, Arrow, JSON-lines)
- UI polish

See [`CONTRIBUTING.md`](./CONTRIBUTING.md) for guidelines and the contributor covenant.

---

## Roadmap

- [ ] Hosted web version (browser-only, still no server processing) — *in development*
- [ ] CLI mode (`cleanschema input.csv -o output.csv --auto-yes`)
- [ ] Parquet / Arrow / JSON-lines support
- [ ] Plugin API for custom detectors
- [ ] Locale packs (de, es, fr, ja…)
- [ ] Reproducible cleans via `--seed` flag

---

## License

[MIT](./LICENSE) — do whatever you want, just keep the copyright notice.

Built by [Dr. Renaldo "Jonesy" Jones](https://drjonesy.com) · [@therealdrjonesy](https://twitter.com/therealdrjonesy)
