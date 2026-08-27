def maintenance_recommendation(
    telemetry: dict,
    residuals: dict,
    health: dict,
    ai: dict,
    sensor_trust: dict,
) -> dict:
    fault = ai.get("fault", "unknown")
    probability = float(ai.get("fault_probability", 0) or 0)

    if sensor_trust and min(sensor_trust.values()) < 45:
        sensor = min(sensor_trust, key=sensor_trust.get)
        return {
            "priority": "CHECK_SENSOR",
            "message": f"Verify {sensor} sensor integrity before making a maintenance decision.",
        }

    if fault == "lubrication" and probability >= 0.55:
        return {
            "priority": "INSPECT_BEFORE_ENDURANCE_MISSION",
            "message": "Inspect the lubrication subsystem; oil-pressure behavior and related features indicate possible degradation.",
        }

    if fault == "overheating" and probability >= 0.55:
        return {
            "priority": "THERMAL_INSPECTION",
            "message": "Inspect cooling/thermal condition before the next high-load mission.",
        }

    if health.get("overall", 100) < 65:
        return {
            "priority": "MAINTENANCE_REVIEW",
            "message": "Engine health is degraded. Perform engineering review before a demanding mission.",
        }

    return {
        "priority": "MONITOR",
        "message": "No high-priority maintenance action from the current prototype state; continue monitoring.",
    }
