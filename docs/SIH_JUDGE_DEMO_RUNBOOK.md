# TwinGuard — SIH26054 Judge Demo Runbook

## One-sentence positioning

**TwinGuard is a mission-aware hybrid Digital Twin for aero-piston engines in MALE UAVs that converts live engine state into explainable health, degradation, RUL uncertainty, and mission-level reliability intelligence.**

The differentiator is not merely “predict a failure.” The key question is:

> Given this specific engine state and this planned mission profile, how much credible operating margin remains, what is driving the risk, and should the mission profile be reviewed or reduced?

---

## What the demo must prove

The demonstration should prove a causal chain, not just show screens:

```text
engine state changes
→ expected-vs-observed residuals change
→ multiple signals corroborate degradation
→ health/diagnosis changes
→ RUL estimate + uncertainty changes
→ same mission becomes less favorable
→ lower-stress counterfactual improves margin
```

If a screen cannot support that chain, it is secondary in the main demo.

---

## Pre-demo verification

Run the CI-equivalent local checks before presentation day.

```bash
export PYTHONPATH="$PWD/backend"
pytest -q backend/tests
```

Frontend:

```bash
cd frontend
npm install
npm run build
```

Full system:

```bash
bash scripts/start_local.sh
```

Then:

```bash
python scripts/verify_system.py
```

Required manual checks:

- sign in works,
- telemetry is updating,
- data state says decision-eligible rather than DATA HOLD,
- aero-piston 3D view renders,
- Mission Lab runs,
- lubrication injection works,
- reset works,
- simulator stop produces DATA HOLD,
- simulator restart recovers,
- replay records/ends successfully.

---

# Recommended 5–7 minute live demo

## 0:00–0:35 — Problem and differentiation

Say the problem in operational language:

A conventional dashboard can tell an operator that oil pressure is low or vibration is high. A predictive-maintenance model may estimate a fault or RUL. TwinGuard connects the **current engine condition to the planned mission**.

Explain the four conceptual layers:

1. **Real-Time State Twin** — synchronized telemetry.
2. **Hybrid Physics–AI Health Twin** — expected behavior, residuals, health, diagnosis and uncertainty.
3. **Prognostic Twin** — RUL estimate with a conservative uncertainty bound and degradation trends.
4. **Mission Reliability Twin** — mission margin, feasibility index, decision horizon and lower-stress counterfactual.

Do not claim the current synthetic output is flight-certified.

---

## 0:35–1:20 — Healthy synchronized twin

Open **Command Center**.

Show:

- live telemetry,
- aero-piston 3D subsystem view,
- engineering health index,
- RUL estimate,
- conservative RUL,
- data gate state,
- active diagnostic runtime.

Say explicitly:

> The 3D model is the visualization layer, not the Digital Twin itself. The Twin is the synchronized state, expected model, residuals, temporal history, diagnostic/prognostic state and mission analysis behind it.

Open **Diagnostics** briefly.

Point to:

- residuals = observed minus expected,
- Sensor Trust,
- health decomposition,
- model state,
- synthetic validation scope.

---

## 1:20–2:05 — Healthy mission baseline

Open **Mission Lab**.

Use a repeatable profile, for example:

- mission: Endurance / ISR,
- duration: 8 h,
- altitude: 5,500 m,
- ambient: 35 °C,
- average throttle: 75%.

Run the Mission Reliability Twin.

Record:

- risk class,
- Mission Feasibility Index,
- current RUL band,
- conservative RUL/mission ratio,
- projected profile endurance,
- mission margin,
- engineering reserve,
- decision horizon,
- post-mission health/RUL.

Important wording:

> Mission Feasibility Index is a transparent prototype decision-support index. It is not a calibrated probability of mission success.

---

## 2:05–3:20 — Inject progressive lubrication degradation

Return to **Command Center**.

Select:

- `Lubrication Degradation`
- target severity around 80–85%.

Run it.

Show the fault developing progressively rather than instantaneously.

Watch for:

- oil pressure decreasing relative to expected,
- oil temperature increasing,
- vibration corroboration,
- oil-pressure trend worsening,
- lubrication health falling,
- anomaly persistence increasing,
- probable condition changing,
- RUL/conservative RUL falling,
- maintenance recommendation changing.

Explain why this is better than a threshold alarm:

> TwinGuard does not treat one abnormal sensor value as sufficient proof. It checks correlated signals, physics consistency, temporal persistence and Sensor Trust before making a stronger condition assessment.

---

## 3:20–4:15 — Explainability

Open **Diagnostics**.

Show the evidence chain:

```text
Observed oil pressure
− Expected oil pressure
= Oil-pressure residual
```

Then show supporting oil-temperature/vibration evidence.

Explain Sensor Trust distinction:

- If only one channel drifts while correlated channels remain consistent, sensor/data fault becomes plausible.
- If several physically related channels change together, real engine degradation becomes more plausible.

Make clear this is prototype logic awaiting real-engine calibration.

---

## 4:15–5:15 — Same mission, degraded engine

Run **the exact same mission profile** again.

This is one of the strongest parts of the demo.

Compare healthy vs degraded:

- health,
- RUL estimate,
- conservative RUL margin,
- mission margin,
- decision horizon,
- feasibility index,
- overall risk.

Say:

> The mission did not change. The engine state changed. Therefore the mission-level decision support changed. This is the central purpose of the mission-aware Twin.

---

## 5:15–5:50 — Counterfactual replan

Show the automatically generated lower-stress alternative:

