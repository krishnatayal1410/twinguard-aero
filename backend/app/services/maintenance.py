from __future__ import annotations
CHECKS={
 "normal":["Continue routine condition monitoring and trend review."],
 "lubrication":["Verify oil-pressure measurement and line integrity.","Inspect oil level, pump, filter and lubrication circuit.","Review oil-temperature trend.","Inspect bearings / rotating components if vibration is elevated."],
 "overheating":["Inspect cooling airflow and cylinder-head cooling surfaces.","Verify CHT/EGT sensors.","Inspect mixture, combustion and ignition condition.","Review hot-weather / high-load exposure."],
 "vibration":["Inspect mounts, propeller/shaft balance and rotating components.","Check bearing condition and mechanical looseness.","Verify vibration sensor installation and calibration."],
 "sensor_drift":["Cross-check the suspect sensor against correlated signals.","Inspect wiring, connector and calibration.","Use physics consistency before authorizing mechanical replacement."],
 "injector":["Inspect injector flow consistency and fuel delivery.","Review fuel-flow and EGT spread.","Check injection timing / mixture control."],
 "misfire":["Inspect ignition and combustion stability.","Review EGT and vibration signatures.","Check injector and ignition subsystem."],
 "turbine_blade_degradation":["Inspect turbine/blade condition and rotating assembly.","Review vibration trend and EGT residuals.","Inspect bearing/shaft alignment and hot-section evidence.","Perform borescope or authorized internal inspection before release."]
}
class MaintenanceEngine:
    def decide(self,health,ai,trust):
        fault=ai["probable_fault"]
        if health["overall"]<67 or ai["rul_hours"]<30:
            priority="NO_GO"
        elif ai["anomaly"] or health["overall"]<87 or ai["rul_hours"]<80:
            priority="INSPECT_BEFORE_NEXT_MISSION"
        else:
            priority="MONITOR"
        affected={"lubrication":"Lubrication","overheating":"Thermal / Cooling","vibration":"Mechanical","sensor_drift":"Sensor / Data","injector":"Fuel / Combustion","misfire":"Ignition / Combustion","turbine_blade_degradation":"Turbine / Hot Section"}.get(fault,"None")
        return {"priority":priority,"affected_subsystem":affected,"recommended_checks":CHECKS.get(fault,CHECKS["normal"]),"reason":f"Probable condition: {fault}. Overall health {health['overall']:.1f}%, RUL {ai['rul_hours']:.1f} h.","next_mission_suitability":"NOT_RECOMMENDED" if priority=="NO_GO" else "REVIEW" if priority!="MONITOR" else "READY"}
