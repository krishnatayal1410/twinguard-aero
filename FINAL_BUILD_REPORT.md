# TwinGuard Aero — SIH26054 Overhaul Verification Report

**Branch:** `sih26054-overhaul`  
**Target repository:** `krishnatayal1410/twinguard-aero`  
**Main branch status:** intentionally left unchanged pending review/merge authorization.

## Completion status

**Substantially completed and verified as a synthetic software proof-of-concept.**

The overhaul corrects the previous propulsion-system mismatch, strengthens the Digital Twin logic, removes unsupported mission claims, adds temporal degradation intelligence, retrains the synthetic model pack against the new aero-piston contract, and introduces automated end-to-end verification.

It does **not** establish real MALE-UAV engine validation, certified RUL, calibrated mission-success probability, OEM/DRDO geometric fidelity, or operational airworthiness.

---

## Automated verification evidence

Latest CI gate on the overhaul branch:

- Python setup / dependency install: **PASS**
- Python compilation: **PASS**
- Backend test suite: **PASS**
- Frontend dependency install: **PASS**
- TypeScript typecheck / Vite production build: **PASS**
- Live FastAPI backend startup: **PASS**
- Live simulator startup: **PASS**
- End-to-end system verifier: **PASS**
- Authentication flow: **PASS**
- Synchronized Digital Twin state: **PASS**
- Aero-piston physics-model identity: **PASS**
- Temporal trend availability: **PASS**
- Diagnostics / confidence output: **PASS**
- Maintenance output: **PASS**
- Mission Reliability Twin output: **PASS**
- Progressive lubrication scenario observability: **PASS**
- Mission replay flow: **PASS**

The integration verifier launches the actual backend and simulator together instead of testing only isolated functions.

---

## Synthetic model pack

A fresh `aero-piston-v2` synthetic model pack was trained and runtime-contract checked.

Recorded synthetic proof-of-concept metrics:

- Fault classification accuracy: **0.8909**
- Fault macro F1: **0.8880**
- RUL MAE: **10.186 h**
- RUL RMSE: **12.490 h**
- RUL R²: **0.6779**

These numbers come from synthetic data produced by the proof-of-concept generator. They are useful for software/model-development validation only and must **not** be represented as real-engine accuracy or real RUL performance.

The model manifest now records:

- schema: `aero-piston-v2`
- training source: synthetic physics-inspired generator
- validation scope: `SYNTHETIC_PROOF_OF_CONCEPT`
- 10 aero-piston-relevant fault classes
- a 22-feature telemetry/residual contract

Runtime model loading rejects stale artifacts whose feature order or fault taxonomy does not match the current contract.

---

## Major corrections completed

### 1. Correct propulsion-system identity

The previous UI and failure taxonomy contained turboshaft concepts such as compressor/turbine stages and turbine-blade degradation. The overhaul aligns the product with the SIH26054 aero-piston-engine target.

The new conceptual 3D HMI represents:

- horizontally opposed cylinder banks,
- crankcase / rotating core,
- lubrication subsystem,
- fuel / induction path,
- exhaust / thermal path,
- electrical / alternator subsystem.

The 3D geometry is an original conceptual visualization, not proprietary CAD and not the physics model itself.

### 2. Canonical telemetry and units

The Pydantic telemetry schema is now the source of truth and explicitly documents units, including oil pressure in bar for the current proof-of-concept.

Added/retained channels include:

- RPM,
- throttle,
- CHT,
- EGT,
- oil pressure,
- oil temperature,
- fuel flow,
- vibration,
- battery voltage,
- alternator voltage,
- altitude,
- ambient temperature,
- injection/ignition timing proxy,
- operating hours.

### 3. Fixed simulator control path

The simulator can now read the selected fault configuration using the ingest credential. Fault selection no longer silently falls back to healthy operation because of operator-authentication mismatch.

### 4. Progressive aero-piston fault scenarios

The simulator now supports:

- normal,
- lubrication degradation,
- overheating,
- cooling degradation,
- abnormal vibration,
- sensor drift,
- injector abnormality,
- misfire,
- combustion instability,
- alternator degradation.

Fault severity develops progressively instead of switching instantaneously.

### 5. Expected-state Digital Twin

The physics layer is explicitly identified as `generic-aero-piston-surrogate-v2`.

It calculates operating-condition-aware expected values and residuals for thermal, lubrication, fuel, vibration and electrical/timing channels.

This is a low-order generic surrogate for architecture demonstration, not a calibrated OEM performance map.

### 6. Temporal intelligence

TwinGuard now retains short-window history and evaluates:

- oil-pressure trend,
- oil-temperature trend,
- CHT trend,
- EGT trend,
- vibration trend,
- battery-voltage trend,
- alternator-voltage trend,
- health-index trend,
- anomaly persistence.

