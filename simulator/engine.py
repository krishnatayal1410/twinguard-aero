from dataclasses import dataclass, asdict
from datetime import datetime, timezone
import random, math

@dataclass
class EngineState:
    engine_id: str
    timestamp: str
    rpm: float
    throttle: float
    altitude: float
    ambient_temp: float
    cht: float
    egt: float
    oil_pressure: float
    oil_temp: float
    fuel_flow: float
    vibration: float
    battery_voltage: float
    operating_hours: float

class EngineSimulator:
    def __init__(self, seed=42):
        random.seed(seed)
        self.t = 0
        self.hours = 0.0
        self.fault = "normal"
        self.severity = 0.0

    def set_fault(self, fault, severity=.7):
        self.fault = fault
        self.severity = max(0.0, min(1.0, severity))

    def step(self):
        self.t += 1
        self.hours += 1/3600
        throttle = 68 + 7*math.sin(self.t/40) + random.gauss(0,.7)
        altitude = 4200 + 250*math.sin(self.t/120)
        ambient = 28 - altitude*.004 + random.gauss(0,.3)
        rpm = 1900 + throttle*32 + random.gauss(0,25)
        cht = 120 + throttle*.85 + altitude*.0015 + random.gauss(0,1.2)
        egt = 500 + throttle*2.8 + altitude*.002 + random.gauss(0,2.5)
        oil_temp = 70 + throttle*.35 + random.gauss(0,.8)
        oil_pressure = 4.7 - (oil_temp-80)*.012 + random.gauss(0,.04)
        fuel_flow = 2 + throttle*.22 + random.gauss(0,.15)
        vibration = .18 + rpm/50000 + random.gauss(0,.012)
        battery = 27.6 + random.gauss(0,.12)
        s = self.severity

        if self.fault == "lubrication":
            oil_pressure -= 1.2*s; oil_temp += 18*s; vibration += .22*s
        elif self.fault == "overheating":
            cht += 35*s; egt += 55*s; oil_temp += 12*s
        elif self.fault == "vibration":
            vibration += .45*s
        elif self.fault == "sensor_drift":
            cht += min(30, self.t*.05)*s

        return asdict(EngineState(
            "ENGINE-01", datetime.now(timezone.utc).isoformat(),
            round(rpm,2), round(throttle,2), round(altitude,2), round(ambient,2),
            round(cht,2), round(egt,2), round(oil_pressure,3), round(oil_temp,2),
            round(fuel_flow,2), round(max(0,vibration),4), round(battery,2),
            round(self.hours,4)
        ))
