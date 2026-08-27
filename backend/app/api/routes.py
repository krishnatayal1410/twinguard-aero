from fastapi import APIRouter, Query, WebSocket, WebSocketDisconnect
from ..schemas.telemetry import Telemetry
from ..services.twin import twin_state
from ..services.models import model_service
from ..services.mission import simulate_mission
from ..services.simulation_control import SimulationControlRequest, simulation_control
from ..database import save_telemetry, get_history
from ..websocket_manager import manager

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
    return simulation_control.set(payload)


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
