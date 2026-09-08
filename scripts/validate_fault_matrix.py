"""Validate every synthetic fault against an isolated Digital Twin pipeline."""

from __future__ import annotations

import importlib.util
import sys
from datetime import UTC, datetime, timedelta
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "backend"))

SIMULATOR_SPEC = importlib.util.spec_from_file_location("twinguard_sim", ROOT / "simulator/run.py")
if SIMULATOR_SPEC is None or SIMULATOR_SPEC.loader is None:
    raise RuntimeError("Unable to load the TwinGuard simulator")

simulator_module = importlib.util.module_from_spec(SIMULATOR_SPEC)
SIMULATOR_SPEC.loader.exec_module(simulator_module)

from app.services.twin_manager import TwinManager  # noqa: E402

FAULTS = (
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
)


def evaluate_fault(fault: str) -> dict:
    """Run one scenario with fresh model history so cases cannot contaminate each other."""
    simulator_module.random.seed(42)
    simulator = simulator_module.EngineSimulator()
    simulator.config = lambda: {
        "fault": fault,
        "severity": 0 if fault == "normal" else 0.72,
    }
    twin = TwinManager()
    state = None
    started_at = datetime.now(UTC)

    for offset in range(70):
        sample = simulator.sample()
        sample["timestamp"] = (started_at + timedelta(seconds=offset)).isoformat()
        state = twin.ingest(sample)

    if state is None:
        raise RuntimeError(f"No state produced for {fault}")
    return state


def main() -> int:
    print(f"{'Injected':<25} {'Predicted':<25} {'Health':>8} {'RUL':>8} {'Model':>22}")
    print("-" * 94)
    failures: list[tuple[str, str]] = []

    for fault in FAULTS:
        state = evaluate_fault(fault)
        predicted = str(state["ai"]["probable_fault"])
        if predicted != fault:
            failures.append((fault, predicted))
        print(
            f"{fault:<25} {predicted:<25} "
            f"{state['health']['overall']:>7.1f}% {state['ai']['rul_hours']:>7.1f}h "
            f"{state['ai']['model_state']:>22}"
        )

    if failures:
        details = ", ".join(f"{injected}→{predicted}" for injected, predicted in failures)
        print(f"\nFAILED: {len(failures)}/{len(FAULTS)} scenarios misclassified: {details}")
        return 1

    print(f"\nPASSED: all {len(FAULTS)} isolated scenarios classified correctly")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
