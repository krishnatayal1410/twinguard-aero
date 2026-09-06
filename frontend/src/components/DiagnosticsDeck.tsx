import{motion}from"framer-motion";
import{Activity,BrainCircuit,CheckCircle2,ShieldAlert,ShieldCheck,Signal,TriangleAlert}from"lucide-react";
import{useTwinStore}from"../store/twinStore";
import{Badge,Card,Progress,SectionTitle,fmt,pct,pretty,tone}from"./ui";
import{TrendChart}from"./TrendChart";

export default function DiagnosticsDeck(){
 const twin=useTwinStore(s=>s.twin),history=useTwinStore(s=>s.history);
 if(!twin)return <div className="empty-screen">Waiting for telemetry…</div>;
 const fault=twin.ai.probable_fault,normal=!twin.ai.anomaly&&fault==="normal";
 const confidence=[["Diagnostic engine",twin.confidence.ai],["Sensor integrity",twin.confidence.sensor],["Physics corroboration",twin.confidence.physics_agreement],["Data quality",twin.confidence.data_quality],["Decision confidence",twin.confidence.decision]];
 const synthetic=twin.ai.validation_scope==="SYNTHETIC_PROOF_OF_CONCEPT"||twin.twin_meta?.validation_scope==="SYNTHETIC_PROOF_OF_CONCEPT";
 return <motion.div className="diagnostics-page" initial={{opacity:0,y:8}} animate={{opacity:1,y:0}}>
  <Card className="diagnosis-hero">
   <div className="diagnosis-copy">
    <span className="eyebrow">HYBRID PHYSICS + DIAGNOSTIC CORE</span>
    <div className="diagnosis-title"><h1>{pretty(fault)}</h1><Badge kind={normal?"good":"warn"}>{normal?<CheckCircle2 size={13}/>:<TriangleAlert size={13}/>} {normal?"Normal operation":"Condition detected"}</Badge>{synthetic&&<Badge kind="blue">Synthetic POC</Badge>}</div>
    <p>{normal?"No dominant fault mechanism is identified. The Digital Twin remains inside the current generic aero-piston surrogate envelope.":twin.maintenance.reason}</p>
    <div className="diag-kpi-row">{[["Anomaly score",fmt(twin.ai.anomaly_score,3)],["Diagnostic confidence",pct(twin.ai.fault_confidence*100)],["Simulation RUL",`${fmt(twin.ai.rul_hours,1)} h`],["Runtime",pretty(twin.ai.model_state)]].map(x=><div key={x[0]}><span>{x[0]}</span><strong>{x[1]}</strong></div>)}</div>
    {twin.ai.model_warning&&<p className="fineprint">{twin.ai.model_warning}</p>}
   </div>
   <div className={`diag-shield ${normal?"good":"warn"}`}><ShieldCheck/><strong>{pct(twin.confidence.decision)}</strong><span>Decision confidence</span></div>
  </Card>

  <div className="diag-main-grid">
   <Card className="evidence-card"><SectionTitle eyebrow="EXPLAINABILITY" title="Evidence spectrum" action={<Badge kind="blue"><BrainCircuit size={13}/> Residual + diagnostic evidence</Badge>}/><div className="evidence-spectrum">{twin.ai.evidence.map((x,i)=><motion.div key={x.feature} initial={{opacity:0,x:-8}} animate={{opacity:1,x:0}} transition={{delay:i*.05}}><div><span>{pretty(x.feature)}</span><strong>{pct(x.weight*100)}</strong></div><Progress value={x.weight*100}/><small>Residual/current evidence value: {fmt(x.value,3)}</small></motion.div>)}</div></Card>
   <Card><SectionTitle eyebrow="CONFIDENCE FUSION" title="Decision evidence quality"/><div className="confidence-list">{confidence.map(([name,v])=><div key={String(name)}><span>{name}</span><b>{pct(Number(v))}</b><Progress value={Number(v)} kind={Number(v)>88?"good":Number(v)>70?"blue":"warn"}/></div>)}</div><p className="fineprint">Scores are prototype engineering confidence indices, not calibrated aviation probabilities.</p></Card>
  </div>

  <div className="diag-chart-grid">
   <Card><SectionTitle eyebrow="THERMAL TREND" title="Cylinder Head Temperature"/><TrendChart data={history.cht??[]} label="CHT" unit="°C" height={220}/></Card>
   <Card><SectionTitle eyebrow="LUBRICATION TREND" title="Oil Pressure"/><TrendChart data={history.oil_pressure??[]} label="Oil pressure" unit="bar" height={220} color="#20b783"/></Card>
   <Card><SectionTitle eyebrow="MECHANICAL TREND" title="Vibration"/><TrendChart data={history.vibration??[]} label="Vibration" unit="g" height={220} color="#826ee6"/></Card>
  </div>

  <div className="diag-bottom-grid">
   <Card><SectionTitle eyebrow="SUBSYSTEM HEALTH" title="Engineering health indices"/><div className="health-list">{Object.entries(twin.health).filter(([k])=>k!=="overall").map(([k,v])=><div key={k}><span>{pretty(k)}</span><b className={tone(v)}>{pct(v)}</b><Progress value={v} kind={tone(v)==="good"?"good":tone(v)==="warn"?"warn":"bad"}/></div>)}</div></Card>
   <Card><SectionTitle eyebrow="SENSOR TRUST" title="Measurement integrity"/><div className="health-list">{Object.entries(twin.sensor_trust).map(([k,v])=><div key={k}><span>{pretty(k)}</span><b className={tone(v)}>{pct(v)}</b><Progress value={v}/></div>)}</div></Card>
   <Card><SectionTitle eyebrow="PHYSICS RESIDUALS" title="Observed − expected"/><div className="residual-table">{Object.entries(twin.residuals).map(([k,v])=><div key={k}><span>{pretty(k)}</span><b>{Number(v)>=0?"+":""}{fmt(v,k.includes("pressure")||k.includes("vibration")?3:1)}</b></div>)}</div><p className="fineprint">Baseline: {twin.twin_meta?.physics_model??"generic surrogate"}</p></Card>
  </div>

  <Card className="event-console"><SectionTitle eyebrow="LIVE EVENT INTELLIGENCE" title="Current decision chain"/><div className="decision-chain">{[[Signal,"Telemetry","Validated, time-aligned and quality-scored"],[Activity,"Twin residuals",`${Object.keys(twin.residuals).length} observed-vs-expected channels evaluated`],[BrainCircuit,"Diagnosis",normal?"No persistent condition detected":`${pretty(fault)} is the leading hypothesis`],[ShieldCheck,"Decision support",`${twin.readiness.label} · ${pretty(twin.maintenance.priority)}`]].map(([Icon,title,txt],i)=><div key={String(title)}><span>{i+1}</span><Icon size={18}/><div><strong>{title as string}</strong><small>{txt as string}</small></div></div>)}</div></Card>
 </motion.div>
}
