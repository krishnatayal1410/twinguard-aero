#!/bin/bash
set -e

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"
mkdir -p .runtime/logs

if [ ! -d ".venv" ]; then
  echo "Missing .venv"
  exit 1
fi

source .venv/bin/activate

cleanup() {
  kill "${BACKEND_PID:-}" "${SIM_PID:-}" "${FRONT_PID:-}" 2>/dev/null || true
}
trap cleanup EXIT INT TERM

uvicorn backend.app.main:app --reload > .runtime/logs/backend.log 2>&1 &
BACKEND_PID=$!

sleep 3

python simulator/run_simulator.py > .runtime/logs/simulator.log 2>&1 &
SIM_PID=$!

(
  cd frontend
  npm run dev
) > .runtime/logs/frontend.log 2>&1 &
FRONT_PID=$!

echo "TwinGuard MVP started"
echo "Frontend: http://localhost:5173"
echo "Backend:  http://127.0.0.1:8000"
echo "Swagger:  http://127.0.0.1:8000/docs"
echo "Logs: .runtime/logs/"
echo "Press Ctrl+C to stop all services"

wait
