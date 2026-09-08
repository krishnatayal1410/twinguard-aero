from datetime import UTC, datetime

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
