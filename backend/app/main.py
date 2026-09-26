from __future__ import annotations

import asyncio
import hmac
import json
import logging
from contextlib import asynccontextmanager
from datetime import UTC, datetime

from fastapi import (
    Depends,
    FastAPI,
    Header,
    HTTPException,
    Request,
    WebSocket,
    WebSocketDisconnect,
)
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from sqlalchemy import text
from starlette.concurrency import run_in_threadpool
from starlette.datastructures import MutableHeaders
from starlette.responses import JSONResponse

from .core import settings
from .db import engine
from .integrations.mqtt_consumer import start_mqtt, stop_mqtt
from .integrations.unreal_udp import send_to_unreal
from .schemas import (
    FaultCommand,
    MissionRequest,
    ReplayStart,
    SignInRequest,
    SignUpRequest,
    Telemetry,
)
from .services.auth import AuthError, session_user, signin, signout, signup
from .services.explainability import tree_contributions
from .services.operations import check_production, request_limiter, validate_live_sample
from .services.replay import RecordingInProgressError
from .services.twin_manager import manager

log = logging.getLogger("twinguard")
logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s %(message)s")


class TwinPeer:
    """Serialize socket writes and prevent concurrent ingestion from rewinding a client."""

    def __init__(self, socket):
        self.socket = socket
        self.lock = asyncio.Lock()
        self.last_sample = None
        self.failed = False

    async def send(self, payload, sample_timestamp=None):
        async with self.lock:
            if self.failed or (
                sample_timestamp is not None
                and self.last_sample is not None
                and sample_timestamp <= self.last_sample
            ):
                return
            try:
                await asyncio.wait_for(self.socket.send_text(payload), timeout=2.0)
            except Exception:
                self.failed = True
                raise
            if sample_timestamp is not None:
                self.last_sample = sample_timestamp


clients: dict[WebSocket, TwinPeer] = {}


class SecurityMiddleware:
    """Bound the actual request bytes, including chunked and misdeclared bodies."""

    def __init__(self, app):
        self.app = app

    async def __call__(self, scope, receive, send):
        if scope["type"] != "http":
            return await self.app(scope, receive, send)
        request = Request(scope)

        async def secure_send(message):
            if message["type"] == "http.response.start":
                headers = MutableHeaders(scope=message)
                headers.update(
                    {
                        "X-Content-Type-Options": "nosniff",
                        "X-Frame-Options": "DENY",
                        "Referrer-Policy": "no-referrer",
                        "Permissions-Policy": "camera=(), microphone=(), geolocation=()",
                        "Cache-Control": "no-store" if request.url.path.startswith("/api/") else "no-cache",
                    }
                )
            await send(message)

        async def reject(detail, status, headers=None):
            response = JSONResponse({"detail": detail}, status, headers=headers)
            await response(scope, receive, secure_send)

        if not request_limiter.allow(request):
            return await reject(
                "Too many authentication attempts. Retry in a minute.",
                429,
                headers={"Retry-After": "60"},
            )
        try:
            length = int(request.headers.get("content-length", "0") or 0)
        except ValueError:
            return await reject("Invalid Content-Length", 400)
        if length < 0 or length > settings.max_body_bytes:
            return await reject("Request too large", 413)

        body = bytearray()
        while True:
            message = await receive()
            if message["type"] == "http.disconnect":
                return
            chunk = message.get("body", b"")
            if len(body) + len(chunk) > settings.max_body_bytes:
                return await reject("Request too large", 413)
            body.extend(chunk)
            if not message.get("more_body", False):
                break

        delivered = False

        async def bounded_receive():
            nonlocal delivered
            if not delivered:
                delivered = True
                return {"type": "http.request", "body": bytes(body), "more_body": False}
            return await receive()

        await self.app(scope, bounded_receive, secure_send)


async def broadcast(state):
    payload = json.dumps(_runtime_snapshot(state), default=str)
    timestamp = datetime.fromisoformat(str(state["timestamp"]).replace("Z", "+00:00"))

    async def deliver(ws, peer):
        try:
            await peer.send(payload, timestamp)
        except Exception:
            clients.pop(ws, None)

    await asyncio.gather(*(deliver(ws, peer) for ws, peer in tuple(clients.items())))


