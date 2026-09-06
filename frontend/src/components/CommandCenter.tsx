import{Activity,AlertTriangle,BatteryCharging,Database,Droplets,Fuel,HeartPulse,Mountain,Shield,Signal,Thermometer,Timer,Zap}from"lucide-react";
import{useState}from"react";
import{useTwinStore}from"../store/twinStore";
import EngineTwin from"./EngineTwin";
import{fmt,pct,pretty}from"./ui";
import{MetricCard,PageHeader,Panel,PanelTitle,StatusPill}from"./ReferenceUI";

export default function CommandCenter(){
 const twin=useTwinStore(s=>s.twin),runtime=useTwinStore(s=>s.runtimeValidity),runs=useTwinStore(s=>s.missionRuns),setView=useTwinStore(s=>s.setView),[mode,setMode]=useState<"3d"|"map">("3d");
 const t=twin?.telemetry??{},e=twin?.expected??{},r=twin?.residuals??{},h=twin?.health,ai=twin?.ai,last=runs.length?runs[runs.length-1].result:undefined,eligible=runtime?.decision_eligible!==false;
 const fault=ai?.anomaly?pretty(ai.probable_fault):"Normal Operation",risk=last?.overall_risk??(h&&h.overall<70?"HIGH":h&&h.overall<86?"MEDIUM":"LOW"),feas=last?.mission_feasibility_index??Math.max(0,Math.min(100,Math.round((h?.overall??96)*.86)));
 const oilKpa=Number(t.oil_pressure??0)*100,expectedOilKpa=Number(e.oil_pressure??0)*100,residualOilKpa=Number(r.oil_pressure??0)*100;
 const residual=(key:string,scale=1,d=1)=>{const n=Number(r[key]??0)*scale;return `${n>=0?"+":""}${fmt(n,d)}`};
 return <div className="ref-page command-page">
  <PageHeader title="Command Center" subtitle="Live aero-piston telemetry, digital-twin comparison, diagnosis and mission readiness"/>
  <div className="cc-metrics cc-metrics-exact">
   <MetricCard icon={<Activity/>} label="RPM" value={Number(t.rpm??0)} unit="rpm" quality={98} expected={`${fmt(e.rpm??t.rpm,0)} rpm`} delta={`${residual("rpm",1,0)} rpm`}/>
   <MetricCard icon={<Activity/>} label="Throttle" value={Number(t.throttle??0)} unit="%" quality={98} precision={1} helper="Current engine demand"/>
   <MetricCard icon={<Mountain/>} label="Altitude" value={Number(t.altitude??0)} unit="m" quality={97} helper={`Ambient ${fmt(t.ambient_temperature,1)} °C`}/>
   <MetricCard icon={<Thermometer/>} label="CHT" value={Number(t.cht??0)} unit="°C" quality={96} precision={1} expected={`${fmt(e.cht,1)} °C`} delta={`${residual("cht",1,1)} °C`}/>
   <MetricCard icon={<Thermometer/>} label="EGT" value={Number(t.egt??0)} unit="°C" quality={95} precision={1} expected={`${fmt(e.egt,1)} °C`} delta={`${residual("egt",1,1)} °C`}/>
   <MetricCard icon={<Droplets/>} label="Oil Pressure" value={oilKpa} unit="kPa" quality={91} precision={1} expected={`${fmt(expectedOilKpa,1)} kPa`} delta={`${residualOilKpa>=0?"+":""}${fmt(residualOilKpa,1)} kPa`}/>
   <MetricCard icon={<Thermometer/>} label="Oil Temp" value={Number(t.oil_temperature??0)} unit="°C" quality={93} precision={1} expected={`${fmt(e.oil_temperature,1)} °C`} delta={`${residual("oil_temperature",1,1)} °C`}/>
   <MetricCard icon={<Fuel/>} label="Fuel Flow" value={Number(t.fuel_flow??0)} unit="L/h" quality={94} precision={2} expected={e.fuel_flow!==undefined?`${fmt(e.fuel_flow,2)} L/h`:undefined}/>
   <MetricCard icon={<Activity/>} label="Vibration" value={Number(t.vibration??0)} unit="g" quality={92} precision={3} expected={`${fmt(e.vibration,3)} g`} delta={`${residual("vibration",1,3)} g`}/>
   <MetricCard icon={<BatteryCharging/>} label="Battery Voltage" value={Number(t.battery_voltage??0)} unit="V" quality={96} precision={2} helper={`Alternator ${fmt(t.alternator_voltage,2)} V`}/>
  </div>
  <div className="cc-main-grid">
   <Panel className="cc-engine-panel">
    <PanelTitle title="Engine System Overview" subtitle="TG-01 aero-piston engine · subsystem health and live engineering state" right={<div className="ref-toggle"><button className={mode==="3d"?"active":""} onClick={()=>setMode("3d")}>3D View</button><button className={mode==="map"?"active":""} onClick={()=>setMode("map")}>System Map</button></div>}/>
    <div className="cc-engine-stage">{mode==="3d"?<EngineTwin compact focus="all"/>:<div className="system-map"><div className="sys core">CRANKCASE</div><div className="sys s1">CYL A</div><div className="sys s2">CYL B</div><div className="sys s3">INDUCTION</div><div className="sys s4">LUBRICATION</div><div className="sys s5">EXHAUST</div><div className="sys s6">ELECTRICAL</div></div>}
     <div className="engine-callout induction"><b>Induction / Combustion</b><span className="good">● {pct(h?.combustion??96)}</span><small>Fuel {fmt(t.fuel_flow,2)} L/h</small></div>
     <div className="engine-callout bank-a"><b>Cylinder Bank A</b><span className={(h?.thermal??94)<86?"warn":"good"}>● {pct(Math.min(h?.thermal??94,h?.combustion??94))}</span><small>CHT {fmt(t.cht,1)} °C</small></div>
     <div className="engine-callout bank-b"><b>Cylinder Bank B</b><span className={(h?.thermal??95)<86?"warn":"good"}>● {pct(Math.min(h?.thermal??95,h?.combustion??95))}</span><small>EGT {fmt(t.egt,1)} °C</small></div>
     <div className="engine-callout lubrication"><b>Lubrication System</b><span className={(h?.lubrication??82)<86?"warn":"good"}>● {pct(h?.lubrication??82)}</span><small>{fmt(oilKpa,1)} kPa · {fmt(t.oil_temperature,1)} °C</small></div>
     <div className="engine-callout electrical"><b>Electrical System</b><span className={(h?.electrical??97)<86?"warn":"good"}>● {pct(h?.electrical??97)}</span><small>{fmt(t.battery_voltage,2)} V battery</small></div>
     <div className="engine-callout exhaust"><b>Mechanical / Exhaust</b><span className={(h?.mechanical??91)<86?"warn":"good"}>● {pct(h?.mechanical??91)}</span><small>{fmt(t.vibration,3)} g vibration</small></div>
    </div>
   </Panel>
   <Panel className="cc-ai-panel">
    <PanelTitle icon={<Zap/>} title="AI Decision Center" subtitle="Current diagnosis, exact evidence and mission context"/>
    <div className={`cc-alert ${ai?.anomaly?"bad":"good"}`}><AlertTriangle/><div><small>Probable Condition</small><b>{fault}</b></div></div>
    <div className="cc-ai-pair"><div><Signal/><span>Diagnostic Confidence</span><b>{pct(ai?.fault_confidence??twin?.confidence.decision??86)}</b><div className="mini-progress"><i style={{width:`${Math.min(100,Number(ai?.fault_confidence??86))}%`}}/></div></div><div><Shield/><span>Mission Risk</span><StatusPill tone={risk==="LOW"?"green":risk==="MEDIUM"?"orange":"red"}>{risk}</StatusPill></div></div>
    <div className="decision-readouts"><div><span>Oil-pressure residual</span><b className={Math.abs(residualOilKpa)>20?"red-text":"blue-text"}>{residualOilKpa>=0?"+":""}{fmt(residualOilKpa,1)} kPa</b></div><div><span>CHT residual</span><b>{residual("cht",1,1)} °C</b></div><div><span>Vibration residual</span><b>{residual("vibration",1,3)} g</b></div><div><span>Telemetry age</span><b>{runtime?.telemetry_age_seconds==null?"--":`${fmt(runtime.telemetry_age_seconds,1)} s`}</b></div></div>
    <div className="cc-recommend"><div><b>Recommended Action</b><p>{twin?.maintenance.reason??"Continue monitoring current operating condition."}</p><small>{eligible?"Telemetry and model state are decision-eligible.":"DATA HOLD: restore live telemetry before using mission analysis."}</small></div></div>
    <div className="cc-action-row"><button className="ref-primary" onClick={()=>setView("diagnostics")}>Detailed Analysis →</button><button className="ref-outline" onClick={()=>setView("mission")}>Open Mission Lab</button></div>
   </Panel>
  </div>
  <div className="cc-bottom">
   <Panel className="cc-stat"><div className="stat-icon blue"><HeartPulse/></div><span>Engine Health</span><b className={(h?.overall??84)<70?"red-text":(h?.overall??84)<86?"orange-text":"green-text"}>{fmt(h?.overall??84,1)}%</b><small>Thermal {fmt(h?.thermal,1)}% · Lubrication {fmt(h?.lubrication,1)}%</small><div className="donut" style={{"--v":`${Math.round(h?.overall??84)*3.6}deg`} as any}/></Panel>
   <Panel className="cc-stat"><div className="stat-icon orange"><AlertTriangle/></div><span>Mission Risk</span><StatusPill tone={risk==="LOW"?"green":risk==="MEDIUM"?"orange":"red"}>{risk}</StatusPill><small>{last?`Stress index ${fmt(last.stress_index,1)} · ${fmt(last.mission_margin_hours,2)} h margin`:"Run Mission Lab for exact profile risk"}</small></Panel>
   <Panel className="cc-stat"><div className="stat-icon blue"><Timer/></div><span>RUL Estimate</span><b>{fmt(ai?.rul_hours,1)} <small>h</small></b><small>{ai?.rul_interval_hours?`Conservative ${fmt(ai.rul_interval_hours.lower,1)}–${fmt(ai.rul_interval_hours.upper,1)} h`:"Engineering estimate"}</small></Panel>
   <Panel className="cc-stat"><div className="stat-icon blue"><Signal/></div><span>Mission Feasibility</span><b className={feas<60?"red-text":feas<80?"orange-text":"green-text"}>{fmt(feas,1)}%</b><small>{last?`Post-mission health ${fmt(last.post_mission_health,1)}% · horizon ${fmt(last.decision_horizon_hours,2)} h`:"No profile analyzed yet"}</small><div className="donut" style={{"--v":`${Math.round(feas)*3.6}deg`} as any}/></Panel>
   <Panel className="cc-stat"><div className="stat-icon blue"><Database/></div><span>Data Status</span><b className={eligible?"green-text":"orange-text"}>● {eligible?"LIVE":"HOLD"}</b><small>Quality {fmt(runtime?.data_quality??twin?.confidence.data_quality,1)}% · age {runtime?.telemetry_age_seconds==null?"--":`${fmt(runtime.telemetry_age_seconds,1)} s`}</small></Panel>
  </div>
 </div>
}
