# TwinGuard Aero - Final MVP Runbook

This pack adds the remaining core software MVP pieces:

- Mission Replay
- persistent SQLite mission history
- post-flight summary
- intelligent event timeline
- RUL/health history
- JSON mission export
- MVP status API
- one-command local startup
- core API verification
- Docker and Docker Compose deployment files

## One-command local startup

```bash
cd ~/Desktop/twinguard-aero
bash scripts/start_mvp.sh
```

## Final demo

1. RESET HEALTHY
2. START RECORDING
3. show healthy telemetry
4. run Mission Lab
5. inject Lubrication 70%
6. show anomaly/fault/physics/XAI
7. run same Mission Lab profile
8. show worse mission risk and lower post-mission RUL
9. END & ANALYZE
10. REFRESH HISTORY
11. select the mission
12. show event timeline and RUL/health change
13. export JSON
14. RESET HEALTHY

## Verification

```bash
cd ~/Desktop/twinguard-aero
source .venv/bin/activate
python scripts/verify_mvp.py
```

## Docker

```bash
docker compose -f docker-compose.mvp.yml up --build
```

## Still future work, not required to claim the software MVP complete

- real DRDO engine telemetry
- proprietary CAN/DBC mappings
- hardware-in-the-loop validation
- engine-specific calibration
- aerospace certification
- CAD-accurate 3D engine
- fleet optimization
- federated learning

Always describe the current system as a synthetic MVP decision-support demonstrator.
