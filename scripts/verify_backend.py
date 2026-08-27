import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from fastapi.testclient import TestClient
from backend.app.main import app

payload = {
    "engine_id": "ENGINE-01",
    "rpm": 4100,
    "throttle": 70,
    "altitude": 4200,
    "ambient_temp": 22,
    "cht": 185,
    "egt": 700,
    "oil_pressure": 4.1,
    "oil_temp": 92,
    "fuel_flow": 17.5,
    "vibration": 0.28,
    "battery_voltage": 27.5,
    "operating_hours": 10,
}

with TestClient(app) as client:
    assert client.get("/healthz").status_code == 200
    r = client.post("/telemetry", json=payload)
    assert r.status_code == 200, r.text
    assert client.get("/history").status_code == 200
    assert client.post("/mission/simulate", json={
        "duration_hours": 8,
        "altitude": 5500,
        "ambient_temp": 38,
        "throttle": 78,
    }).status_code == 200

print("TwinGuard backend smoke test passed.")
