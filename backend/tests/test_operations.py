from datetime import UTC, datetime, timedelta
from types import SimpleNamespace

import pytest
from app.main import app
from app.services.operations import AuthLimiter, validate_live_sample
from fastapi import HTTPException
from fastapi.testclient import TestClient


def test_live_timestamp_rejection():
    now = datetime.now(UTC)
    for timestamp in [now + timedelta(minutes=5), now - timedelta(minutes=5), now.replace(tzinfo=None)]:
        with pytest.raises(HTTPException) as error:
            validate_live_sample(SimpleNamespace(engine_id="ENGINE-01", timestamp=timestamp), None)
        assert error.value.status_code == 422
    sample = SimpleNamespace(engine_id="ENGINE-01", timestamp=now)
    validate_live_sample(sample, None)
    with pytest.raises(HTTPException) as error:
        validate_live_sample(sample, {"timestamp": now.isoformat()})
    assert error.value.status_code == 409
    with pytest.raises(HTTPException) as error:
        validate_live_sample(SimpleNamespace(engine_id="OTHER", timestamp=now), None)
    assert error.value.status_code == 403


def test_auth_limit_and_expiry(monkeypatch):
    limiter = AuthLimiter(limit=2, window=60)
    clock = [100]
    monkeypatch.setattr("app.services.operations.time.monotonic", lambda: clock[0])
    request = SimpleNamespace(
        url=SimpleNamespace(path="/api/v1/auth/signin"),
        method="POST",
        client=SimpleNamespace(host="127.0.0.1"),
    )
    assert limiter.allow(request)
    assert limiter.allow(request)
    assert not limiter.allow(request)
    clock[0] += 61
    assert limiter.allow(request)


def test_readiness_and_malformed_body_length():
    client = TestClient(app)
    assert client.get("/ready").json()["database"] == "connected"
    assert client.post("/api/v1/auth/signin", headers={"content-length": "oops"}).status_code == 400
    assert client.post("/api/v1/auth/signin", headers={"content-length": "999999"}).status_code == 413


def test_readiness_database_failure(monkeypatch):
    def unavailable():
        raise RuntimeError("database unavailable")

    monkeypatch.setattr("app.main.engine.connect", unavailable)
    result = TestClient(app).get("/ready")
    assert result.status_code == 503
    assert "RuntimeError" not in result.text


def test_production_requires_credentials_and_persistent_storage(monkeypatch):
    from app.services.operations import check_production

    config = SimpleNamespace(
        environment="production",
        ingest_api_key="",
        cors_origins=("https://app.example.com",),
        trusted_hosts=("api.example.com",),
        database_url="postgresql://placeholder",
        mqtt_enabled=False,
    )
    monkeypatch.setattr("app.services.operations.settings", config)
    with pytest.raises(RuntimeError, match="INGEST_KEY"):
        check_production()
    config.ingest_api_key = "x" * 40
    check_production()
    config.database_url = "sqlite:///volatile.db"
    with pytest.raises(RuntimeError, match="PostgreSQL"):
        check_production()
