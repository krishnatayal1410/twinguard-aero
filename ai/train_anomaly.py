from pathlib import Path
import sys
import json
import joblib
import pandas as pd
from sklearn.ensemble import IsolationForest
from sklearn.metrics import roc_auc_score, precision_recall_fscore_support
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from ai.features import select_features

DATA = ROOT / "data/generated/engine_training.csv"
MODEL = ROOT / "models/anomaly.joblib"
METRICS = ROOT / "models/anomaly_metrics.json"

df = pd.read_csv(DATA)

# Train only on healthy missions 00-07.
healthy_train = df[
    (df["scenario_fault"] == "normal")
    & (~df["mission_id"].str.endswith(("08", "09")))
]
X_train = select_features(healthy_train)

# Evaluate on held-out mission IDs 08-09 for every scenario.
evaluation = df[df["mission_id"].str.endswith(("08", "09"))].copy()
X_eval = select_features(evaluation)
y_true = (evaluation["fault_label"] != "normal").astype(int)

model = Pipeline([
    ("scaler", StandardScaler()),
    ("model", IsolationForest(
        n_estimators=180,
        contamination=0.03,
        random_state=42,
        n_jobs=-1,
    )),
])
model.fit(X_train)

y_pred = (model.predict(X_eval) == -1).astype(int)
scores = -model.decision_function(X_eval)

precision, recall, f1, _ = precision_recall_fscore_support(
    y_true, y_pred, average="binary", zero_division=0
)

metrics = {
    "roc_auc": round(float(roc_auc_score(y_true, scores)), 4),
    "precision": round(float(precision), 4),
    "recall": round(float(recall), 4),
    "f1": round(float(f1), 4),
    "train_split": "healthy missions 00-07",
    "test_split": "held-out missions 08-09 across all scenarios",
    "note": "Synthetic proof-of-concept metrics only.",
}

MODEL.parent.mkdir(exist_ok=True)
joblib.dump(model, MODEL)
METRICS.write_text(json.dumps(metrics, indent=2))
print(metrics)
