from __future__ import annotations

import os
from dataclasses import dataclass


def _env_flag(name: str, default: str) -> bool:
    return os.getenv(name, default).strip().lower() in {"1", "true", "yes", "on"}


_RUNTIME_ENV = os.getenv("TWINGUARD_ENV", "development").strip().lower()


@dataclass(frozen=True)
class Settings:
    app_name: str = "TwinGuard Aero"
    version: str = "3.2.0"
    environment: str = _RUNTIME_ENV
    engine_id: str = os.getenv("TWINGUARD_ENGINE_ID", "ENGINE-01")
    database_url: str = os.getenv("DATABASE_URL", "sqlite:///./data/runtime/twinguard.db")
    cors_origins: tuple[str, ...] = tuple(
        x.strip()
        for x in os.getenv("CORS_ORIGINS", "http://localhost:5173,http://127.0.0.1:5173").split(",")
        if x.strip()
    )
    trusted_hosts: tuple[str, ...] = tuple(
        x.strip()
        for x in os.getenv("TRUSTED_HOSTS", "localhost,127.0.0.1,testserver").split(",")
        if x.strip()
    )
    ingest_api_key: str = os.getenv("TWINGUARD_INGEST_KEY", "")
    max_body_bytes: int = int(os.getenv("MAX_BODY_BYTES", "131072"))
    model_dir: str = os.getenv("MODEL_DIR", "./models")

    allow_signup: bool = _env_flag("ALLOW_SIGNUP", "0" if _RUNTIME_ENV == "production" else "1")

    telemetry_stale_seconds: float = float(os.getenv("TELEMETRY_STALE_SECONDS", "8"))
    mission_min_data_quality: float = float(os.getenv("MISSION_MIN_DATA_QUALITY", "70"))

    mqtt_enabled: bool = _env_flag("MQTT_ENABLED", "0")
    mqtt_host: str = os.getenv("MQTT_HOST", "mosquitto")
    mqtt_port: int = int(os.getenv("MQTT_PORT", "1883"))
    mqtt_topic: str = os.getenv("MQTT_TOPIC", "twinguard/engine/+/telemetry")

    can_enabled: bool = _env_flag("CAN_ENABLED", "0")

    unreal_udp_enabled: bool = _env_flag("UNREAL_UDP_ENABLED", "0")
    unreal_udp_host: str = os.getenv("UNREAL_UDP_HOST", "127.0.0.1")
    unreal_udp_port: int = int(os.getenv("UNREAL_UDP_PORT", "7777"))


settings = Settings()
