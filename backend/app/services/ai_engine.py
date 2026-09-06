from __future__ import annotations
from pathlib import Path
import json
import math
import os

import joblib
import numpy as np

FEATURES = [
    "rpm", "throttle", "cht", "egt", "oil_pressure", "oil_temperature", "fuel_flow", "vibration",
    "battery_voltage", "alternator_voltage", "injection_timing", "altitude", "ambient_temperature",
    "cht_residual", "egt_residual", "oil_pressure_residual", "oil_temperature_residual", "fuel_flow_residual",
    "vibration_residual", "battery_voltage_residual", "alternator_voltage_residual", "injection_timing_residual",
]

SUPPORTED_LABELS = [
    "normal", "lubrication", "overheating", "cooling_degradation", "vibration", "sensor_drift",
    "injector", "misfire", "combustion_instability", "alternator_degradation",
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
        try:
            feature_order = json.loads((model_path / "feature_order.json").read_text())
            self.artifact_features = feature_order if isinstance(feature_order, list) else []
        except Exception:
            self.artifact_features = []
        try:
            metrics = json.loads((model_path / "synthetic_metrics.json").read_text())
            self.synthetic_metrics = metrics if isinstance(metrics, dict) else {}
        except Exception:
            self.synthetic_metrics = {}

        self.features_match = self.artifact_features == FEATURES
        self.labels_match = self.labels == SUPPORTED_LABELS
        self.artifacts_compatible = self.features_match and self.labels_match
        self.artifact_files = {
            "anomaly": (model_path / "anomaly_model.joblib").exists(),
            "fault": (model_path / "fault_model.joblib").exists(),
            "rul": (model_path / "rul_model.joblib").exists(),
        }

        self.anomaly = safe("anomaly_model.joblib") if self.features_match else None
        self.native_ml = self.native_ml_requested and self.artifacts_compatible
        self.fault = safe("fault_model.joblib") if self.native_ml else None
        self.rul = safe("rul_model.joblib") if self.native_ml else None

        warnings = []
        if not self.features_match and self.artifact_features:
            warnings.append("Packaged models use an older feature contract")
        if not self.labels_match and self.labels:
            warnings.append("packaged classifier uses an older fault taxonomy")
        if self.native_ml_requested and not self.artifacts_compatible:
            warnings.append("native ML was requested but incompatible artifacts were rejected")
        self.model_warning = "; ".join(warnings) + ". Retrain the synthetic model pack before enabling native ML." if warnings else None

    def vector(self, telemetry, residuals):
        merged = {**telemetry, **residuals}
        return np.asarray([[float(merged.get(k, 0)) for k in FEATURES]], dtype=float)

    @staticmethod
    def _softmax_scores(scores: dict[str, float]) -> dict[str, float]:
        peak = max(scores.values()) if scores else 0.0
        exp = {k: math.exp((v - peak) * 2.0) for k, v in scores.items()}
        total = sum(exp.values()) or 1.0
        return {k: v / total for k, v in exp.items()}

    def predict(self, t, r, trends=None):
        trends = trends or {}
        x = self.vector(t, r)
        if self.anomaly is not None:
            try:
                raw = float(-self.anomaly.score_samples(x)[0])
                anomaly = bool(self.anomaly.predict(x)[0] == -1)
                anomaly_score = max(0.0, min(1.0, (raw - .35) / .45))
            except Exception:
                anomaly_score, anomaly = self._engineering_anomaly(t, r, trends)
        else:
            anomaly_score, anomaly = self._engineering_anomaly(t, r, trends)

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
                fault, confidence, probs = self._engineering_fault(t, r, trends, anomaly)
        else:
            fault, confidence, probs = self._engineering_fault(t, r, trends, anomaly)

        if self.rul is not None:
            try:
                rul = max(1.0, float(self.rul.predict(x)[0]))
                rul_basis = "synthetic_xgboost_regressor"
            except Exception:
                rul = self._engineering_rul(t, r, trends)
                rul_basis = "engineering_surrogate"
        else:
            rul = self._engineering_rul(t, r, trends)
            rul_basis = "engineering_surrogate"

        interval = self._rul_interval(rul, rul_basis, trends, anomaly_score)
        evidence = self.explain(t, r, fault)
        return {
            "anomaly": anomaly,
            "anomaly_score": anomaly_score,
            "probable_fault": fault,
            "fault_confidence": float(confidence),
            "fault_probabilities": probs,
            "rul_hours": rul,
            "rul_interval_hours": interval,
            "rul_uncertainty_hours": round((interval["upper"] - interval["lower"]) / 2, 2),
            "evidence": evidence,
            "model_state": "NATIVE_ML" if self.native_ml and self.fault is not None else "ENGINEERING_FALLBACK",
            "validation_scope": "SYNTHETIC_PROOF_OF_CONCEPT",
            "rul_basis": rul_basis,
            "rul_interval_basis": interval["basis"],
            "feature_contract": "aero-piston-v2",
            "model_warning": self.model_warning,
        }

    def runtime_status(self):
        return {
            "active_mode": "NATIVE_ML" if self.native_ml and self.fault is not None and self.rul is not None else "ENGINEERING_FALLBACK",
            "native_ml_requested": self.native_ml_requested,
            "artifact_contract_compatible": self.artifacts_compatible,
            "feature_contract": "aero-piston-v2",
            "packaged_artifacts": dict(self.artifact_files),
            "active_models": {
                "anomaly": self.anomaly is not None,
                "fault": self.fault is not None,
                "rul": self.rul is not None,
            },
            "synthetic_metrics_available": bool(self.synthetic_metrics),
            "validation_scope": "SYNTHETIC_PROOF_OF_CONCEPT",
            "warning": self.model_warning,
        }

    def _rul_interval(self, estimate, basis, trends, anomaly_score):
        estimate = max(0.0, float(estimate))
        if basis == "synthetic_xgboost_regressor":
            rmse = float(self.synthetic_metrics.get("rul_rmse", 12.5) or 12.5)
            base_half_width = max(12.0, 1.65 * rmse)
            interval_basis = "synthetic_validation_rmse_plus_state_uncertainty"
        else:
            base_half_width = max(20.0, estimate * .24)
            interval_basis = "engineering_surrogate_conservative_band"
        trend_load = (
            abs(float(trends.get("health_index_per_min", 0.0))) * .55
            + abs(float(trends.get("oil_pressure_per_min", 0.0))) * 2.4
            + abs(float(trends.get("cht_per_min", 0.0))) * .08
            + abs(float(trends.get("vibration_per_min", 0.0))) * 4.0
        )
        half_width = min(max(8.0, base_half_width + trend_load + 7.0 * float(anomaly_score)), max(25.0, estimate * .55))
        return {
            "lower": round(max(0.0, estimate - half_width), 2),
            "estimate": round(estimate, 2),
            "upper": round(estimate + half_width, 2),
            "basis": interval_basis,
            "calibrated_probability_interval": False,
        }

    def _engineering_anomaly(self, t, r, trends):
        residual_evidence = (
            abs(r["cht_residual"]) / 35 + abs(r["egt_residual"]) / 80 + abs(r["oil_pressure_residual"]) / 1.5
            + max(0, t["vibration"] - .3) / .7 + abs(r.get("battery_voltage_residual", 0)) / 2.2
            + abs(r.get("alternator_voltage_residual", 0)) / 2.5 + abs(r.get("injection_timing_residual", 0)) / 3.0
        )
        trend_evidence = (
            max(0, -float(trends.get("oil_pressure_per_min", 0))) / 1.3
            + max(0, float(trends.get("cht_per_min", 0))) / 45
            + max(0, float(trends.get("oil_temperature_per_min", 0))) / 30
            + max(0, float(trends.get("vibration_per_min", 0))) / .45
        )
        score = max(0.0, min(1.0, (residual_evidence + .45 * trend_evidence) / 3.2))
        return score, score > .32

    def _engineering_fault(self, t, r, trends, anomaly):
        oil_drop = max(0, -float(trends.get("oil_pressure_per_min", 0)))
        cht_rise = max(0, float(trends.get("cht_per_min", 0)))
        oil_temp_rise = max(0, float(trends.get("oil_temperature_per_min", 0)))
        vibration_rise = max(0, float(trends.get("vibration_per_min", 0)))
        alternator_drop = max(0, -float(trends.get("alternator_voltage_per_min", 0)))
        heur = {
            "lubrication": max(0, -r["oil_pressure_residual"]) / 1.5 + max(0, r["oil_temperature_residual"]) / 30 + oil_drop / 1.2,
            "overheating": max(0, r["cht_residual"]) / 35 + max(0, r["egt_residual"]) / 80 + cht_rise / 42,
            "cooling_degradation": max(0, r["cht_residual"]) / 38 + max(0, r["oil_temperature_residual"]) / 28 + oil_temp_rise / 28,
            "vibration": max(0, t["vibration"] - .3) / .7 + vibration_rise / .4,
            "sensor_drift": max(0, abs(r["oil_pressure_residual"]) - .8) / 1.5,
            "injector": max(0, abs(r["fuel_flow_residual"]) - 1) / 4 + max(0, abs(r["egt_residual"]) - 35) / 100 + abs(r.get("injection_timing_residual", 0)) / 5,
            "misfire": max(0, t["vibration"] - .35) / .8 + max(0, abs(r["egt_residual"]) - 30) / 120,
            "combustion_instability": max(0, abs(r["egt_residual"]) - 20) / 90 + max(0, t["vibration"] - .28) / .75 + max(0, abs(r["fuel_flow_residual"]) - .5) / 4,
            "alternator_degradation": max(0, -r.get("alternator_voltage_residual", 0)) / 3 + max(0, -r.get("battery_voltage_residual", 0)) / 2 + alternator_drop / 4,
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
    def _engineering_rul(t, r, trends):
        worsening = (
            max(0, -float(trends.get("health_index_per_min", 0))) * 1.8
            + max(0, -float(trends.get("oil_pressure_per_min", 0))) * 5
            + max(0, float(trends.get("cht_per_min", 0))) * .25
        )
        penalty = (
            abs(r["cht_residual"]) * .6 + abs(r["egt_residual"]) * .15 + max(0, -r["oil_pressure_residual"]) * 24
            + max(0, t["vibration"] - .3) * 85 + max(0, -r.get("alternator_voltage_residual", 0)) * 5 + worsening
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
            "injection_timing_residual": abs(r.get("injection_timing_residual", 0)) / 3,
        }
        total = sum(candidates.values()) or 1
        return [
            {"feature": k, "weight": v / total, "value": float(r.get(k, 0))}
            for k, v in sorted(candidates.items(), key=lambda kv: kv[1], reverse=True)[:5]
        ]
