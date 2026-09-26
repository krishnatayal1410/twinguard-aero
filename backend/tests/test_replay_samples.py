from concurrent.futures import ThreadPoolExecutor
from datetime import UTC, datetime, timedelta, timezone

import pytest
from app.services.replay import RecordingInProgressError, ReplayService
from app.services.twin_manager import manager


def telemetry(step=0):
    return {
        "engine_id": "ENGINE-01",
        "timestamp": datetime.now(UTC),
        "rpm": 4100 + step,
        "throttle": 70,
        "cht": 181 + step,
        "egt": 702,
        "oil_pressure": 4.47 - step * 0.05,
        "oil_temperature": 108,
        "fuel_flow": 20.6,
        "vibration": 0.23 + step * 0.01,
        "battery_voltage": 27.85,
        "alternator_voltage": 28.15,
        "altitude": 4300,
        "ambient_temperature": 25,
        "injection_timing": 18.8,
        "operating_hours": 42,
    }


def test_replay_returns_actual_persisted_samples():
    run = manager.replay.start("Replay sample contract")
    for step in range(3):
        manager.ingest(telemetry(step))
    completed = manager.replay.end()
    assert completed and completed["id"] == run["id"]
    samples = manager.replay.samples(run["id"])
    assert samples is not None and len(samples) == 3
    assert samples[0]["cht"] == 181
    assert samples[-1]["cht"] == 183
    assert samples[-1]["oil_pressure"] < samples[0]["oil_pressure"]
    assert {
        "timestamp",
        "health",
        "rul",
        "cht",
        "oil_pressure",
        "vibration",
        "anomaly",
        "fault",
        "maintenance",
    } <= set(samples[-1])


def test_twin_state_exposes_real_event_history():
    state = manager.ingest(telemetry())
    assert "events" in state
    assert isinstance(state["events"], list)
    if state["events"]:
        assert {"timestamp", "type", "severity", "message"} <= set(state["events"][-1])


def test_replay_preserves_sensor_timestamp_and_sampling_interval():
    replay = ReplayService()
    run = replay.start("Sensor time fidelity")
    started = datetime(2026, 9, 26, 12, 0, tzinfo=timezone(timedelta(hours=5, minutes=30)))
    for offset in (0, 3, 9):
        sample = telemetry()
        sample["timestamp"] = started + timedelta(seconds=offset)
        state = manager.ingest(sample)
        replay.sample(state)
    completed = replay.end()
    assert completed["summary"]["duration_seconds"] == 9
    rows = replay.samples(run["id"])
    assert datetime.fromisoformat(rows[0]["timestamp"]) == started
    assert rows[0]["timestamp"].endswith("+00:00")


def test_duplicate_recording_start_does_not_orphan_the_active_run():
    replay = ReplayService()
    run = replay.start("Original run")
    with pytest.raises(RecordingInProgressError, match="already active"):
        replay.start("Accidental double click")
    assert replay.active_id == run["id"]
    assert replay.end()["id"] == run["id"]


def test_concurrent_recording_starts_select_exactly_one_active_run():
    replay = ReplayService()

    def start(_):
        try:
            return replay.start("Concurrent operator request")["id"]
        except RecordingInProgressError:
            return None

    with ThreadPoolExecutor(max_workers=4) as pool:
        ids = list(pool.map(start, range(4)))
    assert sum(value is not None for value in ids) == 1
    assert replay.end()["id"] == next(value for value in ids if value is not None)


def test_api_returns_conflict_for_duplicate_recording_start(monkeypatch):
    from app.main import app, require_user
    from fastapi.testclient import TestClient

    replay = ReplayService()
    monkeypatch.setattr(manager, "replay", replay)
    monkeypatch.setitem(app.dependency_overrides, require_user, lambda: {"id": 1})
    client = TestClient(app)
    first = client.post("/api/v1/replay/start", json={"label": "First"})
    duplicate = client.post("/api/v1/replay/start", json={"label": "Duplicate"})
    assert first.status_code == 200
    assert duplicate.status_code == 409
    assert client.post("/api/v1/replay/end").json()["id"] == first.json()["id"]
