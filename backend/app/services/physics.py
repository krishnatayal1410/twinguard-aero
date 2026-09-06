from __future__ import annotations
from typing import Dict


class PhysicsEngine:
    """Low-order, explainable aero-piston surrogate physics for MVP use.

    The equations are deliberately generic and are used to create an
    operating-condition-aware healthy baseline. They are not an OEM engine
    performance map and must be calibrated with authorized test-rig/ECU data
    before operational use.
    """

    MODEL_ID = "generic-aero-piston-surrogate-v2"

    def expected(self, t: dict) -> Dict[str, float]:
        rpm = float(t["rpm"])
        throttle = float(t["throttle"])
        altitude = float(t["altitude"])
        ambient = float(t["ambient_temperature"])
        oil_t = float(t["oil_temperature"])
        load = throttle / 100.0

        # Conservative low-order altitude term. It keeps the twin contextual
        # while avoiding a false claim that this is a calibrated thermodynamic
        # model of a specific DRDO engine.
        density_factor = max(0.58, 1.0 - altitude / 21000.0)

        cht = ambient + 105 + 58 * load + 0.0048 * (rpm - 2500) + 10 * (1 - density_factor)
        egt = 500 + 250 * load + 0.015 * (rpm - 2500) + 16 * (1 - density_factor)
        oil_pressure = 3.0 + 0.00046 * rpm - 0.018 * max(oil_t - 85, 0)
        oil_temperature = ambient + 48 + 46 * load + 0.002 * (rpm - 2500)
        fuel_flow = 5.2 + 0.0022 * rpm + 7.2 * load / density_factor
        vibration = 0.16 + abs(rpm - 3900) / 11000 + 0.07 * load
        battery_voltage = 27.6 + 0.25 * min(1, rpm / 2500)
        alternator_voltage = 28.15 if rpm >= 1500 else 25.8 + 2.35 * (rpm / 1500)
        injection_timing = 17.2 + 0.00032 * (rpm - 2500) + 1.6 * load

        return {
            "cht": cht,
            "egt": egt,
            "oil_pressure": oil_pressure,
            "oil_temperature": oil_temperature,
            "fuel_flow": fuel_flow,
            "vibration": vibration,
            "battery_voltage": battery_voltage,
            "alternator_voltage": alternator_voltage,
            "injection_timing": injection_timing,
        }

    def residuals(self, t: dict, expected: dict) -> Dict[str, float]:
        channels = (
            "cht",
            "egt",
            "oil_pressure",
            "oil_temperature",
            "fuel_flow",
            "vibration",
            "battery_voltage",
            "alternator_voltage",
            "injection_timing",
        )
        return {f"{key}_residual": float(t[key]) - float(expected[key]) for key in channels}
