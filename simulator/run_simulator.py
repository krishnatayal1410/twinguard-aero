import time

import requests

from engine import EngineSimulator


TELEMETRY_API = "http://127.0.0.1:8000/telemetry"
CONTROL_API = "http://127.0.0.1:8000/simulation/control"

CONTROL_TIMEOUT_SECONDS = 1.0
TELEMETRY_TIMEOUT_SECONDS = 2.0
SEVERITY_RAMP_PER_SECOND = 0.04

sim = EngineSimulator()

applied_fault = "normal"
applied_severity = 0.0

print("TwinGuard simulator started.")
print("Fault control: GET/POST http://127.0.0.1:8000/simulation/control")


def move_toward(current: float, target: float, step: float) -> float:
    if current < target:
        return min(target, current + step)
    if current > target:
        return max(target, current - step)
    return current


while True:
    target_fault = applied_fault
    target_severity = applied_severity

    try:
        control_response = requests.get(
            CONTROL_API,
            timeout=CONTROL_TIMEOUT_SECONDS,
        )
        control_response.raise_for_status()
        control = control_response.json()

        target_fault = str(control.get("fault", "normal"))
        target_severity = float(control.get("severity", 0.0))
    except (requests.RequestException, ValueError, TypeError):
        pass

    if target_fault == "normal":
        applied_fault = "normal"
        applied_severity = 0.0
    else:
        if target_fault != applied_fault:
            applied_fault = target_fault
            applied_severity = 0.0

        applied_severity = move_toward(
            applied_severity,
            max(0.0, min(1.0, target_severity)),
            SEVERITY_RAMP_PER_SECOND,
        )

    sim.set_fault(applied_fault, applied_severity)
    payload = sim.step()

    try:
        response = requests.post(
            TELEMETRY_API,
            json=payload,
            timeout=TELEMETRY_TIMEOUT_SECONDS,
        )
        print(
            response.status_code,
            f"fault={applied_fault}",
            f"severity={applied_severity:.2f}",
            f"rpm={payload['rpm']}",
            f"cht={payload['cht']}",
            f"oilP={payload['oil_pressure']}",
            f"oilT={payload['oil_temp']}",
            f"vib={payload['vibration']}",
        )
    except requests.RequestException as exc:
        print("Backend unavailable:", exc)

    time.sleep(1)
