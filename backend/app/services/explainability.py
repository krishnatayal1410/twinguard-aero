from __future__ import annotations
import numpy as np
from .ai_engine import FEATURES
def tree_contributions(ai_engine,t,r):
    """Return local XGBoost feature contributions where available."""
    if ai_engine.fault is None:
        return {"method":"physics_evidence","items":ai_engine.explain(t,r,"normal")}
    try:
        import xgboost as xgb
        x=ai_engine.vector(t,r)
        dm=xgb.DMatrix(x,feature_names=FEATURES)
        raw=ai_engine.fault.get_booster().predict(dm,pred_contribs=True)
        # XGBoost multiclass may be (n, classes, features+1).
        if raw.ndim==3:
            pred=int(np.argmax(ai_engine.fault.predict_proba(x)[0]))
            vals=raw[0,pred,:-1]
        else:
            vals=raw[0,:-1]
        order=np.argsort(np.abs(vals))[::-1][:6]
        items=[{"feature":FEATURES[int(i)],"contribution":float(vals[int(i)]),"abs_contribution":float(abs(vals[int(i)]))} for i in order]
        return {"method":"xgboost_tree_contributions","items":items}
    except Exception:
        return {"method":"physics_evidence","items":ai_engine.explain(t,r,"normal")}
