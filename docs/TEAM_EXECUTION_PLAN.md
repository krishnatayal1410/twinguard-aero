# TwinGuard SIH26054 — Team Execution Plan

This plan turns the current codebase into parallel, reviewable work for the three team members already assigned learning tracks. It is intentionally tied to real repository modules so each person learns by shipping a subsystem rather than only watching tutorials.

## Shared engineering rule

Every task must finish with all four items:

1. working code or validated data,
2. a test/check that proves the change,
3. a short note explaining the engineering assumption,
4. a demo path showing where the result appears in TwinGuard.

Do not present synthetic outputs as real engine validation. The current branch is a synthetic hybrid Digital Twin demonstrator until real/test-rig data and engine-specific calibration are available.

---

## Member 1 — Frontend / Operator HMI

### Existing skills path

Frontend development.

### Repository ownership

Primary folders/files:

- `frontend/src/components/`
- `frontend/src/store/`
- `frontend/src/types/`
- `frontend/src/styles/`
- `frontend/src/services/twinApi.ts`

Do not change backend formulas without review from the backend/data owners.

### What this member is actually building

The frontend is not just a dashboard. It is the operator-facing explanation layer for the Digital Twin decision chain:

```text
Live telemetry
→ expected state
→ residuals
→ trend/persistence
→ diagnosis
→ RUL + uncertainty
→ mission margin
→ decision horizon
→ maintenance recommendation
```

### Sprint A — Command Center reliability

Tasks:

- verify every displayed number comes from the backend or is clearly labeled visual context,
- remove hard-coded operational claims,
- show `DATA HOLD` when `runtime_validity.decision_eligible == false`,
- show RUL estimate and conservative lower bound separately,
- show active runtime mode (`ENGINEERING_FALLBACK` or `NATIVE_ML`),
- ensure health, fault and mission state visibly change under fault injection,
- verify responsive behavior on the exact laptop/browser used for SIH.

Acceptance checks:

- stop the simulator: UI must not continue claiming decision-ready live data,
- restart simulator: data gate must recover,
- inject lubrication degradation: lubrication subsystem and decision center must react,
- reset healthy: state must recover without page reload.

### Sprint B — Diagnostics / explainability

Tasks:

- make observed-vs-expected residuals easy to read,
- show subsystem health decomposition,
- show Sensor Trust separately from physical health,
- show temporal trend direction,
- show model/runtime provenance,
- make synthetic/POC validation scope permanently visible where needed.

### Sprint C — Mission Lab

Tasks:

- expose current RUL interval,
- expose conservative RUL/mission ratio,
- expose mission margin and engineering reserve,
- expose decision horizon,
- compare healthy vs degraded engine using the same mission profile,
- show lower-stress counterfactual profile and its rescored result,
- show API errors when mission analysis is blocked by stale/low-quality telemetry.

### Sprint D — Demo hardening

Tasks:

- add useful loading/error states,
- prevent blank panels if WebGL is unavailable,
- verify keyboard/mouse controls,
- ensure no overlapping text at 100% browser zoom,
- run `npm run build` before every integration handoff.

Definition of done:

```bash
cd frontend
npm install
npm run build
```

must pass.

---

## Member 2 — Python / FastAPI / Docker / Integration

### Existing skills path

Python + FastAPI + Docker.

### Repository ownership

Primary folders/files:

- `backend/app/main.py`
- `backend/app/core.py`
- `backend/app/db.py`
- `backend/app/integrations/`
- `backend/app/services/persistence.py`
- `simulator/`
- `docker-compose.yml`
- `backend/Dockerfile`
- `scripts/`

Changes to health/AI/mission formulas should be reviewed with Member 3 and the team lead.

### What this member is actually building

This person owns the data path that keeps the physical/simulated engine synchronized with the Twin:

```text
Simulator / CAN / MQTT
→ validation
→ FastAPI ingestion
→ Twin Manager
→ persistence
→ WebSocket
→ frontend / Unreal bridge
```

### Sprint A — API contract mastery

Member should be able to explain and manually exercise:

- `POST /api/v1/telemetry`
- `GET /api/v1/twin/ENGINE-01`
- diagnostics endpoint,
- maintenance endpoint,
- mission analysis endpoint,
- simulation fault/reset endpoints,
- replay endpoints,
- system status endpoint,
- WebSocket twin stream.

Tasks:

- understand every field in `Telemetry`,
- verify invalid ranges are rejected,
- verify wrong engine ID is rejected,
- verify ingest key behavior,
- verify protected operator endpoints require authentication,
- verify mission analysis blocks stale/low-quality data.

### Sprint B — Simulator and fault control

Tasks:

- understand the progressive fault ramp,
- make fault scenario start/reset deterministic enough for demo,
- validate all ten aero-piston scenarios,
- verify simulator config authentication,
- add logs showing active fault and effective severity,
- make sure a simulator crash cannot be confused with healthy telemetry.

### Sprint C — Docker / reproducibility

Tasks:

- run full stack through Docker Compose,
- verify backend, frontend, database/MQTT services start cleanly,
- document one-command setup,
- ensure local environment secrets are not committed,
- verify persistent volumes where appropriate,
- verify clean shutdown/restart.

Acceptance check:

A new laptop with Docker should be able to run the demonstrator using documented steps without manually editing source code.

### Sprint D — hardware adapter path

Do not invent real CAN IDs.

Tasks:

