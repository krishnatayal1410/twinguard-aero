from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field


MissionType = Literal[
    "patrol",
    "endurance",
    "high_altitude",
    "hot_weather",
]


class MissionLabRequest(BaseModel):
    duration_hours: float = Field(default=8.0, gt=0.0, le=30.0)
    cruise_altitude_m: float = Field(default=5500.0, ge=0.0, le=12000.0)
    ambient_temp_c: float = Field(default=35.0, ge=-40.0, le=60.0)
    average_throttle_pct: float = Field(default=75.0, ge=20.0, le=100.0)
    mission_type: MissionType = "endurance"


def _clamp(value: float, low: float, high: float) -> float:
    return max(low, min(high, value))


def _risk_label(score: float) -> str:
    if score >= 70:
        return "HIGH"
    if score >= 40:
        return "MEDIUM"
    return "LOW"


def analyze_mission(payload: MissionLabRequest, twin: dict) -> dict:
    telemetry = twin.get("telemetry") or {}
    health = twin.get("health") or {}
    ai = twin.get("ai") or {}

    current_health = float(health.get("overall", 95.0) or 95.0)
    current_rul_raw = ai.get("rul_hours")
    current_rul = float(current_rul_raw) if current_rul_raw is not None else None

    anomaly = bool(ai.get("anomaly", False))
    fault = str(ai.get("fault", "normal"))
    fault_probability = float(ai.get("fault_probability", 0.0) or 0.0)

    altitude_stress = _clamp(
        (payload.cruise_altitude_m - 2500.0) / 5000.0, 0.0, 1.4
    )
    thermal_stress = _clamp(
        (payload.ambient_temp_c - 20.0) / 30.0, 0.0, 1.3
    )
    throttle_stress = _clamp(
        (payload.average_throttle_pct - 50.0) / 45.0, 0.0, 1.3
    )
    endurance_stress = _clamp(
        payload.duration_hours / 10.0, 0.1, 1.5
    )

    mission_type_factor = {
        "patrol": 0.85,
        "endurance": 1.10,
        "high_altitude": 1.18,
        "hot_weather": 1.15,
    }[payload.mission_type]

    current_condition_penalty = _clamp(
        (100.0 - current_health) / 35.0, 0.0, 1.5
    )

    fault_penalty = 0.0
    if anomaly:
        fault_penalty += 0.35
    if fault not in {"normal", "model_not_trained"}:
        fault_penalty += 0.25 + 0.35 * _clamp(
            fault_probability, 0.0, 1.0
        )

    stress_index = (
        0.24 * altitude_stress
        + 0.23 * thermal_stress
        + 0.24 * throttle_stress
        + 0.29 * endurance_stress
    ) * mission_type_factor

    combined_stress = _clamp(
        stress_index + 0.45 * current_condition_penalty + fault_penalty,
        0.0,
        2.5,
    )

    life_consumption_multiplier = 1.0 + 1.25 * combined_stress
    effective_life_consumption = (
        payload.duration_hours * life_consumption_multiplier
    )

    projected_health_drop = _clamp(
        payload.duration_hours * (0.30 + 0.75 * combined_stress),
        1.0,
        45.0,
    )
    projected_health = round(
        _clamp(current_health - projected_health_drop, 0.0, 100.0),
        1,
    )

    projected_rul = None
    if current_rul is not None:
        projected_rul = round(
            max(0.0, current_rul - effective_life_consumption), 1
        )

    thermal_risk_score = _clamp(
        18.0
        + 40.0 * thermal_stress
        + 22.0 * throttle_stress
        + 18.0 * altitude_stress
        + (12.0 if fault == "overheating" else 0.0),
        0.0,
        100.0,
    )

    mechanical_risk_score = _clamp(
        12.0
        + 28.0 * endurance_stress
        + 20.0 * throttle_stress
        + 20.0 * current_condition_penalty
        + (25.0 if fault in {"vibration", "lubrication"} else 0.0),
        0.0,
        100.0,
    )

    overall_risk_score = _clamp(
        20.0
        + 35.0 * combined_stress
        + 0.45 * (100.0 - projected_health)
        + (12.0 if anomaly else 0.0),
        0.0,
        100.0,
    )

    if projected_rul is not None:
        if projected_rul < payload.duration_hours:
            overall_risk_score = max(overall_risk_score, 92.0)
        elif projected_rul < payload.duration_hours * 2.0:
            overall_risk_score = max(overall_risk_score, 75.0)

    if projected_health < 60.0:
        overall_risk_score = max(overall_risk_score, 82.0)
    elif projected_health < 75.0:
        overall_risk_score = max(overall_risk_score, 62.0)

    overall_label = _risk_label(overall_risk_score)

    if overall_label == "HIGH":
        decision = "NO_GO_REVIEW_REQUIRED"
        recommendation = (
            "High predicted mission stress. Engineering review and a safer "
            "mission profile are recommended before assignment."
        )
    elif overall_label == "MEDIUM":
        decision = "PROCEED_WITH_CAUTION"
        recommendation = (
            "Mission is possible in this synthetic model, but elevated stress "
            "is predicted. Consider reducing altitude, duration or load."
        )
    else:
        decision = "MISSION_PROFILE_ACCEPTABLE"
        recommendation = (
            "Current Digital Twin state is compatible with this nominal "
            "mission profile in the synthetic MVP model."
        )

    return {
        "model_scope": "synthetic_mvp_decision_support",
        "mission": payload.model_dump(),
        "current_state": {
            "health": round(current_health, 1),
            "rul_hours": round(current_rul, 1) if current_rul is not None else None,
            "fault": fault,
            "anomaly": anomaly,
            "rpm": telemetry.get("rpm"),
        },
        "prediction": {
            "post_mission_health": projected_health,
            "post_mission_rul_hours": projected_rul,
            "effective_life_consumption_hours": round(
                effective_life_consumption, 1
            ),
            "stress_index": round(combined_stress, 3),
        },
        "risk": {
            "overall": overall_label,
            "overall_score": round(overall_risk_score, 1),
            "thermal": _risk_label(thermal_risk_score),
            "thermal_score": round(thermal_risk_score, 1),
            "mechanical": _risk_label(mechanical_risk_score),
            "mechanical_score": round(mechanical_risk_score, 1),
        },
        "decision": decision,
        "recommendation": recommendation,
        "counterfactual": {
            "lower_altitude_m": round(max(1500.0, payload.cruise_altitude_m - 1000.0)),
            "shorter_duration_hours": round(max(1.0, payload.duration_hours - 2.0), 1),
            "reduced_throttle_pct": round(max(45.0, payload.average_throttle_pct - 10.0)),
            "message": (
                "Try one or more of these lower-stress values and compare "
                "the predicted risk."
            ),
        },
    }
