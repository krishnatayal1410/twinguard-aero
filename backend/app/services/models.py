from pathlib import Path
import joblib
import numpy as np
import pandas as pd

MODEL_DIR = Path(__file__).resolve().parents[3] / "models"

FEATURE_COLUMNS = [
    "rpm",
    "throttle",
    "altitude",
    "ambient_temp",
    "cht",
    "egt",
    "oil_pressure",
    "oil_temp",
    "fuel_flow",
    "vibration",
    "battery_voltage",
    "cht_residual",
    "egt_residual",
    "oil_pressure_residual",
    "fuel_flow_residual",
]


class ModelService:
    def __init__(self):
        self.anomaly = None
        self.fault_bundle = None
        self.rul = None
        self.reload()

    def reload(self):
        anomaly_path = MODEL_DIR / "anomaly.joblib"
        fault_path = MODEL_DIR / "fault_classifier.joblib"
        rul_path = MODEL_DIR / "rul.joblib"

        self.anomaly = joblib.load(anomaly_path) if anomaly_path.exists() else None
        self.fault_bundle = joblib.load(fault_path) if fault_path.exists() else None
        self.rul = joblib.load(rul_path) if rul_path.exists() else None

    def _frame(self, telemetry: dict, residuals: dict) -> pd.DataFrame:
        merged = {**telemetry, **residuals}
        return pd.DataFrame(
            [[float(merged[name]) for name in FEATURE_COLUMNS]],
            columns=FEATURE_COLUMNS,
        )

    def predict(self, telemetry: dict, residuals: dict, health: dict) -> dict:
        x = self._frame(telemetry, residuals)

        output = {
            "anomaly": False,
            "anomaly_score": 0.0,
            "fault": "model_not_trained",
            "fault_probability": 0.0,
            "fault_probabilities": {},
            "rul_hours": None,
        }

        if self.anomaly is not None:
            prediction = int(self.anomaly.predict(x)[0])
            raw = float(-self.anomaly.decision_function(x)[0])
            output["anomaly"] = prediction == -1
            output["anomaly_score"] = round(max(0.0, raw), 4)

        if self.fault_bundle is not None:
            model = self.fault_bundle["model"]
            encoder = self.fault_bundle["encoder"]
            probabilities = model.predict_proba(x)[0]
            best = int(np.argmax(probabilities))
            names = encoder.inverse_transform(np.arange(len(probabilities)))
            output["fault"] = str(names[best])
            output["fault_probability"] = round(float(probabilities[best]), 4)
            output["fault_probabilities"] = {
                str(name): round(float(prob), 4)
                for name, prob in zip(names, probabilities)
            }

        if self.rul is not None:
            xrul = x.copy()
            xrul["health_overall"] = float(health.get("overall", 100.0))
            output["rul_hours"] = round(
                max(0.0, float(self.rul.predict(xrul)[0])),
                1,
            )

        return output


model_service = ModelService()
