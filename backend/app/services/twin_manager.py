from __future__ import annotations
from collections import deque
from datetime import datetime
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
        self.history = deque(maxlen=120)
        self.event_history = deque(maxlen=120)
        self.anomaly_streak = 0

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
            corroborating = sum(1 for value in normalized if value >= .35)
            strongest = max(normalized) if normalized else 0
            return max(45.0, min(100.0, 52 + 9 * corroborating + 16 * min(1.0, strongest)))
        mean = sum(normalized) / max(1, len(normalized))
        return max(45.0, min(100.0, 100 - mean * 38))

    @staticmethod
    def _seconds(timestamp) -> float | None:
        try:
            if isinstance(timestamp, str):
                timestamp = datetime.fromisoformat(timestamp.replace("Z", "+00:00"))
            return timestamp.timestamp()
        except Exception:
            return None

    def _trend(self, current: dict, key: str, section: str = "telemetry", window: int = 12) -> float:
        points = []
        for item in list(self.history)[-(window - 1):]:
            source = item.get(section, {})
            if key in source:
                ts = self._seconds(item.get("timestamp"))
                if ts is not None:
                    points.append((ts, float(source[key])))
        current_source = current if section == "telemetry" else current.get(section, {})
        if key in current_source:
            ts = self._seconds(current.get("timestamp"))
            if ts is not None:
                points.append((ts, float(current_source[key])))
        if len(points) < 2:
            return 0.0
        dt = points[-1][0] - points[0][0]
        if dt <= 0:
            return 0.0
        return (points[-1][1] - points[0][1]) / dt * 60.0

    def _telemetry_trends(self, t: dict) -> dict:
        return {
            "oil_pressure_per_min": self._trend(t, "oil_pressure"),
            "oil_temperature_per_min": self._trend(t, "oil_temperature"),
            "cht_per_min": self._trend(t, "cht"),
            "egt_per_min": self._trend(t, "egt"),
            "vibration_per_min": self._trend(t, "vibration"),
            "battery_voltage_per_min": self._trend(t, "battery_voltage"),
            "alternator_voltage_per_min": self._trend(t, "alternator_voltage"),
        }

    def _health_trend(self, t: dict, health: dict) -> float:
        points = []
        for item in list(self.history)[-11:]:
            if "overall" in item.get("health", {}):
                ts = self._seconds(item.get("timestamp"))
                if ts is not None:
                    points.append((ts, float(item["health"]["overall"])))
        ts = self._seconds(t.get("timestamp"))
        if ts is not None:
            points.append((ts, float(health["overall"])))
        if len(points) < 2 or points[-1][0] <= points[0][0]:
            return 0.0
        return (points[-1][1] - points[0][1]) / (points[-1][0] - points[0][0]) * 60.0

    def _event(self, timestamp: str, event_type: str, severity: str, message: str):
        self.event_history.append({"timestamp": timestamp, "type": event_type, "severity": severity, "message": message})

    def _record_events(self, previous: dict | None, current: dict):
        ts = str(current["timestamp"])
        if previous is None:
            self._event(ts, "TWIN_SYNCHRONIZED", "success", "Digital Twin synchronized with live telemetry.")
            return

        prev_ai = previous.get("ai", {})
        cur_ai = current.get("ai", {})
        if cur_ai.get("anomaly") and not prev_ai.get("anomaly"):
            self._event(ts, "ANOMALY_DETECTED", "warning", "Persistent residual evidence crossed the anomaly threshold.")

        prev_fault = str(prev_ai.get("probable_fault", "normal"))
        cur_fault = str(cur_ai.get("probable_fault", "normal"))
        if cur_fault != "normal" and cur_fault != prev_fault:
            self._event(ts, "FAULT_IDENTIFIED", "warning", f"Probable fault changed to {cur_fault}.")

        prev_priority = str(previous.get("maintenance", {}).get("priority", ""))
        cur_priority = str(current.get("maintenance", {}).get("priority", ""))
        if cur_priority and cur_priority != prev_priority:
            severity = "critical" if cur_priority in {"NO_GO", "HIGH"} else "warning"
            self._event(ts, "MAINTENANCE_CHANGE", severity, f"Maintenance priority changed to {cur_priority}.")

        prev_health = float(previous.get("health", {}).get("overall", 100.0))
        cur_health = float(current.get("health", {}).get("overall", 100.0))
        if prev_health >= 86 > cur_health:
            self._event(ts, "HEALTH_CAUTION", "warning", f"Overall health crossed the caution threshold at {cur_health:.1f}/100.")
        if prev_health >= 70 > cur_health:
            self._event(ts, "HEALTH_CRITICAL", "critical", f"Overall health crossed the high-risk threshold at {cur_health:.1f}/100.")

        prev_quality = float(previous.get("data_quality", {}).get("overall", 100.0))
        cur_quality = float(current.get("data_quality", {}).get("overall", 100.0))
        if prev_quality >= settings.mission_min_data_quality > cur_quality:
            self._event(ts, "DATA_QUALITY_HOLD", "critical", f"Data quality fell below the mission threshold at {cur_quality:.1f}/100.")

    def ingest(self, telemetry: dict):
        with self.lock:
            t = dict(telemetry)
            ts = t.get("timestamp")
            if hasattr(ts, "isoformat"):
                t["timestamp"] = ts.isoformat()

            expected = self.physics.expected(t)
            residuals = self.physics.residuals(t, expected)
            trends = self._telemetry_trends(t)
            trust = self.trust.evaluate(t, residuals, self.previous)
            quality = self.trust.quality(t, trust)
            health = self.health.compute(t, residuals, trust)
            trends["health_index_per_min"] = self._health_trend(t, health)
            ai = self.ai.predict(t, residuals, trends)

            self.anomaly_streak = self.anomaly_streak + 1 if ai["anomaly"] else 0
            ai["anomaly_persistence_samples"] = self.anomaly_streak

            ai_conf = ai["fault_confidence"] * 100
            sensor_conf = sum(trust.values()) / max(1, len(trust))
            physics_conf = self._physics_confidence(residuals, bool(ai["anomaly"]))
            data_conf = float(quality["overall"])
            persistence_conf = min(100.0, 35.0 + self.anomaly_streak * 8.0) if ai["anomaly"] else 100.0
            fused = .34 * ai_conf + .23 * sensor_conf + .20 * physics_conf + .10 * data_conf + .13 * persistence_conf
            confidence = {
                "ai": ai_conf,
                "sensor": sensor_conf,
                "physics_agreement": physics_conf,
                "data_quality": data_conf,
                "temporal_persistence": persistence_conf,
                "decision": max(0.0, min(100.0, fused)),
            }

            maintenance = self.maint.decide(health, ai, trust)
            ready = readiness(health, ai, maintenance, quality)
            new_state = {
                "engine_id": t.get("engine_id", settings.engine_id),
                "timestamp": t["timestamp"],
                "telemetry": t,
                "expected": expected,
                "residuals": residuals,
                "trends": trends,
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
                    "freshness_gate_seconds": settings.telemetry_stale_seconds,
                    "mission_min_data_quality": settings.mission_min_data_quality,
                },
            }
            self._record_events(self.state, new_state)
            new_state["events"] = list(self.event_history)
            self.state = new_state
            self.previous = t
            self.history.append({"timestamp": t["timestamp"], "telemetry": t, "health": health, "ai": ai})
            self.replay.sample(self.state)
            persistence.save(self.state)
            return self.state

    def get(self):
        return self.state


manager = TwinManager()
