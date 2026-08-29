from __future__ import annotations
from pathlib import Path
from datetime import datetime, timezone
from sqlalchemy import create_engine, String, Float, Integer, DateTime, Text, ForeignKey, Boolean
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, sessionmaker
from .core import settings

if settings.database_url.startswith("sqlite"):
    Path("./data/runtime").mkdir(parents=True,exist_ok=True)
engine=create_engine(settings.database_url,connect_args={"check_same_thread":False} if settings.database_url.startswith("sqlite") else {},pool_pre_ping=True)
SessionLocal=sessionmaker(bind=engine,autoflush=False,expire_on_commit=False)

class Base(DeclarativeBase): pass


class UserAccount(Base):
    __tablename__="users"
    id: Mapped[int]=mapped_column(Integer,primary_key=True,autoincrement=True)
    email: Mapped[str]=mapped_column(String(255),unique=True,index=True)
    name: Mapped[str]=mapped_column(String(120))
    password_hash: Mapped[str]=mapped_column(String(512))
    role: Mapped[str]=mapped_column(String(32),default="operator")
    active: Mapped[bool]=mapped_column(Boolean,default=True)
    created_at: Mapped[datetime]=mapped_column(DateTime(timezone=True),default=lambda:datetime.now(timezone.utc))

class AuthSession(Base):
    __tablename__="auth_sessions"
    id: Mapped[int]=mapped_column(Integer,primary_key=True,autoincrement=True)
    user_id: Mapped[int]=mapped_column(ForeignKey("users.id"),index=True)
    token_hash: Mapped[str]=mapped_column(String(64),unique=True,index=True)
    created_at: Mapped[datetime]=mapped_column(DateTime(timezone=True),default=lambda:datetime.now(timezone.utc))
    expires_at: Mapped[datetime]=mapped_column(DateTime(timezone=True),index=True)
    last_seen_at: Mapped[datetime]=mapped_column(DateTime(timezone=True),default=lambda:datetime.now(timezone.utc))

class MissionRun(Base):
    __tablename__="missions"
    id: Mapped[int]=mapped_column(Integer,primary_key=True,autoincrement=True)
    engine_id: Mapped[str]=mapped_column(String(64),index=True)
    label: Mapped[str]=mapped_column(String(255))
    status: Mapped[str]=mapped_column(String(32),default="RECORDING")
    started_at: Mapped[datetime]=mapped_column(DateTime(timezone=True),default=lambda:datetime.now(timezone.utc))
    ended_at: Mapped[datetime|None]=mapped_column(DateTime(timezone=True),nullable=True)
    summary_json: Mapped[str|None]=mapped_column(Text,nullable=True)

class MissionSample(Base):
    __tablename__="mission_samples"
    id: Mapped[int]=mapped_column(Integer,primary_key=True,autoincrement=True)
    mission_id: Mapped[int]=mapped_column(ForeignKey("missions.id"),index=True)
    timestamp: Mapped[datetime]=mapped_column(DateTime(timezone=True),default=lambda:datetime.now(timezone.utc))
    health: Mapped[float]=mapped_column(Float)
    rul: Mapped[float]=mapped_column(Float)
    cht: Mapped[float]=mapped_column(Float)
    oil_pressure: Mapped[float]=mapped_column(Float)
    vibration: Mapped[float]=mapped_column(Float)
    anomaly: Mapped[int]=mapped_column(Integer)
    fault: Mapped[str]=mapped_column(String(64))
    maintenance: Mapped[str]=mapped_column(String(64))


class TelemetryPoint(Base):
    __tablename__="telemetry_points"
    id: Mapped[int]=mapped_column(Integer,primary_key=True,autoincrement=True)
    engine_id: Mapped[str]=mapped_column(String(64),index=True)
    timestamp: Mapped[datetime]=mapped_column(DateTime(timezone=True),index=True)
    rpm: Mapped[float]=mapped_column(Float)
    throttle: Mapped[float]=mapped_column(Float)
    cht: Mapped[float]=mapped_column(Float)
    egt: Mapped[float]=mapped_column(Float)
    oil_pressure: Mapped[float]=mapped_column(Float)
    oil_temperature: Mapped[float]=mapped_column(Float)
    fuel_flow: Mapped[float]=mapped_column(Float)
    vibration: Mapped[float]=mapped_column(Float)
    altitude: Mapped[float]=mapped_column(Float)
    battery_voltage: Mapped[float]=mapped_column(Float)

class TwinSnapshot(Base):
    __tablename__="twin_snapshots"
    id: Mapped[int]=mapped_column(Integer,primary_key=True,autoincrement=True)
    engine_id: Mapped[str]=mapped_column(String(64),index=True)
    timestamp: Mapped[datetime]=mapped_column(DateTime(timezone=True),index=True)
    overall_health: Mapped[float]=mapped_column(Float)
    probable_fault: Mapped[str]=mapped_column(String(64))
    anomaly_score: Mapped[float]=mapped_column(Float)
    rul_hours: Mapped[float]=mapped_column(Float)
    maintenance_priority: Mapped[str]=mapped_column(String(64))
    state_json: Mapped[str]=mapped_column(Text)

Base.metadata.create_all(engine)
