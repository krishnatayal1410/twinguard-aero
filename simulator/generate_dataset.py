from pathlib import Path
import sys
import random
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from simulator.engine import EngineSimulator
from backend.app.schemas.telemetry import Telemetry
from backend.app.services.physics import expected_state, residuals

OUT = ROOT / "data" / "generated" / "engine_training.csv"
OUT.parent.mkdir(parents=True, exist_ok=True)

rows = []
faults = ["normal", "lubrication", "overheating", "vibration", "sensor_drift"]

missions_per_fault = 10
samples_per_mission = 500

for fault_index, fault in enumerate(faults):
    for mission_index in range(missions_per_fault):
        mission_id = f"{fault}-{mission_index:02d}"
        rng = random.Random(1000 + fault_index * 100 + mission_index)
        target_severity = 0.0 if fault == "normal" else rng.uniform(0.50, 0.90)

        sim = EngineSimulator(seed=2000 + fault_index * 100 + mission_index)

        for step in range(samples_per_mission):
            if fault == "normal":
                current_severity = 0.0
                current_label = "normal"
                sim.set_fault("normal", 0.0)
            else:
                onset = int(samples_per_mission * 0.20)
                progress = max(0.0, (step - onset) / max(1, samples_per_mission - onset - 1))
                current_severity = target_severity * progress
                sim.set_fault(fault, current_severity)
                current_label = fault if current_severity >= 0.10 else "normal"

            row = sim.step()
            t = Telemetry(**row)
            exp = expected_state(t)
            res = residuals(t, exp)

            row.update(res)
            row["fault_label"] = current_label
            row["scenario_fault"] = fault
            row["fault_severity"] = round(current_severity, 4)
            row["mission_id"] = mission_id
            rows.append(row)

df = pd.DataFrame(rows)
df.to_csv(OUT, index=False)

print(
    f"Wrote {len(df):,} rows across {df['mission_id'].nunique()} missions "
    f"to {OUT}"
)
print(df["fault_label"].value_counts().to_dict())
