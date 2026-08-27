import json
import sys
from urllib.request import Request, urlopen

BASE = "http://127.0.0.1:8000"

def call(path, method="GET", body=None):
    data = None
    headers = {}
    if body is not None:
        data = json.dumps(body).encode()
        headers["Content-Type"] = "application/json"
    req = Request(BASE + path, data=data, headers=headers, method=method)
    with urlopen(req, timeout=5) as response:
        return json.loads(response.read().decode())

checks = []

for name, fn in [
    ("Backend", lambda: call("/")),
    ("Digital Twin", lambda: call("/state")),
    ("Mission Replay", lambda: call("/replay/status")),
    ("MVP Status", lambda: call("/mvp/status")),
]:
    try:
        fn()
        checks.append((name, True))
    except Exception as exc:
        checks.append((name, False))
        print(name, "failed:", exc)

try:
    result = call(
        "/mission/analyze",
        "POST",
        {
            "duration_hours": 8,
            "cruise_altitude_m": 5500,
            "ambient_temp_c": 35,
            "average_throttle_pct": 75,
            "mission_type": "endurance",
        },
    )
    checks.append(("Mission Lab", "risk" in result))
except Exception as exc:
    checks.append(("Mission Lab", False))
    print("Mission Lab failed:", exc)

print("\nTwinGuard MVP Verification")
print("==========================")
failed = False
for name, ok in checks:
    print(("PASS" if ok else "FAIL"), name)
    failed = failed or not ok

sys.exit(1 if failed else 0)
