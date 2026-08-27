from pathlib import Path

from backend.app.services.mission_replay import MissionReplayStore


def state(i: int, anomaly: bool = False, fault: str = "normal"):
    return {
        "telemetry": {
            "timestamp": f"2026-08-27T12:00:{i:02d}+00:00",
            "cht": 180 + i,
            "egt": 690 + i,
            "oil_pressure": 4.5 - 0.1 * i,
            "vibration": 0.25 + 0.02 * i,
        },
        "health": {"overall": 95 - i * 3},
        "ai": {"anomaly": anomaly, "fault": fault, "rul_hours": 180 - i * 2},
        "maintenance": {
            "priority": "MONITOR" if not anomaly else "INSPECT_BEFORE_NEXT_MISSION"
        },
        "residuals": {"cht_residual": i * 4.0},
        "sensor_trust": {},
    }


def test_replay_summary(tmp_path: Path):
    store = MissionReplayStore(tmp_path / "replay.db")
    mission = store.start("Test Mission")
    store.record(state(0))
    store.record(state(1))
    store.record(state(2, True, "lubrication"))
    finished = store.end()

    assert finished["status"] == "COMPLETED"
    assert finished["summary"]["sample_count"] == 3
    assert finished["summary"]["end_health"] < finished["summary"]["start_health"]
    assert "lubrication" in finished["summary"]["faults_observed"]
    assert any(
        event["type"] == "ANOMALY_DETECTED"
        for event in finished["summary"]["events"]
    )

    detail = store.get_mission(mission["id"])
    assert detail is not None
    assert len(detail["samples"]) == 3
