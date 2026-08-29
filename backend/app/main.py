from __future__ import annotations
import asyncio,json,logging,hmac,time
from datetime import datetime,timezone
from contextlib import asynccontextmanager
from fastapi import FastAPI,WebSocket,WebSocketDisconnect,HTTPException,Header,Request,Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse
from .schemas import Telemetry,MissionRequest,FaultCommand,ReplayStart,SignUpRequest,SignInRequest
from .services.twin_manager import manager
from .core import settings
from .integrations.mqtt_consumer import start_mqtt
from .integrations.unreal_udp import send_to_unreal
from .services.explainability import tree_contributions
from .services.auth import signup,signin,signout,session_user,AuthError

log=logging.getLogger("twinguard");logging.basicConfig(level=logging.INFO,format="%(asctime)s %(levelname)s %(name)s %(message)s")
clients:set[WebSocket]=set()

class SecurityMiddleware(BaseHTTPMiddleware):
 async def dispatch(self,request:Request,call_next):
  if request.method in {"POST","PUT","PATCH"} and int(request.headers.get("content-length","0") or 0)>settings.max_body_bytes:return JSONResponse({"detail":"Request too large"},413)
  response=await call_next(request)
  response.headers.update({"X-Content-Type-Options":"nosniff","X-Frame-Options":"DENY","Referrer-Policy":"no-referrer","Permissions-Policy":"camera=(), microphone=(), geolocation=()","Cache-Control":"no-store" if request.url.path.startswith("/api/") else "no-cache"})
  return response

async def broadcast(state):
 payload=json.dumps(state,default=str);dead=[]
 for ws in tuple(clients):
  try:await ws.send_text(payload)
  except Exception:dead.append(ws)
 for ws in dead:clients.discard(ws)

def ingest_sync(data):
 try:
  t=Telemetry.model_validate(data);state=manager.ingest(t.model_dump());send_to_unreal(state);return state
 except Exception as exc:log.warning("Rejected telemetry: %s",type(exc).__name__);return None

@asynccontextmanager
async def lifespan(app:FastAPI):
 loop=asyncio.get_running_loop()
 def mqtt_ingest(data):
  if state:=ingest_sync(data):asyncio.run_coroutine_threadsafe(broadcast(state),loop)
 start_mqtt(mqtt_ingest);yield

docs=None if settings.environment=="production" else "/docs"
app=FastAPI(title="TwinGuard Aero API",version=settings.version,lifespan=lifespan,docs_url=docs,redoc_url=None)
app.add_middleware(TrustedHostMiddleware,allowed_hosts=list(settings.trusted_hosts))
app.add_middleware(CORSMiddleware,allow_origins=list(settings.cors_origins),allow_credentials=False,allow_methods=["GET","POST"],allow_headers=["Content-Type","X-Requested-With","X-TwinGuard-Ingest-Key","Authorization"])
app.add_middleware(SecurityMiddleware)

@app.get("/health")
def health():return{"status":"ok","service":settings.app_name,"version":settings.version,"engine_id":settings.engine_id}


def _bearer(authorization:str|None)->str|None:
 if not authorization:return None
 parts=authorization.split(" ",1)
 return parts[1].strip() if len(parts)==2 and parts[0].lower()=="bearer" else None

def require_user(authorization:str|None=Header(default=None)):
 user=session_user(_bearer(authorization))
 if not user:raise HTTPException(401,"Authentication required")
 return user

@app.post("/api/v1/auth/signup")
def auth_signup(req:SignUpRequest):
 try:
  token,user=signup(req.name,req.email,req.password);return{"token":token,"user":user}
 except AuthError as exc:raise HTTPException(400,str(exc))

@app.post("/api/v1/auth/signin")
def auth_signin(req:SignInRequest):
 try:
  token,user=signin(req.email,req.password);return{"token":token,"user":user}
 except AuthError as exc:raise HTTPException(401,str(exc))

@app.get("/api/v1/auth/me")
def auth_me(user=Depends(require_user)):return user

@app.post("/api/v1/auth/signout")
def auth_signout(authorization:str|None=Header(default=None)):
 signout(_bearer(authorization));return{"ok":True}


@app.post("/api/v1/telemetry")
async def telemetry(t:Telemetry,x_twinguard_ingest_key:str|None=Header(default=None)):
 if settings.ingest_api_key and not hmac.compare_digest(x_twinguard_ingest_key or"",settings.ingest_api_key):raise HTTPException(401,"Invalid telemetry ingest key")
 if t.engine_id!=settings.engine_id:raise HTTPException(403,"Engine ID is not authorized")
 state=manager.ingest(t.model_dump());send_to_unreal(state);await broadcast(state);return state

