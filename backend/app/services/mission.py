def simulate_mission(
    current_state: dict,
    duration_hours: float,
    altitude: float,
    ambient_temp: float,
    throttle: float,
) -> dict:
    """
    Lightweight mission-stress model for the MVP.
    Starts from current Twin health rather than assuming a perfect engine.
    """
    current_health = float(
        (current_state.get("health") or {}).get("overall", 100.0)
    )
    current_rul = (current_state.get("ai") or {}).get("rul_hours")
    if current_rul is None:
        current_rul = max(20.0, current_health * 1.6)

    duration_stress = min(1.0, duration_hours / 12.0)
    altitude_stress = min(1.0, altitude / 8000.0)
    heat_stress = min(1.0, max(0.0, ambient_temp - 20.0) / 30.0)
    load_stress = min(1.0, max(0.0, throttle - 45.0) / 55.0)

    stress_index = (
        0.30 * duration_stress
        + 0.25 * altitude_stress
        + 0.20 * heat_stress
        + 0.25 * load_stress
    )

    health_loss = duration_hours * (1.1 + 4.0 * stress_index)
    predicted_health = max(0.0, current_health - health_loss)
    rul_consumption = duration_hours * (1.0 + 1.7 * stress_index)
    predicted_rul = max(0.0, float(current_rul) - rul_consumption)

    risk_score = 0.55 * stress_index + 0.45 * (1 - predicted_health / 100)
    risk = "HIGH" if risk_score >= 0.62 else "MEDIUM" if risk_score >= 0.36 else "LOW"

    return {
        "stress_index": round(stress_index, 3),
        "current_health": round(current_health, 1),
        "predicted_post_mission_health": round(predicted_health, 1),
        "current_rul_hours": round(float(current_rul), 1),
        "predicted_post_mission_rul_hours": round(predicted_rul, 1),
        "mission_risk": risk,
        "prototype_note": "Synthetic mission model; engine-specific calibration is required.",
    }
