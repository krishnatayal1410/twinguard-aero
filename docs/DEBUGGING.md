# Debugging

Run:
```bash
bash scripts/doctor.sh
```

Logs:
- `.runtime/logs/backend.log`
- `.runtime/logs/frontend.log`
- `.runtime/logs/simulator.log`

Useful checks:
```bash
curl http://127.0.0.1:8000/health
curl http://127.0.0.1:8000/api/v1/system/status
lsof -i :5173
lsof -i :8000
```

Frontend:
```bash
cd frontend
npm run typecheck
npm run build
```

Backend:
```bash
export PYTHONPATH="$PWD/backend"
pytest -q backend/tests
```
