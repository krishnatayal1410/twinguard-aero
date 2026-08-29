from __future__ import annotations
import os
from dataclasses import dataclass
@dataclass(frozen=True)
class Settings:
    app_name:str="TwinGuard Aero";version:str="3.0.0";environment:str=os.getenv("TWINGUARD_ENV","development")
    engine_id:str=os.getenv("TWINGUARD_ENGINE_ID","ENGINE-01")
    database_url:str=os.getenv("DATABASE_URL","sqlite:///./data/runtime/twinguard.db")
    cors_origins:tuple[str,...]=tuple(x.strip() for x in os.getenv("CORS_ORIGINS","http://localhost:5173,http://127.0.0.1:5173").split(",") if x.strip())
    trusted_hosts:tuple[str,...]=tuple(x.strip() for x in os.getenv("TRUSTED_HOSTS","localhost,127.0.0.1,testserver").split(",") if x.strip())
    ingest_api_key:str=os.getenv("TWINGUARD_INGEST_KEY","")
    max_body_bytes:int=int(os.getenv("MAX_BODY_BYTES","131072"))
    model_dir:str=os.getenv("MODEL_DIR","./models")
    mqtt_enabled:bool=os.getenv("MQTT_ENABLED","0")=="1";mqtt_host:str=os.getenv("MQTT_HOST","mosquitto");mqtt_port:int=int(os.getenv("MQTT_PORT","1883"));mqtt_topic:str=os.getenv("MQTT_TOPIC","twinguard/engine/+/telemetry")
    can_enabled:bool=os.getenv("CAN_ENABLED","0")=="1"
    unreal_udp_enabled:bool=os.getenv("UNREAL_UDP_ENABLED","0")=="1";unreal_udp_host:str=os.getenv("UNREAL_UDP_HOST","127.0.0.1");unreal_udp_port:int=int(os.getenv("UNREAL_UDP_PORT","7777"))
settings=Settings()
