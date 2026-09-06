import{useEffect,useMemo,useState}from"react";
import{motion}from"framer-motion";
import{Activity,BatteryCharging,Crosshair,Droplets,Expand,Eye,Layers3,Pause,Play,RotateCw,ZoomOut,ZoomIn,ShieldCheck,Thermometer,Wind,Zap}from"lucide-react";
import{useTwinStore}from"../store/twinStore";
import{setFault}from"../services/twinApi";
import type{FaultName}from"../types/twin";
import EngineTwin from"./EngineTwin";
import UAVContext from"./UAVContext";
import MissionThumbnail from"./MissionThumbnail";
import type{MissionVariant}from"./MissionThumbnail";
import{Badge,Card,MiniSpark,Progress,SectionTitle,fmt,pct,pretty}from"./ui";

const defs=[
 ["rpm","RPM","RPM",0,Activity],
 ["cht","CHT","°C",1,Thermometer],
 ["egt","EGT","°C",1,Thermometer],
 ["oil_pressure","OIL PRESSURE","bar",2,Droplets],
 ["vibration","VIBRATION","g RMS",3,Activity],
 ["altitude","ALTITUDE","m",0,Wind],
 ["battery_voltage","BATTERY","V",1,BatteryCharging]
]as const;

const replayEvents:Array<{label:string;variant:MissionVariant;time:string}>=[
 {label:"Flight Start",variant:"start",time:"00:00"},
 {label:"Cruise Phase",variant:"cruise",time:"00:08"},
 {label:"Wind Shear",variant:"shear",time:"00:25"},
 {label:"Altitude Change",variant:"altitude",time:"00:33"},
 {label:"Mission Complete",variant:"complete",time:"00:53"}
];

