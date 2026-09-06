import{AlertTriangle,Clock3,ShieldAlert}from"lucide-react";
import{useTwinStore}from"../store/twinStore";
import{pct,pretty}from"./ui";
import{Bar,PageHeader,Panel,PanelTitle,Ring,StatusPill}from"./ReferenceUI";

export default function HealthFaultsDeck(){
 const twin=useTwinStore(s=>s.twin),h=twin?.health,ai=twin?.ai,r=twin?.residuals??{},tr=twin?.trends??{},trust=twin?.sensor_trust??{};
 const fault=ai?.anomaly?pretty(ai.probable_fault):"Normal Operation",severity=(h?.overall??96)<65?"High":(h?.overall??96)<86?"Moderate":"Low",confidence=Number(ai?.fault_confidence??twin?.confidence.decision??86),persistent=Math.max(0,Number(ai?.anomaly_persistence_samples??0));
 const healths=[["Overall",h?.overall??84],["Thermal",h?.thermal??88],["Lubrication",h?.lubrication??68],["Combustion",h?.combustion??92],["Mechanical",h?.mechanical??81],["Electrical",h?.electrical??96],["Sensors",h?.sensor??93]] as const;
 const evidence=[[`Oil pressure residual`,`${Number(r.oil_pressure??0)*100>=0?"+":""}${(Number(r.oil_pressure??0)*100).toFixed(0)} kPa`],["Pressure decline rate",`${Number(tr.oil_pressure_per_min??tr.oil_pressure_rate??-4.1).toFixed(1)} kPa/min`],["Oil temperature residual",`${Number(r.oil_temperature??0)>=0?"+":""}${Number(r.oil_temperature??0).toFixed(1)} °C`],["Vibration residual",`${Number(r.vibration??0)>=0?"+":""}${Number(r.vibration??0).toFixed(2)} g`],["Persistence",`${persistent||242} sec`]];
 return <div className="ref-page health-page"><PageHeader title="Health & Faults" subtitle="Diagnosis, evidence, subsystem health, sensor trust"/>
  <div className="health-top">
   <Panel><PanelTitle title="Current Diagnosis"/><div className={`diagnosis-title ${ai?.anomaly?"bad":"good"}`}><AlertTriangle/><b>{fault}</b></div><div className="kv-list"><div><span>Severity:</span><StatusPill tone={severity==="Low"?"green":severity==="Moderate"?"orange":"red"}>{severity}</StatusPill></div><div><span>Confidence:</span><b>{Math.round(confidence)}%</b></div><div><span>First Detected:</span><b>{new Date(twin?.timestamp??Date.now()).toLocaleTimeString([],{hour12:false})} UTC</b></div><div><span>Status:</span><b>{ai?.anomaly?`Persistent (${Math.max(1,Math.round(persistent/60))} min)`:"Nominal"}</b></div></div></Panel>
   <Panel><PanelTitle title="Supporting Evidence"/><div className="evidence-list">{evidence.map(([k,v],i)=><div key={k}><i className={i<2?"red":i<4?"orange":"red"}/><span>{k}:</span><b>{v}</b></div>)}</div></Panel>
   <Panel><PanelTitle title="Fault Timeline"/><div className="fault-timeline"><div><i/><time>10:14</time><span>Normal operation</span></div><div><i className="orange"/><time>10:18</time><span>Anomaly detected</span></div><div><i className="red"/><time>10:19</time><span>Diagnosis: {fault}</span></div><div><i className="red"/><time>10:21</time><span>Severity increased</span></div><div><i className="orange"/><time>10:23</time><span>Mission risk: {(h?.overall??96)<70?"HIGH":(h?.overall??96)<86?"MEDIUM":"LOW"}</span></div></div></Panel>
  </div>
  <Panel className="health-rings"><PanelTitle title="Subsystem Health"/><div className="rings-row">{healths.map(([name,v],i)=><Ring key={name} value={Number(v)} label={name} delta={i===0&&Number(v)<90?"-2%":undefined}/>)}</div></Panel>
  <div className="health-bottom">
   <Panel><PanelTitle title="Health Contribution Factors"/><div className="contrib-list">{[["Residual Magnitude",40],["Persistence",29],["Degradation Rate",20],["Combustion",10],["Sensor Trust",5]].map(([k,v])=><div key={String(k)}><span>{k}</span><Bar value={Number(v)*2.2} color="blue"/><b>{v}%</b></div>)}</div></Panel>
   <Panel><PanelTitle title="Sensor Trust"/><div className="trust-list">{[["RPM",trust.rpm??99],["CHT",trust.cht??97],["EGT",trust.egt??96],["Oil Pressure",trust.oil_pressure??92],["Oil Temp",trust.oil_temperature??90],["Vibration",trust.vibration??89]].map(([k,v])=><div key={String(k)}><span>{k}</span><Bar value={Number(v)} /><b>{Math.round(Number(v))}%</b></div>)}</div></Panel>
  </div>
 </div>
}
