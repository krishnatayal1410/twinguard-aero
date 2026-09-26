import json
from types import SimpleNamespace

import numpy as np
import pytest
from app.services.ai_engine import FEATURES, SUPPORTED_LABELS, AIEngine
from app.services.physics import PhysicsEngine


def nominal_sample():
    telemetry = {
        "rpm": 4100,
        "throttle": 70,
        "altitude": 4300,
        "ambient_temperature": 25,
        "oil_temperature": 108,
        "operating_hours": 42,
    }
    physics = PhysicsEngine()
    telemetry.update(physics.expected(telemetry))
    return telemetry, physics.residuals(telemetry, physics.expected(telemetry))


def test_nominal_engineering_scores_are_a_normalized_distribution(monkeypatch):
    monkeypatch.setenv("TWINGUARD_NATIVE_ML", "0")
    prediction = AIEngine("models").predict(*nominal_sample())
    probabilities = prediction["fault_probabilities"]
    assert prediction["probable_fault"] == "normal"
    assert sum(probabilities.values()) == pytest.approx(1.0)
    assert all(0 <= probability <= 1 for probability in probabilities.values())
    assert prediction["fault_confidence"] == probabilities["normal"]
    assert prediction["fault_probability_basis"] == "normalized_engineering_scores_uncalibrated"


@pytest.mark.parametrize("broken_component", ["anomaly", "fault", "rul"])
def test_native_failure_uses_consistent_fallback_with_truthful_provenance(monkeypatch, broken_component):
    monkeypatch.setenv("TWINGUARD_NATIVE_ML", "0")
    engine = AIEngine("models")
    expected = engine.predict(*nominal_sample())
    engine.native_ml = True
    engine.labels = SUPPORTED_LABELS
    engine.anomaly = SimpleNamespace(
        score_samples=lambda x: np.asarray([-0.4]),
        predict=lambda x: np.asarray([1]),
    )
    engine.fault = SimpleNamespace(
        classes_=np.arange(len(SUPPORTED_LABELS)),
        predict_proba=lambda x: np.asarray([[0.91, *([0.01] * 9)]]),
    )
    engine.rul = SimpleNamespace(predict=lambda x: np.asarray([170.0]))

    def fail(_):
        raise RuntimeError("inference unavailable")

    method = {"anomaly": "score_samples", "fault": "predict_proba", "rul": "predict"}[broken_component]
    setattr(getattr(engine, broken_component), method, fail)
    prediction = engine.predict(*nominal_sample())
    assert prediction["rul_hours"] == expected["rul_hours"]
    assert prediction["fault_probabilities"] == expected["fault_probabilities"]
    assert prediction["rul_basis"] == "engineering_surrogate"
    assert prediction["model_state"] == "ENGINEERING_FALLBACK"
    assert "Native inference failed" in prediction["model_warning"]
    assert engine.runtime_status()["active_mode"] == "ENGINEERING_FALLBACK"


@pytest.mark.parametrize("invalid_value", [float("nan"), float("inf")])
def test_nonfinite_native_output_cannot_escape_in_json(monkeypatch, invalid_value):
    monkeypatch.setenv("TWINGUARD_NATIVE_ML", "0")
    engine = AIEngine("models")
    engine.native_ml = True
    engine.labels = SUPPORTED_LABELS
    engine.anomaly = SimpleNamespace(
        score_samples=lambda x: np.asarray([-0.4]),
        predict=lambda x: np.asarray([1]),
    )
    engine.fault = SimpleNamespace(
        classes_=np.arange(len(SUPPORTED_LABELS)),
        predict_proba=lambda x: np.asarray([[0.91, *([0.01] * 9)]]),
    )
    engine.rul = SimpleNamespace(predict=lambda x: np.asarray([invalid_value]))
    prediction = engine.predict(*nominal_sample())
    assert prediction["model_state"] == "ENGINEERING_FALLBACK"
    json.dumps(prediction, allow_nan=False)


def test_incomplete_native_pack_is_disabled_as_a_unit(monkeypatch, tmp_path):
    monkeypatch.setenv("TWINGUARD_NATIVE_ML", "1")
    (tmp_path / "fault_labels.json").write_text(json.dumps(SUPPORTED_LABELS))
    (tmp_path / "feature_order.json").write_text(json.dumps(FEATURES))
    for filename in ("anomaly_model.joblib", "fault_model.joblib"):
        (tmp_path / filename).touch()
    monkeypatch.setattr("app.services.ai_engine.joblib.load", lambda path: object())
    engine = AIEngine(tmp_path)
    assert not engine.native_ml
    assert engine.anomaly is engine.fault is engine.rul is None
    assert "incomplete" in engine.runtime_status()["warning"]
