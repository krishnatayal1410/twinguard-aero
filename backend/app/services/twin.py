from threading import Lock

from ..schemas.telemetry import Telemetry
from .physics import expected_state, residuals
from .health import calculate_health
from .models import model_service
from .sensor_trust import calculate_sensor_trust
from .explainability import explain_prediction
from .decision_support import (
    refine_sensor_trust,
    maintenance_recommendation,
    rul_stabilizer,
)


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

        # Initial health is used as input to the current synthetic RUL model.
        health = calculate_health(raw, res, 0.0)

        # AI inference: anomaly + fault classifier + raw RUL estimate.
        ai = model_service.predict(raw, res, health)

        # Recompute health with anomaly information.
        health = calculate_health(
            raw,
            res,
            ai.get("anomaly_score", 0.0),
        )

        # Base residual-derived trust.
        trust = calculate_sensor_trust(raw, res)

        # Cross-sensor reasoning distinguishes likely physical faults from
        # isolated sensor inconsistencies.
        trust = refine_sensor_trust(
            telemetry=raw,
            residuals=res,
            sensor_trust=trust,
            ai=ai,
        )

        # Stabilize synthetic RUL so it does not jump unrealistically.
        previous_ai = self._state.get("ai") or {}
        previous_rul = previous_ai.get("rul_hours")

        ai["rul_hours"] = rul_stabilizer.update(
            raw_rul=ai.get("rul_hours"),
            health=health,
            ai=ai,
        )

        # Final state-aware guard for the synthetic MVP.
        # A developing anomaly/fault must not make RUL suddenly increase.
        current_rul = ai.get("rul_hours")
        fault_active = (
            bool(ai.get("anomaly", False))
            or str(ai.get("fault", "normal")) != "normal"
            or float(health.get("overall", 100)) < 90
        )

        if previous_rul is not None and current_rul is not None:
            previous_rul = float(previous_rul)
            current_rul = float(current_rul)

            if fault_active:
                current_rul = min(current_rul, previous_rul - 0.15)
                current_rul = max(current_rul, previous_rul - 2.0)
            else:
                current_rul = max(
                    previous_rul - 1.0,
                    min(current_rul, previous_rul + 0.5),
                )

            ai["rul_hours"] = round(max(0.0, current_rul), 1)

        # Maintenance decision uses telemetry + AI + health + sensor trust.
        ai["explanation"] = explain_prediction(
            model_service=model_service,
            telemetry=raw,
            residuals=res,
            health=health,
            ai=ai,
        )

        maintenance = maintenance_recommendation(
            telemetry=raw,
            residuals=res,
            sensor_trust=trust,
            ai=ai,
            health=health,
        )

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

    def reset(self) -> dict:
        rul_stabilizer.reset()

        clean_state = {
            "engine_id": "ENGINE-01",
            "status": "waiting_for_healthy_telemetry",
            "telemetry": None,
            "expected": None,
            "residuals": None,
            "sensor_trust": None,
            "health": None,
            "ai": {
                "anomaly": False,
                "anomaly_score": 0.0,
                "fault": "normal",
                "fault_probability": 0.0,
                "fault_probabilities": {},
                "rul_hours": None,
            },
            "maintenance": {
                "priority": "MONITOR",
                "system": "none",
                "message": "Healthy reset requested. Waiting for fresh telemetry.",
            },
        }

        with self._lock:
            self._state = clean_state
            return self._state

    def get(self) -> dict:
        with self._lock:
            return self._state


twin_state = TwinState()
