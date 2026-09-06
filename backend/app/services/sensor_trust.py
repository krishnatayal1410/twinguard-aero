from __future__ import annotations
from datetime import datetime, timezone

LIMITS = {
    "cht": 35.0,
    "egt": 85.0,
    "oil_pressure": 1.6,
    "oil_temperature": 28.0,
    "fuel_flow": 4.0,
    "vibration": 0.65,
    "battery_voltage": 2.0,
    "alternator_voltage": 2.5,
    "injection_timing": 3.0,
}

RELATED = {
    "cht": ("egt", "oil_temperature"),
    "egt": ("cht", "fuel_flow", "injection_timing"),
    "oil_pressure": ("oil_temperature", "vibration"),
    "oil_temperature": ("oil_pressure", "cht"),
    "fuel_flow": ("egt", "injection_timing"),
    "vibration": ("oil_pressure", "egt"),
    "battery_voltage": ("alternator_voltage",),
    "alternator_voltage": ("battery_voltage",),
    "injection_timing": ("egt", "fuel_flow"),
}

JUMP_LIMITS = {
    "cht": 16,
    "egt": 45,
    "oil_pressure": .7,
    "oil_temperature": 12,
    "fuel_flow": 2.5,
    "vibration": .3,
    "battery_voltage": 1.1,
    "alternator_voltage": 1.3,
    "injection_timing": 2.2,
}


class SensorTrustEngine:
    """Estimate measurement trust independently from engine health.

    A large residual is not automatically a bad sensor: it may be the physical
    fault TwinGuard is trying to detect. Trust is reduced most strongly when a
    channel is an isolated outlier, changes implausibly fast, or disagrees with
    correlated measurements.
    """

    @staticmethod
    def _normalized(residuals: dict, key: str) -> float:
        return abs(float(residuals.get(f"{key}_residual", 0.0))) / LIMITS[key]

    def evaluate(self, t: dict, residuals: dict, previous: dict | None = None):
        trust = {}
        for key in LIMITS:
            severity = self._normalized(residuals, key)
            corroboration = max((self._normalized(residuals, other) for other in RELATED.get(key, ())), default=0.0)

            score = 98.0
            if severity > .65:
                # Isolated disagreement is suspicious. Corroborated disagreement
                # is evidence of a real engine condition, not sensor failure.
                isolation = max(0.0, severity - .55 * corroboration)
                score -= min(58.0, 42.0 * isolation ** 1.25)

            if previous and key in previous:
                delta = abs(float(t[key]) - float(previous[key]))
                jump = max(0.0, delta - JUMP_LIMITS[key]) / max(JUMP_LIMITS[key], 1e-6)
                score -= min(30.0, jump * 22.0)

            trust[key] = max(12.0, min(100.0, score))
        return trust

    def quality(self, t: dict, trust: dict):
        required = [
            "rpm",
            "throttle",
            "cht",
            "egt",
            "oil_pressure",
            "oil_temperature",
            "fuel_flow",
            "vibration",
            "battery_voltage",
            "alternator_voltage",
            "altitude",
            "ambient_temperature",
            "injection_timing",
        ]
        complete = sum(1 for k in required if k in t and t[k] is not None) / len(required) * 100
        freshness = 100.0
        try:
            ts = t.get("timestamp")
            if isinstance(ts, str):
                ts = datetime.fromisoformat(ts.replace("Z", "+00:00"))
            age = abs((datetime.now(timezone.utc) - ts).total_seconds())
            freshness = max(0.0, 100 - age * 12)
        except Exception:
            freshness = 75.0

        integrity = sum(trust.values()) / max(1, len(trust))
        signal_quality = max(45.0, min(100.0, 94 - (100 - integrity) * .20))
        overall = .34 * complete + .22 * freshness + .30 * integrity + .14 * signal_quality
        label = "GOOD" if overall >= 88 else "REVIEW" if overall >= 70 else "POOR"
        return {
            "completeness": complete,
            "freshness": freshness,
            "sensor_integrity": integrity,
            "signal_quality": signal_quality,
            "overall": overall,
            "label": label,
        }
