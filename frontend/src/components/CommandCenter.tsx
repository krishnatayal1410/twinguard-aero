import{Activity,AlertTriangle,BatteryCharging,Database,Droplets,HeartPulse,Shield,Signal,Thermometer,Timer,Wind,Zap}from"lucide-react";
import{useState}from"react";
import{useTwinStore}from"../store/twinStore";
import EngineTwin from"./EngineTwin";
import{fmt,pct,pretty}from"./ui";
import{MetricCard,PageHeader,Panel,PanelTitle,StatusPill}from"./ReferenceUI";

export default function CommandCenter(){
 const twin=useTwinStore(s=>s.twin),runtime=useTwinStore(s=>s.runtimeValidity),runs=useTwinStore(s=>s.missionRuns),setView=useTwinStore(s=>s.setView),[mode,setMode]=useState<"3d"|"map">("3d");
 const t=twin?.telemetry??{},h=twin?.health,ai=twin?.ai,last=runs.length?runs[runs.length-1].result:undefined,eligible=runtime?.decision_eligible!==false;
 const fault=ai?.anomaly?pretty(ai.probable_fault):"Normal Operation",risk=last?.overall_risk??(h&&h.overall<70?"HIGH":h&&h.overall<86?"MEDIUM":"LOW"),feas=last?.mission_feasibility_index??Math.max(0,Math.min(100,Math.round((h?.overall??96)*.86)));
 const oilKpa=Number(t.oil_pressure??0)*100;
 return <div className="ref-page command-page">
  <PageHeader title="Command Center" subtitle="Real-time overview, AI decision support, and key engine metrics"/>
  <div className="cc-metrics">
   <MetricCard icon={<Activity/>} label="RPM" value={Number(t.rpm??0)} quality={98}/>
   <MetricCard icon={<Thermometer/>} label="CHT" value={Number(t.cht??0)} unit="°C" quality={96}/>
   <MetricCard icon={<Thermometer/>} label="EGT" value={Number(t.egt??0)} unit="°C" quality={95}/>
   <MetricCard icon={<Droplets/>} label="Oil Pressure" value={oilKpa} unit="kPa" quality={91}/>
   <MetricCard icon={<Activity/>} label="Vibration" value={Number(t.vibration??0)} unit="g" quality={92}/>
   <MetricCard icon={<Database/>} label="Data Quality" value={Math.round(Number(twin?.confidence.data_quality??98))} unit="%" quality={Number(twin?.confidence.data_quality??98)}/>
  </div>
  <div className="cc-main-grid">
   <Panel className="cc-engine-panel">
    <PanelTitle title="Engine System Overview" subtitle="TG-01 Aero-Piston Engine - Key Subsystems Health" right={<div className="ref-toggle"><button className={mode==="3d"?"active":""} onClick={()=>setMode("3d")}>3D View</button><button className={mode==="map"?"active":""} onClick={()=>setMode("map")}>System Map</button></div>}/>
    <div className="cc-engine-stage">{mode==="3d"?<EngineTwin compact focus="all"/>:<div className="system-map"><div className="sys core">CRANKCASE</div><div className="sys s1">CYL A</div><div className="sys s2">CYL B</div><div className="sys s3">INDUCTION</div><div className="sys s4">LUBRICATION</div><div className="sys s5">EXHAUST</div><div className="sys s6">ELECTRICAL</div></div>}
     <div className="engine-callout induction"><b>Induction System</b><span className="good">● {pct(h?.combustion??96)}</span><small>Healthy</small></div>
     <div className="engine-callout bank-a"><b>Cylinder Bank A</b><span className="good">● {pct(Math.min(h?.thermal??94,h?.combustion??94))}</span><small>Normal</small></div>
     <div className="engine-callout bank-b"><b>Cylinder Bank B</b><span className="good">● {pct(Math.min(h?.thermal??95,h?.combustion??95))}</span><small>Normal</small></div>
     <div className="engine-callout lubrication"><b>Lubrication System</b><span className={(h?.lubrication??82)<86?"warn":"good"}>● {pct(h?.lubrication??82)} Attention</span></div>
     <div className="engine-callout electrical"><b>Electrical System</b><span className="good">● {pct(h?.electrical??97)}</span><small>Healthy</small></div>
     <div className="engine-callout exhaust"><b>Exhaust System</b><span className="good">● {pct(h?.thermal??91)}</span><small>Normal</small></div>
    </div>
   </Panel>
   <Panel className="cc-ai-panel">
    <PanelTitle icon={<Zap/>} title="AI Decision Center" subtitle="Continuous analysis of engine data and mission context"/>
    <div className={`cc-alert ${ai?.anomaly?"bad":"good"}`}><AlertTriangle/><div><small>Probable Issue</small><b>{ai?.anomaly?fault:"No Active Fault"}</b></div></div>
    <div className="cc-ai-pair"><div><Signal/><span>Confidence</span><b>{pct(ai?.fault_confidence??twin?.confidence.decision??86)}</b><div className="mini-progress"><i style={{width:`${Math.min(100,Number(ai?.fault_confidence??86))}%`}}/></div></div><div><Shield/><span>Risk Level</span><StatusPill tone={risk==="LOW"?"green":risk==="MEDIUM"?"orange":"red"}>{risk}</StatusPill></div></div>
    <div className="cc-recommend"><div><b>Recommended Action</b><p>{twin?.maintenance.reason??"Continue with reduced load and monitor oil parameters."}</p><small>{eligible?"Telemetry and model state are decision-eligible.":"Data hold is active. Do not use mission analysis until telemetry recovers."}</small></div></div>
    <button className="ref-primary" onClick={()=>setView("diagnostics")}>View Detailed Analysis →</button>
   </Panel>
  </div>
  <div className="cc-bottom">
   <Panel className="cc-stat"><div className="stat-icon blue"><HeartPulse/></div><span>Engine Health</span><b className="green-text">{pct(h?.overall??84)}</b><small>Overall engine health index</small><div className="donut" style={{"--v":`${Math.round(h?.overall??84)*3.6}deg`} as any}/></Panel>
   <Panel className="cc-stat"><div className="stat-icon orange"><AlertTriangle/></div><span>Mission Risk</span><StatusPill tone={risk==="LOW"?"green":risk==="MEDIUM"?"orange":"red"}>{risk}</StatusPill><small>Based on current condition and mission profile</small></Panel>
   <Panel className="cc-stat"><div className="stat-icon blue"><Timer/></div><span>RUL (Est.)</span><b>{fmt(ai?.rul_hours,0)} <small>h</small></b><small>Remaining useful life {ai?.rul_interval_hours?`(${fmt(ai.rul_interval_hours.lower,0)}–${fmt(ai.rul_interval_hours.upper,0)} h)`:""}</small></Panel>
   <Panel className="cc-stat"><div className="stat-icon blue"><Signal/></div><span>Mission Feasibility</span><b className="green-text">{Math.round(feas)}%</b><small>{last?"Backend mission analysis":"Run Mission Lab for a full evaluation"}</small><div className="donut" style={{"--v":`${Math.round(feas)*3.6}deg`} as any}/></Panel>
   <Panel className="cc-stat"><div className="stat-icon blue"><Database/></div><span>Data Status</span><b className={eligible?"green-text":"orange-text"}>● {eligible?"LIVE":"HOLD"}</b><small>{eligible?"Telemetry, model & AI systems operational":"Telemetry not decision-eligible"}</small></Panel>
  </div>
 </div>
}
