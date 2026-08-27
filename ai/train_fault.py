from pathlib import Path
import sys
import json
import joblib
import numpy as np
import pandas as pd
from sklearn.metrics import classification_report, confusion_matrix, f1_score, accuracy_score
from sklearn.preprocessing import LabelEncoder
from xgboost import XGBClassifier

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from ai.features import select_features

DATA = ROOT / "data/generated/engine_training.csv"
MODEL = ROOT / "models/fault_classifier.joblib"
METRICS = ROOT / "models/fault_metrics.json"

df = pd.read_csv(DATA)
encoder = LabelEncoder()
y_all = encoder.fit_transform(df["fault_label"])

test_mask = df["mission_id"].str.endswith(("08", "09"))
train_df = df[~test_mask].copy()
test_df = df[test_mask].copy()

X_train = select_features(train_df)
X_test = select_features(test_df)
y_train = encoder.transform(train_df["fault_label"])
y_test = encoder.transform(test_df["fault_label"])

model = XGBClassifier(
    n_estimators=160,
    max_depth=6,
    learning_rate=0.07,
    subsample=0.9,
    colsample_bytree=0.9,
    objective="multi:softprob",
    eval_metric="mlogloss",
    random_state=42,
    n_jobs=-1,
)
model.fit(X_train, y_train)
pred = model.predict(X_test)

labels = np.arange(len(encoder.classes_))
report = classification_report(
    y_test,
    pred,
    labels=labels,
    target_names=encoder.classes_,
    output_dict=True,
    zero_division=0,
)

metrics = {
    "accuracy": round(float(accuracy_score(y_test, pred)), 4),
    "macro_f1": round(float(f1_score(y_test, pred, average="macro")), 4),
    "classes": list(encoder.classes_),
    "confusion_matrix": confusion_matrix(y_test, pred, labels=labels).tolist(),
    "classification_report": report,
    "split": "missions 00-07 train; missions 08-09 test for every scenario",
    "note": "Synthetic proof-of-concept metrics only.",
}

MODEL.parent.mkdir(exist_ok=True)
joblib.dump({"model": model, "encoder": encoder}, MODEL)
METRICS.write_text(json.dumps(metrics, indent=2))
print({"accuracy": metrics["accuracy"], "macro_f1": metrics["macro_f1"]})
