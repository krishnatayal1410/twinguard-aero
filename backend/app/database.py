import os
from datetime import datetime
from sqlalchemy import create_engine, DateTime, Float, Integer, String, select
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, sessionmaker

DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./twinguard.db")

connect_args = {"check_same_thread": False} if DATABASE_URL.startswith("sqlite") else {}
engine = create_engine(DATABASE_URL, connect_args=connect_args)
SessionLocal = sessionmaker(bind=engine)


class Base(DeclarativeBase):
    pass


class TelemetryRow(Base):
    __tablename__ = "telemetry"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    engine_id: Mapped[str] = mapped_column(String(64), index=True)
    timestamp: Mapped[datetime] = mapped_column(DateTime(timezone=True), index=True)
    rpm: Mapped[float] = mapped_column(Float)
    throttle: Mapped[float] = mapped_column(Float)
    altitude: Mapped[float] = mapped_column(Float)
    ambient_temp: Mapped[float] = mapped_column(Float)
    cht: Mapped[float] = mapped_column(Float)
    egt: Mapped[float] = mapped_column(Float)
    oil_pressure: Mapped[float] = mapped_column(Float)
    oil_temp: Mapped[float] = mapped_column(Float)
    fuel_flow: Mapped[float] = mapped_column(Float)
    vibration: Mapped[float] = mapped_column(Float)
    battery_voltage: Mapped[float] = mapped_column(Float)
    operating_hours: Mapped[float] = mapped_column(Float)


def init_db():
    Base.metadata.create_all(engine)


def save_telemetry(payload: dict):
    with SessionLocal() as session:
        row = TelemetryRow(**{
            key: payload[key]
            for key in [
                "engine_id", "timestamp", "rpm", "throttle", "altitude",
                "ambient_temp", "cht", "egt", "oil_pressure", "oil_temp",
                "fuel_flow", "vibration", "battery_voltage", "operating_hours",
            ]
        })
        session.add(row)
        session.commit()


def get_history(engine_id: str = "ENGINE-01", limit: int = 300) -> list[dict]:
    with SessionLocal() as session:
        rows = session.scalars(
            select(TelemetryRow)
            .where(TelemetryRow.engine_id == engine_id)
            .order_by(TelemetryRow.timestamp.desc())
            .limit(limit)
        ).all()

    return [
        {
            "timestamp": row.timestamp.isoformat(),
            "rpm": row.rpm,
            "throttle": row.throttle,
            "altitude": row.altitude,
            "ambient_temp": row.ambient_temp,
            "cht": row.cht,
            "egt": row.egt,
            "oil_pressure": row.oil_pressure,
            "oil_temp": row.oil_temp,
            "fuel_flow": row.fuel_flow,
            "vibration": row.vibration,
            "battery_voltage": row.battery_voltage,
            "operating_hours": row.operating_hours,
        }
        for row in reversed(rows)
    ]
