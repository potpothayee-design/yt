#!/usr/bin/env bash
# AI Kids Video Studio - one-command local launcher (macOS / Linux).
# Needs: Python 3.10+, Node.js 18+.
set -euo pipefail
cd "$(dirname "$0")"

echo ""
echo "  AI Kids Video Studio - local launcher"
echo "  --------------------------------------"

if ! command -v python3 >/dev/null; then
  echo "[MISSING] Python 3.10+ - install it (e.g. 'brew install python@3.12' or your distro packages)"; exit 1
fi
if ! command -v npm >/dev/null; then
  echo "[MISSING] Node.js - install the LTS from https://nodejs.org"; exit 1
fi

echo "[1/4] Python dependencies..."
[ -d backend/.venv ] || python3 -m venv backend/.venv
backend/.venv/bin/pip install -q -r backend/requirements.txt

echo "[2/4] Frontend dependencies..."
[ -d frontend/node_modules ] || (cd frontend && npm ci --no-audit --no-fund)

echo "[3/4] Building frontend..."
[ -d frontend/.next ] || (cd frontend && npm run build)

echo "[4/4] Starting servers..."
(backend/.venv/bin/uvicorn app.main:app --host 0.0.0.0 --port 8000 > /tmp/studio-api.log 2>&1 &)
sleep 3
(cd frontend && node_modules/.bin/next start -H 0.0.0.0 -p 3000 > /tmp/studio-web.log 2>&1 &)
sleep 3

URL="http://localhost:3000"
echo ""
echo "  App:  $URL     (logs: /tmp/studio-api.log, /tmp/studio-web.log)"
echo "  Register any account on the login page. Ctrl+C won't stop the two"
echo "  background servers - use: pkill -f 'uvicorn app.main' ; pkill -f 'next start'"
echo ""
(command -v open >/dev/null && open "$URL") || (command -v xdg-open >/dev/null && xdg-open "$URL") || true
