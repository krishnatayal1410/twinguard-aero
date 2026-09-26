# TwinGuard Aero — four-minute evaluator demonstration

Use the running build's actual readings. Never recite a prewritten accuracy, latency, RUL or mission-risk number as a measured result.

## Prepare before the timer

1. Confirm the header identifies **HOSTED DEMO** or **LIVE BACKEND**. For the live backend, sign in and verify incoming telemetry and a decision-eligible data gate.
2. Open **Settings → Simulator**, choose **Reset Healthy**, and allow the state to settle. Keep **Auto Reset** off for the progressive-fault demonstration.
3. For a local demonstration, open **Replay**, name a run `SIH26054 healthy-to-lubrication`, and press **Record**. For the hosted demonstration, use the new **Evaluation Center** workflow below; its exported evidence records the baseline and observations.
4. In the hosted demo, open **Evaluation Center** and press **Start healthy baseline** first. Then open **Mission Lab → Mission Evaluation**. Use **Endurance**, **8 h**, **5,500 m**, **35 °C**, **75% throttle**. These are illustrative model inputs, not a recommended flight profile. Run once and retain the healthy output as an exported snapshot or screenshot; changing pages may clear a component-local result.
5. Return to **Evaluation Center** without restarting the baseline; this keeps the healthy mission within the same evidence session. Rehearse the fault ramp on the actual deployment. Timing depends on runtime and update rate; start the injection before the timed talk if needed, and say that you did so. Keep a recorded synthetic replay available if the presentation network fails.

## Spoken script and screen sequence

| Time | Screen/action | Suggested wording |
|---|---|---|
| 0:00–0:30 | Command Center; show runtime badge | “TwinGuard Aero addresses PS54: an explainable digital twin for aero-piston engine health and mission-profile review. Our prototype asks three connected questions: can we trust the measurement, what evidence explains the engine condition, and what does that condition mean for the proposed operating profile? This demonstration uses synthetic telemetry.” |
| 0:30–1:00 | Diagnostics; expected values, residuals, Sensor Trust | “The twin compares measurements with an operating-condition-aware healthy reference. It then follows residuals over time and checks related channels. An abnormal value alone is not enough to establish a physical fault. Sensor Trust and engine health are separate outputs. The active model and its validation scope remain visible.” |
| 1:00–1:25 | Mission Lab; show healthy run | “We first evaluate one fixed profile. These are transparent simulation indices and RUL projections, not a probability of mission success. Keep the inputs fixed: the next comparison changes the engine condition.” |
| 1:25–1:45 | Hosted: return to the existing Evaluation Center session → Lubrication loss → 85% → Apply selected fault. Local: Settings → Simulator → Lubrication Degradation → Apply Scenario | “We inject a progressive lubrication condition. The simulator is deliberately controllable so the evidence chain can be inspected and repeated. No real aircraft or engine is being controlled.” |
| 1:45–2:40 | Hosted: Evaluation Center baseline/current table; Capture observation → Export evidence while the fault develops. Local: Command Center, then Diagnostics | “Watch oil pressure relative to its expected value, then oil temperature and vibration. The related signals and persistence support a lubrication hypothesis. We can inspect which subsystem is affected, how the health trend changes and what guidance is produced. In the Evaluation Center, we capture the observed state and export its provenance, units and SHA-256 integrity checksum. The checksum detects file changes; it is not a signature proving authenticity.” |
| 2:40–3:20 | Mission Lab; rerun the exact five inputs | “Now we run the same profile on the degraded state. Compare the engineering risk, margin and dominant contributors with the healthy snapshot. We also rescore a lower-stress alternative. The value is a traceable comparison for engineering review, not an automatic flight-release decision.” |
| 3:20–3:40 | Hosted: return to Evaluation Center and Export evidence, including the mission runs. Local: Replay → End, then select the recording | “This record preserves the scenario, observations and model assumptions for review. It proves what we observed in the demonstrator, not independent classifier accuracy. The local backend also supports historical replay and separate evaluation of labeled recordings.” |
| 3:40–4:00 | Settings → Model Info or Diagnostics | “Today we can demonstrate the software chain and synthetic consistency. Our next milestone is authorized test-rig data, calibrated engine maps and held-out validation against a threshold baseline. We will measure false alarms, detection lead time, diagnostic performance and hardware cost before making operational claims.” |

The Evaluation Center scenario controls apply only to hosted synthetic mode. Its browser results are scenario-conditioned and must not be presented as independently detected engine faults. Baseline and observations survive navigation between views during the current page session. After Mission Lab, return and export the evidence so it includes the mission runs. Reloading the page clears this in-memory session, so export before reloading.

## Optional fifth minute: evidence under failure

For a local demonstration, interrupt the simulator using the team's documented process, show **DATA HOLD**, then restore it and confirm recovery. Explain that a connected browser alone does not make old telemetry suitable for a new decision. Do not simulate a network interruption on the hosted demo and claim it proves live-backend recovery.

