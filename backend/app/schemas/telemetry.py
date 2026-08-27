from datetime import datetime, timezone
from pydantic import BaseModel, Field


class Telemetry(BaseModel):
    engine_id: str = "ENGINE-01"
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    rpm: float = Field(ge=0)
    throttle: float = Field(ge=0, le=100)
    altitude: float = Field(ge=0)
    ambient_temp: float

    cht: float
    egt: float
    oil_pressure: float
    oil_temp: float
    fuel_flow: float = Field(ge=0)
    vibration: float = Field(ge=0)
    battery_voltage: float = Field(ge=0)

    injection_timing: float | None = None
    operating_hours: float = Field(default=0, ge=0)
