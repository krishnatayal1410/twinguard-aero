from __future__ import annotations
import argparse
import json
import math
import os
import random
import time
from datetime import datetime, timezone
from urllib.request import Request, urlopen

API = os.getenv("TWINGUARD_API", "http://127.0.0.1:8000")
ENGINE = os.getenv("TWINGUARD_ENGINE_ID", "ENGINE-01")
INGEST_KEY = os.getenv("TWINGUARD_INGEST_KEY", "")
random.seed(int(os.getenv("SIM_SEED", "42")))


class EngineSimulator:
    """Physics-inspired aero-piston telemetry demonstrator.

    This is intentionally not a manufacturer-calibrated engine model. It
    generates coherent operating-condition-dependent telemetry so the complete
    TwinGuard ingestion, residual, diagnostic and mission-decision pipeline can
    be demonstrated without proprietary engine data.
    """

    def __init__(self):
        self.hours = 42.0
        self.phase = 0.0
        self.active_fault = "normal"
        self.fault_level = 0.0

    def config(self):
        headers = {}
        if INGEST_KEY:
            headers["X-TwinGuard-Ingest-Key"] = INGEST_KEY
        try:
            req = Request(API + "/api/v1/simulation/config", headers=headers)
            with urlopen(req, timeout=1.5) as r:
                return json.loads(r.read().decode())
        except Exception:
            return {"fault": "normal", "severity": 0.0}

    def _fault_progress(self, fault: str, target: float) -> float:
        target = max(0.0, min(1.0, target))
        if fault != self.active_fault:
            self.active_fault = fault
            self.fault_level = 0.0
        if fault == "normal":
            self.fault_level = max(0.0, self.fault_level - 0.035)
        else:
            # Progressive degradation is easier to diagnose and more credible
            # than an instantaneous step change in a demo.
            self.fault_level = min(target, self.fault_level + 0.012)
        return self.fault_level

    def sample(self):
        cfg = self.config()
        fault = str(cfg.get("fault", "normal"))
        target_severity = float(cfg.get("severity", 0.0))
        s = self._fault_progress(fault, target_severity)

        self.phase += .08
        self.hours += 1 / 3600
        throttle = 70 + 5 * math.sin(self.phase * .35) + random.gauss(0, 1.4)
        altitude = 4300 + 380 * math.sin(self.phase * .12) + random.gauss(0, 18)
        ambient = 25 + 2.0 * math.sin(self.phase * .08) + random.gauss(0, .25)
        rpm = 4050 + 260 * math.sin(self.phase * .55) + random.gauss(0, 45)

        # Low-order altitude correction used by both simulator and twin. This is
        # a generic surrogate, not an OEM performance map.
        density = max(.58, 1 - altitude / 21000)
        load = throttle / 100
        cht = ambient + 105 + 58 * load + .0048 * (rpm - 2500) + 10 * (1 - density) + random.gauss(0, 2.2)
        egt = 500 + 250 * load + .015 * (rpm - 2500) + 16 * (1 - density) + random.gauss(0, 7)
        oil_t = ambient + 48 + 46 * load + .002 * (rpm - 2500) + random.gauss(0, 1.5)
        oil_p = 3 + .00046 * rpm - .018 * max(oil_t - 85, 0) + random.gauss(0, .045)
        fuel = 5.2 + .0022 * rpm + 7.2 * load / density + random.gauss(0, .18)
        vib = .16 + abs(rpm - 3900) / 11000 + .07 * load + random.gauss(0, .012)
        battery = 27.6 + .25 * min(1, rpm / 2500) + random.gauss(0, .06)
        alternator = 28.15 + random.gauss(0, .05)
        timing = 17.2 + .00032 * (rpm - 2500) + 1.6 * load + random.gauss(0, .12)

        if fault == "lubrication":
            oil_p -= 1.45 * s
            oil_t += 25 * s
            vib += .26 * s
        elif fault == "overheating":
            cht += 45 * s
            egt += 66 * s
            oil_t += 17 * s
        elif fault == "cooling_degradation":
            cht += 34 * s
            oil_t += 20 * s
            egt += 18 * s
        elif fault == "vibration":
            vib += .78 * s
        elif fault == "sensor_drift":
            # Single-channel bias without supporting physical changes.
            oil_p += .85 * s + .25 * s * math.sin(self.phase * .08)
        elif fault == "injector":
            fuel += 2.4 * s
            egt += 75 * s
            timing += 1.7 * s
        elif fault == "misfire":
            rpm += random.gauss(0, 300 * s)
            egt += random.gauss(0, 55 * s)
            vib += .30 * s
        elif fault == "combustion_instability":
            rpm += 130 * s * math.sin(self.phase * 3.3)
            egt += 48 * s * math.sin(self.phase * 2.7)
            fuel += .9 * s * math.sin(self.phase * 2.1)
            vib += .18 * s
        elif fault == "alternator_degradation":
            alternator -= 5.0 * s
            battery -= 2.0 * s

        return {
            "engine_id": ENGINE,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "rpm": rpm,
            "throttle": throttle,
            "cht": cht,
            "egt": egt,
            "oil_pressure": oil_p,
            "oil_temperature": oil_t,
            "fuel_flow": fuel,
            "vibration": max(.05, vib),
            "battery_voltage": battery,
            "alternator_voltage": alternator,
            "altitude": altitude,
            "ambient_temperature": ambient,
            "injection_timing": timing,
            "operating_hours": self.hours,
        }


def post_json(url, data):
    payload = json.dumps(data).encode()
    headers = {"Content-Type": "application/json"}
    if INGEST_KEY:
        headers["X-TwinGuard-Ingest-Key"] = INGEST_KEY
    req = Request(url, data=payload, method="POST", headers=headers)
    with urlopen(req, timeout=2) as r:
        return json.loads(r.read().decode())


def run_http(rate):
    sim = EngineSimulator()
    print("TwinGuard aero-piston simulator →", API)
    while True:
        try:
            state = post_json(API + "/api/v1/telemetry", sim.sample())
            print(
                f"\rhealth {state['health']['overall']:5.1f}% | "
                f"{state['ai']['probable_fault']:<24} | "
                f"RUL {state['ai']['rul_hours']:6.1f} h",
                end="",
                flush=True,
            )
        except Exception as exc:
            print("\nwaiting for backend:", exc)
        time.sleep(1 / rate)


def run_mqtt(rate):
    try:
        import paho.mqtt.client as mqtt
    except ImportError:
        raise SystemExit("Install paho-mqtt first")
    host = os.getenv("MQTT_HOST", "127.0.0.1")
    port = int(os.getenv("MQTT_PORT", "1883"))
    topic = f"twinguard/engine/{ENGINE}/telemetry"
    client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2)
    client.connect(host, port, 60)
    client.loop_start()
    sim = EngineSimulator()
    while True:
        client.publish(topic, json.dumps(sim.sample()), qos=0)
        time.sleep(1 / rate)


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--transport", choices=["http", "mqtt"], default=os.getenv("SIM_TRANSPORT", "http"))
    ap.add_argument("--rate", type=float, default=1.0)
    args = ap.parse_args()
    (run_mqtt if args.transport == "mqtt" else run_http)(args.rate)
