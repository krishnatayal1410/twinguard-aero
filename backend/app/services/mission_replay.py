from __future__ import annotations

import json
import sqlite3
import threading
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from pydantic import BaseModel, Field


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _number(value: Any) -> float | None:
    if isinstance(value, bool):
        return None
    if isinstance(value, (int, float)):
        return float(value)
    return None


class MissionStartRequest(BaseModel):
    label: str = Field(default="TwinGuard Demo Mission", min_length=1, max_length=120)


class MissionReplayStore:
    def __init__(self, db_path: str | Path | None = None):
        root = Path(__file__).resolve().parents[3]
        default_path = root / "data" / "runtime" / "mission_replay.db"
        self.db_path = Path(db_path) if db_path else default_path
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._lock = threading.RLock()
        self._initialize()

    def _connect(self) -> sqlite3.Connection:
        db = sqlite3.connect(self.db_path, timeout=5)
        db.row_factory = sqlite3.Row
        return db

    def _initialize(self) -> None:
        with self._connect() as db:
            db.execute(
                "CREATE TABLE IF NOT EXISTS missions ("
                "id TEXT PRIMARY KEY, label TEXT NOT NULL, started_at TEXT NOT NULL, "
                "ended_at TEXT, status TEXT NOT NULL, summary_json TEXT)"
            )
            db.execute(
                "CREATE TABLE IF NOT EXISTS mission_samples ("
                "id INTEGER PRIMARY KEY AUTOINCREMENT, mission_id TEXT NOT NULL, "
                "timestamp TEXT NOT NULL, state_json TEXT NOT NULL)"
            )
            db.execute(
                "CREATE INDEX IF NOT EXISTS idx_mission_samples_mission_id "
                "ON mission_samples(mission_id, id)"
            )

    def _active_id(self, db: sqlite3.Connection) -> str | None:
        row = db.execute(
            "SELECT id FROM missions WHERE status='ACTIVE' "
            "ORDER BY started_at DESC LIMIT 1"
        ).fetchone()
        return str(row["id"]) if row else None

    def start(self, label: str) -> dict:
        with self._lock, self._connect() as db:
            old = self._active_id(db)
            if old:
                db.execute(
                    "UPDATE missions SET status='INTERRUPTED', ended_at=? WHERE id=?",
                    (_utc_now(), old),
                )
            mission_id = str(uuid.uuid4())
            started_at = _utc_now()
            db.execute(
                "INSERT INTO missions(id,label,started_at,status) VALUES(?,?,?,'ACTIVE')",
                (mission_id, label.strip(), started_at),
            )
            return {
                "id": mission_id,
                "label": label.strip(),
                "started_at": started_at,
                "status": "ACTIVE",
            }

    def record(self, state: dict) -> None:
        with self._lock, self._connect() as db:
            mission_id = self._active_id(db)
            if not mission_id:
                return
            telemetry = state.get("telemetry") or {}
            timestamp = str(telemetry.get("timestamp") or _utc_now())
            snapshot = {
                "timestamp": timestamp,
                "telemetry": telemetry,
                "health": state.get("health") or {},
                "ai": state.get("ai") or {},
                "maintenance": state.get("maintenance") or {},
                "residuals": state.get("residuals") or {},
                "sensor_trust": state.get("sensor_trust") or {},
            }
            db.execute(
                "INSERT INTO mission_samples(mission_id,timestamp,state_json) VALUES(?,?,?)",
                (mission_id, timestamp, json.dumps(snapshot, default=str)),
            )

    def _samples(self, db: sqlite3.Connection, mission_id: str) -> list[dict]:
        rows = db.execute(
            "SELECT timestamp,state_json FROM mission_samples "
            "WHERE mission_id=? ORDER BY id",
            (mission_id,),
        ).fetchall()
        result = []
        for row in rows:
            try:
                item = json.loads(row["state_json"])
                item["timestamp"] = row["timestamp"]
                result.append(item)
            except json.JSONDecodeError:
                pass
        return result

    def _events(self, samples: list[dict]) -> list[dict]:
        events = []
        prev_anomaly = False
        prev_fault = "normal"
        prev_priority = "MONITOR"
        health_floor = 100

        for sample in samples:
            timestamp = sample.get("timestamp")
            ai = sample.get("ai") or {}
            health = sample.get("health") or {}
            maintenance = sample.get("maintenance") or {}

            anomaly = ai.get("anomaly") is True
            fault = str(ai.get("fault", "normal"))
            priority = str(maintenance.get("priority", "MONITOR"))
            overall = _number(health.get("overall"))

            if anomaly and not prev_anomaly:
                events.append({
                    "timestamp": timestamp,
                    "type": "ANOMALY_DETECTED",
                    "severity": "warning",
                    "message": "AI anomaly detection changed to DETECTED.",
                })

            if fault != prev_fault and fault not in {"normal", "model_not_trained"}:
                events.append({
                    "timestamp": timestamp,
                    "type": "FAULT_IDENTIFIED",
                    "severity": "warning",
                    "message": f"Probable condition changed to {fault.replace('_', ' ')}.",
                })

            if priority != prev_priority:
                events.append({
                    "timestamp": timestamp,
                    "type": "MAINTENANCE_CHANGE",
                    "severity": "warning" if priority != "MONITOR" else "info",
                    "message": f"Maintenance priority changed to {priority}.",
                })

            if overall is not None:
                new_floor = 60 if overall < 60 else 75 if overall < 75 else 90 if overall < 90 else 100
                if new_floor < health_floor:
                    events.append({
                        "timestamp": timestamp,
                        "type": "HEALTH_DEGRADATION",
                        "severity": "critical" if new_floor <= 60 else "warning",
                        "message": f"Overall health degraded to {overall:.1f}%.",
                    })
                    health_floor = new_floor

            prev_anomaly = anomaly
            prev_fault = fault
            prev_priority = priority

        return events[:120]

    def _summary(self, samples: list[dict]) -> dict:
        healths, ruls, chts, egts, oils, vibs = [], [], [], [], [], []
        faults = set()
        anomaly_samples = 0

        for sample in samples:
            telemetry = sample.get("telemetry") or {}
            health = sample.get("health") or {}
            ai = sample.get("ai") or {}

            pairs = [
                (_number(health.get("overall")), healths),
                (_number(ai.get("rul_hours")), ruls),
                (_number(telemetry.get("cht")), chts),
                (_number(telemetry.get("egt")), egts),
                (_number(telemetry.get("oil_pressure")), oils),
                (_number(telemetry.get("vibration")), vibs),
            ]
            for value, target in pairs:
                if value is not None:
                    target.append(value)

            if ai.get("anomaly") is True:
                anomaly_samples += 1

            fault = str(ai.get("fault", "normal"))
            if fault not in {"normal", "model_not_trained"}:
                faults.add(fault)

        start_health = healths[0] if healths else None
        end_health = healths[-1] if healths else None
        start_rul = ruls[0] if ruls else None
        end_rul = ruls[-1] if ruls else None

        return {
            "sample_count": len(samples),
            "start_health": round(start_health, 1) if start_health is not None else None,
            "end_health": round(end_health, 1) if end_health is not None else None,
            "minimum_health": round(min(healths), 1) if healths else None,
            "start_rul_hours": round(start_rul, 1) if start_rul is not None else None,
            "end_rul_hours": round(end_rul, 1) if end_rul is not None else None,
            "rul_change_hours": (
                round(end_rul - start_rul, 1)
                if start_rul is not None and end_rul is not None else None
            ),
            "max_cht": round(max(chts), 1) if chts else None,
            "max_egt": round(max(egts), 1) if egts else None,
            "min_oil_pressure": round(min(oils), 3) if oils else None,
            "max_vibration": round(max(vibs), 4) if vibs else None,
            "anomaly_samples": anomaly_samples,
            "faults_observed": sorted(faults),
            "events": self._events(samples),
        }

    def end(self) -> dict:
        with self._lock, self._connect() as db:
            mission_id = self._active_id(db)
            if not mission_id:
                return {"status": "NO_ACTIVE_MISSION"}

            samples = self._samples(db, mission_id)
            summary = self._summary(samples)
            ended_at = _utc_now()
            db.execute(
                "UPDATE missions SET status='COMPLETED', ended_at=?, summary_json=? WHERE id=?",
                (ended_at, json.dumps(summary), mission_id),
            )
            row = db.execute(
                "SELECT label,started_at FROM missions WHERE id=?",
                (mission_id,),
            ).fetchone()
            return {
                "id": mission_id,
                "label": row["label"],
                "started_at": row["started_at"],
                "ended_at": ended_at,
                "status": "COMPLETED",
                "summary": summary,
            }

    def list_missions(self, limit: int = 20) -> list[dict]:
        with self._connect() as db:
            rows = db.execute(
                "SELECT id,label,started_at,ended_at,status,summary_json "
                "FROM missions ORDER BY started_at DESC LIMIT ?",
                (max(1, min(int(limit), 100)),),
            ).fetchall()

            missions = []
            for row in rows:
                summary = None
                if row["summary_json"]:
                    try:
                        summary = json.loads(row["summary_json"])
                    except json.JSONDecodeError:
                        pass
                missions.append({
                    "id": row["id"],
                    "label": row["label"],
                    "started_at": row["started_at"],
                    "ended_at": row["ended_at"],
                    "status": row["status"],
                    "summary": summary,
                })
            return missions

    def get_mission(self, mission_id: str) -> dict | None:
        with self._connect() as db:
            row = db.execute(
                "SELECT id,label,started_at,ended_at,status,summary_json "
                "FROM missions WHERE id=?",
                (mission_id,),
            ).fetchone()
            if not row:
                return None

            samples = self._samples(db, mission_id)
            summary = self._summary(samples)
            if row["summary_json"]:
                try:
                    summary = json.loads(row["summary_json"])
                except json.JSONDecodeError:
                    pass

            if len(samples) > 600:
                step = max(1, len(samples) // 600)
                samples = samples[::step]

            return {
                "id": row["id"],
                "label": row["label"],
                "started_at": row["started_at"],
                "ended_at": row["ended_at"],
                "status": row["status"],
                "summary": summary,
                "samples": samples,
            }

    def status(self) -> dict:
        with self._connect() as db:
            mission_id = self._active_id(db)
            if not mission_id:
                return {"recording": False, "mission_id": None}
            row = db.execute(
                "SELECT label,started_at FROM missions WHERE id=?",
                (mission_id,),
            ).fetchone()
            count = db.execute(
                "SELECT COUNT(*) AS c FROM mission_samples WHERE mission_id=?",
                (mission_id,),
            ).fetchone()["c"]
            return {
                "recording": True,
                "mission_id": mission_id,
                "label": row["label"],
                "started_at": row["started_at"],
                "sample_count": int(count),
            }


mission_replay = MissionReplayStore()
