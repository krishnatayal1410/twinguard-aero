from pathlib import Path
import os

# Keep tests isolated from the normal development DB.
TEST_DB = Path(__file__).resolve().parents[1] / "test_twinguard.db"
os.environ["DATABASE_URL"] = f"sqlite:///{TEST_DB}"

from fastapi.testclient import TestClient
from backend.app.main import app

client = TestClient(app)

PAYLOAD = {
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


def test_healthz():
    with client:
        response = client.get("/healthz")
        assert response.status_code == 200
        assert response.json()["status"] == "ok"


def test_telemetry_roundtrip_and_history():
    with client:
        response = client.post("/telemetry", json=PAYLOAD)
        assert response.status_code == 200
        state = response.json()
        assert state["status"] == "live"
        assert "residuals" in state
        assert "health" in state
        assert "sensor_trust" in state
        assert "maintenance" in state

        history = client.get("/history?limit=10")
        assert history.status_code == 200
        assert len(history.json()["items"]) >= 1


def test_mission_simulation():
    with client:
        client.post("/telemetry", json=PAYLOAD)
        response = client.post(
            "/mission/simulate",
            json={
                "duration_hours": 8,
                "altitude": 5500,
                "ambient_temp": 38,
                "throttle": 78,
            },
        )
        assert response.status_code == 200
        result = response.json()
        assert result["mission_risk"] in {"LOW", "MEDIUM", "HIGH"}
        assert "predicted_post_mission_health" in result

def test_simulation_control():
    with client:
        response = client.post(
            "/simulation/control",
            json={"fault": "lubrication", "severity": 0.7},
        )
        assert response.status_code == 200
        body = response.json()
        assert body["fault"] == "lubrication"
        assert body["severity"] == 0.7

        response = client.get("/simulation/control")
        assert response.status_code == 200
        assert response.json()["fault"] == "lubrication"

        reset = client.post(
            "/simulation/control",
            json={"fault": "normal", "severity": 0.0},
        )
        assert reset.status_code == 200
        assert reset.json()["fault"] == "normal"
        assert reset.json()["severity"] == 0.0