export default function CommandCenter(){
 const twin=useTwinStore(s=>s.twin),history=useTwinStore(s=>s.history),missionRuns=useTwinStore(s=>s.missionRuns),setView=useTwinStore(s=>s.setView),setFocus=useTwinStore(s=>s.setFocus);
 const[explode,setExplode]=useState(true),[xray,setXray]=useState(false),[rotate,setRotate]=useState(false),[zoom,setZoom]=useState(1),[resetToken,setResetToken]=useState(0);
 const[fault,setFaultName]=useState<FaultName>("normal"),[severity,setSeverity]=useState(50),[playing,setPlaying]=useState(false),[replayProgress,setReplayProgress]=useState(48),[selectedEvent,setSelectedEvent]=useState(2);
 const health=twin?.health.overall??94,faultName=twin?.ai.probable_fault??"normal",evidence=twin?.ai.evidence??[],ready=twin?.readiness.label??"READY";
 const latestMission=missionRuns.length?missionRuns[missionRuns.length-1].result:undefined;
 const metrics=useMemo(()=>defs.map(([key,label,unit,d,Icon])=>({key,label,unit,d,Icon,value:Number(twin?.telemetry[key]??0),hist:history[key]??[]})),[twin,history]);
 useEffect(()=>{if(!playing)return;const id=window.setInterval(()=>setReplayProgress(v=>v>=100?0:v+1),300);return()=>window.clearInterval(id)},[playing]);
 const inject=()=>setFault(fault,fault==="normal"?0:severity/100).catch(()=>undefined);
 const fullscreen=()=>document.getElementById("engine-reference-stage")?.requestFullscreen?.();
 const resetCamera=()=>{setZoom(1);setRotate(false);setResetToken(v=>v+1)};
 const replayTime=Math.round(53*replayProgress/100),timeLabel=`${String(Math.floor(replayTime/60)).padStart(2,"0")}:${String(replayTime%60).padStart(2,"0")}`;
 const synthetic=twin?.ai.validation_scope==="SYNTHETIC_PROOF_OF_CONCEPT"||twin?.twin_meta?.validation_scope==="SYNTHETIC_PROOF_OF_CONCEPT";

 return <motion.div className="reference-page" initial={{opacity:0}} animate={{opacity:1}}>
  <div className="reference-top">
   <Card className="exact-engine-card">
    <div className="engine-card-heading">
     <SectionTitle eyebrow="DIGITAL TWIN  •  ENGINE-01" title="Aero-Piston Engine Digital Twin" action={<Badge kind="blue"><Activity size={12}/>Live</Badge>}/>
     <div className="overall-health-mini"><ShieldCheck/><div><span>Engineering Health Index</span><strong>{pct(health)}</strong><small>{health>=94?"Nominal":health>=85?"Monitor":"Review"}</small></div><b>⋮</b></div>
    </div>
    <div id="engine-reference-stage" className="engine-reference-stage true-3d-engine">
     <EngineTwin compact explode={explode} xray={xray} focus="all" autoRotate={rotate} zoom={zoom} resetToken={resetToken} onFocus={m=>{setFocus(m);setView("diagnostics")}}/>
     <div className="engine-data-box box-a"><span>CYLINDER BANKS</span><div><i/>Health <b>{pct(Math.min(twin?.health.thermal??96,twin?.health.combustion??96))}</b><em>CHT {fmt(twin?.telemetry.cht,0)}°C</em></div></div>
     <div className="engine-data-box box-b"><span>LUBRICATION</span><div><i/>Health <b>{pct(twin?.health.lubrication)}</b><em>Oil {fmt(twin?.telemetry.oil_pressure,2)} bar</em></div></div>
     <div className="engine-data-box box-e"><span>FUEL / INDUCTION</span><div><i className="hot"/>Health <b>{pct(twin?.health.combustion)}</b><em>Flow {fmt(twin?.telemetry.fuel_flow,1)} L/h</em></div></div>
     <div className="engine-data-box box-c"><span>EXHAUST / THERMAL</span><div><i/>Health <b>{pct(twin?.health.thermal)}</b><em>EGT {fmt(twin?.telemetry.egt,0)}°C</em></div></div>
     <div className="engine-data-box box-d"><span>ELECTRICAL</span><div><i/>Health <b>{pct(twin?.health.electrical)}</b><em>ALT {fmt(twin?.telemetry.alternator_voltage,1)} V</em></div></div>
     <div className="exact-model-controls">
      <button className={rotate?"active":""} onClick={()=>setRotate(v=>!v)}><RotateCw size={14}/>Rotate</button>
      <button className={explode?"active":""} onClick={()=>setExplode(v=>!v)}><Layers3 size={14}/>{explode?"Assemble":"Explode"}</button>
      <button title="Zoom out" onClick={()=>setZoom(v=>Math.min(1.35,v+.10))}><ZoomOut size={14}/></button>
      <button title="Zoom in" onClick={()=>setZoom(v=>Math.max(.72,v-.10))}><ZoomIn size={14}/></button>
      <button title="Reset view" onClick={resetCamera}><Crosshair size={14}/></button>
      <button className={xray?"active":""} title="X-Ray" onClick={()=>setXray(v=>!v)}><Eye size={14}/></button>
      <button title="Fullscreen" onClick={fullscreen}><Expand size={14}/></button>
     </div>
    </div>
   </Card>

   <Card className="exact-context-card">
    <SectionTitle eyebrow="ASSET CONTEXT" title="MALE UAV System View" action={<button className="dots">⋮</button>}/>
    <div className="exact-uav-view true-uav-view"><UAVContext/></div>
    <div className="exact-context-kpis">{[["Altitude",`${fmt(twin?.telemetry.altitude,0)} m`],["Throttle",`${fmt(twin?.telemetry.throttle,0)}%`],["Engine Speed",`${fmt(twin?.telemetry.rpm,0)} RPM`],["Mission Phase","Cruise"]].map(x=><div key={x[0]}><span>{x[0]}</span><strong>{x[1]}</strong></div>)}</div>
   </Card>

   <Card className="exact-decision-card">
    <SectionTitle eyebrow="DECISION SUPPORT" title="" action={synthetic?<Badge kind="blue">Synthetic POC</Badge>:<button className="dots">⋮</button>}/>
    <div className="decision-heading"><div><strong>{ready==="READY"?"Mission Release: Ready":pretty(ready)}</strong><span>{twin?.readiness.reason??"Waiting for synchronized twin state"}</span></div><div className="decision-shield"><ShieldCheck/></div></div>
    <div className="decision-stats"><div><span>Simulation-derived RUL</span><b>{fmt(twin?.ai.rul_hours,1)} h</b></div><div><span>Diagnostic Confidence</span><Badge kind="good">{(twin?.confidence.decision??92)>84?"High":"Review"}</Badge><b>{pct(twin?.confidence.decision)}</b></div></div>
    <div className="decision-maintenance"><span>Maintenance Assessment</span><strong>{twin?.maintenance.priority==="MONITOR"?"Monitor / Trend":pretty(twin?.maintenance.priority)}</strong><p>{twin?.maintenance.reason??"Awaiting telemetry."}</p></div>
    <button className="view-ai-report" onClick={()=>setView("diagnostics")}><Zap size={13}/>View Evidence Report</button>
   </Card>
  </div>

  <div className="reference-lower">
   <div className="lower-main">
    <div className="exact-metrics">{metrics.map(({key,label,unit,d,Icon,value,hist})=><Card key={key} className="exact-metric-card"><div className="metric-label"><Icon size={14}/><span>{label}</span></div><strong>{fmt(value,d)} <small>{unit}</small></strong><MiniSpark values={hist}/><em>{hist.length>1?`${(hist[hist.length-1]-hist[hist.length-2])>=0?"↗":"↘"} ${Math.abs((hist[hist.length-1]??0)-(hist[hist.length-2]??0)).toFixed(d?d:1)}`:"—"}</em></Card>)}</div>

    <div className="exact-bottom-row">
     <Card className="exact-mission-card">
      <SectionTitle eyebrow="MISSION RELIABILITY TWIN" title="Latest mission analysis" action={latestMission?<Badge kind={latestMission.overall_risk==="LOW"?"good":latestMission.overall_risk==="MEDIUM"?"warn":"bad"}>{latestMission.overall_risk}</Badge>:undefined}/>
      <div className="mission-reference-content">
       <div className="mission-input-panel"><strong>Current Twin Inputs</strong>{[["Health index",pct(twin?.health.overall)],["RUL basis",pretty(twin?.ai.rul_basis??"engineering_surrogate")],["Active condition",twin?.ai.anomaly?pretty(faultName):"Normal"],["Validation","Synthetic POC"]].map(x=><div key={x[0]}><span>{x[0]}</span><b>{x[1]}</b></div>)}</div>
       <div className="future-simulation"><strong>{latestMission?"Backend Mission Result":"Mission analysis not run yet"}</strong>{latestMission?<><div className="future-stat-row"><div><span>Mission Risk</span><b>{latestMission.overall_risk}</b></div><div><span>Post-Mission Health</span><b>{pct(latestMission.post_mission_health)}</b></div><div><span>Post-Mission RUL</span><b>{fmt(latestMission.post_mission_rul_hours,1)} h</b></div><div><span>Stress Index</span><b>{fmt(latestMission.stress_index,2)}</b></div></div><div className="key-trends"><span>Decision</span><p>{pretty(latestMission.decision)}</p><small>{latestMission.explanation}</small></div></>:<div className="empty-state"><strong>No fabricated prediction shown</strong><p>Open Mission Lab and run a profile. This panel will display only backend-generated results.</p></div>}<button onClick={()=>setView("mission")}>{latestMission?"Open Full Mission Analysis":"Configure Mission"}</button></div>
      </div>
     </Card>

     <div className="replay-stack">
      <Card className="exact-replay-card">
       <SectionTitle eyebrow="MISSION REPLAY" title="Recent Events" action={<button className="text-link" onClick={()=>setView("replay")}>View All</button>}/>
       <div className="reference-events">{replayEvents.map((event,i)=><button key={event.label} className={`replay-event ${selectedEvent===i?"selected":""} ${i===2&&twin?.ai.anomaly?"warn":""}`} onClick={()=>{setSelectedEvent(i);setReplayProgress(i*25)}}><div className="reference-thumb true-replay-thumb"><MissionThumbnail variant={event.variant}/><span><Play size={10}/></span></div><strong>{i===2&&twin?.ai.anomaly?"Condition Detected":event.label}</strong><small>Today {event.time}</small></button>)}</div>
       <div className="replay-player"><span>{timeLabel} / 00:53</span><div><i style={{width:`${replayProgress}%`}}/></div><button title="Play" onClick={()=>setPlaying(true)} className={playing?"active":""}><Play size={11}/></button><button title="Pause" onClick={()=>setPlaying(false)}><Pause size={11}/></button><b>1x</b></div>
      </Card>
      <Card className="exact-simulator-strip"><span>SIMULATOR · SYNTHETIC</span><label>Inject Aero-Piston Scenario<select value={fault} onChange={e=>setFaultName(e.target.value as FaultName)}><option value="normal">Normal / Healthy</option><option value="lubrication">Lubrication Degradation</option><option value="overheating">Overheating</option><option value="cooling_degradation">Cooling Degradation</option><option value="vibration">Abnormal Vibration</option><option value="sensor_drift">Sensor Drift</option><option value="injector">Injector Abnormality</option><option value="misfire">Misfire</option><option value="combustion_instability">Combustion Instability</option><option value="alternator_degradation">Alternator Degradation</option></select></label><label className="exact-severity">Target Severity<input type="range" min="0" max="100" value={severity} onChange={e=>setSeverity(Number(e.target.value))}/><b>{severity<35?"Low":severity<70?"Medium":"Severe"}</b></label><button onClick={inject}><Play size={12}/>Run Scenario</button></Card>
     </div>
    </div>
   </div>

   <Card className="exact-diagnostics-card">
    <SectionTitle eyebrow="DIAGNOSTICS  •  EXPLAINABILITY" title="" action={<button className="dots">⋮</button>}/>
    <div className="exact-condition"><span>Probable Condition</span><Badge kind={twin?.ai.anomaly?"warn":"good"}>{twin?.ai.anomaly?pretty(faultName):"Normal Operation"}</Badge><span>Diagnostic Confidence</span><div className="exact-confidence"><b>{pct(Math.min(99,twin?.confidence.decision??92))}</b></div></div>
    <div className="evidence-label">Evidence</div>
    <div className="exact-evidence">{(evidence.length?evidence:[{feature:"egt_residual",weight:.25,value:0},{feature:"cht_residual",weight:.25,value:0},{feature:"vibration_residual",weight:.25,value:0},{feature:"oil_pressure_residual",weight:.25,value:0}]).slice(0,4).map(x=><div key={x.feature}><span>{pretty(x.feature)}</span><Progress value={x.weight*100}/><b>{pct(x.weight*100)}</b></div>)}</div>
    <div className="ai-brain-visual"><div className="brain-network"><i/><i/><i/><i/><i/><i/><i/><i/><i/></div></div>
    <div className="model-insight-reference"><strong>Model Insight</strong><p>{twin?.ai.anomaly?twin?.maintenance.reason:"Residuals are currently within the demonstrator's nominal envelope."}</p><p>{twin?.ai.model_warning??(synthetic?"Synthetic proof-of-concept: engine-specific calibration and test-rig validation are still required.":"No significant degradation detected.")}</p></div>
   </Card>
  </div>
 </motion.div>
}
