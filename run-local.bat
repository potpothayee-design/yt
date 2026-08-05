@echo off
rem  AI Kids Video Studio - one-click local launcher for Windows.
rem  Needs: Python 3.10+ (tick "Add to PATH") and Node.js 18+ (LTS).
setlocal
cd /d "%~dp0"
title AI Kids Video Studio - setup

echo.
echo  ======================================
echo   AI Kids Video Studio - local launcher
echo  ======================================
echo.

rem ---- find Python 3.10+ ---------------------------------------------
set "PY="
where py >nul 2>nul && py -3 -c "import sys;raise SystemExit(0 if sys.version_info>=(3,10) else 1)" >nul 2>nul && set "PY=py -3"
if not defined PY (
  where python >nul 2>nul && python -c "import sys;raise SystemExit(0 if sys.version_info>=(3,10) else 1)" >nul 2>nul && set "PY=python"
)
if not defined PY (
  echo  [MISSING] Python 3.10+ was not found.
  echo  Install it from https://www.python.org/downloads/ and make sure to
  echo  TICK "Add python.exe to PATH", then run this file again.
  start https://www.python.org/downloads/
  pause
  exit /b 1
)

rem ---- find Node.js ---------------------------------------------------
where npm >nul 2>nul
if errorlevel 1 (
  echo  [MISSING] Node.js was not found.
  echo  Install the LTS version from https://nodejs.org then run this file again.
  start https://nodejs.org
  pause
  exit /b 1
)

echo  [1/4] Installing Python dependencies (first run takes a few minutes)...
if not exist backend\.venv %PY% -m venv backend\.venv
backend\.venv\Scripts\python.exe -m pip install -q -r backend\requirements.txt
if errorlevel 1 (
  echo  [ERROR] pip install failed. Using Python 3.11 or 3.12 is recommended.
  pause
  exit /b 1
)

echo  [2/4] Installing frontend dependencies...
if not exist frontend\node_modules (
  pushd frontend
  call npm ci --no-audit --no-fund
  popd
) else (
  echo        already installed - skipping
)

echo  [3/4] Building the frontend (first run takes about a minute)...
if not exist frontend\.next (
  pushd frontend
  call npm run build
  popd
) else (
  echo        already built - skipping
)

echo  [4/4] Starting servers - keep the two new windows open while you work.
start "Studio API (keep open)" cmd /k "cd /d %~dp0backend && .venv\Scripts\python.exe -m uvicorn app.main:app --host 0.0.0.0 --port 8000"
timeout /t 4 /nobreak >nul
start "Studio Web (keep open)" cmd /k "cd /d %~dp0frontend && node_modules\.bin\next start -H 0.0.0.0 -p 3000"
timeout /t 5 /nobreak >nul
start http://localhost:3000

echo.
echo  Done! The app opened in your browser: http://localhost:3000
echo  Register any account on the login page and start generating.
pause
