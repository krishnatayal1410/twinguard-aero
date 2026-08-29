from __future__ import annotations
from datetime import datetime, timezone
import json
from ..db import SessionLocal,TelemetryPoint,TwinSnapshot

class PersistenceService:
    def save(self,state):
        t=state["telemetry"]
        ts=t.get("timestamp")
        if isinstance(ts,str):
            try: ts=datetime.fromisoformat(ts.replace("Z","+00:00"))
            except Exception: ts=datetime.now(timezone.utc)
        with SessionLocal() as s:
            s.add(TelemetryPoint(
              engine_id=state["engine_id"],timestamp=ts,
              rpm=t["rpm"],throttle=t["throttle"],cht=t["cht"],egt=t["egt"],
              oil_pressure=t["oil_pressure"],oil_temperature=t["oil_temperature"],fuel_flow=t["fuel_flow"],
              vibration=t["vibration"],altitude=t["altitude"],battery_voltage=t["battery_voltage"]
            ))
            s.add(TwinSnapshot(
              engine_id=state["engine_id"],timestamp=ts,overall_health=state["health"]["overall"],
              probable_fault=state["ai"]["probable_fault"],anomaly_score=state["ai"]["anomaly_score"],
              rul_hours=state["ai"]["rul_hours"],maintenance_priority=state["maintenance"]["priority"],
              state_json=json.dumps(state,default=str,separators=(",",":"))
            ))
            s.commit()
persistence=PersistenceService()
