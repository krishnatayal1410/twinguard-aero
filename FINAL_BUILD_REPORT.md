# TwinGuard Aero — SIH26054 Verified Build Report

**Repository:** `krishnatayal1410/twinguard-aero`  
**Verified branch:** `main`  
**Verified merge commit:** `94a2a26033d0c868b6b8a9c98e9b04dbe15de17e`  
**CI run:** `34016621172`  
**CI result:** **PASS**

## Completion status

**Substantially completed and verified as a synthetic software proof-of-concept.**

The SIH26054 overhaul is merged into `main` and the post-merge CI pipeline passed backend, frontend and live integration gates.

TwinGuard now aligns to the actual problem target: a mission-aware hybrid Digital Twin for **aero-piston engines used in MALE UAVs**. It no longer relies on the previous turboshaft/turbine-blade runtime framing or hard-coded mission-success values.

It does **not** establish real MALE-UAV engine validation, certified RUL, calibrated mission-success probability, OEM/DRDO geometric fidelity, or operational airworthiness.

---

## Post-merge verification evidence

The verified `main` CI run passed:

- Docker Compose configuration validation: **PASS**
- Python dependency/setup path: **PASS**
- Python compilation: **PASS**
- SIH26054 aero-piston domain-consistency guard: **PASS**
- production signup-default security gate: **PASS**
- backend regression/unit suite: **PASS**
- packaged native synthetic ML artifact loading: **PASS**
- frontend dependency installation: **PASS**
- TypeScript/Vite production build: **PASS**
- live FastAPI backend startup: **PASS**
- live synthetic simulator startup: **PASS**
- end-to-end system verifier: **PASS**
- authentication flow: **PASS**
- synchronized Digital Twin state: **PASS**
- runtime telemetry-validity gate: **PASS**
- RUL uncertainty band: **PASS**
- maintenance output: **PASS**
- Mission Reliability Twin output: **PASS**
- conservative mission margin / decision horizon: **PASS**
- progressive lubrication degradation observability: **PASS**
- same-mission degraded-state reliability direction: **PASS**
- mission replay flow: **PASS**

The integration verifier runs the actual backend and simulator together rather than validating only isolated functions.

---

## Verified architecture

```text
Simulator / future ECU-CAN-MQTT source
            │
            ▼
Canonical Telemetry Contract
            │
            ▼
FastAPI validation + synchronization
            │
            ▼
Real-Time Twin State
            │
     ┌──────┴──────┐
     ▼             ▼
Observed       Expected Healthy
State          Surrogate State
     └──────┬──────┘
            ▼
         Residuals
            │
            ▼
 Temporal Trends / Persistence
            │
   ┌────────┼────────┐
   ▼        ▼        ▼
Sensor   Diagnosis  Health
Trust    / Anomaly  Indices
   └────────┼────────┘
            ▼
      RUL + Uncertainty
            │
            ▼
 Mission Reliability Twin
            │
   ┌────────┴─────────┐
   ▼                  ▼
Mission Margin    Counterfactual
Decision Horizon  Lower-Stress Plan
            │
            ▼
 Explainability / Replay / HMI
```

---

## Major engineering corrections

### 1. Correct propulsion-system identity

Runtime taxonomy and HMI are now aero-piston specific. The conceptual 3D HMI represents cylinder banks, crankcase/rotating core, lubrication, fuel/induction, exhaust/thermal and electrical/alternator subsystems.

The 3D geometry is an engineering visualization, not proprietary CAD and not the Digital Twin physics model itself.

### 2. Canonical telemetry and units

The Pydantic telemetry schema is the source of truth. Current proof-of-concept channels include RPM, throttle, CHT, EGT, oil pressure, oil temperature, fuel flow, vibration, battery voltage, alternator voltage, altitude, ambient temperature, timing proxy and operating hours.

Oil pressure is explicitly represented in **bar** in the current demonstrator.

### 3. Progressive aero-piston fault simulation

The synthetic simulator supports:

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

Fault severity ramps progressively so the demo shows degradation developing over time.

### 4. Expected-state hybrid Twin

The physics layer is identified as `generic-aero-piston-surrogate-v2` and produces operating-condition-aware expected values and observed-minus-expected residuals.

This is intentionally a generic low-order surrogate, not an OEM performance map.

### 5. Sensor Trust redesign

Sensor Trust is separated from engine health. A real multi-signal degradation can produce large residuals while the underlying sensors remain credible; isolated, poorly corroborated disagreement can instead reduce sensor trust.

### 6. Expanded subsystem health

Current prototype engineering health indices:

- thermal,
- lubrication,
- mechanical,
- combustion,
- electrical,
- sensor integrity,
- overall.

These are not certified airworthiness percentages.

### 7. Temporal intelligence

The Twin tracks short-window trends for oil pressure, oil temperature, CHT, EGT, vibration, battery voltage, alternator voltage and overall health, plus anomaly persistence.

### 8. Diagnostic / prognostic model provenance

The stable default computation path is explicit `ENGINEERING_FALLBACK` logic. A compatible packaged synthetic Isolation Forest/XGBoost fault/RUL model pack is also present and separately verified by CI when native ML is enabled.

The runtime validates feature order and fault taxonomy before native artifacts are accepted.

### 9. RUL uncertainty

TwinGuard now exposes:

