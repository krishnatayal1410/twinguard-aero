from backend.app.services.decision_support import RULStabilizer
from backend.app.services.simulation_control import (
    SimulationControl,
    SimulationControlRequest,
)


def test_simulation_reset_increments_token_and_clears_fault():
    control = SimulationControl()

    control.set(
        SimulationControlRequest(
            fault="lubrication",
            severity=0.7,
        )
    )

    before = control.get()
    after = control.reset()

    assert before["fault"] == "lubrication"
    assert after["fault"] == "normal"
    assert after["severity"] == 0.0
    assert after["reset_token"] == before["reset_token"] + 1


def test_rul_stabilizer_can_be_reset():
    stabilizer = RULStabilizer()

    value = stabilizer.update(
        raw_rul=120.0,
        health={"overall": 95.0},
        ai={
            "fault": "normal",
            "fault_probability": 0.99,
            "anomaly": False,
        },
    )

    assert value is not None
    assert stabilizer.previous is not None

    stabilizer.reset()

    assert stabilizer.previous is None
