# Bootstrap Verification Status

The starter repository was exercised in the build environment after scaffolding.

## Backend automated tests

- **3 tests passed**
- `/healthz`
- telemetry ingestion + Digital Twin update + SQLite history
- mission simulation endpoint

## Synthetic AI baseline

These values are **synthetic proof-of-concept measurements only**. They are not claims about a real UAV engine.

| Model | Current synthetic result |
|---|---:|
| Anomaly ROC-AUC | 0.9147 |
| Anomaly precision | 0.9569 |
| Anomaly recall | 0.5603 |
| Anomaly F1 | 0.7068 |
| Fault classification accuracy | 0.949 |
| Fault classification macro F1 | 0.9494 |
| Synthetic RUL MAE | 4.156 h |
| Synthetic RUL RMSE | 5.418 h |
| Synthetic RUL R² | 0.9906 |

## Validation design

- Anomaly model trains on healthy missions `00-07`.
- Anomaly evaluation uses held-out missions `08-09`.
- Fault classifier trains on missions `00-07` and tests on `08-09` for every scenario.
- RUL trains on synthetic degradation missions `00-23` and tests on `24-29`.
- This avoids the simplest form of row-level time-series leakage.

## Important limitation

The physics equations, generated faults, health score and RUL target are synthetic. Real engine performance maps, test-rig telemetry and degradation histories are required before operational claims can be made.

## Frontend verification

Frontend source, dependency manifest and CI workflow are included. Package installation was not completed in the isolated build environment, so the frontend build should be run on a normal development machine with npm registry access.
