from __future__ import annotations
from datetime import datetime, timezone
import math

LIMITS = {
 "cht": 35.0, "egt": 85.0, "oil_pressure": 1.6, "oil_temperature": 28.0,
 "fuel_flow": 4.0, "vibration": 0.65, "battery_voltage": 2.0,
}
class SensorTrustEngine:
    def evaluate(self, t: dict, residuals: dict, previous: dict|None=None):
        trust={}
        for key,limit in LIMITS.items():
            r=abs(float(residuals.get(f"{key}_residual",0)))
            score=100 - min(72, 70*(r/limit)**1.35)
            if previous and key in previous:
                delta=abs(float(t[key])-float(previous[key]))
                # Generic sudden-jump penalties.
                jumps={"cht":16,"egt":45,"oil_pressure":.7,"oil_temperature":12,"fuel_flow":2.5,"vibration":.3,"battery_voltage":1.1}
                score -= min(25, max(0,delta-jumps[key])*8)
            trust[key]=max(15,min(100,score))
        return trust

    def quality(self, t: dict, trust: dict):
        required=["rpm","throttle","cht","egt","oil_pressure","oil_temperature","fuel_flow","vibration","battery_voltage","altitude","ambient_temperature"]
        complete=sum(1 for k in required if k in t and t[k] is not None)/len(required)*100
        freshness=100
        try:
            ts=t.get("timestamp")
            if isinstance(ts,str):
                ts=datetime.fromisoformat(ts.replace("Z","+00:00"))
            age=abs((datetime.now(timezone.utc)-ts).total_seconds())
            freshness=max(0,100-age*12)
        except Exception:
            freshness=75
        avg=sum(trust.values())/max(1,len(trust))
        # "noise" here is a conservative proxy until a rolling buffer is available.
        noise=max(45,min(100, 92-(100-avg)*.22))
        overall=.34*complete+.22*freshness+.30*avg+.14*noise
        label="GOOD" if overall>=88 else "REVIEW" if overall>=70 else "POOR"
        return {"completeness":complete,"freshness":freshness,"sensor_integrity":avg,"signal_quality":noise,"overall":overall,"label":label}
