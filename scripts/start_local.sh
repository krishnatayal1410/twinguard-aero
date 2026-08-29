#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")/.."
ROOT="$PWD"
mkdir -p .runtime/logs data/runtime

command -v python3 >/dev/null || { echo "ERROR: Python 3 is required."; exit 1; }
command -v node >/dev/null || { echo "ERROR: Node.js is required."; exit 1; }
command -v npm >/dev/null || { echo "ERROR: npm is required."; exit 1; }
command -v curl >/dev/null || { echo "ERROR: curl is required."; exit 1; }

[ -d .venv ] || python3 -m venv .venv
source .venv/bin/activate

echo "[1/7] Installing Python dependencies…"
python -m pip install --disable-pip-version-check -q --upgrade pip
python -m pip install --disable-pip-version-check -q -r backend/requirements.txt

echo "[2/7] Installing frontend dependencies…"
if [ ! -d frontend/node_modules ]; then
  (cd frontend && npm install --no-fund --no-audit)
else
  echo "Frontend dependencies already installed."
fi

echo "[3/7] Preflight-building frontend…"
if ! (cd frontend && npm run build) >.runtime/logs/frontend-build.log 2>&1; then
  echo
  echo "ERROR: Frontend build failed."
  tail -n 140 .runtime/logs/frontend-build.log
  exit 1
fi
echo "Frontend build: PASS"

export PYTHONPATH="$ROOT/backend"
export MODEL_DIR="$ROOT/models"
export DATABASE_URL="${DATABASE_URL:-sqlite:///$ROOT/data/runtime/twinguard.db}"
export CORS_ORIGINS="http://localhost:5173,http://127.0.0.1:5173"
export TRUSTED_HOSTS="localhost,127.0.0.1"
export PYTHONUNBUFFERED=1

# Stable macOS default: avoid native XGBoost libraries during app boot.
# The app still runs anomaly detection + engineering fault/RUL fallback.
export TWINGUARD_NATIVE_ML="${TWINGUARD_NATIVE_ML:-0}"

if [ ! -f .runtime/ingest.key ]; then
  python - <<'PY' > .runtime/ingest.key
import secrets
print(secrets.token_urlsafe(32))
PY
fi
export TWINGUARD_INGEST_KEY="$(cat .runtime/ingest.key)"

cleanup() {
  [ -n "${FRONTEND_PID:-}" ] && kill "$FRONTEND_PID" 2>/dev/null || true
  [ -n "${SIMULATOR_PID:-}" ] && kill "$SIMULATOR_PID" 2>/dev/null || true
  [ -n "${BACKEND_PID:-}" ] && kill "$BACKEND_PID" 2>/dev/null || true
}
trap cleanup EXIT INT TERM

echo "[4/7] Testing FastAPI imports…"
: > .runtime/logs/backend-import.log
if ! python -c "import app.main; print('FastAPI import: PASS')" >.runtime/logs/backend-import.log 2>&1; then
  echo
  echo "ERROR: FastAPI import failed."
  cat .runtime/logs/backend-import.log
  exit 1
fi
cat .runtime/logs/backend-import.log

echo "[5/7] Starting FastAPI backend…"
: > .runtime/logs/backend.log
python -m uvicorn app.main:app --host 127.0.0.1 --port 8000 >.runtime/logs/backend.log 2>&1 &
BACKEND_PID=$!

BACKEND_READY=0
for i in $(seq 1 240); do
  if ! kill -0 "$BACKEND_PID" 2>/dev/null; then
    echo
    echo "ERROR: Backend process exited before becoming ready."
    echo "----- backend.log -----"
    cat .runtime/logs/backend.log
    echo "-----------------------"
    exit 1
  fi

  if curl -fsS --max-time 1 http://127.0.0.1:8000/health >/dev/null 2>&1; then
    BACKEND_READY=1
    break
  fi

  if [ $((i % 20)) -eq 0 ]; then
    echo "Waiting for backend… $((i / 2))s"
  fi
  sleep .5
done

if [ "$BACKEND_READY" -ne 1 ]; then
  echo
  echo "ERROR: Backend did not become ready within 120 seconds."
  echo "----- backend.log -----"
  cat .runtime/logs/backend.log
  echo "-----------------------"
  exit 1
fi

echo "Backend health: PASS"
curl -fsS http://127.0.0.1:8000/health
echo

echo "[6/7] Starting engine simulator…"
: > .runtime/logs/simulator.log
python simulator/run.py --transport http --rate 1 >.runtime/logs/simulator.log 2>&1 &
SIMULATOR_PID=$!

echo "[7/7] Starting frontend…"
: > .runtime/logs/frontend.log
(cd frontend && npm run dev -- --force --host 127.0.0.1) >.runtime/logs/frontend.log 2>&1 &
FRONTEND_PID=$!

FRONTEND_READY=0
for i in $(seq 1 120); do
  if ! kill -0 "$FRONTEND_PID" 2>/dev/null; then
    echo
    echo "ERROR: Frontend process exited."
    cat .runtime/logs/frontend.log
    exit 1
  fi
  if curl -fsS --max-time 1 http://127.0.0.1:5173 >/dev/null 2>&1; then
    FRONTEND_READY=1
    break
  fi
  sleep .5
done

if [ "$FRONTEND_READY" -ne 1 ]; then
  echo "ERROR: Frontend did not become ready."
  cat .runtime/logs/frontend.log
  exit 1
fi

echo
echo "=================================================="
echo " TwinGuard Aero is running"
echo "=================================================="
echo " Dashboard: http://localhost:5173"
echo " API:       http://127.0.0.1:8000"
echo " Docs:      http://127.0.0.1:8000/docs"
echo
echo " Backend mode:"
if [ "$TWINGUARD_NATIVE_ML" = "1" ]; then
  echo " Native ML: enabled"
else
  echo " Stable local mode: enabled"
  echo " Isolation Forest + engineering fault/RUL fallback"
fi
echo
echo " Logs: $ROOT/.runtime/logs"

command -v open >/dev/null && open http://localhost:5173 >/dev/null 2>&1 || true
wait
