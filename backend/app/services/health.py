def clamp(value: float, low: float = 0.0, high: float = 100.0) -> float:
    return max(low, min(high, value))


def calculate_health(
    telemetry: dict,
    residuals: dict,
    anomaly_score: float = 0.0,
) -> dict[str, float]:
    """
    Explainable MVP health index.

    This is a documented prototype score, not an aerospace-certified health
    index. The weights must later be calibrated against real engine data.
    """
    thermal_penalty = min(35, abs(residuals.get("cht_residual", 0)) * 1.2)
    lubrication_penalty = min(
        45,
        abs(min(residuals.get("oil_pressure_residual", 0), 0)) * 30,
    )
    mechanical_penalty = min(
        45,
        max(0, telemetry.get("vibration", 0) - 0.25) * 100,
    )
    anomaly_penalty = min(20, max(0, anomaly_score) * 20)

    thermal = clamp(100 - thermal_penalty)
    lubrication = clamp(100 - lubrication_penalty)
    mechanical = clamp(100 - mechanical_penalty)
    electrical = clamp(
        100 - max(0, 25 - telemetry.get("battery_voltage", 27)) * 6
    )

    overall = clamp(
        (thermal + lubrication + mechanical + electrical) / 4
        - anomaly_penalty
    )

    return {
        "overall": round(overall, 1),
        "thermal": round(thermal, 1),
        "lubrication": round(lubrication, 1),
        "mechanical": round(mechanical, 1),
        "electrical": round(electrical, 1),
    }
