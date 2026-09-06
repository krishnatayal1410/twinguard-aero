from __future__ import annotations

CHECKS = {
    "normal": ["Continue routine condition monitoring and trend review."],
    "lubrication": [
        "Verify oil-pressure measurement and line integrity.",
        "Inspect oil level, pump, filter and lubrication circuit.",
        "Review oil-temperature trend.",
        "Inspect bearings / rotating components if vibration is elevated.",
    ],
    "overheating": [
        "Inspect cylinder-head cooling path and airflow.",
        "Verify CHT/EGT instrumentation.",
        "Review mixture/injection, ignition and sustained high-load exposure.",
    ],
    "cooling_degradation": [
        "Inspect cooling airflow, ducting and liquid-cooling circuit where applicable.",
        "Check coolant condition/flow and cylinder-head thermal trend.",
        "Review high-altitude and hot-weather exposure.",
    ],
    "vibration": [
        "Inspect engine mounts, propeller/reduction-drive balance and rotating components.",
        "Check bearing condition and mechanical looseness.",
        "Verify vibration sensor installation and calibration.",
    ],
    "sensor_drift": [
        "Cross-check the suspect sensor against correlated signals.",
        "Inspect wiring, connector and calibration.",
        "Use physics consistency before authorizing mechanical replacement.",
    ],
    "injector": [
        "Inspect injector flow consistency and fuel delivery.",
        "Review fuel-flow and EGT behavior.",
        "Check injection timing / mixture control.",
    ],
    "misfire": [
        "Inspect ignition and combustion stability.",
        "Review EGT and vibration signatures.",
        "Check fuel delivery and ignition subsystem.",
    ],
    "combustion_instability": [
        "Review cylinder/EGT behavior for unstable combustion.",
        "Inspect ignition, mixture/fuel delivery and timing consistency.",
        "Check vibration and RPM oscillation history.",
    ],
    "alternator_degradation": [
        "Verify alternator output under load.",
        "Inspect regulator, wiring, grounds and electrical connections.",
        "Check battery state and bus-voltage trend.",
    ],
}


class MaintenanceEngine:
    def decide(self, health, ai, trust):
        fault = ai["probable_fault"]
        if health["overall"] < 67 or ai["rul_hours"] < 30:
            priority = "NO_GO"
        elif ai["anomaly"] or health["overall"] < 87 or ai["rul_hours"] < 80:
            priority = "INSPECT_BEFORE_NEXT_MISSION"
        else:
            priority = "MONITOR"

        affected = {
            "lubrication": "Lubrication",
            "overheating": "Thermal",
            "cooling_degradation": "Cooling",
            "vibration": "Mechanical / Propulsion Mounting",
            "sensor_drift": "Sensor / Data Integrity",
            "injector": "Fuel / Combustion",
            "misfire": "Ignition / Combustion",
            "combustion_instability": "Combustion",
            "alternator_degradation": "Electrical / Alternator",
        }.get(fault, "None")

        return {
            "priority": priority,
            "affected_subsystem": affected,
            "recommended_checks": CHECKS.get(fault, CHECKS["normal"]),
            "reason": (
                f"Probable condition: {fault}. Engineering health index "
                f"{health['overall']:.1f}/100; simulation-derived RUL {ai['rul_hours']:.1f} h."
            ),
            "next_mission_suitability": "NOT_RECOMMENDED" if priority == "NO_GO" else "REVIEW" if priority != "MONITOR" else "READY",
            "validation_scope": "PROTOTYPE_DECISION_SUPPORT_ONLY",
        }
