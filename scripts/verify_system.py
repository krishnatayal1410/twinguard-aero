from __future__ import annotations
import json
import os
import secrets
import time
from urllib.request import Request, urlopen

BASE="http://127.0.0.1:8000";KEY=os.getenv("TWINGUARD_INGEST_KEY","");TOKEN=""


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
check("Digital Twin",lambda:0<=get("/api/v1/twin/ENGINE-01")["health"]["overall"]<=100)
check("Aero-piston model identity",lambda:get("/api/v1/twin/ENGINE-01")["twin_meta"]["physics_model"]=="generic-aero-piston-surrogate-v2")
check("Temporal trends",lambda:"oil_pressure_per_min" in get("/api/v1/twin/ENGINE-01")["trends"])
check("Diagnostics",lambda:get("/api/v1/diagnostics/ENGINE-01")["confidence"]["decision"]>=0)
check("System Status",lambda:bool(get("/api/v1/system/status")["security"]["trusted_hosts"]))
check("Maintenance",lambda:bool(get("/api/v1/maintenance/ENGINE-01")["maintenance"]["priority"]))


def mission_check():
    result=post("/api/v1/mission/analyze",{"mission_type":"endurance","duration_hours":8,"cruise_altitude_m":5500,"ambient_temp_c":35,"average_throttle_pct":75})
    assert result["overall_risk"] in {"LOW","MEDIUM","HIGH"}
    assert 0<=result["mission_feasibility_index"]<=100
    assert result["rul_margin_ratio"]>=0
    assert result["risk_factors"]
    assert "projected_risk" in result["lower_stress_alternative"]
check("Mission Reliability Twin",mission_check)


def lubrication_fault():
    post("/api/v1/simulation/fault",{"fault":"lubrication","severity":0.85})
    deadline=time.time()+45
    detected=False
    while time.time()<deadline:
        time.sleep(1)
        state=get("/api/v1/twin/ENGINE-01")
        if state["ai"]["anomaly"] and state["health"]["lubrication"]<85:
            detected=True;break
    post("/api/v1/simulation/reset")
    assert detected,"progressive lubrication scenario did not become observable within 45 s"
check("Aero-piston Lubrication Scenario",lubrication_fault)


def replay():
    post("/api/v1/replay/start",{"label":"Automated Verification"});time.sleep(2)
    assert post("/api/v1/replay/end")["status"]=="COMPLETED"
check("Mission Replay",replay)

try:post("/api/v1/auth/signout")
except Exception:pass

print("\nTwinGuard Aero verification\n"+"="*32)
for name,ok,msg in checks:print("PASS" if ok else "FAIL",name,"" if ok else msg)
raise SystemExit(0 if all(x[1] for x in checks) else 1)
