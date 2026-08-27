from pathlib import Path
import sys
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from simulator.engine import EngineSimulator
from backend.app.schemas.telemetry import Telemetry
from backend.app.services.physics import expected_state, residuals
from backend.app.services.health import calculate_health

OUT = ROOT / "data" / "generated" / "rul_training.csv"
rows = []

missions = 30
steps = 700

for mission_index in range(missions):
    sim = EngineSimulator(seed=5000 + mission_index)
    mission_id = f"degradation-{mission_index:02d}"

    for step in range(steps):
        severity = min(1.0, step / (steps - 1))
        sim.set_fault("lubrication", severity)
        row = sim.step()

        t = Telemetry(**row)
        exp = expected_state(t)
        res = residuals(t, exp)
        health = calculate_health(t.model_dump(), res)

        # Synthetic target: remaining operating hours until simulated threshold.
        remaining_fraction = max(0.0, 1.0 - severity)
        base_life = 180 + (mission_index % 7) * 4
        rul_hours = remaining_fraction * base_life

        row.update(res)
        row["health_overall"] = health["overall"]
        row["mission_id"] = mission_id
        row["rul_hours"] = round(rul_hours, 3)
        rows.append(row)

pd.DataFrame(rows).to_csv(OUT, index=False)
print(f"Wrote {len(rows):,} RUL rows to {OUT}")
