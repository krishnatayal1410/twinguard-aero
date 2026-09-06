from copy import deepcopy
from datetime import datetime, timedelta, timezone

from app.main import _runtime_snapshot


def state(timestamp=None, quality=96.0):
    return {
        "engine_id": "ENGINE-01",
        "timestamp": (timestamp or datetime.now(timezone.utc)).isoformat(),
        "data_quality": {"overall": quality, "label": "GOOD" if quality >= 88 else "POOR" if quality < 70 else "REVIEW"},
        "readiness": {"status": "READY", "label": "READY", "reason": "nominal"},
    }


def test_stale_state_forces_data_hold():
    old = datetime.now(timezone.utc) - timedelta(seconds=60)
    snapshot = _runtime_snapshot(state(timestamp=old))
    assert snapshot["runtime_validity"]["stale"] is True
    assert snapshot["runtime_validity"]["decision_eligible"] is False
    assert snapshot["readiness"]["status"] == "DATA_HOLD"
    assert "stale" in snapshot["readiness"]["reason"].lower()


def test_low_quality_state_forces_data_hold_even_when_fresh():
    snapshot = _runtime_snapshot(state(quality=55.0))
    assert snapshot["runtime_validity"]["stale"] is False
    assert snapshot["runtime_validity"]["decision_eligible"] is False
    assert snapshot["readiness"]["status"] == "DATA_HOLD"
    assert "data-quality" in snapshot["readiness"]["reason"].lower()


def test_runtime_snapshot_does_not_mutate_saved_twin_state():
    original = state()
    saved = deepcopy(original)
    _runtime_snapshot(original)
    assert original == saved