def ingest_sync(data):
    try:
        telemetry = Telemetry.model_validate(data)
        with manager.lock:
            validate_live_sample(telemetry, manager.get())
            state = manager.ingest(telemetry.model_dump())
        send_to_unreal(state)
        return state
    except Exception as exc:
        log.warning("Rejected telemetry: %s", type(exc).__name__)
        return None


@asynccontextmanager
async def lifespan(app: FastAPI):
    check_production()
    loop = asyncio.get_running_loop()

    def mqtt_ingest(data):
        if state := ingest_sync(data):
            asyncio.run_coroutine_threadsafe(broadcast(state), loop)

    mqtt_client = start_mqtt(mqtt_ingest)
    try:
        yield
    finally:
        stop_mqtt(mqtt_client)


docs = None if settings.environment == "production" else "/docs"
app = FastAPI(
    title="TwinGuard Aero API",
    version=settings.version,
    lifespan=lifespan,
    docs_url=docs,
    redoc_url=None,
)
app.add_middleware(TrustedHostMiddleware, allowed_hosts=list(settings.trusted_hosts))
app.add_middleware(
    CORSMiddleware,
    allow_origins=list(settings.cors_origins),
    allow_credentials=False,
    allow_methods=["GET", "POST"],
    allow_headers=[
        "Content-Type",
        "X-Requested-With",
        "X-TwinGuard-Ingest-Key",
        "Authorization",
    ],
)
app.add_middleware(SecurityMiddleware)


@app.get("/health")
def health():
    return {
        "status": "ok",
        "service": settings.app_name,
        "version": settings.version,
        "engine_id": settings.engine_id,
    }


def _bearer(authorization: str | None) -> str | None:
    if not authorization:
        return None
    parts = authorization.split(" ", 1)
    return parts[1].strip() if len(parts) == 2 and parts[0].lower() == "bearer" else None


def require_user(authorization: str | None = Header(default=None)):
    user = session_user(_bearer(authorization))
    if not user:
        raise HTTPException(401, "Authentication required")
    return user


def require_simulation_reader(
    authorization: str | None = Header(default=None),
    x_twinguard_ingest_key: str | None = Header(default=None),
):
    if session_user(_bearer(authorization)):
        return True
    if not settings.ingest_api_key:
        return True
    if hmac.compare_digest(x_twinguard_ingest_key or "", settings.ingest_api_key):
        return True
    raise HTTPException(401, "Simulation configuration authentication required")


def _state_age_seconds(state: dict | None) -> float | None:
    if not state:
        return None
    try:
        ts = datetime.fromisoformat(str(state["timestamp"]).replace("Z", "+00:00"))
        if ts.tzinfo is None:
            ts = ts.replace(tzinfo=UTC)
        return (datetime.now(UTC) - ts).total_seconds()
    except Exception:
        return None


def _runtime_snapshot(state: dict) -> dict:
    age = _state_age_seconds(state)
    quality = float(state.get("data_quality", {}).get("overall", 0.0))
    stale = age is None or age < -5 or age > settings.telemetry_stale_seconds
    sensor_integrity_ok = float(state.get("health", {}).get("sensor", 100.0)) >= 55
    quality_ok = (
        quality >= settings.mission_min_data_quality
        and state.get("data_quality", {}).get("label") != "POOR"
        and sensor_integrity_ok
    )
    decision_eligible = not stale and quality_ok
    snapshot = dict(state)
    snapshot["runtime_validity"] = {
        "telemetry_age_seconds": age,
        "stale": stale,
        "freshness_limit_seconds": settings.telemetry_stale_seconds,
        "data_quality": quality,
        "minimum_data_quality": settings.mission_min_data_quality,
        "sensor_integrity_ok": sensor_integrity_ok,
        "decision_eligible": decision_eligible,
    }
    if stale:
        snapshot["readiness"] = {
            "status": "DATA_HOLD",
            "label": "DATA HOLD",
            "reason": f"Latest telemetry is stale for mission decision support ({age:.1f}s old; limit {settings.telemetry_stale_seconds:.1f}s). Restore live synchronization before release assessment."
            if age is not None
            else "Telemetry timestamp is invalid; restore live synchronization before release assessment.",
        }
    elif not quality_ok:
        snapshot["readiness"] = {
            "status": "DATA_HOLD",
            "label": "DATA HOLD",
            "reason": f"Data-quality score {quality:.1f} or sensor integrity fails the mission-analysis gate (minimum quality {settings.mission_min_data_quality:.1f}; minimum sensor integrity 55).",
        }
    return snapshot


