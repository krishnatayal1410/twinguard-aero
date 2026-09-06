import{useEffect,useState}from"react";
import{motion}from"framer-motion";
import{Box,CheckCircle2,Database,Gamepad2,LogOut,Radio,RefreshCcw,ShieldCheck,Usb,UserRound}from"lucide-react";
import{getSystemStatus}from"../services/twinApi";
import type{SystemStatus}from"../types/twin";
import{Badge,Card,SectionTitle,pretty}from"./ui";
import{useAuthStore}from"../store/authStore";
import{useTwinStore}from"../store/twinStore";
import{signOut}from"../services/authApi";

export default function SettingsDeck(){
 const[status,setStatus]=useState<SystemStatus>();
 const user=useAuthStore(s=>s.user),token=useAuthStore(s=>s.token),clear=useAuthStore(s=>s.clear);
 const twin=useTwinStore(s=>s.twin),runtimeValidity=useTwinStore(s=>s.runtimeValidity);
 const load=()=>getSystemStatus().then(setStatus).catch(()=>setStatus(undefined));
 useEffect(()=>{void load()},[]);
 const items=[["Database",status?.database,Database],["MQTT",status?.integrations.mqtt?"Enabled":"Local / disabled",Radio],["CAN / SocketCAN",status?.integrations.can?"Enabled":"Adapter ready",Usb],["Unreal UDP",status?.integrations.unreal_udp?"Enabled":"Adapter ready",Gamepad2]]as const;
 const modelItems=[
  ["Runtime mode",pretty(twin?.ai.model_state??"waiting")],
  ["Feature contract",twin?.ai.feature_contract??"--"],
  ["Anomaly detector",status?.models.anomaly?"Active":"Engineering fallback"],
  ["Fault classifier",status?.models.fault?"Active native model":"Engineering fallback"],
  ["RUL regressor",status?.models.rul?"Active native model":"Engineering surrogate"],
  ["Validation scope",pretty(twin?.ai.validation_scope??"synthetic proof of concept")],
 ] as const;
 return <motion.div className="settings-page" initial={{opacity:0,y:8}} animate={{opacity:1,y:0}}>
  <Card className="settings-hero"><SectionTitle eyebrow="SYSTEM INTEGRATION" title="TwinGuard platform status" action={<button className="icon-button" onClick={load}><RefreshCcw size={15}/></button>}/><div className="system-status-grid">{items.map(([n,v,Icon])=><div key={n}><Icon size={24}/><span>{n}</span><strong>{v??"Waiting…"}</strong><CheckCircle2 size={15}/></div>)}</div><p className="fineprint">Decision data gate: {runtimeValidity?.decision_eligible===false?"HOLD":"eligible"} · telemetry age {runtimeValidity?.telemetry_age_seconds==null?"--":`${runtimeValidity.telemetry_age_seconds.toFixed(1)} s`}.</p></Card>
  <div className="settings-grid">
   <Card><SectionTitle eyebrow="OPERATOR ACCOUNT" title="Signed-in identity"/><div className="account-settings-card"><UserRound/><div><strong>{user?.name}</strong><span>{user?.email}</span><Badge kind="blue">{pretty(user?.role??"operator")}</Badge></div><button onClick={async()=>{await signOut(token);clear()}}><LogOut size={14}/>Sign out</button></div></Card>
   <Card><SectionTitle eyebrow="DIAGNOSTIC / PROGNOSTIC RUNTIME" title="Active computation path"/><div className="status-list">{modelItems.map(([k,v])=><div key={k}><span>{k}</span><Badge kind={String(v).toLowerCase().includes("fallback")||String(v).toLowerCase().includes("surrogate")?"warn":"good"}>{v}</Badge></div>)}</div>{twin?.ai.model_warning&&<p className="fineprint">{twin.ai.model_warning}</p>}<p className="fineprint">Compatible synthetic native models are verified separately in CI; the live runtime only claims them active when `TWINGUARD_NATIVE_ML=1` and the artifact contract matches.</p></Card>
   <Card><SectionTitle eyebrow="SECURITY DEFAULTS" title="Local MVP hardening"/><div className="security-list"><div><ShieldCheck/><span>Operator sign-in and expiring sessions</span></div><div><ShieldCheck/><span>PBKDF2-SHA256 password hashing</span></div><div><ShieldCheck/><span>Restricted CORS origins</span></div><div><ShieldCheck/><span>Trusted host validation</span></div><div><ShieldCheck/><span>Telemetry ingest key</span></div><div><ShieldCheck/><span>Security response headers</span></div><div><ShieldCheck/><span>Local-development deployment defaults</span></div></div></Card>
   <Card><SectionTitle eyebrow="3D / INTEROPERABILITY" title="Digital Twin bridges"/><div className="bridge-list"><div><Box/><span>Procedural aero-piston WebGL engineering visualization</span></div><div><Box/><span>glTF / GLB UAV context asset</span></div><div><Gamepad2/><span>Unreal Engine UDP JSON stream</span></div><div><Radio/><span>MQTT telemetry adapter</span></div><div><Usb/><span>python-can / SocketCAN adapter</span></div></div></Card>
  </div>
  <Card><SectionTitle eyebrow="DEPLOYMENT NOTE" title="Production boundary"/><p className="settings-note">This project is a synthetic engineering demonstrator. Before connection to a physical UAV engine, calibrate the physics and AI models using authorized engine/test-rig data, place the API behind authenticated network controls, use TLS/mTLS as appropriate, validate all CAN/ECU mappings against official interface documentation, and complete the applicable safety/cybersecurity validation pathway.</p></Card>
 </motion.div>
}
