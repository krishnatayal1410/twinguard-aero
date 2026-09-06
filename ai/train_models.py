from __future__ import annotations
from datetime import datetime, timezone
from pathlib import Path
import json

import joblib
import numpy as np
from sklearn.ensemble import IsolationForest
from sklearn.metrics import accuracy_score, f1_score, mean_absolute_error, mean_squared_error, r2_score
from sklearn.model_selection import train_test_split
from xgboost import XGBClassifier, XGBRegressor

FEATURES=[
 "rpm","throttle","cht","egt","oil_pressure","oil_temperature","fuel_flow","vibration",
 "battery_voltage","alternator_voltage","injection_timing","altitude","ambient_temperature",
 "cht_residual","egt_residual","oil_pressure_residual","oil_temperature_residual",
 "fuel_flow_residual","vibration_residual","battery_voltage_residual",
 "alternator_voltage_residual","injection_timing_residual"
]
LABELS=[
 "normal","lubrication","overheating","cooling_degradation","vibration",
 "sensor_drift","injector","misfire","combustion_instability","alternator_degradation"
]
SCHEMA_VERSION="aero-piston-v2"


def make(seed=42):
    rng=np.random.default_rng(seed);rows=[];y=[];ruls=[]
    for lid,label in enumerate(LABELS):
        n=900 if label=="normal" else 520
        for _ in range(n):
            rpm=float(np.clip(rng.normal(4050,350),2200,5800));thr=float(np.clip(rng.normal(70,14),30,100));alt=float(np.clip(rng.normal(4200,1800),0,9000));amb=float(np.clip(rng.normal(25,12),-20,55));density=max(.58,1-alt/21000);load=thr/100
            exp_cht=amb+105+58*load+.0048*(rpm-2500)+10*(1-density)
            exp_egt=500+250*load+.015*(rpm-2500)+16*(1-density)
            exp_oilt=amb+48+46*load+.002*(rpm-2500)
            oilt=exp_oilt+rng.normal(0,3)
            exp_oil=3+.00046*rpm-.018*max(oilt-85,0)
            exp_fuel=5.2+.0022*rpm+7.2*load/density
            exp_vib=.16+abs(rpm-3900)/11000+.07*load
            exp_batt=27.6+.25*min(1,rpm/2500)
            exp_alt=28.15 if rpm>=1500 else 25.8+2.35*(rpm/1500)
            exp_timing=17.2+.00032*(rpm-2500)+1.6*load

            cht=exp_cht+rng.normal(0,5);egt=exp_egt+rng.normal(0,14);oil=exp_oil+rng.normal(0,.12);fuel=exp_fuel+rng.normal(0,.35);vib=exp_vib+rng.normal(0,.025);batt=exp_batt+rng.normal(0,.08);alternator=exp_alt+rng.normal(0,.08);timing=exp_timing+rng.normal(0,.18)
            sev=float(rng.uniform(.35,.95))
            if label=="lubrication":oil-=1.4*sev;oilt+=24*sev;vib+=.25*sev
            elif label=="overheating":cht+=42*sev;egt+=64*sev;oilt+=16*sev
            elif label=="cooling_degradation":cht+=34*sev;oilt+=20*sev;egt+=18*sev
            elif label=="vibration":vib+=.75*sev
            elif label=="sensor_drift":oil+=.85*sev
            elif label=="injector":fuel+=2.3*sev;egt+=70*sev;timing+=1.6*sev
            elif label=="misfire":vib+=.28*sev;egt+=rng.normal(0,60*sev);rpm+=rng.normal(0,350*sev)
            elif label=="combustion_instability":vib+=.18*sev;egt+=rng.normal(0,48*sev);fuel+=rng.normal(0,.9*sev);rpm+=rng.normal(0,160*sev)
            elif label=="alternator_degradation":alternator-=5.0*sev;batt-=2.0*sev

            residuals=[cht-exp_cht,egt-exp_egt,oil-exp_oil,oilt-exp_oilt,fuel-exp_fuel,vib-exp_vib,batt-exp_batt,alternator-exp_alt,timing-exp_timing]
            row=[rpm,thr,cht,egt,oil,oilt,fuel,vib,batt,alternator,timing,alt,amb,*residuals]
            rows.append(row);y.append(lid)
            stress=(abs(residuals[0])*.45+abs(residuals[1])*.10+max(0,-residuals[2])*20+max(0,vib-.3)*50+max(0,-residuals[7])*4)
            ruls.append(max(8,190-rng.uniform(0,35)-(0 if label=="normal" else 45*sev)-stress+rng.normal(0,5)))
    return np.asarray(rows),np.asarray(y),np.asarray(ruls)


def main():
    X,y,rul=make()
    Xtr,Xte,ytr,yte,rtr,rte=train_test_split(X,y,rul,test_size=.22,random_state=42,stratify=y)
    anomaly=IsolationForest(n_estimators=180,contamination=.08,random_state=42,n_jobs=-1).fit(Xtr[ytr==0])
    fault=XGBClassifier(n_estimators=190,max_depth=5,learning_rate=.065,subsample=.9,colsample_bytree=.9,eval_metric="mlogloss",random_state=42,n_jobs=-1).fit(Xtr,ytr)
    rul_model=XGBRegressor(n_estimators=210,max_depth=4,learning_rate=.055,subsample=.9,colsample_bytree=.9,random_state=42,n_jobs=-1).fit(Xtr,rtr)
    out=Path("models");out.mkdir(exist_ok=True)
    joblib.dump(anomaly,out/"anomaly_model.joblib");joblib.dump(fault,out/"fault_model.joblib");joblib.dump(rul_model,out/"rul_model.joblib")
    (out/"fault_labels.json").write_text(json.dumps(LABELS,indent=2));(out/"feature_order.json").write_text(json.dumps(FEATURES,indent=2))
    pred=fault.predict(Xte);rp=rul_model.predict(Xte)
    metrics={
      "fault_accuracy":accuracy_score(yte,pred),"fault_macro_f1":f1_score(yte,pred,average="macro"),
      "rul_mae":mean_absolute_error(rte,rp),"rul_rmse":mean_squared_error(rte,rp)**.5,"rul_r2":r2_score(rte,rp),
      "note":"Synthetic proof-of-concept metrics only; not real-engine validation."
    }
    (out/"synthetic_metrics.json").write_text(json.dumps(metrics,indent=2))
    manifest={
      "schema_version":SCHEMA_VERSION,"created_at":datetime.now(timezone.utc).isoformat(),
      "fault_labels":LABELS,"feature_order":FEATURES,"training_source":"synthetic_physics_inspired_generator",
      "validation_scope":"SYNTHETIC_PROOF_OF_CONCEPT","metrics_file":"synthetic_metrics.json"
    }
    (out/"model_manifest.json").write_text(json.dumps(manifest,indent=2))
    print(json.dumps(metrics,indent=2))


if __name__=="__main__":main()
