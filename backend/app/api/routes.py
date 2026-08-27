from fastapi import APIRouter, Query, WebSocket, WebSocketDisconnect
from ..schemas.telemetry import Telemetry
from ..services.twin import twin_state
from ..services.models import model_service
from ..services.mission import simulate_mission
from ..services.mission_lab import MissionLabRequest, analyze_mission
from ..services.simulation_control import SimulationControlRequest, simulation_control
from ..database import save_telemetry, get_history
from ..websocket_manager import manager

from ..services.mission_replay import MissionStartRequest, mission_replay
router = APIRouter()


@router.get("/")
def root():
    return {
        "project": "TwinGuard Aero",
        "status": "development",
        "docs": "/docs",
    }


@router.get("/healthz")
def healthz():
    return {"status": "ok", "service": "TwinGuard Aero API"}


@router.get("/state")
def get_state():
    return twin_state.get()


@router.get("/history")
def history(
    engine_id: str = "ENGINE-01",
    limit: int = Query(default=300, ge=1, le=5000),
):
    return {"engine_id": engine_id, "items": get_history(engine_id, limit)}


@router.post("/telemetry")
async def ingest_telemetry(telemetry: Telemetry):
    state = twin_state.update(telemetry)
    mission_replay.record(state)
    save_telemetry(telemetry.model_dump())
    await manager.broadcast(state)
    return state


@router.post("/models/reload")
def reload_models():
    model_service.reload()
    return {"status": "reloaded"}


@router.get("/simulation/control")
def get_simulation_control():
    return simulation_control.get()


@router.post("/simulation/control")
def set_simulation_control(payload: SimulationControlRequest):
    if payload.fault == "normal":
        control = simulation_control.reset()
        twin_state.reset()
        return control

    return simulation_control.set(payload)


@router.post("/mission/analyze")
def analyze_future_mission(payload: MissionLabRequest):
    return analyze_mission(payload, twin_state.get())


@router.post("/mission/simulate")
def mission(payload: dict):
    return simulate_mission(
        current_state=twin_state.get(),
        duration_hours=float(payload.get("duration_hours", 1)),
        altitude=float(payload.get("altitude", 0)),
        ambient_temp=float(payload.get("ambient_temp", 25)),
        throttle=float(payload.get("throttle", 65)),
    )


@router.websocket("/ws/telemetry")
async def telemetry_socket(websocket: WebSocket):
    await manager.connect(websocket)
    try:
        await websocket.send_json(twin_state.get())
        while True:
            # Client may send keepalive text; server mainly pushes state.
            await websocket.receive_text()
    except WebSocketDisconnect:
        manager.disconnect(websocket)


@router.get("/replay/status")
def replay_status():
    return mission_replay.status()


@router.post("/replay/start")
def replay_start(payload: MissionStartRequest):
    return mission_replay.start(payload.label)


@router.post("/replay/end")
def replay_end():
    return mission_replay.end()


@router.get("/replay/missions")
def replay_missions(limit: int = 20):
    return mission_replay.list_missions(limit=limit)


@router.get("/replay/missions/{mission_id}")
def replay_mission_detail(mission_id: str):
    mission = mission_replay.get_mission(mission_id)
    if mission is None:
        return {"error": "mission_not_found", "mission_id": mission_id}
    return mission


@router.get("/mvp/status")
def mvp_status():
    state = twin_state.get()
    ai = state.get("ai") or {}
    health = state.get("health") or {}
    return {
        "status": "operational" if state.get("telemetry") else "waiting_for_telemetry",
        "modules": {
            "telemetry": state.get("telemetry") is not None,
            "digital_twin": state.get("telemetry") is not None,
            "physics_residuals": state.get("residuals") is not None,
            "health": health.get("overall") is not None,
            "anomaly_detection": "anomaly" in ai,
            "fault_classification": ai.get("fault") is not None,
            "rul": ai.get("rul_hours") is not None,
            "explainability": ai.get("explanation") is not None,
            "mission_lab": True,
            "mission_replay": True,
        },
        "replay": mission_replay.status(),
    }