- reduced duration,
- reduced throttle,
- adjusted altitude,
- independently rescored stress/risk,
- new mission margin,
- new decision horizon.

Do not call this an autonomous flight command.

Say:

> TwinGuard proposes a lower-stress profile for engineering/operator review. It does not directly command the aircraft.

---

## 5:50–6:20 — Data fail-safe

This is optional but very strong if reliable.

Stop or disconnect the simulator.

After the configured freshness window, show:

- telemetry age increasing,
- `DATA HOLD`,
- decision eligibility becoming false,
- Mission Lab refusing a new mission analysis.

Explain:

> A Digital Twin should not keep making fresh decisions using stale data merely because the dashboard is still open.

Restart the simulator and show recovery.

---

## 6:20–6:45 — Integration path and boundary

Show Settings / architecture briefly.

Explain adapter model:

```text
Synthetic simulator today
↓
Same canonical telemetry contract
↓
MQTT / CAN / ECU replay / test-rig tomorrow
```

Mention:

- FastAPI,
- WebSocket,
- MQTT adapter,
- SocketCAN/python-can adapter,
- persistence,
- Docker,
- Unreal JSON bridge,
- CI.

State the next validation tier:

- authorized target-engine signals,
- real healthy test-rig data,
- known degradation/fault cases,
- calibrated physics maps,
- real RUL ground truth,
- domain-expert validation.

---

# Judge questions and defensible answers

## “Where did your data come from?”

Current demonstrator data is synthetic and physics-inspired. The repository deliberately labels the validation scope as `SYNTHETIC_PROOF_OF_CONCEPT`. The architecture is designed so the simulator can be replaced by authorized CAN/MQTT/test-rig telemetry without rewriting the Twin contract.

## “Is this really AI?”

TwinGuard has two diagnostic paths:

- stable engineering fallback for deterministic demo/runtime robustness,
- packaged synthetic Isolation Forest/XGBoost classifier/RUL regressor compatible with the current feature/fault contract.

CI separately verifies that the native synthetic model artifacts load and execute when enabled. Neither path is claimed as real-engine validated.

## “Why not just use thresholds?”

Thresholds cannot distinguish operating-condition changes from degradation well. TwinGuard estimates expected behavior based on operating conditions, calculates residuals, uses multiple correlated channels, checks temporal persistence, tracks Sensor Trust and then translates the state into mission impact.

## “Why is your RUL trustworthy?”

It should not be treated as certified RUL yet. TwinGuard exposes its RUL basis and an uncertainty band. Mission analysis uses the conservative lower bound rather than blindly trusting the point estimate. Real run-to-failure/test-rig data is required for operational calibration.

## “Is the feasibility score a probability?”

No. It is explicitly an engineering decision-support index. The product avoids presenting it as a calibrated probability of mission completion.

## “What is the Digital Twin here?”

The twin is not the 3D model. It is the synchronized engine state plus expected-state model, observed-vs-expected residuals, temporal evidence, Sensor Trust, subsystem health, diagnosis, RUL/uncertainty and mission-context simulation. The 3D view is the HMI representation of that state.

## “How would you connect a real engine?”

Replace the simulator adapter with an authorized telemetry adapter. Decode actual ECU/CAN/test-rig signals into the canonical telemetry schema, calibrate units/ranges and physics, retrain/validate models, then repeat HIL/test-rig verification. Do not invent CAN IDs.

## “Can this control the UAV?”

Current TwinGuard is decision support only. It does not issue flight-critical control commands. Any future closed-loop actuation would require a separate safety/certification/cybersecurity pathway.

## “What happens if a sensor fails?”

Sensor Trust checks isolated disagreement and sudden jumps separately from multi-channel physical corroboration. A low-trust input can lead to a data-quality hold instead of an automatic mechanical diagnosis.

## “What happens if data stops arriving?”

TwinGuard tracks telemetry age. Once state exceeds the freshness limit, it enters DATA HOLD and blocks new mission analysis until synchronization recovers.

## “What makes this different from predictive maintenance?”

Predictive maintenance asks what fault exists and when maintenance may be needed. TwinGuard adds mission context: whether the current engine condition has sufficient conservative margin for a specific proposed mission and how a lower-stress alternative changes that margin.

---

# Claims you should not make

Do not say:

- “98% real accuracy” from synthetic metrics,
- “guarantees mission completion,”
- “certified RUL,”
- “DRDO engine model” unless DRDO actually supplied/validated it,
- “real FADEC/CAN integration” unless it is actually connected,
- “flight ready,”
- “production ready,”
- “zero false alarms,”
- “AI prevents crashes.”

Instead say:

- synthetic proof-of-concept,
- architecture demonstrator,
- engine-specific calibration pending,
- decision-support index,
- conservative RUL bound,
- test-rig validation is the next tier.

---

# Demo fallback strategy

Prepare three levels:

### Level 1 — Full live system

Backend + simulator + frontend + mission analysis.

### Level 2 — Local replay

Use a previously recorded mission/replay if live fault progression fails.

### Level 3 — Screenshots/video

Keep screenshots/video of:

- healthy state,
- degraded lubrication state,
- diagnostics evidence,
- healthy/degraded mission comparison,
- DATA HOLD.

Fallback media is evidence of prior operation, not a substitute for saying the live system is currently working if it is not.

---

# Best final line

> **TwinGuard does not just ask, “Will this engine fail?” It asks, “Given this engine’s condition right now, what does that mean for the mission we are about to fly?”**
