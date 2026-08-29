# Real Engine and Unreal Integration Path

The current project is already organized so its synthetic simulator can later be replaced by real telemetry. Do not change the Digital Twin/AI/frontend contract when moving to hardware; change the **telemetry adapter**.

## 1. Canonical telemetry contract

Send JSON to:

`POST /api/v1/telemetry`

Required engineering fields:

- engine_id
- timestamp
- rpm
- throttle
- cht
- egt
- oil_pressure
- oil_temperature
- fuel_flow
- vibration
- battery_voltage
- alternator_voltage
- altitude
- ambient_temperature
- injection_timing
- operating_hours

Before using real hardware, units, ranges and sensor names must be matched to the actual ECU/FADEC/test-rig documentation.

## 2. MQTT

Topic pattern:

`twinguard/engine/<ENGINE_ID>/telemetry`

Backend environment:

```text
MQTT_ENABLED=1
MQTT_HOST=<broker>
MQTT_PORT=1883
MQTT_TOPIC=twinguard/engine/+/telemetry
```

## 3. CAN / SocketCAN

`backend/app/integrations/can_bridge.py` is a configurable adapter using:
- python-can [Python]
- cantools [Python]
- SocketCAN [Linux/C]

Do not invent CAN IDs. Obtain the real DBC / ECU message specification, then decode it into the canonical telemetry schema.

Development can use `vcan0` on Linux.

## 4. Unreal Engine

TwinGuard can send each complete Twin State as UDP JSON.

Enable:

```text
UNREAL_UDP_ENABLED=1
UNREAL_UDP_HOST=127.0.0.1
UNREAL_UDP_PORT=7777
```

The payload includes:
- telemetry
- expected physics state
- residuals
- health
- anomaly/fault/RUL
- Sensor Trust
- Data Quality
- confidence
- maintenance
- mission readiness

Unreal should map subsystem health to:
- material color/emissive state,
- animations,
- component labels,
- maintenance overlays.

For bidirectional control, use REST endpoints instead of allowing Unreal to directly manipulate an engine bus.

## 5. Hardware validation sequence

Software simulator
→ virtual CAN / MQTT
→ sensor replay
→ test-rig read-only telemetry
→ calibrated physics
→ retrained AI
→ HIL
→ controlled engine test
→ operational evaluation

Do not connect maintenance/mission decisions directly to flight-critical control until the complete safety and certification pathway is addressed.
