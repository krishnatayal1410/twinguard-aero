# Validation Snapshot

The project was validated in the build environment at the Python/service layer.

## Automated backend tests

`backend/tests/test_pipeline.py`

Result: **3 passed**

Covered:
- end-to-end Digital Twin state generation,
- mission analysis direction,
- lubrication physics direction.

## Synthetic fault scenario check

The included simulator and trained synthetic AI were checked across:

| Injected scenario | Predicted condition | Expected health behavior |
|---|---|---|
| Normal | Normal | high / stable |
| Lubrication | Lubrication | lubrication + overall health decrease |
| Overheating | Overheating | thermal + overall health decrease |
| Vibration | Vibration | mechanical health decrease |
| Sensor drift | Sensor drift | trust/diagnostic issue with less physical degradation |
| Injector | Injector | combustion/fuel evidence |
| Misfire | Misfire | vibration/combustion evidence |

## Current synthetic ML metrics

- Fault accuracy: 0.9668
- Fault macro F1: 0.9691
- RUL MAE: 12.44 h
- RUL RMSE: 15.03 h
- RUL R²: 0.6867

These metrics are generated entirely from synthetic data and **must not be presented as real UAV-engine validation**.

## Frontend validation

All TypeScript / TSX source files were syntax-parsed with the TypeScript compiler in the build environment.

The package registry was not reachable from the build sandbox, so `npm install && npm run build` could not be executed here. The repository includes the complete package manifest and one-command installer/start script for a normal internet-connected development machine.

## 3D asset validation

The shipped GLB is an original 95-component generic flat-four aero-piston visualization with named subsystem nodes. It was exported and reloaded successfully using a glTF-capable geometry library.
