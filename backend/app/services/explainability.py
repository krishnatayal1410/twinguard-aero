from __future__ import annotations

from typing import Any

import numpy as np


FAULT_HINTS = {
    "lubrication": [
        "oil_pressure_residual",
        "oil_pressure",
        "oil_temp",
        "vibration",
    ],
    "overheating": [
        "cht_residual",
        "egt_residual",
        "cht",
        "egt",
        "oil_temp",
    ],
    "vibration": [
        "vibration",
        "oil_pressure_residual",
        "rpm",
    ],
    "sensor_drift": [
        "oil_pressure_residual",
        "cht_residual",
        "egt_residual",
    ],
}


def _pretty(name: str) -> str:
    replacements = {
        "cht": "CHT",
        "egt": "EGT",
        "rpm": "RPM",
        "rul": "RUL",
    }
    words = name.replace("_residual", " residual").replace("_", " ").split()
    return " ".join(replacements.get(word, word.capitalize()) for word in words)


def _combined_features(
    telemetry: dict,
    residuals: dict,
    health: dict,
) -> dict[str, float]:
    values: dict[str, float] = {}

    for source in (telemetry or {}, residuals or {}, health or {}):
        for key, value in source.items():
            if isinstance(value, (int, float)) and not isinstance(value, bool):
                values[str(key)] = float(value)

    return values


def _find_fault_model(model_service: Any) -> Any | None:
    candidates = [
        "fault_model",
        "fault_classifier",
        "classifier",
        "_fault_model",
        "_fault_classifier",
    ]

    for name in candidates:
        model = getattr(model_service, name, None)
        if model is not None:
            return model

    models = getattr(model_service, "models", None)
    if isinstance(models, dict):
        for key in ("fault", "fault_model", "classifier"):
            if models.get(key) is not None:
                return models[key]

    return None


def _feature_names(model: Any) -> list[str]:
    names = getattr(model, "feature_names_in_", None)
    if names is not None:
        return [str(name) for name in list(names)]

    try:
        booster = model.get_booster()
        names = booster.feature_names
        if names:
            return [str(name) for name in names]
    except Exception:
        pass

    return []


def _tree_shap(
    model: Any,
    features: dict[str, float],
    predicted_fault: str,
) -> list[dict] | None:
    try:
        import xgboost as xgb

        booster = model.get_booster()
        names = _feature_names(model)
        if not names:
            return None

        row = [float(features.get(name, 0.0)) for name in names]
        matrix = xgb.DMatrix(
            np.asarray([row], dtype=float),
            feature_names=names,
        )

        contributions = booster.predict(
            matrix,
            pred_contribs=True,
        )

        if contributions.ndim == 2:
            shap_values = contributions[0][:-1]
        elif contributions.ndim == 3:
            classes = list(getattr(model, "classes_", []))
            try:
                class_index = classes.index(predicted_fault)
            except ValueError:
                probabilities = model.predict_proba(np.asarray([row]))[0]
                class_index = int(np.argmax(probabilities))
            shap_values = contributions[0][class_index][:-1]
        else:
            return None

        ranked = sorted(
            zip(names, shap_values),
            key=lambda pair: abs(float(pair[1])),
            reverse=True,
        )[:5]

        total = sum(abs(float(value)) for _, value in ranked) or 1.0

        return [
            {
                "feature": name,
                "label": _pretty(name),
                "value": round(float(features.get(name, 0.0)), 4),
                "contribution": round(float(value), 5),
                "importance_pct": round(abs(float(value)) / total * 100.0, 1),
                "direction": "supports" if float(value) >= 0 else "opposes",
            }
            for name, value in ranked
        ]

    except Exception:
        return None


def _evidence_fallback(
    telemetry: dict,
    residuals: dict,
    predicted_fault: str,
) -> list[dict]:
    features = _combined_features(telemetry, residuals, {})
    preferred = FAULT_HINTS.get(predicted_fault, [])

    scores: list[tuple[str, float]] = []

    for name in preferred:
        value = abs(float(features.get(name, 0.0)))
        if value > 0:
            scores.append((name, value))

    if not scores:
        for name, value in residuals.items():
            if isinstance(value, (int, float)):
                scores.append((str(name), abs(float(value))))

    scores = sorted(scores, key=lambda item: item[1], reverse=True)[:5]
    total = sum(score for _, score in scores) or 1.0

    return [
        {
            "feature": name,
            "label": _pretty(name),
            "value": round(float(features.get(name, 0.0)), 4),
            "contribution": None,
            "importance_pct": round(score / total * 100.0, 1),
            "direction": "evidence",
        }
        for name, score in scores
    ]


def explain_prediction(
    model_service: Any,
    telemetry: dict,
    residuals: dict,
    health: dict,
    ai: dict,
) -> dict:
    predicted_fault = str(ai.get("fault", "normal"))
    confidence = float(ai.get("fault_probability", 0.0) or 0.0)

    features = _combined_features(telemetry, residuals, health)
    model = _find_fault_model(model_service)

    top_features = None
    method = "physics_evidence"

    if model is not None:
        top_features = _tree_shap(
            model=model,
            features=features,
            predicted_fault=predicted_fault,
        )
        if top_features:
            method = "xgboost_tree_shap"

    if not top_features:
        top_features = _evidence_fallback(
            telemetry=telemetry,
            residuals=residuals,
            predicted_fault=predicted_fault,
        )

    if predicted_fault in {"normal", "model_not_trained"}:
        summary = (
            "No dominant fault mechanism is currently identified. "
            "The explanation shows the strongest monitored deviations."
        )
    else:
        strongest = top_features[0]["label"] if top_features else "current telemetry"
        summary = (
            f"The predicted {predicted_fault.replace('_', ' ')} condition is "
            f"primarily supported by {strongest} and related engine evidence."
        )

    return {
        "method": method,
        "predicted_fault": predicted_fault,
        "confidence": round(confidence, 4),
        "summary": summary,
        "top_features": top_features,
        "scope": "synthetic_mvp_explanation",
    }