@app.post("/api/v1/auth/signup")
def auth_signup(req: SignUpRequest):
    try:
        token, user = signup(req.name, req.email, req.password)
        return {"token": token, "user": user}
    except AuthError as exc:
        raise HTTPException(400, str(exc))


@app.post("/api/v1/auth/signin")
def auth_signin(req: SignInRequest):
    try:
        token, user = signin(req.email, req.password)
        return {"token": token, "user": user}
    except AuthError as exc:
        raise HTTPException(401, str(exc))


@app.get("/api/v1/auth/me")
def auth_me(user=Depends(require_user)):
    return user


@app.post("/api/v1/auth/signout")
def auth_signout(authorization: str | None = Header(default=None)):
    signout(_bearer(authorization))
    return {"ok": True}


@app.post("/api/v1/telemetry")
async def telemetry(t: Telemetry, x_twinguard_ingest_key: str | None = Header(default=None)):
    if settings.ingest_api_key and not hmac.compare_digest(
        x_twinguard_ingest_key or "", settings.ingest_api_key
    ):
        raise HTTPException(401, "Invalid telemetry ingest key")
    if t.engine_id != settings.engine_id:
        raise HTTPException(403, "Engine ID is not authorized")

    def process():
        with manager.lock:
            validate_live_sample(t, manager.get())
            return manager.ingest(t.model_dump())

    # Native inference and database commits must not block the ASGI event loop.
    state = await run_in_threadpool(process)
    send_to_unreal(state)
    await broadcast(state)
    return state


def current(engine_id: str):
    state = manager.get()
    if engine_id != settings.engine_id:
        raise HTTPException(404, "Engine not found")
    if not state:
        raise HTTPException(404, "No telemetry received yet")
    return _runtime_snapshot(state)


@app.get("/api/v1/twin/{engine_id}")
def twin(engine_id: str, user=Depends(require_user)):
    return current(engine_id)


@app.get("/api/v1/diagnostics/{engine_id}")
def diagnostics(engine_id: str, user=Depends(require_user)):
    state = current(engine_id)
    return {
        k: state[k]
        for k in (
            "ai",
            "residuals",
            "trends",
            "events",
            "sensor_trust",
            "data_quality",
            "health",
            "confidence",
            "runtime_validity",
        )
    }


@app.get("/api/v1/diagnostics/{engine_id}/explain")
def explain(engine_id: str, user=Depends(require_user)):
    state = current(engine_id)
    return tree_contributions(manager.ai, state["telemetry"], state["residuals"])


@app.get("/api/v1/maintenance/{engine_id}")
def maintenance(engine_id: str, user=Depends(require_user)):
    state = current(engine_id)
    return {
        "maintenance": state["maintenance"],
        "readiness": state["readiness"],
        "rul_hours": state["ai"]["rul_hours"],
        "rul_interval_hours": state["ai"].get("rul_interval_hours"),
        "runtime_validity": state["runtime_validity"],
    }


@app.post("/api/v1/mission/analyze")
def mission(req: MissionRequest, user=Depends(require_user)):
    state = current(settings.engine_id)
    validity = state["runtime_validity"]
    if validity["stale"]:
        raise HTTPException(
            409,
            "Mission analysis blocked: latest telemetry is stale. Restore live telemetry synchronization and retry.",
        )
    if not validity["decision_eligible"]:
        raise HTTPException(
            409,
            "Mission analysis blocked: current data quality is below the configured decision threshold.",
        )
    return manager.mission.analyze(state, req)


@app.post("/api/v1/simulation/fault")
def set_fault(cmd: FaultCommand, user=Depends(require_user)):
    manager.simulation = {"fault": cmd.fault, "severity": cmd.severity}
    return manager.simulation


@app.post("/api/v1/simulation/reset")
def reset_fault(user=Depends(require_user)):
    manager.simulation = {"fault": "normal", "severity": 0.0}
    return manager.simulation


@app.get("/api/v1/simulation/config")
def simulation_config(_=Depends(require_simulation_reader)):
    return manager.simulation


@app.post("/api/v1/replay/start")
def replay_start(req: ReplayStart, user=Depends(require_user)):
    try:
        return manager.replay.start(req.label)
    except RecordingInProgressError as exc:
        raise HTTPException(409, str(exc)) from exc


