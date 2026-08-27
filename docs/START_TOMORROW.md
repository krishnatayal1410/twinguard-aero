# Start Tomorrow — 28 August 2026

## First team meeting: 45 minutes

1. Everyone clones the repository.
2. Everyone reads `PROJECT_SPEC.md`, `ARCHITECTURE.md`, and `docs/TEAM_ROLES.md`.
3. Freeze telemetry field names. Do not rename them independently.
4. Each member creates/uses their role branch.
5. Run the backend and simulator once on at least two laptops.
6. Open the frontend and confirm live data is visible.

## Day 1 ownership

### M1 — Lead / Integration
- verify everybody can run the project
- explain repository structure
- keep `main` stable
- maintain architecture and telemetry contract

### M2 — AI
- run `python simulator/generate_dataset.py`
- explore CSV with Pandas [Python]
- understand every feature and label
- run anomaly baseline only after understanding data

### M3 — Digital Twin / Simulation
- read `simulator/engine.py`
- verify healthy telemetry relationships
- document why each simulated variable changes
- improve one healthy operating scenario without adding random complexity

### M4 — Frontend
- run React [TypeScript] frontend
- understand each card/component
- add one clean live chart after telemetry is visible

### M5 — Backend
- run FastAPI [Python]
- inspect `/docs`
- understand `/telemetry`, `/state`, `/history`, `/ws/telemetry`
- verify SQLite [SQL] history persists

## Day 1 definition of done
- 5 people can pull code
- backend runs
- simulator sends telemetry
- frontend displays live state
- SQLite records history
- everybody has pushed at least one meaningful commit to their branch
