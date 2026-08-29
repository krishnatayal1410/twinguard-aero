from __future__ import annotations
import json,time,os,secrets
from urllib.request import urlopen,Request
BASE="http://127.0.0.1:8000";KEY=os.getenv("TWINGUARD_INGEST_KEY","");TOKEN=""
def headers(extra=None):
 h={"Content-Type":"application/json"}
 if TOKEN:h["Authorization"]=f"Bearer {TOKEN}"
 if extra:h.update(extra)
 return h
def get(path):
 req=Request(BASE+path,headers=headers(),method="GET")
 with urlopen(req,timeout=5) as r:return json.loads(r.read().decode())
def post(path,obj=None,ingest=False):
 extra={"X-TwinGuard-Ingest-Key":KEY} if ingest and KEY else {}
 req=Request(BASE+path,data=json.dumps(obj or {}).encode(),method="POST",headers=headers(extra))
 with urlopen(req,timeout=5) as r:return json.loads(r.read().decode())

checks=[]
def check(name,fn):
 try:fn();checks.append((name,True,"PASS"))
 except Exception as e:checks.append((name,False,str(e)))

check("Backend",lambda:get("/health")["status"]=="ok")

try:
 email=f"verify-{secrets.token_hex(5)}@twinguard.local"
 auth=post("/api/v1/auth/signup",{"name":"Automated Verifier","email":email,"password":"VerifyTwin9!"})
 TOKEN=auth["token"]
 checks.append(("Authentication",True,"PASS"))
except Exception as e:
 checks.append(("Authentication",False,str(e)))

time.sleep(2)
check("Digital Twin",lambda:get("/api/v1/twin/ENGINE-01")["health"]["overall"])
check("Diagnostics",lambda:get("/api/v1/diagnostics/ENGINE-01")["confidence"]["decision"])
check("System Status",lambda:get("/api/v1/system/status")["security"]["trusted_hosts"])
check("Maintenance",lambda:get("/api/v1/maintenance/ENGINE-01")["maintenance"]["priority"])
check("Mission Lab",lambda:post("/api/v1/mission/analyze",{"mission_type":"endurance","duration_hours":8,"cruise_altitude_m":5500,"ambient_temp_c":35,"average_throttle_pct":75})["overall_risk"])

def turbine_fault():
 post("/api/v1/simulation/fault",{"fault":"turbine_blade_degradation","severity":0.75})
 time.sleep(5)
 s=get("/api/v1/twin/ENGINE-01")
 assert s["ai"]["anomaly"] is True
 post("/api/v1/simulation/reset")
check("Turbine Fault Simulation",turbine_fault)

def replay():
 post("/api/v1/replay/start",{"label":"Automated Verification"});time.sleep(2)
 assert post("/api/v1/replay/end")["status"]=="COMPLETED"
check("Mission Replay",replay)

try:post("/api/v1/auth/signout")
except Exception:pass

print("\nTwinGuard Aero verification\n"+"="*32)
for n,ok,msg in checks:print("PASS" if ok else "FAIL",n,"" if ok else msg)
raise SystemExit(0 if all(x[1] for x in checks) else 1)
