from collections import deque
from datetime import UTC, datetime, timedelta

from app.services.twin_manager import TwinManager


def test_short_observation_does_not_amplify_single_sensor_noise():
    twin = TwinManager.__new__(TwinManager)
    now = datetime.now(UTC)
    twin.history = deque([{"timestamp": now.isoformat(), "telemetry": {"cht": 180}}])
    assert twin._trend({"timestamp": (now + timedelta(milliseconds=100)).isoformat(), "cht": 182}, "cht") == 0
    twin.history = deque(
        [
            {"timestamp": (now + timedelta(seconds=i)).isoformat(), "telemetry": {"cht": 180 + i}}
            for i in range(5)
        ]
    )
    assert twin._trend({"timestamp": (now + timedelta(seconds=5)).isoformat(), "cht": 185}, "cht") == 60
