from __future__ import annotations
def _c(v): return max(0,min(100,float(v)))

class HealthEngine:
    def compute(self,t,r,trust):
        thermal=_c(99 - abs(r["cht_residual"])*0.75 - abs(r["egt_residual"])*0.18 - max(0,t["cht"]-215)*.45)
        lube=_c(99 - max(0,-r["oil_pressure_residual"])*22 - max(0,r["oil_temperature_residual"])*.65 - max(0,90-trust["oil_pressure"])*.20)
        mech=_c(99 - max(0,t["vibration"]-.27)*65 - abs(r["vibration_residual"])*28)
        elec=_c(99 - abs(r["battery_voltage_residual"])*8)
        overall=.31*thermal+.31*lube+.27*mech+.11*elec
        return {"thermal":thermal,"lubrication":lube,"mechanical":mech,"electrical":elec,"overall":overall}

def readiness(health, ai, maintenance):
    if health["overall"]<67 or maintenance["priority"]=="NO_GO":
        return {"status":"NO_GO","label":"NO-GO","reason":"Current predicted engine condition is not suitable for mission release."}
    if ai.get("anomaly") or health["overall"]<86 or maintenance["priority"]=="INSPECT_BEFORE_NEXT_MISSION":
        return {"status":"REVIEW","label":"REVIEW","reason":"Engineering review is recommended before mission release."}
    return {"status":"READY","label":"READY","reason":"Current synthetic twin state is within nominal mission-release limits."}
