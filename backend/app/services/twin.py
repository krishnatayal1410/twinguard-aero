from threading import Lock
from ..schemas.telemetry import Telemetry
from .physics import expected_state, residuals
from .health import calculate_health
from .models import model_service
from .sensor_trust import calculate_sensor_trust
from .maintenance import maintenance_recommendation


class TwinState:
    def __init__(self):
        self._lock = Lock()
        self._state: dict = {
            "engine_id": "ENGINE-01",
            "status": "waiting_for_telemetry",
            "telemetry": None,
            "expected": None,
            "residuals": None,
            "sensor_trust": None,
            "health": None,
            "ai": {
                "anomaly": False,
                "anomaly_score": 0.0,
                "fault": "model_not_trained",
                "fault_probability": 0.0,
                "fault_probabilities": {},
                "rul_hours": None,
            },
            "maintenance": None,
        }

    def update(self, telemetry: Telemetry) -> dict:
        expected = expected_state(telemetry)
        res = residuals(telemetry, expected)
        raw = telemetry.model_dump()

        # Initial health is used as an input to the current RUL baseline.
        health = calculate_health(raw, res, 0.0)
        ai = model_service.predict(raw, res, health)
        health = calculate_health(raw, res, ai.get("anomaly_score", 0.0))
        trust = calculate_sensor_trust(raw, res)
        maintenance = maintenance_recommendation(raw, res, health, ai, trust)

        with self._lock:
            self._state = {
                "engine_id": telemetry.engine_id,
                "status": "live",
                "telemetry": telemetry.model_dump(mode="json"),
                "expected": expected,
                "residuals": res,
                "sensor_trust": trust,
                "health": health,
                "ai": ai,
                "maintenance": maintenance,
            }
            return self._state

    def get(self) -> dict:
        with self._lock:
            return self._state


twin_state = TwinState()
