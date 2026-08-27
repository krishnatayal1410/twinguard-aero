import time, requests
from engine import EngineSimulator

sim = EngineSimulator()
API = "http://localhost:8000/telemetry"

print("TwinGuard simulator started.")
while True:
    payload = sim.step()
    try:
        r = requests.post(API, json=payload, timeout=2)
        print(r.status_code, payload["rpm"], payload["cht"], payload["oil_pressure"])
    except requests.RequestException as e:
        print("Backend unavailable:", e)
    time.sleep(1)