If a scenario has not developed enough, show the current state honestly or use the already-recorded synthetic run and identify it as a replay. Do not assert the expected diagnosis regardless of the screen.

## Questions evaluators are likely to ask

**What makes this a digital twin rather than a dashboard?**  
The implementation maintains synchronized engine state, computes an expected healthy state, records residual and trend evidence, generates diagnostic/prognostic state, and reuses it for profile comparison and replay. The 3D view is one way of presenting that state.

**What is original about your work?**  
Our contribution is the integrated workflow: measurement trust → explainable subsystem evidence → condition-dependent mission-profile comparison. We are not claiming to have invented digital twins, residual analysis or the model families. The implementation makes their relationship inspectable by an operator and preserves the evidence for engineering review.

**Do you have real DRDO engine data?**  
The repository's current demonstrator uses synthetic data. It does not establish access to proprietary DRDO telemetry or an OEM performance map. The next validation milestone is an authorized dataset or read-only rig connection with agreed signal definitions and labels.

**What exactly is the physics model?**  
A generic low-order aero-piston surrogate estimates several expected channels from operating context such as RPM, load, altitude and ambient temperature. It is not a full thermodynamic solver or a calibrated manufacturer map. Engine-specific calibration is required before real-engine conclusions.

**Is the AI really running?**  
Check the active runtime indicator. The default engineering path uses transparent residual and trend rules. The repository also contains a synthetic Isolation Forest/XGBoost training pipeline and compatible model loading. If native ML is disabled or rejected, we identify the fallback and do not claim an ML model produced that result.

**How accurate is it?**  
Only quote a fresh, versioned evaluation report and state its dataset scope. Automated software checks show expected software behavior; synthetic model scores measure agreement with the generator. Neither establishes field accuracy. Real performance needs independently labeled recordings and held-out engines or operating conditions.

**How can you estimate RUL without run-to-failure data?**  
The present RUL is a simulation-derived engineering estimate. The displayed range is a prototype uncertainty band, not a calibrated probability interval. Operational prognostics would require relevant degradation/maintenance ground truth, censored-data handling where appropriate and calibration over the intended operating envelope.

**How do you distinguish sensor drift from engine damage?**  
We inspect plausibility, rate of change and agreement with related channels. Corroborated pressure, temperature and vibration changes support a physical-fault hypothesis; an isolated inconsistent measurement reduces trust. Common-mode and simultaneous faults remain validation challenges, so the output is a hypothesis for review.

**Can this connect to a real ECU?**  
There is a canonical telemetry contract and a configurable CAN/DBC bridge. A real connection needs the authorized ECU specification, units, ranges, timing and test-rig approval. We do not assume CAN identifiers or claim compatibility with an engine that has not been integrated.

**Does a green mission result authorize a flight?**  
No. It describes the model's engineering index for that input state and profile. It is not a calibrated success probability, flight-release recommendation or certified safety decision. It is an input to engineering review.

**What happens if telemetry stops?**  
The live runtime checks freshness and quality and enters DATA HOLD when current evidence is inadequate. Live ingestion also checks engine identity and timestamp order. The operator can still inspect historical information without treating it as a new live measurement.

**Why have both a hosted demo and a local backend?**  
The hosted synthetic demo gives evaluators immediate access to the workflow. The local/Docker stack demonstrates the actual ingestion, authentication and persistence architecture. A future controlled deployment can retain telemetry within an approved local network; public hosting is not a requirement for operational data.

**Is it defence-grade or certified?**  
The prototype implements useful controls, but certification, adversarial security testing and defence deployment approval have not been established. Those require the target environment, responsible authorities and evidence beyond a hackathon build.

**Can it scale to a fleet today?**  
The current runtime serves one configured engine and process. The module boundaries support extension, but fleet support needs per-engine state isolation, tenancy/authorization, durable event processing, observability and measured load tests. We will not present a scalability roadmap as an already validated fleet deployment.

**What experiment would most strengthen your submission next?**  
An independent labeled test-rig recording spanning healthy operation, transients and known faults. Compare threshold-only, residual-based and hybrid approaches on the same held-out data, report false alarms per hour and time to useful warning, and disclose failure cases.

**What is the practical benefit?**  
An engineer can see why a condition is suspected, compare the consequences of different model inputs and retain the evidence for maintenance review. Reduced aborts, avoided failures and cost savings are future impact measures; we have not measured them on a fleet.

**Are your “confidence” percentages calibrated?**  
Current engineering confidence is a heuristic score and synthetic classifier probabilities depend on synthetic training data. Neither should be read as a verified probability that a diagnosis is correct on real engines. Independent reliability diagrams/calibration tests and out-of-distribution handling are part of the next validation tier.
