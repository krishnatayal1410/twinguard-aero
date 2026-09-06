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


def test_rul_interval_is_ordered_and_explicitly_uncalibrated():
    state = manager.ingest(sample())
    interval = state["ai"]["rul_interval_hours"]
    assert 0 <= interval["lower"] <= interval["estimate"] <= interval["upper"]
    assert interval["calibrated_probability_interval"] is False
    assert state["ai"]["rul_uncertainty_hours"] > 0


def test_mission_analysis_direction():
    state = manager.ingest(sample())
    result = manager.mission.analyze(state, MissionRequest())
    assert result["overall_risk"] in {"LOW", "MEDIUM", "HIGH"}
    assert result["post_mission_health"] < result["current_health"]
    assert result["post_mission_rul_hours"] < result["current_rul_hours"]
    assert result["decision_horizon_hours"] >= 0
    assert result["engineering_reserve_hours"] > 0
    assert result["current_rul_interval_hours"]["lower"] <= result["current_rul_hours"] <= result["current_rul_interval_hours"]["upper"]
    assert result["post_mission_rul_interval_hours"]["lower"] <= result["post_mission_rul_hours"] <= result["post_mission_rul_interval_hours"]["upper"]
    assert result["conservative_rul_margin_ratio"] <= result["rul_margin_ratio"]
    assert result["lower_stress_alternative"]["projected_stress_index"] <= result["stress_index"]


def test_mission_profile_is_not_a_decorative_label():
    state = manager.ingest(sample())
    common = dict(duration_hours=8, cruise_altitude_m=5500, ambient_temp_c=35, average_throttle_pct=75)
    endurance = manager.mission.analyze(state, MissionRequest(mission_type="endurance", **common))
    rapid = manager.mission.analyze(state, MissionRequest(mission_type="rapid_throttle", **common))
    hot = manager.mission.analyze(state, MissionRequest(mission_type="hot_weather", **common))
    altitude = manager.mission.analyze(state, MissionRequest(mission_type="high_altitude", **common))

    assert endurance["mission_type"] == "endurance"
    assert rapid["mission_type"] == "rapid_throttle"
    assert rapid["stress_index"] > endurance["stress_index"]
    assert rapid["profile_modifiers"]["mechanical"] > endurance["profile_modifiers"]["mechanical"]
    assert hot["profile_modifiers"]["thermal"] > endurance["profile_modifiers"]["thermal"]
    assert altitude["profile_modifiers"]["combustion"] > endurance["profile_modifiers"]["combustion"]
    assert rapid["profile_modifier_description"]


def test_degraded_state_reduces_mission_margin():
    healthy = manager.ingest(sample())
    healthy_result = manager.mission.analyze(healthy, MissionRequest())

    degraded = sample()
    degraded["oil_pressure"] = 2.8
    degraded["oil_temperature"] = 132
    degraded["vibration"] = .56
    degraded["cht"] = 205
    degraded_state = manager.ingest(degraded)
    degraded_result = manager.mission.analyze(degraded_state, MissionRequest())

    assert degraded_result["current_health"] < healthy_result["current_health"]
    assert degraded_result["mission_margin_hours"] < healthy_result["mission_margin_hours"]
    assert degraded_result["mission_feasibility_index"] <= healthy_result["mission_feasibility_index"]


def test_lubrication_degradation_is_multi_signal_and_not_just_bad_sensor():
    telemetry = sample()
    telemetry["oil_pressure"] = 2.85
    telemetry["oil_temperature"] = 129
    telemetry["vibration"] = .52
    state = manager.ingest(telemetry)
    assert state["residuals"]["oil_pressure_residual"] < -1.0
    assert state["health"]["lubrication"] < 75
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
