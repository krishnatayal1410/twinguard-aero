from __future__ import annotations
import importlib.util
import sys
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/"backend"))
spec=importlib.util.spec_from_file_location("twinguard_sim",ROOT/"simulator/run.py")
simmod=importlib.util.module_from_spec(spec);spec.loader.exec_module(simmod)
from app.services.twin_manager import manager

FAULTS=[
    "normal",
    "lubrication",
    "overheating",
    "cooling_degradation",
    "vibration",
    "sensor_drift",
    "injector",
    "misfire",
    "combustion_instability",
    "alternator_degradation",
]

print(f"{'Injected':<25} {'Predicted':<25} {'Health':>8} {'RUL':>8} {'Model':>22}")
print("-"*94)
for fault in FAULTS:
    sim=simmod.EngineSimulator()
    sim.config=lambda f=fault:{"fault":f,"severity":0 if f=="normal" else .72}
    state=None
    # Progressive simulator faults ramp instead of jumping instantly. Give each
    # scenario enough samples to reach its requested severity and stabilize.
    for _ in range(70):
        state=manager.ingest(sim.sample())
    print(
        f"{fault:<25} {state['ai']['probable_fault']:<25} "
        f"{state['health']['overall']:>7.1f}% {state['ai']['rul_hours']:>7.1f}h "
        f"{state['ai']['model_state']:>22}"
    )
