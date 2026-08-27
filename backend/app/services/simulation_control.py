from datetime import datetime, timezone
from threading import Lock
from typing import Literal

from pydantic import BaseModel, Field


FaultType = Literal[
    "normal",
    "lubrication",
    "overheating",
    "vibration",
    "sensor_drift",
]


class SimulationControlRequest(BaseModel):
    fault: FaultType = "normal"
    severity: float = Field(default=0.0, ge=0.0, le=1.0)


class SimulationControl:
    # Development-only control state for the synthetic engine simulator.

    def __init__(self):
        self._lock = Lock()
        self._fault: FaultType = "normal"
        self._severity: float = 0.0
        self._updated_at = datetime.now(timezone.utc)

    def get(self) -> dict:
        with self._lock:
            return {
                "fault": self._fault,
                "severity": self._severity,
                "updated_at": self._updated_at.isoformat(),
            }

    def set(self, request: SimulationControlRequest) -> dict:
        severity = 0.0 if request.fault == "normal" else float(request.severity)

        with self._lock:
            self._fault = request.fault
            self._severity = severity
            self._updated_at = datetime.now(timezone.utc)
            return {
                "fault": self._fault,
                "severity": self._severity,
                "updated_at": self._updated_at.isoformat(),
            }


simulation_control = SimulationControl()
