# Demo Flow

1. Start TwinGuard with `bash scripts/start_local.sh`.
2. Open OPS DECK and show healthy live telemetry and the synchronized 3D engine.
3. Open TWIN LAB and isolate thermal / lubrication / mechanical / electrical systems.
4. Run an 8 h, 5500 m, 35 °C, 75% Endurance mission in MISSION mode.
5. Start mission recording in REPLAY.
6. Open the Fault Injection drawer and inject **Lubrication 70%**.
7. Watch oil pressure decrease, oil temperature/vibration increase, residuals react, the AI classify lubrication degradation, health/RUL fall and maintenance change.
8. Open DIAGNOSTICS to show physics evidence, AI confidence, Sensor Trust, Data Quality and residuals.
9. Run the exact same mission again and show the degraded mission outcome.
10. Show the lower-stress counterfactual mission.
11. End recording and show the post-flight event timeline in REPLAY.
12. Open MAINTENANCE and show the affected subsystem, RUL, inspection plan and next-mission suitability.
13. Reset Healthy.

All values and AI performance are synthetic proof-of-concept outputs until calibrated/validated on a real engine or test rig.
