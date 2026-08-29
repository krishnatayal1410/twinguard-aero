from __future__ import annotations
import importlib.util,os,sys
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/"backend"))
spec=importlib.util.spec_from_file_location("twinguard_sim",ROOT/"simulator/run.py")
simmod=importlib.util.module_from_spec(spec);spec.loader.exec_module(simmod)
from app.services.twin_manager import manager

print(f"{'Injected':<16} {'Predicted':<16} {'Health':>8} {'RUL':>8}")
print("-"*54)
for fault in ["normal","lubrication","overheating","vibration","sensor_drift","injector","misfire","turbine_blade_degradation"]:
    sim=simmod.EngineSimulator()
    sim.config=lambda f=fault:{"fault":f,"severity":0 if f=="normal" else .72}
    state=None
    for _ in range(10): state=manager.ingest(sim.sample())
    print(f"{fault:<16} {state['ai']['probable_fault']:<16} {state['health']['overall']:>7.1f}% {state['ai']['rul_hours']:>7.1f}h")
