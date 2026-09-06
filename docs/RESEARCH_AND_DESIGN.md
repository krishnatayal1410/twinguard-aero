# TwinGuard Aero — Research and Design Basis

TwinGuard is designed around a strict separation between **visualization**, **state estimation**, **health intelligence** and **mission decision support**.

## 1. A 3D model is not the Digital Twin

The 3D engine helps an operator understand where a condition is occurring, but the Digital Twin is the synchronized computational state behind it:

- observed telemetry,
- operating context,
- expected healthy behavior,
- residuals,
- temporal trends,
- Sensor Trust,
- subsystem health,
- diagnostic hypotheses,
- RUL/degradation state,
- mission-risk state,
- replay/evidence history.

This is why TwinGuard can continue operating even if the WebGL view is unavailable.

## 2. Hybrid rather than black-box-first

The proof-of-concept follows this reasoning chain:

```text
Operating condition
→ expected healthy state
→ observed - expected residuals
→ temporal/multi-signal evidence
→ anomaly / fault hypothesis
→ health / degradation
→ mission impact
```

A learned model can be inserted into the diagnostic/prognostic stages, but it does not replace the expected-state model, provenance or evidence chain.

## 3. Why residuals matter

A fixed threshold asks whether a value crossed a universal limit.

TwinGuard instead also asks whether the measurement is abnormal **for the current operating state**. The same CHT, EGT or oil-pressure value can carry different meaning at different RPM, load, altitude and ambient conditions.

The current baseline is a generic low-order aero-piston surrogate. Real deployment requires target-engine performance maps or calibrated physics.

## 4. Why time matters

Single-sample rules are fragile. TwinGuard therefore tracks rates and persistence such as:

- pressure decline,
- temperature rise,
- vibration growth,
- electrical decay,
- health-index decline,
- consecutive anomaly persistence.

This allows the system to distinguish a transient/noisy sample from a developing degradation pattern.

## 5. Sensor Trust is separate from engine health

A sensor that disagrees with a healthy model is not automatically faulty: the engine itself may be degraded.

TwinGuard therefore considers **corroboration**. A low oil-pressure residual combined with increasing oil temperature and vibration supports a physical lubrication condition. A large isolated oil-pressure deviation without correlated evidence is more suspicious as a sensor/data problem.

## 6. Mission-aware prognosis

RUL by itself is not a mission decision. An engine with an estimated 5 h of remaining useful operation has very different implications for a 30 min return leg versus a 6 h high-load continuation.

The Mission Reliability Twin therefore uses:

- current subsystem health,
- active diagnostic condition,
- degradation rate,
- anomaly persistence,
- simulation-derived RUL margin,
- planned duration,
- altitude,
- ambient temperature,
- average throttle/load.

It reports an engineering **Mission Feasibility Index** rather than pretending to know a calibrated real-world probability of mission success.

## 7. Counterfactual planning

A useful twin should not only say that risk is high. It should let the operator/engineer test a modified mission profile.

TwinGuard independently rescores a lower-stress alternative using reduced duration/load/altitude rather than displaying a hard-coded recommendation.

## 8. Explainability

Every major decision should be traceable to evidence:

```text
Telemetry
→ expected state
→ residual
→ trend/persistence
→ corroborating sensors
→ subsystem health
→ fault hypothesis
→ mission-risk contributors
```

This is more defensible than displaying only an AI label or a confidence percentage.

## 9. Web 3D strategy

The current HMI uses a **procedural Three.js / React Three Fiber aero-piston representation** instead of the previous turboshaft-style GLB semantics. It represents cylinder banks, crankcase, lubrication, induction/fuel, exhaust/thermal and electrical modules.

The purpose is subsystem localization and state visualization—not geometric certification or OEM CAD fidelity.

## 10. Real telemetry integration principle

TwinGuard treats the simulator as one telemetry adapter. Moving to hardware should replace the source adapter, not the downstream Digital Twin contract:

```text
Simulator / MQTT / CAN / ECU replay
              ↓
        Canonical schema
              ↓
       Same Twin pipeline
```

This prevents the prototype from being architecturally tied to synthetic data.

## 11. Research claims policy

The project deliberately distinguishes:

- **working software architecture**,
- **synthetic scenario behavior**,
- **generic engineering assumptions**,
- **future engine-specific validation**.

Synthetic metrics, health percentages, RUL and mission indices must not be represented as validated MALE-UAV engine performance until authorized real-engine evidence exists.
