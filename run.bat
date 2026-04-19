@echo off
REM CleanSchema — Windows one-click launcher
REM Double-click this file to install dependencies (first run) and launch.

cd /d "%~dp0"

where python >nul 2>&1
if errorlevel 1 (
    echo Python 3.9+ is required. Install it from python.org then try again.
    pause
    exit /b 1
)

if not exist ".venv" (
    echo First run: creating local virtualenv in .venv\ ...
    python -m venv .venv
    echo Installing dependencies (one-time)...
    call .venv\Scripts\pip.exe install --upgrade pip >nul
    call .venv\Scripts\pip.exe install -r requirements.txt
)

echo Launching CleanSchema...
echo If a browser tab does not open automatically, visit http://localhost:8501
call .venv\Scripts\streamlit.exe run app.py --server.port 8501 --browser.gatherUsageStats false --theme.base dark
