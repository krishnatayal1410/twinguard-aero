from __future__ import annotations


def clamp(value: float, low: float, high: float) -> float:
    return max(low, min(high, value))


def refine_sensor_trust(
    telemetry: dict,
    residuals: dict,
    sensor_trust: dict,
    ai: dict,
) -> dict:
    """
    Cross-sensor refinement for the synthetic MVP.

    A sensor disagreeing with the physics model does not automatically mean
    the sensor has failed. When related physical signals agree, preserve trust
    in that sensor and treat the pattern as evidence of a real engine fault.
    """

    trust = dict(sensor_trust or {})

    oil_pressure = float(telemetry.get("oil_pressure", 0) or 0)
    oil_temp = float(telemetry.get("oil_temp", 0) or 0)
    vibration = float(telemetry.get("vibration", 0) or 0)
    oil_residual = abs(float(residuals.get("oil_pressure_residual", 0) or 0))

    predicted_fault = str(ai.get("fault", "normal"))
    fault_probability = float(ai.get("fault_probability", 0) or 0)

    correlated_lubrication_evidence = (
        oil_pressure < 4.0
        and oil_temp > 98
        and vibration > 0.32
    )

    ai_supports_lubrication = (
        predicted_fault == "lubrication"
        and fault_probability >= 0.55
    )

    if correlated_lubrication_evidence or ai_supports_lubrication:
        current = float(trust.get("oil_pressure", 80) or 80)
        trust["oil_pressure"] = max(current, 82.0)

    elif oil_residual > 0.8:
        other_signals_normal = oil_temp < 98 and vibration < 0.32

        if other_signals_normal:
            current = float(trust.get("oil_pressure", 80) or 80)
            trust["oil_pressure"] = min(current, 55.0)

    return {
        key: round(clamp(float(value), 0.0, 100.0), 1)
        for key, value in trust.items()
    }


def maintenance_recommendation(
    telemetry: dict,
    residuals: dict,
    sensor_trust: dict,
    ai: dict,
    health: dict,
) -> dict:
    """
    Transparent prototype decision-support logic.

    It intentionally uses cross-sensor evidence so a real physical fault is
    not incorrectly reduced to a single-sensor warning.
    """

    oil_pressure = float(telemetry.get("oil_pressure", 0) or 0)
    oil_temp = float(telemetry.get("oil_temp", 0) or 0)
    vibration = float(telemetry.get("vibration", 0) or 0)
    cht = float(telemetry.get("cht", 0) or 0)
    egt = float(telemetry.get("egt", 0) or 0)

    overall_health = float(health.get("overall", 100) or 100)

    fault = str(ai.get("fault", "normal"))
    probability = float(ai.get("fault_probability", 0) or 0)
    anomaly = bool(ai.get("anomaly", False))

    oil_sensor_trust = float(sensor_trust.get("oil_pressure", 100) or 100)

    lubrication_evidence = (
        oil_pressure < 4.0
        and (oil_temp > 98 or vibration > 0.32)
    )

    if lubrication_evidence or (
        fault == "lubrication" and probability >= 0.55
    ):
        return {
            "priority": "INSPECT_BEFORE_NEXT_MISSION",
            "system": "lubrication",
            "message": (
                "Lubrication degradation is likely. Inspect oil pressure, "
                "lubrication condition, oil temperature and related mechanical "
                "components before the next mission."
            ),
        }

    if (
        fault == "overheating" and probability >= 0.55
    ) or cht > 215 or egt > 780:
        return {
            "priority": "INSPECT_BEFORE_NEXT_MISSION",
            "system": "thermal",
            "message": (
                "Abnormal thermal behaviour detected. Inspect cooling, "
                "combustion and thermal management before the next mission."
            ),
        }

    if (
        fault == "vibration" and probability >= 0.55
    ) or vibration > 0.50:
        return {
            "priority": "INSPECT_BEFORE_NEXT_MISSION",
            "system": "mechanical",
            "message": (
                "Abnormal vibration detected. Inspect mounting, rotating "
                "components and mechanical condition."
            ),
        }

    if fault == "sensor_drift" and probability >= 0.55:
        return {
            "priority": "CHECK_SENSOR",
            "system": "sensor",
            "message": (
                "Sensor drift is likely. Verify sensor integrity and "
                "cross-check the measurement before making a maintenance decision."
            ),
        }

    if oil_sensor_trust < 60 and oil_temp < 98 and vibration < 0.32:
        return {
            "priority": "CHECK_SENSOR",
            "system": "oil_pressure_sensor",
            "message": (
                "Oil-pressure reading is inconsistent with related engine "
                "behaviour. Verify sensor integrity before making a maintenance "
                "decision."
            ),
        }

    if anomaly or overall_health < 75:
        return {
            "priority": "ENGINEERING_REVIEW",
            "system": "general",
            "message": (
                "Abnormal engine behaviour detected. Perform engineering "
                "review before the next demanding mission."
            ),
        }

    return {
        "priority": "MONITOR",
        "system": "none",
        "message": (
            "No high-priority maintenance action from the current prototype "
            "state; continue monitoring."
        ),
    }


class RULStabilizer:
    """
    Prototype temporal smoothing for synthetic RUL predictions.

    This prevents unrealistic second-to-second jumps and prevents RUL from
    increasing materially while a fault/anomaly is active.
    """

    def __init__(self):
        self.previous: float | None = None

    def reset(self) -> None:
        self.previous = None

    def update(
        self,
        raw_rul: float | None,
        health: dict,
        ai: dict,
    ) -> float | None:
        if raw_rul is None:
            return self.previous

        raw_rul = max(0.0, float(raw_rul))
        overall_health = float(health.get("overall", 100) or 100)

        fault = str(ai.get("fault", "normal"))
        fault_probability = float(ai.get("fault_probability", 0) or 0)
        anomaly = bool(ai.get("anomaly", False))

        health_factor = clamp(
            0.55 + (overall_health / 100.0) * 0.45,
            0.55,
            1.0,
        )

        adjusted = raw_rul * health_factor

        if anomaly:
            adjusted *= 0.90

        if fault != "normal":
            fault_penalty = 1.0 - (
                0.20 * clamp(fault_probability, 0.0, 1.0)
            )
            adjusted *= fault_penalty

        if self.previous is None:
            self.previous = adjusted
            return round(adjusted, 1)

        fault_active = anomaly or fault != "normal" or overall_health < 90

        if fault_active:
            # During degradation, do not allow a large artificial increase.
            adjusted = min(adjusted, self.previous + 0.2)

        alpha = 0.12
        smoothed = alpha * adjusted + (1.0 - alpha) * self.previous

        # Bound second-to-second movement in either direction.
        max_change = 2.0
        smoothed = clamp(
            smoothed,
            self.previous - max_change,
            self.previous + max_change,
        )

        self.previous = max(0.0, smoothed)
        return round(self.previous, 1)


rul_stabilizer = RULStabilizer()