- understand `python-can`, SocketCAN and DBC concept,
- validate adapter with `vcan0` if Linux is available,
- map decoded fields into the canonical `Telemetry` schema,
- keep real-hardware integration read-only until a safe validation path exists,
- document the exact dependency needed from DRDO/OEM/test-rig side: signal definitions, units, ranges, message mapping, sampling rates.

### Definition of done

Backend tests and live integration verifier must pass:

```bash
export PYTHONPATH="$PWD/backend"
pytest -q backend/tests
python scripts/verify_system.py
```

CI is the authoritative repeatable gate.

---

## Member 3 — Python / Pandas / NumPy / Data & Validation

### Existing skills path

Python + Pandas + NumPy.

### Repository ownership

Primary folders/files:

- `backend/app/services/physics.py`
- `backend/app/services/sensor_trust.py`
- `backend/app/services/health.py`
- `backend/app/services/ai_engine.py`
- `backend/app/services/mission.py`
- `ai/train_models.py`
- `models/`
- validation tests/scripts

### What this member is actually building

This member owns the numerical evidence chain:

```text
Raw telemetry
→ cleaning / validation
→ expected behavior
→ residual features
→ trends
→ Sensor Trust
→ health indices
→ anomaly/fault evidence
→ RUL + uncertainty
→ mission risk
```

### Sprint A — Telemetry data notebook

Create a local analysis notebook or script that:

- loads captured/replayed telemetry into Pandas,
- checks missing values,
- checks units/ranges,
- plots healthy distributions,
- calculates rolling mean/std/slope,
- compares healthy vs each injected scenario,
- verifies which features actually separate scenarios.

Required output:

A table like:

| Scenario | strongest signals | expected direction | observed direction | usable? |
|---|---|---|---|---|

### Sprint B — Physics residual validation

For every expected channel:

- verify expected-state equation direction,
- test low/high throttle,
- test altitude changes,
- test ambient-temperature changes,
- ensure normal operating changes do not automatically look like faults,
- document limitations of the generic surrogate.

The most important question is not “does the formula look sophisticated?” It is:

> Does observed minus expected behave directionally correctly under normal and injected states?

### Sprint C — Sensor Trust

Validate the distinction between:

- real multi-signal engine degradation,
- isolated sensor drift,
- transient operating-condition change,
- stale/poor telemetry.

Create tests where one sensor is wrong but correlated channels remain healthy, then compare against a real injected lubrication/thermal fault where several channels agree.

### Sprint D — AI/model evaluation

Current model metrics are synthetic-only.

Tasks:

- understand train/test split,
- generate confusion matrix,
- inspect per-class precision/recall/F1,
- inspect false positives between similar scenarios,
- verify no train/test leakage,
- compare XGBoost to simple baselines,
- validate RUL residual/error distribution,
- test behavior outside the synthetic training envelope,
- document failure cases rather than hiding them.

### Sprint E — Mission model validation

Build a scenario matrix with the same mission under multiple engine states:

- healthy,
- lubrication degradation,
- overheating/cooling degradation,
- vibration,
- combustion/injector/misfire,
- alternator degradation,
- sensor drift.

Check monotonic expectations:

- worse engine health should not improve mission feasibility,
- lower-stress counterfactual should not increase projected stress,
- conservative RUL margin should never exceed point-estimate RUL margin,
- longer/hotter/higher-load missions should generally not be scored safer all else equal.

### Definition of done

Every numerical improvement needs a regression test in `backend/tests/` or a validation script under `scripts/`.

---

## Team Lead — Integration / scientific truth / SIH story

The team lead should not become a fourth isolated coder. Own the interfaces and the proof.

Responsibilities:

- protect the aero-piston scope,
- keep units consistent,
- review any new operational claim,
- make sure every UI number has a source,
- maintain the demo scenario,
- maintain the validation limitations,
- run CI before milestone demos,
- decide what enters `main`.

### Daily integration checklist

1. Pull the latest branch.
2. Run backend tests.
3. Run frontend build.
4. Start backend + simulator + frontend.
5. Verify healthy baseline.
6. Run lubrication degradation.
7. Run the same mission healthy/degraded.
8. Verify reset/recovery.
9. Stop simulator and verify `DATA HOLD`.
10. Record any regression as a GitHub issue/task before adding more features.

---

## Recommended order from now

### Phase 1 — Reliability before new features

- make current branch pass CI,
- verify every fault scenario,
- verify stale-data gate,
- verify healthy/degraded mission comparison,
- verify Docker/local launcher.

### Phase 2 — Data credibility

- build the scenario matrix,
- quantify false positives/confusions,
- document surrogate assumptions,
- obtain any authorized real/test-rig data possible.

### Phase 3 — Hardware/replay credibility

- integrate recorded telemetry or virtual CAN,
- demonstrate adapter replacement without changing the Twin contract,
- preserve read-only safety boundary.

### Phase 4 — SIH demo polish

- freeze the demo scenario,
- freeze dependency versions,
- create offline backup recordings/screenshots,
- rehearse judge questions,
- do not add risky features in the final days unless they fix a demonstrated weakness.

## Kill criteria for proposed features

Do not build a new feature if it fails one of these tests:

- Does it directly improve SIH26054 health monitoring, fault prediction, RUL, mission reliability, integration credibility, explainability or validation?
- Can the team demonstrate it reliably?
- Can the team explain where its data comes from?
- Can it be tested?
- Does it avoid implying validation you do not have?

If the answer is no, it is lower priority than making the existing Digital Twin more credible.