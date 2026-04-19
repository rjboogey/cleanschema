#!/usr/bin/env bash
# CleanSchema — macOS one-click launcher
# Double-click this file in Finder to install dependencies (first run)
# and launch the app in your default browser.
#
# Strategy: create a local .venv so we never touch your system Python,
# install deps once, then `streamlit run app.py`.

set -e
cd "$(dirname "$0")"

PY="python3"
if ! command -v "$PY" >/dev/null 2>&1; then
  osascript -e 'display dialog "Python 3.9+ is required. Install it from python.org then try again." buttons {"OK"} default button 1 with icon stop'
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
echo "  If a browser tab does NOT open automatically, visit:"
echo "  http://localhost:8501"
echo ""
./.venv/bin/streamlit run app.py \
  --server.headless false \
  --server.port 8501 \
  --browser.gatherUsageStats false \
  --theme.base dark
