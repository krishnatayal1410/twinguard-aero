import{Activity,AlertTriangle,BatteryCharging,Database,Droplets,Fuel,HeartPulse,Mountain,Shield,Signal,Thermometer,Timer,Zap}from"lucide-react";
import{useState}from"react";
import{useTwinStore}from"../store/twinStore";
import EngineTwin from"./EngineTwin";
import{fmt,pct,pretty}from"./ui";
import{MetricCard,PageHeader,Panel,PanelTitle,StatusPill}from"./ReferenceUI";

export default function CommandCenter(){
 const twin=useTwinStore(s=>s.twin),runtime=useTwinStore(s=>s.runtimeValidity),runs=useTwinStore(s=>s.missionRuns),setView=useTwinStore(s=>s.setView),[mode,setMode]=useState<"3d"|"map">("3d");
 const t=twin?.telemetry,e=twin?.expected,r=twin?.residuals,h=twin?.health,ai=twin?.ai,trust=twin?.sensor_trust??{},last=runs.length?runs[runs.length-1].result:undefined,eligible=runtime?.decision_eligible!==false;
 if(!t||!e||!r||!h||!ai)return <div className="empty-screen">Waiting for synchronized telemetry…</div>;
 const fault=ai.anomaly?pretty(ai.probable_fault):"Normal Operation",risk=last?.overall_risk,feas=last?.mission_feasibility_index;
 const oilKpa=t.oil_pressure*100,expectedOilKpa=e.oil_pressure*100,residualOilKpa=r.oil_pressure_residual*100;
 const faultConfidencePct=ai.fault_confidence*100;
 const quality=(key:string)=>Number(trust[key]??twin.confidence.data_quality??0);
 return <div className="ref-page command-page">
  <PageHeader title="Command Center" subtitle={`${twin.engine_id} · live aero-piston telemetry, Digital Twin comparison, diagnosis and mission readiness`}/>
  <div className="cc-metrics cc-metrics-exact">
   <MetricCard icon={<Activity/>} label="RPM" value={t.rpm} unit="rpm" quality={quality("rpm")} helper="Measured crankshaft speed"/>
   <MetricCard icon={<Activity/>} label="Throttle" value={t.throttle} unit="%" quality={twin.confidence.data_quality} precision={1} helper="Current engine demand"/>
   <MetricCard icon={<Mountain/>} label="Altitude" value={t.altitude} unit="m" quality={twin.confidence.data_quality} helper={`Ambient ${fmt(t.ambient_temperature,1)} °C`}/>
   <MetricCard icon={<Thermometer/>} label="CHT" value={t.cht} unit="°C" quality={quality("cht")} precision={1} expected={`${fmt(e.cht,1)} °C`} delta={`${r.cht_residual>=0?"+":""}${fmt(r.cht_residual,1)} °C`}/>
   <MetricCard icon={<Thermometer/>} label="EGT" value={t.egt} unit="°C" quality={quality("egt")} precision={1} expected={`${fmt(e.egt,1)} °C`} delta={`${r.egt_residual>=0?"+":""}${fmt(r.egt_residual,1)} °C`}/>
   <MetricCard icon={<Droplets/>} label="Oil Pressure" value={oilKpa} unit="kPa" quality={quality("oil_pressure")} precision={1} expected={`${fmt(expectedOilKpa,1)} kPa`} delta={`${residualOilKpa>=0?"+":""}${fmt(residualOilKpa,1)} kPa`}/>
   <MetricCard icon={<Thermometer/>} label="Oil Temp" value={t.oil_temperature} unit="°C" quality={quality("oil_temperature")} precision={1} expected={`${fmt(e.oil_temperature,1)} °C`} delta={`${r.oil_temperature_residual>=0?"+":""}${fmt(r.oil_temperature_residual,1)} °C`}/>
   <MetricCard icon={<Fuel/>} label="Fuel Flow" value={t.fuel_flow} unit="L/h" quality={twin.confidence.data_quality} precision={2} expected={`${fmt(e.fuel_flow,2)} L/h`} delta={`${r.fuel_flow_residual>=0?"+":""}${fmt(r.fuel_flow_residual,2)} L/h`}/>
   <MetricCard icon={<Activity/>} label="Vibration" value={t.vibration} unit="g" quality={quality("vibration")} precision={3} expected={`${fmt(e.vibration,3)} g`} delta={`${r.vibration_residual>=0?"+":""}${fmt(r.vibration_residual,3)} g`}/>
   <MetricCard icon={<BatteryCharging/>} label="Battery Voltage" value={t.battery_voltage} unit="V" quality={quality("battery_voltage")} precision={2} expected={`${fmt(e.battery_voltage,2)} V`} delta={`${r.battery_voltage_residual>=0?"+":""}${fmt(r.battery_voltage_residual,2)} V`}/>
  </div>
  <div className="cc-main-grid">
   <Panel className="cc-engine-panel">
    <PanelTitle title="Engine System Overview" subtitle={`${twin.engine_id} aero-piston engine · subsystem health and exact live engineering state`} right={<div className="ref-toggle"><button className={mode==="3d"?"active":""} onClick={()=>setMode("3d")}>3D View</button><button className={mode==="map"?"active":""} onClick={()=>setMode("map")}>System Map</button></div>}/>
    <div className="cc-engine-stage">{mode==="3d"?<EngineTwin compact focus="all"/>:<div className="system-map"><div className="sys core">CRANKCASE</div><div className="sys s1">CYL A</div><div className="sys s2">CYL B</div><div className="sys s3">INDUCTION</div><div className="sys s4">LUBRICATION</div><div className="sys s5">EXHAUST</div><div className="sys s6">ELECTRICAL</div></div>}
     <div className="engine-callout induction"><b>Induction / Combustion</b><span className="good">● {pct(h.combustion)}</span><small>Fuel {fmt(t.fuel_flow,2)} L/h</small></div>
     <div className="engine-callout bank-a"><b>Cylinder / Thermal</b><span className={h.thermal<86?"warn":"good"}>● {pct(h.thermal)}</span><small>CHT {fmt(t.cht,1)} °C</small></div>
     <div className="engine-callout bank-b"><b>Exhaust / Combustion</b><span className={h.combustion<86?"warn":"good"}>● {pct(h.combustion)}</span><small>EGT {fmt(t.egt,1)} °C</small></div>
     <div className="engine-callout lubrication"><b>Lubrication System</b><span className={h.lubrication<86?"warn":"good"}>● {pct(h.lubrication)}</span><small>{fmt(oilKpa,1)} kPa · {fmt(t.oil_temperature,1)} °C</small></div>
     <div className="engine-callout electrical"><b>Electrical System</b><span className={h.electrical<86?"warn":"good"}>● {pct(h.electrical)}</span><small>{fmt(t.battery_voltage,2)} V battery · {fmt(t.alternator_voltage,2)} V alternator</small></div>
     <div className="engine-callout exhaust"><b>Mechanical State</b><span className={h.mechanical<86?"warn":"good"}>● {pct(h.mechanical)}</span><small>{fmt(t.vibration,3)} g vibration</small></div>
    </div>
   </Panel>
   <Panel className="cc-ai-panel">
    <PanelTitle icon={<Zap/>} title="AI Decision Center" subtitle="Current diagnosis, exact evidence and mission context"/>
    <div className={`cc-alert ${ai.anomaly?"bad":"good"}`}><AlertTriangle/><div><small>Probable Condition</small><b>{fault}</b></div></div>
    <div className="cc-ai-pair"><div><Signal/><span>Diagnostic Confidence</span><b>{pct(faultConfidencePct)}</b><div className="mini-progress"><i style={{width:`${Math.min(100,faultConfidencePct)}%`}}/></div></div><div><Shield/><span>Mission Risk</span>{risk?<StatusPill tone={risk==="LOW"?"green":risk==="MEDIUM"?"orange":"red"}>{risk}</StatusPill>:<StatusPill tone="blue">NOT ANALYZED</StatusPill>}</div></div>
    <div className="decision-readouts"><div><span>Oil-pressure residual</span><b className={Math.abs(residualOilKpa)>20?"red-text":"blue-text"}>{residualOilKpa>=0?"+":""}{fmt(residualOilKpa,1)} kPa</b></div><div><span>CHT residual</span><b>{r.cht_residual>=0?"+":""}{fmt(r.cht_residual,1)} °C</b></div><div><span>Vibration residual</span><b>{r.vibration_residual>=0?"+":""}{fmt(r.vibration_residual,3)} g</b></div><div><span>Telemetry age</span><b>{runtime?.telemetry_age_seconds==null?"--":`${fmt(runtime.telemetry_age_seconds,2)} s`}</b></div></div>
    <div className="cc-recommend"><div><b>Recommended Action</b><p>{twin.maintenance.reason}</p><small>{eligible?"Telemetry and model state are decision-eligible.":"DATA HOLD: restore live telemetry before using mission analysis."}</small></div></div>
    <div className="cc-action-row"><button className="ref-primary" onClick={()=>setView("diagnostics")}>Detailed Analysis →</button><button className="ref-outline" onClick={()=>setView("mission")}>Open Mission Lab</button></div>
   </Panel>
  </div>
  <div className="cc-bottom">
   <Panel className="cc-stat"><div className="stat-icon blue"><HeartPulse/></div><span>Engine Health</span><b className={h.overall<70?"red-text":h.overall<86?"orange-text":"green-text"}>{fmt(h.overall,1)}%</b><small>Thermal {fmt(h.thermal,1)}% · Lubrication {fmt(h.lubrication,1)}%</small><div className="donut" style={{"--v":`${Math.round(h.overall)*3.6}deg`} as any}/></Panel>
   <Panel className="cc-stat"><div className="stat-icon orange"><AlertTriangle/></div><span>Mission Risk</span>{risk?<StatusPill tone={risk==="LOW"?"green":risk==="MEDIUM"?"orange":"red"}>{risk}</StatusPill>:<b className="blue-text">—</b>}<small>{last?`Stress ${fmt(last.stress_index*100,1)}% · ${fmt(last.mission_margin_hours,2)} h margin`:"Run Mission Lab for a real profile-specific result"}</small></Panel>
   <Panel className="cc-stat"><div className="stat-icon blue"><Timer/></div><span>RUL Estimate</span><b>{fmt(ai.rul_hours,1)} <small>h</small></b><small>{ai.rul_interval_hours?`Conservative interval ${fmt(ai.rul_interval_hours.lower,1)}–${fmt(ai.rul_interval_hours.upper,1)} h`:"Engineering estimate"}</small></Panel>
   <Panel className="cc-stat"><div className="stat-icon blue"><Signal/></div><span>Mission Feasibility</span>{feas==null?<b className="blue-text">—</b>:<b className={feas<60?"red-text":feas<80?"orange-text":"green-text"}>{fmt(feas,1)}%</b>}<small>{last?`Post-mission health ${fmt(last.post_mission_health,1)}% · horizon ${fmt(last.decision_horizon_hours,2)} h`:"Mission analysis not run yet"}</small>{feas!=null&&<div className="donut" style={{"--v":`${Math.round(feas)*3.6}deg`} as any}/>}</Panel>
   <Panel className="cc-stat"><div className="stat-icon blue"><Database/></div><span>Data Status</span><b className={eligible?"green-text":"orange-text"}>● {eligible?"LIVE":"HOLD"}</b><small>Quality {fmt(runtime?.data_quality??twin.confidence.data_quality,1)}% · age {runtime?.telemetry_age_seconds==null?"--":`${fmt(runtime.telemetry_age_seconds,2)} s`}</small></Panel>
  </div>
 </div>
}
