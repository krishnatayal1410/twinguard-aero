from __future__ import annotations
from datetime import datetime, timezone
from threading import RLock
from .physics import PhysicsEngine
from .sensor_trust import SensorTrustEngine
from .health import HealthEngine, readiness
from .ai_engine import AIEngine
from .maintenance import MaintenanceEngine
from .mission import MissionEngine
from .replay import ReplayService
from ..core import settings
from .persistence import persistence

class TwinManager:
    def __init__(self):
        self.lock=RLock();self.physics=PhysicsEngine();self.trust=SensorTrustEngine();self.health=HealthEngine();self.ai=AIEngine(settings.model_dir);self.maint=MaintenanceEngine();self.mission=MissionEngine();self.replay=ReplayService(settings.engine_id)
        self.previous=None;self.state=None;self.simulation={"fault":"normal","severity":0.0}
    def ingest(self,telemetry:dict):
        with self.lock:
            t=dict(telemetry);ts=t.get("timestamp")
            if hasattr(ts,"isoformat"):t["timestamp"]=ts.isoformat()
            expected=self.physics.expected(t);res=self.physics.residuals(t,expected);trust=self.trust.evaluate(t,res,self.previous);quality=self.trust.quality(t,trust);health=self.health.compute(t,res,trust);ai=self.ai.predict(t,res)
            ai_conf=ai["fault_confidence"]*100;sensor=sum(trust.values())/len(trust);physics=max(35,100-(abs(res["cht_residual"])/35+abs(res["egt_residual"])/80+abs(res["oil_pressure_residual"])/1.5)/3*38)
            fused=.42*ai_conf+.28*sensor+.20*physics+.10*float(quality["overall"])
            confidence={"ai":ai_conf,"sensor":sensor,"physics_agreement":physics,"data_quality":float(quality["overall"]),"decision":fused}
            maintenance=self.maint.decide(health,ai,trust);ready=readiness(health,ai,maintenance)
            self.state={"engine_id":t.get("engine_id",settings.engine_id),"timestamp":t["timestamp"],"telemetry":t,"expected":expected,"residuals":res,"sensor_trust":trust,"data_quality":quality,"health":health,"ai":ai,"confidence":confidence,"maintenance":maintenance,"readiness":ready}
            self.previous=t;self.replay.sample(self.state);persistence.save(self.state);return self.state
    def get(self): return self.state
manager=TwinManager()
