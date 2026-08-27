from backend.app.services.explainability import explain_prediction


class EmptyModelService:
    pass


def test_explanation_fallback_returns_ranked_evidence():
    result = explain_prediction(
        model_service=EmptyModelService(),
        telemetry={
            "oil_pressure": 3.5,
            "oil_temp": 106.0,
            "vibration": 0.42,
        },
        residuals={
            "oil_pressure_residual": -1.1,
            "cht_residual": 2.0,
        },
        health={"overall": 84.0},
        ai={
            "fault": "lubrication",
            "fault_probability": 0.91,
        },
    )

    assert result["method"] == "physics_evidence"
    assert result["predicted_fault"] == "lubrication"
    assert len(result["top_features"]) > 0
    assert "summary" in result