- RUL point estimate,
- conservative lower bound,
- upper bound,
- uncertainty-band basis,
- explicit flag that the band is **not a calibrated probability interval**.

Mission analysis uses the conservative lower RUL bound rather than blindly trusting the point estimate.

### 10. Mission Reliability Twin

Mission analysis considers current Twin health, subsystem condition, degradation trend, anomaly persistence, uncertainty-aware RUL margin, mission duration, altitude, ambient temperature, average load and an explicit mission-profile duty-cycle modifier.

Supported mission profiles:

- endurance,
- high altitude,
- hot weather,
- rapid throttle,
- patrol.

Outputs include:

- overall risk class,
- Mission Feasibility Index,
- stress index,
- current and post-mission RUL bands,
- conservative RUL/mission ratio,
- projected profile endurance,
- mission margin,
- engineering reserve,
- decision horizon,
- subsystem mission risks,
- dominant risk factors,
- independently rescored lower-stress counterfactual profile.

The Mission Feasibility Index is a transparent **prototype decision-support index**, not a calibrated probability of mission success.

### 11. Fail-safe data validity

TwinGuard separates transport connectivity from decision eligibility.

If telemetry becomes stale or data quality falls below the configured threshold, the runtime enters `DATA HOLD` and blocks new Mission Reliability Twin analysis until valid synchronization is restored.

### 12. Evidence-led HMI

The operator interface communicates:

```text
Observed state
→ Expected state
→ Residuals
→ Trends / persistence
→ Sensor corroboration
→ Fault hypothesis
→ Subsystem health
→ RUL + uncertainty
→ Mission margin / horizon
→ Counterfactual
```

Hard-coded future mission success/fuel-burn claims were removed.

### 13. Deployment and security hardening

The demonstrator includes:

- FastAPI REST/WebSocket backend,
- local authentication and expiring sessions,
- PBKDF2-SHA256 password hashing,
- separate telemetry ingest key,
- explicit CORS/trusted-host controls,
- production signup disabled by default,
- Docker Compose health ordering,
- SQLite local persistence,
- PostgreSQL/TimescaleDB deployment path,
- MQTT, CAN/SocketCAN and Unreal integration scaffolds.

---

## Synthetic model pack

Current packaged model artifacts use the `aero-piston-v2` feature/taxonomy contract and are verified for load/execution in CI.

Recorded synthetic proof-of-concept metrics from the synthetic generator/model evaluation include approximately:

- Fault classification accuracy: **0.8909**
- Fault macro F1: **0.8880**
- RUL MAE: **10.186 h**
- RUL RMSE: **12.490 h**
- RUL R²: **0.6779**

These are **synthetic model-development metrics only** and must not be represented as real-engine accuracy, reliability, or RUL performance.

---

## What is genuinely verified

The repository demonstrates that the software architecture operates coherently end to end with synthetic telemetry:

```text
Simulator
→ FastAPI ingestion
→ synchronized Twin state
→ expected behavior
→ residuals
→ temporal evidence
→ health / diagnosis
→ RUL uncertainty
→ mission reliability analysis
→ replay / HMI
```

The frontend also passes a production TypeScript/Vite build and the backend passes the post-merge automated test/integration pipeline.

---

## What is not yet validated

The repository does not currently provide evidence for:

1. target DRDO/OEM engine-specific calibration,
2. real ECU/test-rig telemetry validation,
3. real fault-label ground truth,
4. real run-to-failure RUL validation,
5. statistically calibrated mission-completion probability,
6. flight-safety or maintenance certification,
7. real-world Sensor Trust false-positive/false-negative characterization,
8. full specific-engine operating-envelope validation,
9. defence-grade cybersecurity assessment,
10. deployment against real CAN/ECU hardware,
11. exact proprietary MALE-UAV engine geometry.

---

## Strongest current SIH demonstration

```text
Healthy synchronized engine Twin
        ↓
Run baseline mission
        ↓
Record RUL band + mission margin + decision horizon
        ↓
Inject progressive lubrication degradation
        ↓
Oil-pressure residual worsens
Oil-temperature/vibration corroborate
        ↓
Temporal persistence increases
        ↓
Lubrication/overall health decline
        ↓
Diagnostic evidence + RUL band change
        ↓
Run the SAME mission again
        ↓
Mission margin / feasibility / horizon worsen
        ↓
TwinGuard rescores a lower-stress alternative
        ↓
Replay preserves the evidence chain
```

This directly demonstrates the core TwinGuard value proposition:

> **Given this specific engine condition right now, what does it mean for the mission we are about to fly?**

---

## Recommended next validation tier

The next high-value work is not adding decorative features. It is replacing generic assumptions with engine-specific evidence:

1. obtain authorized target-engine signal definitions, units and sampling rates,
2. obtain healthy ECU/test-rig telemetry across the relevant operating envelope,
3. calibrate expected-state maps,
4. separate normal transients from true degradations,
5. collect known fault/degradation cases,
6. establish component degradation/maintenance ground truth,
7. validate and calibrate RUL uncertainty,
8. characterize false alarms and missed detections,
9. validate mission-risk rules with propulsion/UAV domain experts,
10. integrate real CAN/ECU replay and repeat the automated verification suite.

Until that tier is complete, the correct status is:

> **Verified synthetic hybrid Digital Twin software demonstrator for aero-piston engine health and mission-reliability research.**
