"""Operational checks for the single-process, single-engine deployment."""

from __future__ import annotations

import time
from collections import OrderedDict, deque
from datetime import UTC, datetime
from threading import Lock

from fastapi import HTTPException

from ..core import settings


def check_production():
    if settings.environment != "production":
        return
    if len(settings.ingest_api_key) < 32:
        raise RuntimeError("Production requires TWINGUARD_INGEST_KEY with at least 32 characters")
    if "*" in settings.cors_origins or "*" in settings.trusted_hosts:
        raise RuntimeError("Production requires explicit allowed hosts and CORS origins")
    if settings.database_url.startswith("sqlite"):
        raise RuntimeError("Production requires persistent PostgreSQL")
    if settings.mqtt_enabled and (not settings.mqtt_tls or not settings.mqtt_username):
        raise RuntimeError("Production MQTT requires TLS and broker credentials")


def validate_live_sample(sample, previous):
    if sample.engine_id != settings.engine_id:
        raise HTTPException(403, "Engine ID is not authorized")
    timestamp = sample.timestamp
    if timestamp.tzinfo is None:
        raise HTTPException(422, "Telemetry timestamp must include a timezone")
    age = (datetime.now(UTC) - timestamp).total_seconds()
    if age < -5 or age > settings.telemetry_stale_seconds:
        raise HTTPException(
            422,
            "Telemetry timestamp is outside the live freshness window; use offline evaluation for recordings",
        )
    if previous:
        prior = previous["timestamp"]
        if isinstance(prior, str):
            prior = datetime.fromisoformat(prior.replace("Z", "+00:00"))
        if prior.tzinfo is None:
            prior = prior.replace(tzinfo=UTC)
        if timestamp <= prior:
            raise HTTPException(409, "Duplicate or out-of-order telemetry timestamp")


class AuthLimiter:
    """Bounded process-local limiter; deploy one worker and add edge limits at scale."""

    def __init__(self, limit=20, window=60):
        self.limit = limit
        self.window = window
        self.entries = OrderedDict()
        self.lock = Lock()

    def allow(self, request):
        if request.url.path not in {"/api/v1/auth/signin", "/api/v1/auth/signup"} or request.method != "POST":
            return True
        key = request.client.host if request.client else "unknown"
        now = time.monotonic()
        with self.lock:
            queue = self.entries.setdefault(key, deque())
            self.entries.move_to_end(key)
            while queue and queue[0] <= now - self.window:
                queue.popleft()
            if len(queue) >= self.limit:
                return False
            queue.append(now)
            while len(self.entries) > 10000:
                self.entries.popitem(last=False)
            return True


request_limiter = AuthLimiter()
