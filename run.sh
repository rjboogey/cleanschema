#!/usr/bin/env bash
# CleanSchema — Linux one-click launcher
# Run: bash run.sh

set -e
cd "$(dirname "$0")"

PY="python3"
if ! command -v "$PY" >/dev/null 2>&1; then
  echo "Python 3.9+ is required. Install it (e.g. sudo apt install python3 python3-venv) then try again."
  exit 1
fi

if [ ! -d ".venv" ]; then
  echo "→ First run: creating local virtualenv in .venv/ …"
  "$PY" -m venv .venv
  echo "→ Installing dependencies (one-time)…"
  ./.venv/bin/pip install --upgrade pip >/dev/null
  ./.venv/bin/pip install -r requirements.txt
fi

echo "→ Launching CleanSchema…"
./.venv/bin/streamlit run app.py \
  --server.port 8501 \
  --browser.gatherUsageStats false \
  --theme.base dark