@app.post("/api/v1/replay/end")
def replay_end(user=Depends(require_user)):
    mission_record = manager.replay.end()
    if not mission_record:
        raise HTTPException(409, "No active mission recording")
    return mission_record


@app.get("/api/v1/replay/missions")
def replay_list(limit: int = 30, user=Depends(require_user)):
    return manager.replay.list(max(1, min(limit, 100)))


@app.get("/api/v1/replay/missions/{mission_id}")
def replay_get(mission_id: int, user=Depends(require_user)):
    mission_record = manager.replay.get(mission_id)
    if not mission_record:
        raise HTTPException(404, "Mission not found")
    return mission_record


@app.get("/api/v1/replay/missions/{mission_id}/samples")
def replay_samples(mission_id: int, limit: int = 5000, user=Depends(require_user)):
    samples = manager.replay.samples(mission_id, limit)
    if samples is None:
        raise HTTPException(404, "Mission not found")
    return samples


@app.get("/api/v1/system/status")
def system_status(user=Depends(require_user)):
    state = manager.get()
    age = _state_age_seconds(state)
    validity = _runtime_snapshot(state)["runtime_validity"] if state else None
    stale = validity["stale"] if validity else True
    quality = float(state.get("data_quality", {}).get("overall", 0.0)) if state else 0.0
    decision_eligible = bool(validity and validity["decision_eligible"])
    return {
        "service": settings.app_name,
        "version": settings.version,
        "environment": settings.environment,
        "engine_id": settings.engine_id,
        "database": settings.database_url.split(":", 1)[0],
        "models": {
            "anomaly": manager.ai.anomaly is not None,
            "fault": manager.ai.fault is not None,
            "rul": manager.ai.rul is not None,
        },
        "model_runtime": manager.ai.runtime_status(),
        "integrations": {
            "mqtt": settings.mqtt_enabled,
            "unreal_udp": settings.unreal_udp_enabled,
            "can": settings.can_enabled,
        },
        "telemetry": {
            "available": bool(state),
            "age_seconds": age,
            "stale": stale,
            "freshness_limit_seconds": settings.telemetry_stale_seconds,
            "data_quality": quality,
            "minimum_data_quality": settings.mission_min_data_quality,
            "decision_eligible": decision_eligible,
        },
        "security": {
            "cors_origins": list(settings.cors_origins),
            "trusted_hosts": list(settings.trusted_hosts),
            "ingest_key_required": bool(settings.ingest_api_key),
            "authentication": True,
        },
    }


@app.websocket("/api/v1/ws/twin/{engine_id}")
async def twin_ws(ws: WebSocket, engine_id: str):
    if engine_id != settings.engine_id:
        return await ws.close(code=1008)
    if not session_user(ws.query_params.get("token")):
        return await ws.close(code=1008)
    await ws.accept()
    peer = TwinPeer(ws)
    clients[ws] = peer
    try:
        initial = manager.get()
        if initial:
            await peer.send(
                json.dumps(_runtime_snapshot(initial), default=str),
                datetime.fromisoformat(str(initial["timestamp"]).replace("Z", "+00:00")),
            )
        while True:
            await asyncio.sleep(5)
            if peer.failed:
                break
            if not session_user(ws.query_params.get("token")):
                await ws.close(code=1008)
                break
            state = manager.get()
            await peer.send(
                json.dumps(
                    {
                        "type": "heartbeat",
                        "timestamp": datetime.now(UTC).isoformat(),
                        "runtime_validity": _runtime_snapshot(state)["runtime_validity"]
                        if state
                        else {"decision_eligible": False, "stale": True},
                    }
                )
            )
    except (WebSocketDisconnect, RuntimeError, OSError, TimeoutError):
        pass
    finally:
        clients.pop(ws, None)
        if peer.failed:
            try:
                await asyncio.wait_for(ws.close(code=1011), timeout=2.0)
            except (WebSocketDisconnect, RuntimeError, OSError, TimeoutError):
                pass


@app.get("/ready")
def ready():
    try:
        with engine.connect() as connection:
            connection.execute(text("SELECT 1"))
    except Exception:
        return JSONResponse({"status": "unavailable", "database": "unavailable"}, 503)
    return {
        "status": "ready",
        "database": "connected",
        "scope": "service readiness; telemetry checked separately",
    }
