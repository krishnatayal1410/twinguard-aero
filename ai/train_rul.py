from pathlib import Path
import sys
import json
import joblib
import numpy as np
import pandas as pd
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
from xgboost import XGBRegressor

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from ai.features import FEATURE_COLUMNS

DATA = ROOT / "data/generated/rul_training.csv"
MODEL = ROOT / "models/rul.joblib"
METRICS = ROOT / "models/rul_metrics.json"

df = pd.read_csv(DATA)
columns = FEATURE_COLUMNS + ["health_overall"]

test_missions = {f"degradation-{i:02d}" for i in range(24, 30)}
test_mask = df["mission_id"].isin(test_missions)

X_train = df.loc[~test_mask, columns]
X_test = df.loc[test_mask, columns]
y_train = df.loc[~test_mask, "rul_hours"]
y_test = df.loc[test_mask, "rul_hours"]

model = XGBRegressor(
    n_estimators=180,
    max_depth=6,
    learning_rate=0.06,
    subsample=0.9,
    colsample_bytree=0.9,
    objective="reg:squarederror",
    random_state=42,
    n_jobs=-1,
)
model.fit(X_train, y_train)
pred = model.predict(X_test)

metrics = {
    "mae_hours": round(float(mean_absolute_error(y_test, pred)), 4),
    "rmse_hours": round(float(np.sqrt(mean_squared_error(y_test, pred))), 4),
    "r2": round(float(r2_score(y_test, pred)), 4),
    "split": "degradation missions 00-23 train; 24-29 test",
    "note": "Synthetic proof-of-concept RUL only; not real-engine validated.",
}

MODEL.parent.mkdir(exist_ok=True)
joblib.dump(model, MODEL)
METRICS.write_text(json.dumps(metrics, indent=2))
print(metrics)
