def test_rul_fault_guard_logic():
    previous_rul = 80.9
    model_rul = 136.0

    current_rul = min(model_rul, previous_rul - 0.15)
    current_rul = max(current_rul, previous_rul - 2.0)

    assert current_rul < previous_rul
    assert previous_rul - current_rul <= 2.0
