from __future__ import annotations


def _clamp(value):
    return max(0.0, min(100.0, float(value)))


class HealthEngine:
    """Transparent subsystem health indices for the proof-of-concept twin.

    The indices are engineering scores derived from residual magnitude,
    corroborating channels and sensor integrity. They are not certified
    airworthiness percentages.
    """

    def compute(self, t, r, trust):
        thermal = _clamp(
            99
            - abs(r["cht_residual"]) * .72
            - abs(r["egt_residual"]) * .16
            - max(0, r["oil_temperature_residual"]) * .24
        )
        lubrication = _clamp(
            99
            - max(0, -r["oil_pressure_residual"]) * 21
            - max(0, r["oil_temperature_residual"]) * .60
            - max(0, t["vibration"] - .30) * 18
        )
        mechanical = _clamp(
            99
            - max(0, t["vibration"] - .27) * 64
            - abs(r["vibration_residual"]) * 27
        )
        combustion = _clamp(
            99
            - abs(r["fuel_flow_residual"]) * 2.8
            - abs(r["egt_residual"]) * .12
            - abs(r.get("injection_timing_residual", 0)) * 3.6
            - max(0, t["vibration"] - .32) * 20
        )
        electrical = _clamp(
            99
            - abs(r["battery_voltage_residual"]) * 7
            - abs(r.get("alternator_voltage_residual", 0)) * 9
        )
        sensor = _clamp(sum(trust.values()) / max(1, len(trust)))

        overall = (
            .23 * thermal
            + .23 * lubrication
            + .19 * mechanical
            + .17 * combustion
            + .10 * electrical
            + .08 * sensor
        )
        return {
            "thermal": thermal,
            "lubrication": lubrication,
            "mechanical": mechanical,
            "combustion": combustion,
            "electrical": electrical,
            "sensor": sensor,
            "overall": overall,
        }


def readiness(health, ai, maintenance):
    if health["overall"] < 67 or maintenance["priority"] == "NO_GO":
        return {
            "status": "NO_GO",
            "label": "NO-GO",
            "reason": "Prototype decision-support logic recommends mission replanning and engineering review for the current simulated state.",
        }
    if ai.get("anomaly") or health["overall"] < 86 or maintenance["priority"] == "INSPECT_BEFORE_NEXT_MISSION":
        return {
            "status": "REVIEW",
            "label": "REVIEW",
            "reason": "Prototype decision-support logic recommends engineering review before mission release.",
        }
    return {
        "status": "READY",
        "label": "READY",
        "reason": "Current synthetic twin state is within the demonstrator's nominal envelope.",
    }
