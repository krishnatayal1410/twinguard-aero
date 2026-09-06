from __future__ import annotations
from threading import RLock

from .ai_engine import AIEngine
from .health import HealthEngine, readiness
from .maintenance import MaintenanceEngine
from .mission import MissionEngine
from .persistence import persistence
from .physics import PhysicsEngine
from .replay import ReplayService
from .sensor_trust import SensorTrustEngine
from ..core import settings


class TwinManager:
    def __init__(self):
        self.lock = RLock()
        self.physics = PhysicsEngine()
        self.trust = SensorTrustEngine()
        self.health = HealthEngine()
        self.ai = AIEngine(settings.model_dir)
        self.maint = MaintenanceEngine()
        self.mission = MissionEngine()
        self.replay = ReplayService(settings.engine_id)
        self.previous = None
        self.state = None
        self.simulation = {"fault": "normal", "severity": 0.0}

    @staticmethod
    def _physics_confidence(residuals: dict, anomaly: bool) -> float:
        normalized = [
            abs(residuals.get("cht_residual", 0)) / 35,
            abs(residuals.get("egt_residual", 0)) / 80,
            abs(residuals.get("oil_pressure_residual", 0)) / 1.5,
            abs(residuals.get("oil_temperature_residual", 0)) / 28,
            abs(residuals.get("fuel_flow_residual", 0)) / 4,
            abs(residuals.get("vibration_residual", 0)) / .65,
            abs(residuals.get("alternator_voltage_residual", 0)) / 2.5,
        ]
        if anomaly:
            # During a real fault we WANT several physically related channels
            # to disagree with the healthy model. Corroboration therefore
            # increases confidence instead of decreasing it.
            corroborating = sum(1 for value in normalized if value >= .35)
            strongest = max(normalized) if normalized else 0
            return max(45.0, min(100.0, 52 + 9 * corroborating + 16 * min(1.0, strongest)))
        mean = sum(normalized) / max(1, len(normalized))
        return max(45.0, min(100.0, 100 - mean * 38))

    def ingest(self, telemetry: dict):
        with self.lock:
            t = dict(telemetry)
            ts = t.get("timestamp")
            if hasattr(ts, "isoformat"):
                t["timestamp"] = ts.isoformat()

            expected = self.physics.expected(t)
            residuals = self.physics.residuals(t, expected)
            trust = self.trust.evaluate(t, residuals, self.previous)
            quality = self.trust.quality(t, trust)
            health = self.health.compute(t, residuals, trust)
            ai = self.ai.predict(t, residuals)

            ai_conf = ai["fault_confidence"] * 100
            sensor_conf = sum(trust.values()) / max(1, len(trust))
            physics_conf = self._physics_confidence(residuals, bool(ai["anomaly"]))
            data_conf = float(quality["overall"])
            fused = .40 * ai_conf + .27 * sensor_conf + .23 * physics_conf + .10 * data_conf
            confidence = {
                "ai": ai_conf,
                "sensor": sensor_conf,
                "physics_agreement": physics_conf,
                "data_quality": data_conf,
                "decision": max(0.0, min(100.0, fused)),
            }

            maintenance = self.maint.decide(health, ai, trust)
            ready = readiness(health, ai, maintenance)
            self.state = {
                "engine_id": t.get("engine_id", settings.engine_id),
                "timestamp": t["timestamp"],
                "telemetry": t,
                "expected": expected,
                "residuals": residuals,
                "sensor_trust": trust,
                "data_quality": quality,
                "health": health,
                "ai": ai,
                "confidence": confidence,
                "maintenance": maintenance,
                "readiness": ready,
                "twin_meta": {
                    "physics_model": self.physics.MODEL_ID,
                    "telemetry_source": "SIMULATED_OR_EXTERNAL",
                    "validation_scope": "SYNTHETIC_PROOF_OF_CONCEPT",
                },
            }
            self.previous = t
            self.replay.sample(self.state)
            persistence.save(self.state)
            return self.state

    def get(self):
        return self.state


manager = TwinManager()
