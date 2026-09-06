from __future__ import annotations
from pathlib import Path
import json
import math
import os

import joblib
import numpy as np

# Keep the packaged anomaly model on its original feature contract so older
# synthetic model artifacts cannot crash a newer runtime. New fault/RUL models
# are only enabled when their label manifest matches the current aero-piston
# taxonomy.
FEATURES = [
    "rpm", "throttle", "cht", "egt", "oil_pressure", "oil_temperature", "fuel_flow", "vibration",
    "altitude", "ambient_temperature", "cht_residual", "egt_residual", "oil_pressure_residual",
    "oil_temperature_residual", "fuel_flow_residual", "vibration_residual",
]
SUPPORTED_LABELS = [
    "normal",
    "lubrication",
    "overheating",
    "cooling_degradation",
    "vibration",
    "sensor_drift",
    "injector",
    "misfire",
    "combustion_instability",
    "alternator_degradation",
]


class AIEngine:
    def __init__(self, model_dir="./models"):
        model_path = Path(model_dir)
        self.native_ml_requested = os.getenv("TWINGUARD_NATIVE_ML", "0") == "1"

        def safe(name):
            try:
                path = model_path / name
                return joblib.load(path) if path.exists() else None
            except BaseException:
                return None

        try:
            labels = json.loads((model_path / "fault_labels.json").read_text())
            self.labels = labels if isinstance(labels, list) else []
        except Exception:
            self.labels = []

        # Isolation Forest remains backward compatible with the legacy feature
        # contract. Fault/RUL artifacts are stricter because a stale label map
        # can silently turn one engine condition into another.
        self.anomaly = safe("anomaly_model.joblib")
        labels_match = self.labels == SUPPORTED_LABELS
        self.native_ml = self.native_ml_requested and labels_match
        self.fault = safe("fault_model.joblib") if self.native_ml else None
        self.rul = safe("rul_model.joblib") if self.native_ml else None
        self.model_warning = None
        if self.native_ml_requested and not labels_match:
            self.model_warning = "Packaged fault/RUL artifacts use an older fault taxonomy; stable engineering fallback is active until models are retrained."

    def vector(self, telemetry, residuals):
        merged = {**telemetry, **residuals}
        return np.asarray([[float(merged.get(k, 0)) for k in FEATURES]], dtype=float)

    @staticmethod
    def _softmax_scores(scores: dict[str, float]) -> dict[str, float]:
        peak = max(scores.values()) if scores else 0.0
        exp = {k: math.exp((v - peak) * 2.0) for k, v in scores.items()}
        total = sum(exp.values()) or 1.0
        return {k: v / total for k, v in exp.items()}

    def predict(self, t, r):
        x = self.vector(t, r)
        if self.anomaly is not None:
            try:
                raw = float(-self.anomaly.score_samples(x)[0])
                anomaly = bool(self.anomaly.predict(x)[0] == -1)
                anomaly_score = max(0.0, min(1.0, (raw - .35) / .45))
            except Exception:
                anomaly_score, anomaly = self._engineering_anomaly(t, r)
        else:
            anomaly_score, anomaly = self._engineering_anomaly(t, r)

        probs: dict[str, float]
        if self.fault is not None:
            try:
                pp = self.fault.predict_proba(x)[0]
                classes = [
                    self.labels[int(c)] if str(c).lstrip("-").isdigit() and int(c) < len(self.labels) else str(c)
                    for c in self.fault.classes_
                ]
                probs = {c: float(v) for c, v in zip(classes, pp)}
                fault = max(probs, key=probs.get)
                confidence = probs[fault]
            except Exception:
                fault, confidence, probs = self._engineering_fault(t, r, anomaly)
        else:
            fault, confidence, probs = self._engineering_fault(t, r, anomaly)

        if self.rul is not None:
            try:
                rul = max(1.0, float(self.rul.predict(x)[0]))
                rul_basis = "synthetic_xgboost_regressor"
            except Exception:
                rul = self._engineering_rul(t, r)
                rul_basis = "engineering_surrogate"
        else:
            rul = self._engineering_rul(t, r)
            rul_basis = "engineering_surrogate"

        evidence = self.explain(t, r, fault)
        return {
            "anomaly": anomaly,
            "anomaly_score": anomaly_score,
            "probable_fault": fault,
            "fault_confidence": float(confidence),
            "fault_probabilities": probs,
            "rul_hours": rul,
            "evidence": evidence,
            "model_state": "NATIVE_ML" if self.native_ml and self.fault is not None else "ENGINEERING_FALLBACK",
            "validation_scope": "SYNTHETIC_PROOF_OF_CONCEPT",
            "rul_basis": rul_basis,
            "model_warning": self.model_warning,
        }

    def _engineering_anomaly(self, t, r):
        z = (
            abs(r["cht_residual"]) / 35
            + abs(r["egt_residual"]) / 80
            + abs(r["oil_pressure_residual"]) / 1.5
            + max(0, t["vibration"] - .3) / .7
            + abs(r.get("battery_voltage_residual", 0)) / 2.2
            + abs(r.get("alternator_voltage_residual", 0)) / 2.5
        )
        score = max(0.0, min(1.0, z / 2.6))
        return score, score > .32

    def _engineering_fault(self, t, r, anomaly):
        heur = {
            "lubrication": max(0, -r["oil_pressure_residual"]) / 1.5 + max(0, r["oil_temperature_residual"]) / 30,
            "overheating": max(0, r["cht_residual"]) / 35 + max(0, r["egt_residual"]) / 80,
            "cooling_degradation": max(0, r["cht_residual"]) / 38 + max(0, r["oil_temperature_residual"]) / 28,
            "vibration": max(0, t["vibration"] - .3) / .7,
            "sensor_drift": max(0, abs(r["oil_pressure_residual"]) - .8) / 1.5,
            "injector": max(0, abs(r["fuel_flow_residual"]) - 1) / 4 + max(0, abs(r["egt_residual"]) - 35) / 100,
            "misfire": max(0, t["vibration"] - .35) / .8 + max(0, abs(r["egt_residual"]) - 30) / 120,
            "combustion_instability": max(0, abs(r["egt_residual"]) - 20) / 90 + max(0, t["vibration"] - .28) / .75 + max(0, abs(r["fuel_flow_residual"]) - .5) / 4,
            "alternator_degradation": max(0, -r.get("alternator_voltage_residual", 0)) / 3 + max(0, -r.get("battery_voltage_residual", 0)) / 2,
            "normal": .65,
        }
        fault = max(heur, key=heur.get)
        probs = self._softmax_scores(heur)
        confidence = probs[fault]
        if not anomaly:
            fault = "normal"
            confidence = max(confidence, .82)
            probs["normal"] = confidence
        return fault, confidence, probs

    @staticmethod
    def _engineering_rul(t, r):
        penalty = (
            abs(r["cht_residual"]) * .6
            + abs(r["egt_residual"]) * .15
            + max(0, -r["oil_pressure_residual"]) * 24
            + max(0, t["vibration"] - .3) * 85
            + max(0, -r.get("alternator_voltage_residual", 0)) * 5
        )
        return max(8.0, 190 - penalty - float(t.get("operating_hours", 0)) * .08)

    def explain(self, t, r, fault):
        candidates = {
            "oil_pressure_residual": abs(r["oil_pressure_residual"]) / 1.5,
            "oil_temperature_residual": abs(r["oil_temperature_residual"]) / 30,
            "cht_residual": abs(r["cht_residual"]) / 35,
            "egt_residual": abs(r["egt_residual"]) / 80,
            "fuel_flow_residual": abs(r["fuel_flow_residual"]) / 4,
            "vibration_residual": abs(r["vibration_residual"]) / .65,
            "battery_voltage_residual": abs(r.get("battery_voltage_residual", 0)) / 2,
            "alternator_voltage_residual": abs(r.get("alternator_voltage_residual", 0)) / 2.5,
        }
        total = sum(candidates.values()) or 1
        return [
            {"feature": k, "weight": v / total, "value": float(r.get(k, 0))}
            for k, v in sorted(candidates.items(), key=lambda kv: kv[1], reverse=True)[:5]
        ]
