from __future__ import annotations
from datetime import datetime, timezone
from typing import Dict, Literal, Optional
from pydantic import BaseModel, Field, StringConstraints
from typing_extensions import Annotated

EngineId = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=64, pattern=r"^[A-Za-z0-9_-]+$")]


class SignUpRequest(BaseModel):
    name: Annotated[str, StringConstraints(strip_whitespace=True, min_length=2, max_length=120)]
    email: Annotated[str, StringConstraints(strip_whitespace=True, min_length=3, max_length=255, pattern=r"^[^\s@]+@[^\s@]+\.[^\s@]+$")]
    password: Annotated[str, StringConstraints(min_length=10, max_length=128)]


class SignInRequest(BaseModel):
    email: Annotated[str, StringConstraints(strip_whitespace=True, min_length=3, max_length=255, pattern=r"^[^\s@]+@[^\s@]+\.[^\s@]+$")]
    password: Annotated[str, StringConstraints(min_length=1, max_length=128)]


class AuthUser(BaseModel):
    id: int
    name: str
    email: str
    role: str


class AuthResponse(BaseModel):
    token: str
    user: AuthUser


class Telemetry(BaseModel):
    """Canonical TwinGuard telemetry contract.

    The proof-of-concept uses bar internally for oil pressure; the HMI converts
    bar to kPa exactly once for engineering display. All components must use
    these names and units so simulator, backend, WebSocket and frontend remain
    contract-compatible.
    """

    engine_id: EngineId = "ENGINE-01"
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    rpm: float = Field(ge=0, le=10000, description="Engine crankshaft speed, rev/min")
    throttle: float = Field(ge=0, le=100, description="Throttle demand, percent")
    cht: float = Field(ge=-80, le=400, description="Cylinder-head temperature, degC")
    egt: float = Field(ge=-80, le=1300, description="Exhaust-gas temperature, degC")
    oil_pressure: float = Field(ge=0, le=15, description="Oil pressure, bar")
    oil_temperature: float = Field(ge=-80, le=250, description="Oil temperature, degC")
    fuel_flow: float = Field(ge=0, le=100, description="Fuel flow, L/h surrogate")
    vibration: float = Field(ge=0, le=10, description="Vibration magnitude, g RMS surrogate")
    battery_voltage: float = Field(ge=0, le=60, description="Battery bus voltage, V")
    alternator_voltage: float = Field(28, ge=0, le=60, description="Alternator output voltage, V")
    altitude: float = Field(ge=-1000, le=20000, description="Geometric altitude, m")
    ambient_temperature: float = Field(ge=-80, le=80, description="Ambient temperature, degC")
    injection_timing: float = Field(18, ge=-30, le=60, description="Injection/ignition timing proxy, deg")
    operating_hours: float = Field(0, ge=0, le=200000, description="Accumulated engine operating time, h")


class MissionRequest(BaseModel):
    mission_type: Literal["endurance", "high_altitude", "hot_weather", "rapid_throttle", "patrol"] = "endurance"
    duration_hours: float = Field(8, ge=.25, le=48, description="Planned mission duration, h")
    cruise_altitude_m: float = Field(5500, ge=0, le=12000, description="Planned representative cruise altitude, m")
    ambient_temp_c: float = Field(35, ge=-50, le=70, description="Representative ambient temperature, degC")
    average_throttle_pct: float = Field(75, ge=10, le=100, description="Representative average throttle/load, percent")


class FaultCommand(BaseModel):
    fault: Literal[
        "normal",
        "lubrication",
        "overheating",
        "cooling_degradation",
        "vibration",
        "sensor_drift",
        "injector",
        "misfire",
        "combustion_instability",
        "alternator_degradation",
    ]
    severity: float = Field(0, ge=0, le=1)


class ReplayStart(BaseModel):
    label: Optional[Annotated[str, StringConstraints(strip_whitespace=True, max_length=120)]] = None


class TwinEvent(BaseModel):
    timestamp: datetime
    type: str
    severity: Literal["info", "warning", "critical", "success"]
    message: str


class TwinState(BaseModel):
    engine_id: str
    timestamp: datetime
    telemetry: Dict[str, float | str]
    expected: Dict[str, float]
    residuals: Dict[str, float]
    trends: Dict[str, float]
    events: list[TwinEvent]
    sensor_trust: Dict[str, float]
    data_quality: Dict[str, float | str]
    health: Dict[str, float]
    ai: Dict[str, object]
    confidence: Dict[str, float]
    maintenance: Dict[str, object]
    readiness: Dict[str, object]
