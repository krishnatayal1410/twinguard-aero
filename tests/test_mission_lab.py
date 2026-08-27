from backend.app.services.mission_lab import MissionLabRequest, analyze_mission


def healthy_twin():
    return {
        "telemetry": {"rpm": 4100},
        "health": {"overall": 94.0},
        "ai": {
            "rul_hours": 180.0,
            "anomaly": False,
            "fault": "normal",
            "fault_probability": 0.99,
        },
    }


def test_mission_reduces_health_and_rul():
    result = analyze_mission(
        MissionLabRequest(
            duration_hours=8,
            cruise_altitude_m=5500,
            ambient_temp_c=35,
            average_throttle_pct=75,
            mission_type="endurance",
        ),
        healthy_twin(),
    )

    assert result["prediction"]["post_mission_health"] < 94.0
    assert result["prediction"]["post_mission_rul_hours"] < 180.0
    assert result["risk"]["overall"] in {"LOW", "MEDIUM", "HIGH"}


def test_harsher_mission_has_more_stress():
    mild = analyze_mission(
        MissionLabRequest(
            duration_hours=3,
            cruise_altitude_m=3000,
            ambient_temp_c=20,
            average_throttle_pct=55,
            mission_type="patrol",
        ),
        healthy_twin(),
    )

    harsh = analyze_mission(
        MissionLabRequest(
            duration_hours=10,
            cruise_altitude_m=7000,
            ambient_temp_c=42,
            average_throttle_pct=90,
            mission_type="endurance",
        ),
        healthy_twin(),
    )

    assert harsh["prediction"]["stress_index"] > mild["prediction"]["stress_index"]
    assert harsh["prediction"]["post_mission_health"] < mild["prediction"]["post_mission_health"]
    assert harsh["prediction"]["post_mission_rul_hours"] < mild["prediction"]["post_mission_rul_hours"]
