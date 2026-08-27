# Architecture

- Engine Simulator [Python]
- FastAPI telemetry ingestion [Python]
- Digital Twin state service [Python]
- simplified physics expected-state model [Python/SciPy]
- residual calculation [Python]
- anomaly model [Python/scikit-learn]
- fault classifier [Python/XGBoost]
- RUL baseline [Python/XGBoost]
- explainability [Python/SHAP]
- SQLite [SQL] initially
- React dashboard [TypeScript]
- Plotly.js charts [JavaScript/TypeScript]
- WebSocket live updates

Future real integration can replace the simulator with ECU/FADEC/CAN telemetry without changing the core software interfaces.