def current(engine_id:str):
 s=manager.get()
 if engine_id!=settings.engine_id:raise HTTPException(404,"Engine not found")
 if not s:raise HTTPException(404,"No telemetry received yet")
 return s

@app.get("/api/v1/twin/{engine_id}")
def twin(engine_id:str,user=Depends(require_user)):return current(engine_id)
@app.get("/api/v1/diagnostics/{engine_id}")
def diagnostics(engine_id:str,user=Depends(require_user)):
 s=current(engine_id);return{k:s[k] for k in("ai","residuals","sensor_trust","data_quality","health","confidence")}
@app.get("/api/v1/diagnostics/{engine_id}/explain")
def explain(engine_id:str,user=Depends(require_user)):
 s=current(engine_id);return tree_contributions(manager.ai,s["telemetry"],s["residuals"])
@app.get("/api/v1/maintenance/{engine_id}")
def maintenance(engine_id:str,user=Depends(require_user)):
 s=current(engine_id);return{"maintenance":s["maintenance"],"readiness":s["readiness"],"rul_hours":s["ai"]["rul_hours"]}
@app.post("/api/v1/mission/analyze")
def mission(req:MissionRequest,user=Depends(require_user)):
 s=manager.get()
 if not s:raise HTTPException(409,"Twin has no current telemetry")
 return manager.mission.analyze(s,req)
@app.post("/api/v1/simulation/fault")
def set_fault(cmd:FaultCommand,user=Depends(require_user)):manager.simulation={"fault":cmd.fault,"severity":cmd.severity};return manager.simulation
@app.post("/api/v1/simulation/reset")
def reset_fault(user=Depends(require_user)):manager.simulation={"fault":"normal","severity":0.0};return manager.simulation
@app.get("/api/v1/simulation/config")
def simulation_config(user=Depends(require_user)):return manager.simulation
@app.post("/api/v1/replay/start")
def replay_start(req:ReplayStart,user=Depends(require_user)):return manager.replay.start(req.label)
@app.post("/api/v1/replay/end")
def replay_end(user=Depends(require_user)):
 x=manager.replay.end()
 if not x:raise HTTPException(409,"No active mission recording")
 return x
@app.get("/api/v1/replay/missions")
def replay_list(limit:int=30,user=Depends(require_user)):return manager.replay.list(max(1,min(limit,100)))
@app.get("/api/v1/replay/missions/{mission_id}")
def replay_get(mission_id:int,user=Depends(require_user)):
 x=manager.replay.get(mission_id)
 if not x:raise HTTPException(404,"Mission not found")
 return x
@app.get("/api/v1/system/status")
def system_status(user=Depends(require_user)):
 s=manager.get();age=None
 if s:
  try:age=max(0,(datetime.now(timezone.utc)-datetime.fromisoformat(str(s["timestamp"]).replace("Z","+00:00"))).total_seconds())
  except Exception:pass
 return{"service":settings.app_name,"version":settings.version,"environment":settings.environment,"engine_id":settings.engine_id,"database":settings.database_url.split(":",1)[0],"models":{"anomaly":manager.ai.anomaly is not None,"fault":manager.ai.fault is not None,"rul":manager.ai.rul is not None},"integrations":{"mqtt":settings.mqtt_enabled,"unreal_udp":settings.unreal_udp_enabled,"can":settings.can_enabled},"telemetry":{"available":bool(s),"age_seconds":age},"security":{"cors_origins":list(settings.cors_origins),"trusted_hosts":list(settings.trusted_hosts),"ingest_key_required":bool(settings.ingest_api_key),"authentication":True}}

@app.websocket("/api/v1/ws/twin/{engine_id}")
async def twin_ws(ws:WebSocket,engine_id:str):
 if engine_id!=settings.engine_id:return await ws.close(code=1008)
 if not session_user(ws.query_params.get("token")):return await ws.close(code=1008)
 await ws.accept();clients.add(ws)
 try:
  if manager.get():await ws.send_json(manager.get())
  while True:await asyncio.sleep(20);await ws.send_json({"type":"heartbeat","timestamp":datetime.now(timezone.utc).isoformat()})
 except WebSocketDisconnect:pass
 finally:clients.discard(ws)
