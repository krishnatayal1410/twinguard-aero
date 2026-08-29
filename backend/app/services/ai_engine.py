from __future__ import annotations
from pathlib import Path
import json, math, joblib, numpy as np, os

FEATURES=[
 "rpm","throttle","cht","egt","oil_pressure","oil_temperature","fuel_flow","vibration",
 "altitude","ambient_temperature","cht_residual","egt_residual","oil_pressure_residual",
 "oil_temperature_residual","fuel_flow_residual","vibration_residual"
]

class AIEngine:
    def __init__(self, model_dir="./models"):
        p=Path(model_dir)
        # XGBoost uses native libraries. Some macOS machines can take a long time
        # to load them or can fail before FastAPI is able to start. TwinGuard
        # therefore boots in a platform-stable mode by default and uses the
        # engineering fallback classifier/RUL logic. Set
        # TWINGUARD_NATIVE_ML=1 after the app is working if you want the packaged
        # XGBoost classifier/regressor loaded.
        self.native_ml=os.getenv("TWINGUARD_NATIVE_ML","0")=="1"

        def safe(name):
            try:
                path=p/name
                return joblib.load(path) if path.exists() else None
            except BaseException:
                return None

        # Isolation Forest is sklearn-only and safe to load in normal mode.
        self.anomaly=safe("anomaly_model.joblib")
        self.fault=safe("fault_model.joblib") if self.native_ml else None
        self.rul=safe("rul_model.joblib") if self.native_ml else None

        try:
            self.labels=json.loads((p/"fault_labels.json").read_text())
        except Exception:
            self.labels=["normal","lubrication","overheating","vibration","sensor_drift","injector","misfire","turbine_blade_degradation"]

    def vector(self,t,r):
        x={**t,**r}
        return np.asarray([[float(x.get(k,0)) for k in FEATURES]],dtype=float)

    def predict(self,t,r):
        x=self.vector(t,r)
        if self.anomaly is not None:
            raw=float(-self.anomaly.score_samples(x)[0])
            anomaly=bool(self.anomaly.predict(x)[0] == -1)
            anomaly_score=max(0,min(1,(raw-.35)/.45))
        else:
            z=abs(r["cht_residual"])/35+abs(r["egt_residual"])/80+abs(r["oil_pressure_residual"])/1.5+max(0,t["vibration"]-.3)/.7
            anomaly_score=max(0,min(1,z/2.3)); anomaly=anomaly_score>.32

        probs={}
        if self.fault is not None:
            pp=self.fault.predict_proba(x)[0]
            classes=[self.labels[int(c)] if str(c).lstrip("-").isdigit() and int(c)<len(self.labels) else str(c) for c in self.fault.classes_]
            probs={c:float(v) for c,v in zip(classes,pp)}
            fault=max(probs,key=probs.get)
            confidence=probs[fault]
        else:
            heur={
              "lubrication": max(0,-r["oil_pressure_residual"])/1.5 + max(0,r["oil_temperature_residual"])/30,
              "overheating": max(0,r["cht_residual"])/35 + max(0,r["egt_residual"])/80,
              "vibration": max(0,t["vibration"]-.3)/.7,
              "sensor_drift": max(0,abs(r["oil_pressure_residual"])-.8)/1.5,
              "injector": max(0,abs(r["fuel_flow_residual"])-1)/4 + max(0,abs(r["egt_residual"])-35)/100,
              "misfire": max(0,t["vibration"]-.35)/.8 + max(0,abs(r["egt_residual"])-30)/120,
              "turbine_blade_degradation": max(0,t["vibration"]-.32)/.55 + max(0,r["egt_residual"]-20)/95 + max(0,r["fuel_flow_residual"]-.4)/3,
              "normal": .65
            }
            fault=max(heur,key=heur.get); total=sum(math.exp(v*2) for v in heur.values())
            probs={k:math.exp(v*2)/total for k,v in heur.items()}; confidence=probs[fault]
            if not anomaly: fault="normal"; confidence=max(confidence,.82); probs["normal"]=confidence

        if self.rul is not None:
            rul=max(1,float(self.rul.predict(x)[0]))
        else:
            penalty=abs(r["cht_residual"])*.6+abs(r["egt_residual"])*.15+max(0,-r["oil_pressure_residual"])*24+max(0,t["vibration"]-.3)*85
            rul=max(8,190-penalty-float(t.get("operating_hours",0))*.08)

        evidence=self.explain(t,r,fault)
        return {"anomaly":anomaly,"anomaly_score":anomaly_score,"probable_fault":fault,"fault_confidence":float(confidence),"fault_probabilities":probs,"rul_hours":rul,"evidence":evidence,"model_state":"NATIVE_ML" if self.native_ml and self.fault is not None else "STABLE_FALLBACK"}

    def explain(self,t,r,fault):
        candidates={
          "oil_pressure_residual":abs(r["oil_pressure_residual"])/1.5,
          "oil_temperature_residual":abs(r["oil_temperature_residual"])/30,
          "cht_residual":abs(r["cht_residual"])/35,
          "egt_residual":abs(r["egt_residual"])/80,
          "fuel_flow_residual":abs(r["fuel_flow_residual"])/4,
          "vibration":max(0,float(t["vibration"])-.2)/.8,
        }
        total=sum(candidates.values()) or 1
        return [{"feature":k,"weight":v/total,"value":float((r if k in r else t).get(k,0))} for k,v in sorted(candidates.items(),key=lambda kv:kv[1],reverse=True)[:5]]
