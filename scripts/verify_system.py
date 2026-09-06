from __future__ import annotations
import json
import os
import secrets
import time
from urllib.request import Request, urlopen

BASE=os.getenv("TWINGUARD_API","http://127.0.0.1:8000");KEY=os.getenv("TWINGUARD_INGEST_KEY","");TOKEN=""


def headers(extra=None):
    h={"Content-Type":"application/json"}
    if TOKEN:h["Authorization"]=f"Bearer {TOKEN}"
    if extra:h.update(extra)
    return h


def get(path,ingest=False):
    extra={"X-TwinGuard-Ingest-Key":KEY} if ingest and KEY else {}
    req=Request(BASE+path,headers=headers(extra),method="GET")
    with urlopen(req,timeout=5) as r:return json.loads(r.read().decode())


def post(path,obj=None,ingest=False):
    extra={"X-TwinGuard-Ingest-Key":KEY} if ingest and KEY else {}
    req=Request(BASE+path,data=json.dumps(obj or {}).encode(),method="POST",headers=headers(extra))
    with urlopen(req,timeout=5) as r:return json.loads(r.read().decode())


checks=[]
def check(name,fn):
    try:
        result=fn()
        if result is False:raise AssertionError("check returned False")
        checks.append((name,True,"PASS"))
    except Exception as exc:
        checks.append((name,False,str(exc)))


check("Backend",lambda:get("/health")["status"]=="ok")

try:
    email=f"verify-{secrets.token_hex(5)}@twinguard.local"
    auth=post("/api/v1/auth/signup",{"name":"Automated Verifier","email":email,"password":"VerifyTwin9!"})
    TOKEN=auth["token"]
    checks.append(("Authentication",True,"PASS"))
except Exception as exc:
    checks.append(("Authentication",False,str(exc)))


time.sleep(2)


def twin_check():
    state=get("/api/v1/twin/ENGINE-01")
    assert 0<=state["health"]["overall"]<=100
    assert state["twin_meta"]["physics_model"]=="generic-aero-piston-surrogate-v2"
    assert "oil_pressure_per_min" in state["trends"]
    interval=state["ai"]["rul_interval_hours"]
    assert 0<=interval["lower"]<=interval["estimate"]<=interval["upper"]
    assert interval["calibrated_probability_interval"] is False
    validity=state["runtime_validity"]
    assert validity["stale"] is False
    assert validity["decision_eligible"] is True
check("Synchronized uncertainty-aware Digital Twin",twin_check)

check("Diagnostics",lambda:get("/api/v1/diagnostics/ENGINE-01")["confidence"]["decision"]>=0)


def status_check():
    status=get("/api/v1/system/status")
    assert status["security"]["trusted_hosts"]
    assert status["telemetry"]["available"] is True
    assert status["telemetry"]["stale"] is False
    assert status["telemetry"]["decision_eligible"] is True
check("Runtime validity gate",status_check)


def maintenance_check():
    result=get("/api/v1/maintenance/ENGINE-01")
    assert result["maintenance"]["priority"]
    assert result["rul_interval_hours"]["lower"]<=result["rul_hours"]<=result["rul_interval_hours"]["upper"]
check("Maintenance + RUL uncertainty",maintenance_check)


def mission_check():
    result=post("/api/v1/mission/analyze",{"mission_type":"endurance","duration_hours":8,"cruise_altitude_m":5500,"ambient_temp_c":35,"average_throttle_pct":75})
    assert result["overall_risk"] in {"LOW","MEDIUM","HIGH"}
    assert 0<=result["mission_feasibility_index"]<=100
    assert result["rul_margin_ratio"]>=0
    assert result["conservative_rul_margin_ratio"]<=result["rul_margin_ratio"]
    assert result["decision_horizon_hours"]>=0
    assert result["engineering_reserve_hours"]>0
    assert result["current_rul_interval_hours"]["lower"]<=result["current_rul_hours"]<=result["current_rul_interval_hours"]["upper"]
    assert result["risk_factors"]
    alt=result["lower_stress_alternative"]
    assert "projected_risk" in alt
    assert alt["projected_stress_index"]<=result["stress_index"]
    assert "mission_margin_hours" in alt and "decision_horizon_hours" in alt
check("Mission Reliability Twin",mission_check)


def lubrication_fault():
    post("/api/v1/simulation/fault",{"fault":"lubrication","severity":0.85})
    deadline=time.time()+45
    detected=False
    baseline_margin=None
    degraded_margin=None
    try:
        baseline=post("/api/v1/mission/analyze",{"mission_type":"endurance","duration_hours":8,"cruise_altitude_m":5500,"ambient_temp_c":35,"average_throttle_pct":75})
        baseline_margin=baseline["mission_margin_hours"]
        while time.time()<deadline:
            time.sleep(1)
            state=get("/api/v1/twin/ENGINE-01")
            if state["ai"]["anomaly"] and state["health"]["lubrication"]<85:
                degraded=post("/api/v1/mission/analyze",{"mission_type":"endurance","duration_hours":8,"cruise_altitude_m":5500,"ambient_temp_c":35,"average_throttle_pct":75})
                degraded_margin=degraded["mission_margin_hours"]
                detected=True
                break
    finally:
        post("/api/v1/simulation/reset")
    assert detected,"progressive lubrication scenario did not become observable within 45 s"
    assert baseline_margin is not None and degraded_margin is not None
    assert degraded_margin<baseline_margin,"degraded engine did not reduce mission margin"
check("Aero-piston degradation changes mission margin",lubrication_fault)


def replay():
    post("/api/v1/replay/start",{"label":"Automated Verification"});time.sleep(2)
    assert post("/api/v1/replay/end")["status"]=="COMPLETED"
check("Mission Replay",replay)

try:post("/api/v1/auth/signout")
except Exception:pass

print("\nTwinGuard Aero verification\n"+"="*32)
for name,ok,msg in checks:print("PASS" if ok else "FAIL",name,"" if ok else msg)
raise SystemExit(0 if all(x[1] for x in checks) else 1)
