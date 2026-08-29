#!/usr/bin/env bash
set -u
cd "$(dirname "$0")/.."

echo "TwinGuard Aero Doctor"
echo "====================="
echo

echo "Project: $PWD"
echo "Python:  $(python3 --version 2>&1)"
echo "Node:    $(node --version 2>&1)"
echo "npm:     $(npm --version 2>&1)"
echo

echo "Port 8000:"
lsof -nP -iTCP:8000 -sTCP:LISTEN 2>/dev/null || echo "not listening"
echo
echo "Port 5173:"
lsof -nP -iTCP:5173 -sTCP:LISTEN 2>/dev/null || echo "not listening"

echo
echo "Backend import log:"
cat .runtime/logs/backend-import.log 2>/dev/null || true

echo
echo "Backend runtime log:"
tail -n 120 .runtime/logs/backend.log 2>/dev/null || true

echo
echo "Frontend build log:"
tail -n 120 .runtime/logs/frontend-build.log 2>/dev/null || true

echo
echo "Frontend runtime log:"
tail -n 120 .runtime/logs/frontend.log 2>/dev/null || true

echo
echo "Simulator log:"
tail -n 100 .runtime/logs/simulator.log 2>/dev/null || true
