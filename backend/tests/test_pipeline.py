from datetime import datetime, timezone
from app.services.twin_manager import manager
from app.schemas import MissionRequest

def sample():
    return {
      "engine_id":"ENGINE-01","timestamp":datetime.now(timezone.utc),
      "rpm":4100,"throttle":70,"cht":185,"egt":700,"oil_pressure":4.55,
      "oil_temperature":94,"fuel_flow":19.0,"vibration":.24,"battery_voltage":27.8,
      "alternator_voltage":28.1,"altitude":4300,"ambient_temperature":-5,
      "injection_timing":18,"operating_hours":42
    }

def test_twin_pipeline():
    s=manager.ingest(sample())
    assert 0<=s["health"]["overall"]<=100
    assert "probable_fault" in s["ai"]
    assert "decision" in s["confidence"]
    assert "priority" in s["maintenance"]

def test_mission_analysis():
    s=manager.ingest(sample())
    r=manager.mission.analyze(s,MissionRequest())
    assert r["overall_risk"] in {"LOW","MEDIUM","HIGH"}
    assert r["post_mission_health"]<r["current_health"]
    assert r["post_mission_rul_hours"]<r["current_rul_hours"]

def test_lubrication_physics_direction():
    x=sample();x["oil_pressure"]=2.9;x["oil_temperature"]=117;x["vibration"]=.48
    s=manager.ingest(x)
    assert s["residuals"]["oil_pressure_residual"]<0
    assert s["health"]["lubrication"]<95
