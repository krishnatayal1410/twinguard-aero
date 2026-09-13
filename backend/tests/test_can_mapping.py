import pytest
from app.integrations.can_bridge import SignalAssembler

VALUES = {
    "rpm": 4000,
    "throttle": 70,
    "cht": 180,
    "egt": 700,
    "oil_pressure": 450,
    "oil_temperature": 105,
    "fuel_flow": 20,
    "vibration": 0.2,
    "battery_voltage": 28,
    "altitude": 4000,
    "ambient_temperature": 25,
}


def test_can_units_assembly_and_stale_signal_hold():
    mapping = {key: {"signal": key} for key in VALUES}
    mapping["oil_pressure"]["scale"] = 0.01  # Vendor kPa to canonical bar.
    assembler = SignalAssembler(mapping)
    assert assembler.update({"rpm": 4000}, now=0) is None
    sample = assembler.update(VALUES, now=1)
    assert sample["oil_pressure"] == 4.5
    assert assembler.update({"rpm": 4100}, now=4) is None
    assert assembler.update({"unmapped": 1}, now=5) is None


def test_can_rejects_incomplete_mapping_and_impossible_sensor_value():
    with pytest.raises(ValueError):
        SignalAssembler({"rpm": {"signal": "rpm"}})
    assembler = SignalAssembler({key: {"signal": key} for key in VALUES})
    with pytest.raises(ValueError):
        assembler.update(VALUES)