Fault/RUL fallback logic therefore uses both current residuals and degradation direction.

### 7. Sensor Trust redesign

Sensor Trust is no longer equivalent to “distance from healthy physics.”

A corroborated physical degradation can create large residuals while its sensors remain credible. Isolated implausible disagreement or sudden jumps reduce trust more strongly.

This helps distinguish:

```text
real engine degradation
```

from:

```text
possible sensor/data fault
```

### 8. Expanded subsystem health

Current engineering health indices:

- thermal,
- lubrication,
- mechanical,
- combustion,
- electrical,
- sensor integrity,
- overall.

These are transparent prototype engineering scores, not certified airworthiness percentages.

### 9. Diagnostic provenance and safe ML loading

The runtime exposes:

- model state,
- feature contract,
- validation scope,
- RUL basis,
- model compatibility warning.

Incompatible old binaries are rejected rather than silently used with the wrong feature or fault definitions.

### 10. Mission Reliability Twin

Mission analysis now considers:

- current health,
- subsystem condition,
- degradation rate,
- anomaly persistence,
- simulation-derived RUL,
- RUL / mission-duration margin,
- planned mission duration,
- cruise altitude,
- ambient temperature,
- average throttle/load.

Outputs now include:

- risk class,
- Mission Feasibility Index,
- stress index,
- post-mission health,
- post-mission RUL,
- RUL margin,
- subsystem mission risks,
- dominant risk factors,
- lower-stress counterfactual profile,
- independently rescored counterfactual risk.

The old hard-coded mission-success/fuel-burn style values were removed from the command center.

### 11. Evidence-led HMI

The frontend now communicates:

```text
Observed state
→ Expected state
→ Residuals
→ Trends / persistence
→ Sensor corroboration
→ Fault hypothesis
→ Subsystem health
→ RUL
→ Mission risk
→ Counterfactual
```

instead of treating a 3D model or unexplained AI percentage as the Digital Twin.

### 12. Documentation and demo narrative

The README, validation notes, research/design basis and SIH demo flow were rewritten around the actual aero-piston hybrid Digital Twin architecture and truthful validation boundary.

---

## What is genuinely verified

The current repository demonstrates that its synthetic software architecture can operate coherently end to end:

```text
Simulator
→ FastAPI ingestion
→ synchronized Twin state
→ expected behavior
→ residuals
→ temporal evidence
→ health / diagnosis
→ mission analysis
→ replay
```

The frontend also compiles successfully as a production Vite build.

---

## What is not yet validated

The following remain outside the evidence available in this repository:

1. Target DRDO/OEM engine-specific calibration.
2. Real ECU/test-rig telemetry validation.
3. Real fault-label ground truth.
4. Real run-to-failure RUL validation.
5. Calibrated probability of mission completion.
6. Flight-safety or maintenance certification.
7. Real-world Sensor Trust false-positive/false-negative characterization.
8. Environmental-envelope validation across a specific engine's operating limits.
9. Defence-grade cybersecurity assessment.
10. Full deployment validation against real CAN/ECU hardware.
11. Exact proprietary MALE-UAV engine geometry.

---

## Strongest current SIH demonstration

Recommended live story:

```text
Healthy engine / mission baseline
        ↓
Progressive lubrication degradation injected
        ↓
Oil-pressure residual becomes increasingly negative
Oil-temperature and vibration provide corroborating evidence
        ↓
Temporal persistence increases
        ↓
Lubrication health and overall health decline
        ↓
Diagnostic condition becomes visible with evidence
        ↓
Simulation-derived RUL decreases
        ↓
Run the SAME mission profile again
        ↓
Mission feasibility/risk changes because engine state changed
        ↓
TwinGuard independently rescores a lower-stress alternative
        ↓
Replay preserves the evidence chain
```

That is the central TwinGuard value proposition: **translate synchronized engine degradation into explainable mission-level reliability intelligence.**

---

## Recommended next validation tier

The next meaningful improvement is not adding more decorative features. It is replacing generic assumptions with engine-specific evidence:

1. obtain authorized target-engine signal definitions and units,
2. obtain healthy ECU/test-rig telemetry across operating conditions,
3. calibrate expected-state maps,
4. validate normal transients separately from faults,
5. collect known fault/degradation cases,
6. build component-specific prognostic ground truth,
7. calibrate uncertainty and false-alarm behavior,
8. validate mission-risk rules with propulsion/UAV domain experts,
9. integrate a real CAN/ECU replay source,
10. repeat the automated verification suite using those real inputs.

Until that tier is complete, the correct status is:

> **Verified synthetic hybrid Digital Twin software demonstrator for aero-piston engine health and mission-reliability research.**
