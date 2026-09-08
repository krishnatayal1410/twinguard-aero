from __future__ import annotations

import json
from datetime import UTC, datetime

from sqlalchemy import select

from ..db import MissionRun, MissionSample, SessionLocal


class ReplayService:
    def __init__(self, engine_id="ENGINE-01"):
        self.engine_id = engine_id
        self.active_id = None

    def start(self, label=None):
        with SessionLocal() as s:
            run = MissionRun(
                engine_id=self.engine_id,
                label=label or f"TwinGuard Mission {datetime.now(UTC).strftime('%Y-%m-%d %H:%M:%S UTC')}",
            )
            s.add(run)
            s.commit()
            s.refresh(run)
            self.active_id = run.id
            return self.serialize(run)

    def sample(self, state):
        if not self.active_id:
            return
        t = state["telemetry"]
        with SessionLocal() as s:
            s.add(
                MissionSample(
                    mission_id=self.active_id,
                    health=state["health"]["overall"],
                    rul=state["ai"]["rul_hours"],
                    cht=t["cht"],
                    oil_pressure=t["oil_pressure"],
                    vibration=t["vibration"],
                    anomaly=1 if state["ai"]["anomaly"] else 0,
                    fault=state["ai"]["probable_fault"],
                    maintenance=state["maintenance"]["priority"],
                )
            )
            s.commit()

    def end(self):
        if not self.active_id:
            return None
        mid = self.active_id
        with SessionLocal() as s:
            run = s.get(MissionRun, mid)
            samples = list(
                s.scalars(
                    select(MissionSample)
                    .where(MissionSample.mission_id == mid)
                    .order_by(MissionSample.timestamp)
                )
            )
            summary = self.analyze(samples)
            run.status = "COMPLETED"
            run.ended_at = datetime.now(UTC)
            run.summary_json = json.dumps(summary)
            s.commit()
            s.refresh(run)
        self.active_id = None
        return self.serialize(run)

    def list(self, limit=30):
        with SessionLocal() as s:
            runs = list(s.scalars(select(MissionRun).order_by(MissionRun.id.desc()).limit(limit)))
            return [self.serialize(x) for x in runs]

    def get(self, mid):
        with SessionLocal() as s:
            r = s.get(MissionRun, mid)
            return self.serialize(r) if r else None

    def samples(self, mid, limit=5000):
        with SessionLocal() as s:
            if not s.get(MissionRun, mid):
                return None
            rows = list(
                s.scalars(
                    select(MissionSample)
                    .where(MissionSample.mission_id == mid)
                    .order_by(MissionSample.timestamp)
                    .limit(max(1, min(limit, 10000)))
                )
            )
            return [self.serialize_sample(x) for x in rows]

    def analyze(self, samples):
        if not samples:
            return {"sample_count": 0, "duration_seconds": 0, "events": []}
        events = []
        prev_anom = 0
        prev_fault = "normal"
        prev_maint = "MONITOR"
        prev_health = samples[0].health
        for x in samples:
            if x.anomaly and not prev_anom:
                events.append(
                    {
                        "timestamp": x.timestamp.isoformat(),
                        "type": "ANOMALY_DETECTED",
                        "severity": "warning",
                        "message": "The anomaly detector moved into an abnormal state.",
                    }
                )
            if x.fault != "normal" and x.fault != prev_fault:
                events.append(
                    {
                        "timestamp": x.timestamp.isoformat(),
                        "type": "FAULT_IDENTIFIED",
                        "severity": "warning",
                        "message": f"Probable fault changed to {x.fault}.",
                    }
                )
            if x.health < prev_health - 4:
                events.append(
                    {
                        "timestamp": x.timestamp.isoformat(),
                        "type": "HEALTH_DEGRADATION",
                        "severity": "warning",
                        "message": f"Health dropped to {x.health:.1f}/100.",
                    }
                )
            if x.maintenance != prev_maint:
                events.append(
                    {
                        "timestamp": x.timestamp.isoformat(),
                        "type": "MAINTENANCE_CHANGE",
                        "severity": "critical" if x.maintenance in {"NO_GO", "HIGH"} else "warning",
                        "message": f"Maintenance priority changed to {x.maintenance}.",
                    }
                )
            prev_anom = x.anomaly
            prev_fault = x.fault
            prev_maint = x.maintenance
            prev_health = x.health
        duration = (
            max(0.0, (samples[-1].timestamp - samples[0].timestamp).total_seconds())
            if len(samples) > 1
            else 0.0
        )
        return {
            "sample_count": len(samples),
            "duration_seconds": duration,
            "start_health": samples[0].health,
            "end_health": samples[-1].health,
            "rul_change_hours": samples[-1].rul - samples[0].rul,
            "max_cht": max(x.cht for x in samples),
            "min_oil_pressure": min(x.oil_pressure for x in samples),
            "max_vibration": max(x.vibration for x in samples),
            "anomaly_samples": sum(x.anomaly for x in samples),
            "faults_observed": sorted({x.fault for x in samples if x.fault != "normal"}),
            "events": events,
        }

    @staticmethod
    def serialize_sample(x):
        return {
            "timestamp": x.timestamp.isoformat(),
            "health": float(x.health),
            "rul": float(x.rul),
            "cht": float(x.cht),
            "oil_pressure": float(x.oil_pressure),
            "vibration": float(x.vibration),
            "anomaly": bool(x.anomaly),
            "fault": x.fault,
            "maintenance": x.maintenance,
        }

    @staticmethod
    def serialize(r):
        return {
            "id": r.id,
            "engine_id": r.engine_id,
            "label": r.label,
            "status": r.status,
            "started_at": r.started_at.isoformat() if r.started_at else None,
            "ended_at": r.ended_at.isoformat() if r.ended_at else None,
            "summary": json.loads(r.summary_json) if r.summary_json else None,
        }
