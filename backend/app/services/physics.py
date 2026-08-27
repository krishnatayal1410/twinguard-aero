from ..schemas.telemetry import Telemetry


def expected_state(t: Telemetry) -> dict[str, float]:
    """
    Lightweight MVP expected-behavior model.

    These equations are intentionally simplified and are NOT calibrated
    engine-specific aerospace equations. They exist to demonstrate the
    Digital Twin architecture until real performance maps/test-rig data exist.
    """
    throttle_fraction = t.throttle / 100.0
    altitude_factor = min(t.altitude / 10000.0, 1.5)

    expected_cht = 120 + 75 * throttle_fraction + 0.10 * t.ambient_temp + 8 * altitude_factor
    expected_egt = 500 + 250 * throttle_fraction + 18 * altitude_factor
    expected_oil_pressure = max(
        2.5,
        4.8 - 0.006 * (t.oil_temp - 80) + 0.00005 * t.rpm,
    )
    expected_fuel_flow = max(0.5, 2.0 + 22 * throttle_fraction)

    return {
        "cht": round(expected_cht, 3),
        "egt": round(expected_egt, 3),
        "oil_pressure": round(expected_oil_pressure, 3),
        "fuel_flow": round(expected_fuel_flow, 3),
    }


def residuals(t: Telemetry, expected: dict[str, float]) -> dict[str, float]:
    return {
        "cht_residual": round(t.cht - expected["cht"], 3),
        "egt_residual": round(t.egt - expected["egt"], 3),
        "oil_pressure_residual": round(
            t.oil_pressure - expected["oil_pressure"], 3
        ),
        "fuel_flow_residual": round(t.fuel_flow - expected["fuel_flow"], 3),
    }
