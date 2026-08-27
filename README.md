# TwinGuard Aero

TwinGuard Aero is an engineering-first software prototype for Digital Twin based health monitoring and prognostics of a UAV aero-piston engine.

## What this starter already contains

- UAV engine simulator [Python]
- controllable synthetic fault scenarios [Python]
- telemetry schema [Python/Pydantic]
- FastAPI backend [Python]
- SQLite history [SQL]
- WebSocket live state
- Digital Twin state service [Python]
- simplified expected-behavior/physics model [Python]
- physics residuals [Python]
- transparent health score [Python]
- sensor-trust baseline [Python]
- maintenance recommendation baseline [Python]
- mission-stress simulator [Python]
- Isolation Forest training pipeline [Python/scikit-learn]
- XGBoost fault-classifier training pipeline [Python/C++]
- XGBoost synthetic RUL training pipeline [Python/C++]
- React dashboard [TypeScript]
- Docker starter
- GitHub Actions CI [YAML]
- tests and project documentation

> The simulator, health formula, mission model and initial ML data are synthetic proof-of-concept components. They are not calibrated to a real DRDO engine and must not be presented as certified aerospace predictions.

## Repository structure

```text
twinguard-aero/
├── ai/                 # ML feature/training code
├── backend/            # FastAPI + Twin + DB
├── data/               # generated synthetic data
├── docs/               # team plan, validation, roadmap
├── frontend/           # React dashboard
├── models/             # generated model artifacts
├── notebooks/          # experiments
├── scripts/            # verification helpers
├── simulator/          # engine/fault simulator
├── tests/              # automated tests
└── .github/workflows/  # CI
```

## Core stack

Python 3.12 [Python], NumPy [Python], Pandas [Python], SciPy [Python], scikit-learn [Python], XGBoost [Python/C++], SHAP [Python], FastAPI [Python], Pydantic [Python], SQLAlchemy [Python], SQLite [SQL], React [TypeScript], Vite [JavaScript/TypeScript], WebSocket, Docker, Git/GitHub.

## 1. Install backend dependencies

From repository root:

```bash
python -m venv .venv
```

Windows:

```powershell
.venv\Scripts\activate
```

Linux/macOS:

```bash
source .venv/bin/activate
```

Then:

```bash
pip install -r backend/requirements.txt
```

## 2. Verify backend

```bash
python scripts/verify_backend.py
```

## 3. Start backend

```bash
uvicorn backend.app.main:app --reload
```

Open `http://localhost:8000/docs`.

## 4. Start simulator

In a second terminal:

```bash
python simulator/run_simulator.py
```

## 5. Start frontend

```bash
cd frontend
npm install
npm run dev
```

Open `http://localhost:5173`.

## 6. Generate synthetic training data and models

From repository root:

```bash
python ai/train_all.py
```

Then restart the backend or call:

```text
POST /models/reload
```

## Tomorrow

Read `docs/START_TOMORROW.md`.
