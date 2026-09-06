import{useEffect,useState}from"react";
import{motion}from"framer-motion";
import{Box,CheckCircle2,Database,Gamepad2,LogOut,Radio,RefreshCcw,ShieldCheck,Usb,UserRound}from"lucide-react";
import{getSystemStatus}from"../services/twinApi";
import type{SystemStatus}from"../types/twin";
import{Badge,Card,SectionTitle,pretty}from"./ui";
import{useAuthStore}from"../store/authStore";
import{useTwinStore}from"../store/twinStore";
import{signOut}from"../services/authApi";
import{isHostedDemo}from"../demo/demoRuntime";

export default function SettingsDeck(){
 const[status,setStatus]=useState<SystemStatus>();const user=useAuthStore(s=>s.user),token=useAuthStore(s=>s.token),clear=useAuthStore(s=>s.clear),twin=useTwinStore(s=>s.twin),runtimeValidity=useTwinStore(s=>s.runtimeValidity),demo=isHostedDemo(),telemetryAge=runtimeValidity?.telemetry_age_seconds;
 const load=()=>getSystemStatus().then(setStatus).catch(()=>setStatus(undefined));useEffect(()=>{void load()},[]);
 const items=[["Database",status?.database,Database],["MQTT",status?.integrations.mqtt?"Enabled":"Local / disabled",Radio],["CAN / SocketCAN",status?.integrations.can?"Enabled":"Adapter ready",Usb],["Unreal UDP",status?.integrations.unreal_udp?"Enabled":"Adapter ready",Gamepad2]]as const;
 const modelItems=[["Runtime mode",pretty(twin?.ai.model_state??"waiting")],["Feature contract",twin?.ai.feature_contract??"--"],["Anomaly detector",status?.models.anomaly?"Active":"Engineering fallback"],["Fault classifier",status?.models.fault?"Active native model":"Engineering fallback"],["RUL regressor",status?.models.rul?"Active native model":"Engineering surrogate"],["Validation scope",pretty(twin?.ai.validation_scope??"synthetic proof of concept")]]as const;
 return <motion.div className="settings-page" initial={{opacity:0,y:8}} animate={{opacity:1,y:0}}>
  <div className="premium-page-head"><div><span>PLATFORM CONTROL</span><h1>Settings & System</h1><p>Connections, simulator state, model provenance, data validity and deployment boundary.</p></div><Badge kind={demo?"blue":"good"}>{demo?"VERCEL HOSTED DEMO":"LOCAL SYSTEM"}</Badge></div>
  <Card className="settings-hero"><SectionTitle eyebrow="SYSTEM STATUS" title="TwinGuard platform status" action={<button className="icon-button" onClick={load}><RefreshCcw size={15}/></button>}/><div className="system-status-grid">{items.map(([n,v,Icon])=><div key={n}><Icon size={24}/><span>{n}</span><strong>{v??"Waiting…"}</strong><CheckCircle2 size={15}/></div>)}</div><p className="fineprint">Decision data gate: {runtimeValidity?.decision_eligible===false?"HOLD":"eligible"} · telemetry age {telemetryAge==null?"--":`${telemetryAge.toFixed(1)} s`} · environment {status?.environment??"--"}.</p></Card>
  <div className="settings-grid">
   <Card><SectionTitle eyebrow="OPERATOR / DEMO IDENTITY" title="Current session"/><div className="account-settings-card"><UserRound/><div><strong>{demo?"TwinGuard Public Demo":user?.name??"Operator"}</strong><span>{demo?"Interactive synthetic demonstrator":user?.email??"Local session"}</span><Badge kind="blue">{demo?"SIH VIEWER":pretty(user?.role??"operator")}</Badge></div>{!demo&&<button onClick={async()=>{await signOut(token);clear()}}><LogOut size={14}/>Sign out</button>}</div></Card>
   <Card><SectionTitle eyebrow="DIAGNOSTIC / PROGNOSTIC RUNTIME" title="Active computation path"/><div className="status-list">{modelItems.map(([k,v])=><div key={k}><span>{k}</span><Badge kind={String(v).toLowerCase().includes("fallback")||String(v).toLowerCase().includes("surrogate")?"warn":"good"}>{v}</Badge></div>)}</div>{twin?.ai.model_warning&&<p className="fineprint">{twin.ai.model_warning}</p>}<p className="fineprint">Compatible synthetic native models are verified separately; the stable runtime only claims them active when the artifact contract matches.</p></Card>
   <Card><SectionTitle eyebrow="SECURITY DEFAULTS" title="Demonstrator hardening"/><div className="security-list"><div><ShieldCheck/><span>{demo?"Public read-only demo mode":"Operator sign-in and expiring sessions"}</span></div><div><ShieldCheck/><span>Explicit synthetic-data provenance</span></div><div><ShieldCheck/><span>Restricted production claims</span></div><div><ShieldCheck/><span>Telemetry validity gate</span></div><div><ShieldCheck/><span>Fail-safe DATA HOLD state</span></div><div><ShieldCheck/><span>Local ingest authentication in full stack</span></div></div></Card>
   <Card><SectionTitle eyebrow="3D / INTEROPERABILITY" title="Digital Twin bridges"/><div className="bridge-list"><div><Box/><span>Procedural aero-piston WebGL engineering visualization</span></div><div><Box/><span>MALE UAV context asset</span></div><div><Gamepad2/><span>Unreal Engine UDP JSON bridge in full stack</span></div><div><Radio/><span>MQTT telemetry adapter in full stack</span></div><div><Usb/><span>python-can / SocketCAN integration path</span></div></div></Card>
  </div>
  <Card><SectionTitle eyebrow="DEPLOYMENT NOTE" title="Production boundary"/><p className="settings-note">The Vercel build is an interactive synthetic showcase of the operator HMI and decision chain. The repository also contains the full FastAPI/WebSocket backend, simulator, persistence, tests and integration scaffolds for local/container deployment. Before connection to a physical UAV engine, calibrate the models using authorized engine/test-rig data and complete the applicable safety and cybersecurity validation pathway.</p></Card>
 </motion.div>
}
