# TwinGuard Aero — SIH Demo Flow

The demo should prove one causal story:

> **A progressive physical condition causes a contextual observed-vs-expected deviation; TwinGuard corroborates it over time, explains the likely subsystem problem, shows health/RUL impact, and translates that into mission-level risk.**

## Before the demo

1. Start TwinGuard with `bash scripts/start_local.sh` or `./START_TWINGUARD.command`.
2. Confirm `http://127.0.0.1:8000/health` returns `ok`.
3. Run `python scripts/verify_system.py` if time allows.
4. Reset the simulator to **Normal / Healthy**.
5. Sign in and leave the Command Center open.

## Live story

### 1. Establish the healthy twin

Show:
- live aero-piston telemetry,
- interactive horizontally-opposed engine view,
- high subsystem health,
- expected-vs-observed residuals near the synthetic nominal envelope,
- Sensor Trust,
- `ENGINEERING_FALLBACK` or compatible model state,
- `Synthetic POC` provenance badge.

Explain that the 3D engine is only the visualization; the synchronized state, expected behavior, residuals, trends, diagnosis and mission model are the Digital Twin.

### 2. Run the healthy mission baseline

Open **Mission Reliability** and use a repeatable profile, for example:

```text
Mission: Endurance / ISR
Duration: 8 h
Cruise altitude: 5,500 m
Ambient temperature: 35 °C
Average throttle: 75%
```

Record:
- Mission Feasibility Index,
- overall risk,
- post-mission health,
- post-mission RUL,
- RUL/mission margin,
- dominant risk factors.

Do not call the feasibility index a probability of mission success.

### 3. Start mission recording

Open Replay and start a recording labelled for the demo.

### 4. Inject progressive lubrication degradation

Return to Command Center and choose:

```text
Lubrication Degradation
Target Severity: ~70–85%
```

Run the scenario.

Do not expect an instant red alarm. The simulator intentionally ramps degradation.

### 5. Show the evidence developing

As the scenario evolves, point out:

```text
Oil pressure              ↓
Oil temperature           ↑
Vibration                 ↑
Oil-pressure residual     increasingly negative
Oil-pressure trend        declining
Anomaly persistence       increasing
Lubrication health        ↓
Overall health            ↓
Simulation-derived RUL    ↓
```

This is the key moment: TwinGuard should not be reacting to a single fixed threshold. It is accumulating contextual and temporal evidence.

### 6. Open Diagnostics

Show:
- observed − expected residuals,
- temporal evidence,
- leading fault hypothesis,
- diagnostic confidence,
- physics corroboration,
- sensor integrity,
- data quality,
- subsystem health.

Explain Sensor Trust:

> A physical fault can create large residuals while the involved sensors remain trustworthy because related channels corroborate the condition. An isolated inconsistent channel is treated differently.

### 7. Re-run the exact same mission

Use the same mission inputs as the healthy baseline.

Compare:
- healthy vs degraded health,
- RUL margin,
- feasibility index,
- risk class,
- post-mission projection.

This is the core **mission-aware** proof: the mission profile did not change; the engine state did.

### 8. Show the counterfactual

Show TwinGuard's lower-stress alternative and its independently calculated:
- altitude,
- duration,
- throttle,
- projected stress index,
- projected risk.

Explain that this is decision-support simulation, not an autonomous flight command.

### 9. Finish Replay

End the recording and show how the mission timeline preserves:
- telemetry,
- residuals,
- health changes,
- diagnostic events,
- decision state.

### 10. Show Maintenance

Show:
- affected subsystem,
- inspection suggestions,
- simulation-derived RUL,
- next-mission review status.

State clearly that actual maintenance release requires engine-specific approved procedures and validation.

## Judge-defense statements

### “Where is the Digital Twin?”

> The synchronized Twin contains the observed engine state, an operating-condition-aware expected state, residuals, temporal trends, Sensor Trust, subsystem health, diagnostic state, RUL and mission state. The 3D engine is only its HMI representation.

### “Where is the AI?”

> TwinGuard supports Isolation Forest and XGBoost synthetic models, but the stable prototype deliberately retains an explainable engineering fallback. Model artifacts are schema-checked before loading, so stale models cannot silently produce incorrect faults.

### “Is the RUL real?”

> The current RUL is simulation-derived and demonstrates the prognostic architecture. Real RUL validation requires engine-specific degradation/run-to-failure evidence.

### “What is your main differentiator?”

> TwinGuard does not stop at fault detection. It translates the current engine condition, degradation trend and RUL margin into mission-level risk, explains the evidence, and independently evaluates lower-stress mission alternatives.

### “Is the 3D engine an exact DRDO engine?”

> No. It is an original conceptual aero-piston visualization for subsystem localization. We do not claim proprietary/OEM CAD fidelity.

## Never claim

- real-engine accuracy from synthetic data,
- certified RUL,
- certified mission-success probability,
- autonomous flight-release authority,
- exact OEM/DRDO engine geometry,
- defence-grade cybersecurity.

Those claims require evidence that the current prototype does not yet possess.
