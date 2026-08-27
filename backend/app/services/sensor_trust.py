def calculate_sensor_trust(telemetry: dict, residuals: dict) -> dict[str, float]:
    """
    Lightweight sensor-consistency score for the MVP.
    It is deliberately transparent and should later be replaced/calibrated
    using real sensor noise/failure data and state estimation.
    """
    trust = {
        "cht": 100 - min(80, abs(residuals.get("cht_residual", 0)) * 2.0),
        "egt": 100 - min(80, abs(residuals.get("egt_residual", 0)) * 0.7),
        "oil_pressure": 100
        - min(80, abs(residuals.get("oil_pressure_residual", 0)) * 55),
        "fuel_flow": 100
        - min(80, abs(residuals.get("fuel_flow_residual", 0)) * 6),
        "vibration": 100
        - min(80, max(0, telemetry.get("vibration", 0) - 0.35) * 120),
    }
    return {name: round(max(0.0, score), 1) for name, score in trust.items()}
