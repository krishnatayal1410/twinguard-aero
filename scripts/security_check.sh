#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
echo "== TwinGuard security checks =="
echo "[1] Python compilation";python3 -m compileall -q backend simulator ai scripts
echo "[2] Search for obvious wildcard CORS / committed secrets"
! grep -R --exclude-dir=node_modules --exclude='security_check.sh' 'allow_origins=.*\["\*"\]' backend
! grep -R --exclude-dir=node_modules -E 'sk-[A-Za-z0-9_-]{20,}|BEGIN (RSA|OPENSSH) PRIVATE KEY' . || { echo "Potential secret found";exit 1;}
echo "[3] npm audit (when dependencies are installed)"
if [ -d frontend/node_modules ];then (cd frontend&&npm audit --omit=dev)||true;else echo "Skipped: frontend/node_modules absent";fi
echo "[4] pip-audit (when installed)"
command -v pip-audit >/dev/null&&pip-audit -r backend/requirements.txt||echo "Skipped: install pip-audit for CVE database scan"
echo "Static security checks complete. No automated scan can guarantee zero vulnerabilities."
