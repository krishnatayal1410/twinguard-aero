from __future__ import annotations
from datetime import datetime,timezone
from typing import Dict,Literal,Optional
from pydantic import BaseModel,Field,StringConstraints
from typing_extensions import Annotated
EngineId=Annotated[str,StringConstraints(strip_whitespace=True,min_length=1,max_length=64,pattern=r"^[A-Za-z0-9_-]+$")]

class SignUpRequest(BaseModel):
 name:Annotated[str,StringConstraints(strip_whitespace=True,min_length=2,max_length=120)]
 email:Annotated[str,StringConstraints(strip_whitespace=True,min_length=3,max_length=255,pattern=r"^[^\s@]+@[^\s@]+\.[^\s@]+$")]
 password:Annotated[str,StringConstraints(min_length=10,max_length=128)]
class SignInRequest(BaseModel):
 email:Annotated[str,StringConstraints(strip_whitespace=True,min_length=3,max_length=255,pattern=r"^[^\s@]+@[^\s@]+\.[^\s@]+$")]
 password:Annotated[str,StringConstraints(min_length=1,max_length=128)]
class AuthUser(BaseModel):
 id:int;name:str;email:str;role:str
class AuthResponse(BaseModel):
 token:str;user:AuthUser

class Telemetry(BaseModel):
 engine_id:EngineId="ENGINE-01";timestamp:datetime=Field(default_factory=lambda:datetime.now(timezone.utc));rpm:float=Field(ge=0,le=10000);throttle:float=Field(ge=0,le=110);cht:float=Field(ge=-80,le=400);egt:float=Field(ge=-80,le=1300);oil_pressure:float=Field(ge=0,le=15);oil_temperature:float=Field(ge=-80,le=250);fuel_flow:float=Field(ge=0,le=100);vibration:float=Field(ge=0,le=10);battery_voltage:float=Field(ge=0,le=60);alternator_voltage:float=Field(28,ge=0,le=60);altitude:float=Field(ge=-1000,le=20000);ambient_temperature:float=Field(ge=-80,le=80);injection_timing:float=Field(18,ge=-30,le=60);operating_hours:float=Field(0,ge=0,le=200000)
class MissionRequest(BaseModel):
 mission_type:Annotated[str,StringConstraints(strip_whitespace=True,min_length=1,max_length=40)]="endurance";duration_hours:float=Field(8,ge=.25,le=48);cruise_altitude_m:float=Field(5500,ge=0,le=12000);ambient_temp_c:float=Field(35,ge=-50,le=70);average_throttle_pct:float=Field(75,ge=10,le=100)
class FaultCommand(BaseModel):fault:Literal["normal","lubrication","overheating","vibration","sensor_drift","injector","misfire","turbine_blade_degradation"];severity:float=Field(0,ge=0,le=1)
class ReplayStart(BaseModel):label:Optional[Annotated[str,StringConstraints(strip_whitespace=True,max_length=120)]]=None
class TwinState(BaseModel):
 engine_id:str;timestamp:datetime;telemetry:Dict[str,float|str];expected:Dict[str,float];residuals:Dict[str,float];sensor_trust:Dict[str,float];data_quality:Dict[str,float|str];health:Dict[str,float];ai:Dict[str,object];confidence:Dict[str,float];maintenance:Dict[str,object];readiness:Dict[str,object]
