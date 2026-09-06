import{useMemo,useState}from"react";
import{motion}from"framer-motion";
import{Activity,Atom,BrainCircuit,CheckCircle2,Clock3,DatabaseZap,GitCompareArrows,RadioTower,TrendingDown,TrendingUp}from"lucide-react";
import{useTwinStore}from"../store/twinStore";
import EngineTwin from"./EngineTwin";
import{Badge,Card,MiniSpark,Progress,SectionTitle,fmt,pct,pretty}from"./ui";

const oilKpa=(v:unknown)=>Number(v||0)*100;
const direction=(v:number)=>v>0.02?"Rising":v<-.02?"Falling":"Stable";

export default function DigitalTwinDeck(){
 const twin=useTwinStore(s=>s.twin),history=useTwinStore(s=>s.history),runtime=useTwinStore(s=>s.runtimeValidity),[tab,setTab]=useState("observer");
 const rows=useMemo(()=>[
  ["RPM","rpm","RPM",0,1],
  ["CHT","cht","°C",1,1],
  ["EGT","egt","°C",1,1],
  ["Oil Pressure","oil_pressure","kPa",0,100],
  ["Oil Temperature","oil_temperature","°C",1,1],
  ["Vibration","vibration","g",3,1],
  ["Battery","battery_voltage","V",1,1],
  ["Alternator","alternator_voltage","V",1,1]
 ]as const,[]);
 const telemetry=(k:string)=>Number(twin?.telemetry[k]??0),expected=(k:string)=>Number(twin?.expected[k]??0),residual=(k:string)=>Number(twin?.residuals[k]??0);
 return <motion.div className="premium-page twin-page-v2" initial={{opacity:0,y:8}} animate={{opacity:1,y:0}}>
  <div className="premium-page-head"><div><span>HYBRID DIGITAL TWIN</span><h1>Digital Twin</h1><p>State observer, expected healthy model, residual intelligence and temporal evidence.</p></div><Badge kind={runtime?.decision_eligible===false?"warn":"good"}><RadioTower size={13}/>{runtime?.decision_eligible===false?"DATA HOLD":"SYNCHRONIZED"}</Badge></div>
  <div className="premium-tabs">{[["observer","State Observer"],["expected","Expected Model"],["residuals","Residuals"],["trends","Trends"],["model","Model Details"]].map(([id,label])=><button key={id} className={tab===id?"active":""} onClick={()=>setTab(id)}>{label}</button>)}</div>

  <div className="twin-overview-grid">
   <Card className="twin-state-card"><SectionTitle eyebrow="ENGINE OPERATING STATE" title="Current synchronized state"/><div className="state-kv">{[["RPM",`${fmt(twin?.telemetry.rpm,0)} rpm`],["Throttle",`${fmt(twin?.telemetry.throttle,0)}%`],["Altitude",`${fmt(twin?.telemetry.altitude,0)} m`],["Ambient",`${fmt(twin?.telemetry.ambient_temperature,0)}°C`],["Fuel Flow",`${fmt(twin?.telemetry.fuel_flow,1)} L/h`],["Operating Hours",`${fmt(twin?.telemetry.operating_hours,1)} h`]].map(x=><div key={x[0]}><span>{x[0]}</span><strong>{x[1]}</strong></div>)}</div></Card>
   <Card className="twin-engine-visual"><div className="twin-engine-stage"><EngineTwin compact xray={tab==="residuals"||tab==="model"} autoRotate focus="all"/></div></Card>
   <Card className="twin-status-card"><SectionTitle eyebrow="TWIN STATUS" title="Runtime identity"/><div className="status-stack"><div><CheckCircle2/><span>Latest update</span><b>{twin?new Date(twin.timestamp).toLocaleTimeString():"--"}</b></div><div><Atom/><span>Physics model</span><b>{twin?.twin_meta?.physics_model??"--"}</b></div><div><BrainCircuit/><span>Diagnostic runtime</span><b>{pretty(twin?.ai.model_state??"waiting")}</b></div><div><DatabaseZap/><span>Validation scope</span><b>{pretty(twin?.twin_meta?.validation_scope??"--")}</b></div><div><Clock3/><span>Telemetry age</span><b>{runtime?.telemetry_age_seconds==null?"--":`${fmt(runtime.telemetry_age_seconds,1)} s`}</b></div></div></Card>
  </div>

  <div className="twin-detail-grid">
   <Card className="twin-compare-card"><SectionTitle eyebrow="OBSERVED vs EXPECTED" title="Residual comparison" action={<Badge kind="blue"><GitCompareArrows size={13}/> Actual − Expected</Badge>}/><div className="twin-table"><div className="twin-table-head"><span>Parameter</span><span>Actual</span><span>Expected</span><span>Residual</span><span>Trend</span></div>{rows.map(([label,key,unit,d,m])=>{const a=telemetry(key)*m,e=expected(key)*m,r=residual(key)*m;return <div className="twin-table-row" key={key}><strong>{label}</strong><span>{fmt(a,d)} {unit}</span><span>{fmt(e,d)} {unit}</span><b className={Math.abs(r)>Math.max(1,Math.abs(e)*.08)?"warn":""}>{r>0?"+":""}{fmt(r,d)}</b><em className={direction(r)==="Stable"?"stable":direction(r)==="Rising"?"up":"down"}>{direction(r)} {direction(r)==="Rising"?<TrendingUp/>:direction(r)==="Falling"?<TrendingDown/>:<Activity/>}</em></div>})}</div></Card>
   <Card className="residual-trend-card"><SectionTitle eyebrow="TEMPORAL RESIDUAL INTELLIGENCE" title="Recent channel behavior"/><div className="residual-sparks">{[["Oil Pressure",history.oil_pressure??[],`${fmt(oilKpa(residual("oil_pressure")),0)} kPa`],["CHT",history.cht??[],`${residual("cht")>0?"+":""}${fmt(residual("cht"),1)}°C`],["Vibration",history.vibration??[],`${residual("vibration")>0?"+":""}${fmt(residual("vibration"),3)} g`]].map(([name,values,r])=><div key={String(name)}><div><span>{name}</span><b>{r}</b></div><MiniSpark values={values as number[]}/></div>)}</div><div className="persistence-box"><span>Anomaly persistence</span><strong>{twin?.ai.anomaly_persistence_samples??0} samples</strong><Progress value={Math.min(100,(twin?.ai.anomaly_persistence_samples??0)*2.4)} kind={twin?.ai.anomaly?"warn":"good"}/></div></Card>
  </div>

  <div className="twin-model-strip"><Card><Atom/><div><span>Expected-state model</span><strong>{twin?.twin_meta?.physics_model??"Generic aero-piston surrogate"}</strong><small>Operating-condition-aware low-order engineering model; not an OEM map.</small></div></Card><Card><BrainCircuit/><div><span>Residual-to-diagnosis path</span><strong>{pretty(twin?.ai.model_state??"Engineering Fallback")}</strong><small>Residual magnitude, persistence, sensor corroboration and temporal direction.</small></div></Card><Card><DatabaseZap/><div><span>Evidence boundary</span><strong>{pretty(twin?.ai.validation_scope??"Synthetic POC")}</strong><small>Architecture demonstrator until engine-specific calibration and test-rig validation.</small></div></Card></div>
 </motion.div>
}
