from __future__ import annotations
from pathlib import Path
import json, joblib, numpy as np
from sklearn.ensemble import IsolationForest
from sklearn.metrics import accuracy_score, f1_score, mean_absolute_error, mean_squared_error, r2_score
from sklearn.model_selection import train_test_split
from xgboost import XGBClassifier, XGBRegressor

FEATURES=[
 "rpm","throttle","cht","egt","oil_pressure","oil_temperature","fuel_flow","vibration",
 "altitude","ambient_temperature","cht_residual","egt_residual","oil_pressure_residual",
 "oil_temperature_residual","fuel_flow_residual","vibration_residual"
]
LABELS=["normal","lubrication","overheating","vibration","sensor_drift","injector","misfire","turbine_blade_degradation"]

def make(seed=42):
    rng=np.random.default_rng(seed);rows=[];y=[];ruls=[]
    for lid,label in enumerate(LABELS):
        n=700 if label=="normal" else 430
        for _ in range(n):
            rpm=rng.normal(4050,350);thr=float(np.clip(rng.normal(70,14),30,100));alt=float(np.clip(rng.normal(4200,1800),0,9000));amb=rng.normal(18,12)
            density=max(.58,1-alt/21000)
            exp_cht=amb+105+58*(thr/100)+.0048*(rpm-2500)+10*(1-density)
            exp_egt=500+250*(thr/100)+.015*(rpm-2500)+16*(1-density)
            oilt=amb+48+46*(thr/100)+.002*(rpm-2500)+rng.normal(0,3)
            exp_oil=3+.00046*rpm-.018*max(oilt-85,0);exp_fuel=5.2+.0022*rpm+7.2*(thr/100)/density
            exp_vib=.16+abs(rpm-3900)/11000+.07*(thr/100)
            cht=exp_cht+rng.normal(0,5);egt=exp_egt+rng.normal(0,14);oil=exp_oil+rng.normal(0,.12);fuel=exp_fuel+rng.normal(0,.35);vib=exp_vib+rng.normal(0,.025)
            sev=rng.uniform(.35,.95)
            if label=="lubrication":oil-=1.4*sev;oilt+=24*sev;vib+=.25*sev
            elif label=="overheating":cht+=42*sev;egt+=64*sev;oilt+=16*sev
            elif label=="vibration":vib+=.75*sev
            elif label=="sensor_drift":oil+=.75*sev
            elif label=="injector":fuel+=2.3*sev;egt+=70*sev
            elif label=="misfire":vib+=.28*sev;egt+=rng.normal(0,60*sev);rpm+=rng.normal(0,350*sev)
            elif label=="turbine_blade_degradation":rpm-=120*sev;egt+=42*sev;vib+=.46*sev;fuel+=1.1*sev
            row=[rpm,thr,cht,egt,oil,oilt,fuel,vib,alt,amb,cht-exp_cht,egt-exp_egt,oil-exp_oil,oilt-(amb+48+46*(thr/100)+.002*(rpm-2500)),fuel-exp_fuel,vib-exp_vib]
            rows.append(row);y.append(lid)
            ruls.append(max(8,190-rng.uniform(0,45)-(0 if label=="normal" else 55*sev)-abs(row[10])*.45-abs(row[11])*.10-max(0,-row[12])*20-max(0,vib-.3)*50+rng.normal(0,4)))
    return np.asarray(rows),np.asarray(y),np.asarray(ruls)

def main():
    X,y,rul=make()
    Xtr,Xte,ytr,yte,rtr,rte=train_test_split(X,y,rul,test_size=.22,random_state=42,stratify=y)
    anomaly=IsolationForest(n_estimators=140,contamination=.08,random_state=42,n_jobs=-1).fit(Xtr[ytr==0])
    fault=XGBClassifier(n_estimators=170,max_depth=5,learning_rate=.07,subsample=.9,colsample_bytree=.9,eval_metric="mlogloss",random_state=42,n_jobs=-1).fit(Xtr,ytr)
    rul_model=XGBRegressor(n_estimators=180,max_depth=4,learning_rate=.06,subsample=.9,colsample_bytree=.9,random_state=42,n_jobs=-1).fit(Xtr,rtr)
    out=Path("models");out.mkdir(exist_ok=True)
    joblib.dump(anomaly,out/"anomaly_model.joblib");joblib.dump(fault,out/"fault_model.joblib");joblib.dump(rul_model,out/"rul_model.joblib")
    (out/"fault_labels.json").write_text(json.dumps(LABELS,indent=2));(out/"feature_order.json").write_text(json.dumps(FEATURES,indent=2))
    pred=fault.predict(Xte);rp=rul_model.predict(Xte)
    metrics={"fault_accuracy":accuracy_score(yte,pred),"fault_macro_f1":f1_score(yte,pred,average="macro"),"rul_mae":mean_absolute_error(rte,rp),"rul_rmse":mean_squared_error(rte,rp)**.5,"rul_r2":r2_score(rte,rp),"note":"Synthetic proof-of-concept metrics only; not real-engine validation."}
    (out/"synthetic_metrics.json").write_text(json.dumps(metrics,indent=2))
    print(json.dumps(metrics,indent=2))
if __name__=="__main__":main()
