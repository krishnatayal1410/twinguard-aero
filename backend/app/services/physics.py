from __future__ import annotations
from typing import Dict

class PhysicsEngine:
    """Low-order, explainable aero-piston surrogate physics for MVP use.

    These equations are intentionally generic and must be calibrated to the
    actual engine/test-rig before operational use.
    """
    def expected(self, t: dict) -> Dict[str,float]:
        rpm = float(t["rpm"]); throttle=float(t["throttle"])
        altitude=float(t["altitude"]); ambient=float(t["ambient_temperature"])
        oil_t=float(t["oil_temperature"])
        load = throttle/100.0
        density_factor=max(0.58, 1.0-altitude/21000.0)
        cht = ambient + 105 + 58*load + 0.0048*(rpm-2500) + 10*(1-density_factor)
        egt = 500 + 250*load + 0.015*(rpm-2500) + 16*(1-density_factor)
        oil_pressure = 3.0 + 0.00046*rpm - 0.018*max(oil_t-85,0)
        oil_temperature = ambient + 48 + 46*load + 0.002*(rpm-2500)
        fuel_flow = 5.2 + 0.0022*rpm + 7.2*load/density_factor
        vibration = 0.16 + abs(rpm-3900)/11000 + 0.07*load
        battery_voltage = 27.6 + 0.25*min(1,rpm/2500)
        return {
            "cht": cht, "egt": egt, "oil_pressure": oil_pressure,
            "oil_temperature": oil_temperature, "fuel_flow": fuel_flow,
            "vibration": vibration, "battery_voltage": battery_voltage,
        }

    def residuals(self, t: dict, e: dict) -> Dict[str,float]:
        out={}
        for k in ("cht","egt","oil_pressure","oil_temperature","fuel_flow","vibration","battery_voltage"):
            out[f"{k}_residual"] = float(t[k])-float(e[k])
        return out
