from backend.app.services.decision_support import (
    RULStabilizer,
    maintenance_recommendation,
    refine_sensor_trust,
)


def test_lubrication_fault_is_not_misclassified_as_sensor_failure():
    telemetry = {
        "oil_pressure": 3.6,
        "oil_temp": 103.0,
        "vibration": 0.41,
        "cht": 185.0,
        "egt": 700.0,
    }
    residuals = {"oil_pressure_residual": -1.1}
    trust = {"oil_pressure": 39.0, "vibration": 90.0}
    ai = {
        "fault": "lubrication",
        "fault_probability": 0.90,
        "anomaly": True,
    }
    health = {"overall": 84.0}

    refined = refine_sensor_trust(telemetry, residuals, trust, ai)
    recommendation = maintenance_recommendation(
        telemetry,
        residuals,
        refined,
        ai,
        health,
    )

    assert refined["oil_pressure"] >= 82.0
    assert recommendation["system"] == "lubrication"
    assert recommendation["priority"] == "INSPECT_BEFORE_NEXT_MISSION"


def test_isolated_oil_pressure_mismatch_can_flag_sensor():
    telemetry = {
        "oil_pressure": 3.4,
        "oil_temp": 92.0,
        "vibration": 0.24,
        "cht": 180.0,
        "egt": 690.0,
    }
    residuals = {"oil_pressure_residual": -1.2}
    trust = {"oil_pressure": 42.0}
    ai = {
        "fault": "normal",
        "fault_probability": 0.95,
        "anomaly": False,
    }
    health = {"overall": 94.0}

    refined = refine_sensor_trust(telemetry, residuals, trust, ai)
    recommendation = maintenance_recommendation(
        telemetry,
        residuals,
        refined,
        ai,
        health,
    )

    assert refined["oil_pressure"] <= 55.0
    assert recommendation["priority"] == "CHECK_SENSOR"


def test_rul_does_not_jump_up_during_active_fault():
    stabilizer = RULStabilizer()

    healthy_ai = {
        "fault": "normal",
        "fault_probability": 0.99,
        "anomaly": False,
    }
    fault_ai = {
        "fault": "lubrication",
        "fault_probability": 0.90,
        "anomaly": True,
    }

    healthy = stabilizer.update(
        100.0,
        {"overall": 95.0},
        healthy_ai,
    )
    degraded = stabilizer.update(
        150.0,
        {"overall": 84.0},
        fault_ai,
    )

    assert healthy is not None
    assert degraded is not None
    assert degraded <= healthy + 0.2
