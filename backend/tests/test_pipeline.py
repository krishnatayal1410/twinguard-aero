from datetime import datetime, timezone

from app.schemas import MissionRequest
from app.services.twin_manager import manager


def sample():
    return {
        "engine_id": "ENGINE-01",
        "timestamp": datetime.now(timezone.utc),
        "rpm": 4100,
        "throttle": 70,
        "cht": 181,
        "egt": 702,
        "oil_pressure": 4.47,
        "oil_temperature": 108,
        "fuel_flow": 20.6,
        "vibration": .23,
        "battery_voltage": 27.85,
        "alternator_voltage": 28.15,
        "altitude": 4300,
        "ambient_temperature": 25,
        "injection_timing": 18.8,
        "operating_hours": 42,
    }


def test_twin_pipeline():
    state = manager.ingest(sample())
    assert 0 <= state["health"]["overall"] <= 100
    assert {"thermal", "lubrication", "mechanical", "combustion", "electrical", "sensor", "overall"} <= set(state["health"])
    assert "probable_fault" in state["ai"]
    assert state["ai"]["validation_scope"] == "SYNTHETIC_PROOF_OF_CONCEPT"
    assert state["twin_meta"]["physics_model"] == "generic-aero-piston-surrogate-v2"
    assert "decision" in state["confidence"]
    assert "priority" in state["maintenance"]


def test_mission_analysis_direction():
    state = manager.ingest(sample())
    result = manager.mission.analyze(state, MissionRequest())
    assert result["overall_risk"] in {"LOW", "MEDIUM", "HIGH"}
    assert result["post_mission_health"] < result["current_health"]
    assert result["post_mission_rul_hours"] < result["current_rul_hours"]


def test_lubrication_degradation_is_multi_signal_and_not_just_bad_sensor():
    telemetry = sample()
    telemetry["oil_pressure"] = 2.85
    telemetry["oil_temperature"] = 129
    telemetry["vibration"] = .52
    state = manager.ingest(telemetry)
    assert state["residuals"]["oil_pressure_residual"] < -1.0
    assert state["health"]["lubrication"] < 75
    # Corroborating oil temperature/vibration should preserve more trust than an
    # isolated implausible oil-pressure channel would receive.
    physical_fault_trust = state["sensor_trust"]["oil_pressure"]

    isolated = sample()
    isolated["oil_pressure"] = 6.4
    isolated_state = manager.ingest(isolated)
    assert isolated_state["sensor_trust"]["oil_pressure"] < physical_fault_trust


def test_electrical_and_timing_channels_are_part_of_the_twin():
    telemetry = sample()
    telemetry["alternator_voltage"] = 23.5
    state = manager.ingest(telemetry)
    assert "alternator_voltage_residual" in state["residuals"]
    assert "injection_timing_residual" in state["residuals"]
    assert state["health"]["electrical"] < 90


def test_no_turboshaft_fault_taxonomy_leaks_into_runtime():
    state = manager.ingest(sample())
    assert "turbine_blade_degradation" not in state["ai"]["fault_probabilities"]
