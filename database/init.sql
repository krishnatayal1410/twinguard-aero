CREATE EXTENSION IF NOT EXISTS timescaledb;

CREATE TABLE IF NOT EXISTS telemetry_points (
  id BIGSERIAL,
  engine_id VARCHAR(64) NOT NULL,
  timestamp TIMESTAMPTZ NOT NULL,
  rpm DOUBLE PRECISION NOT NULL,
  throttle DOUBLE PRECISION NOT NULL,
  cht DOUBLE PRECISION NOT NULL,
  egt DOUBLE PRECISION NOT NULL,
  oil_pressure DOUBLE PRECISION NOT NULL,
  oil_temperature DOUBLE PRECISION NOT NULL,
  fuel_flow DOUBLE PRECISION NOT NULL,
  vibration DOUBLE PRECISION NOT NULL,
  altitude DOUBLE PRECISION NOT NULL,
  battery_voltage DOUBLE PRECISION NOT NULL,
  PRIMARY KEY (id, timestamp)
);
SELECT create_hypertable('telemetry_points','timestamp',if_not_exists => TRUE);

CREATE TABLE IF NOT EXISTS twin_snapshots (
  id BIGSERIAL,
  engine_id VARCHAR(64) NOT NULL,
  timestamp TIMESTAMPTZ NOT NULL,
  overall_health DOUBLE PRECISION NOT NULL,
  probable_fault VARCHAR(64) NOT NULL,
  anomaly_score DOUBLE PRECISION NOT NULL,
  rul_hours DOUBLE PRECISION NOT NULL,
  maintenance_priority VARCHAR(64) NOT NULL,
  state_json TEXT NOT NULL,
  PRIMARY KEY (id, timestamp)
);
SELECT create_hypertable('twin_snapshots','timestamp',if_not_exists => TRUE);
