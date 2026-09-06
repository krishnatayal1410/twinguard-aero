import{lazy,Suspense,useEffect,useState}from"react";
import{Bell,Box,ChevronDown,FlaskConical,HeartPulse,History,Home,ScanSearch,Settings}from"lucide-react";
import{connectTwin,getTwin}from"./services/twinApi";
import{useTwinStore}from"./store/twinStore";
import{useAuthStore}from"./store/authStore";
import type{ViewName}from"./types/twin";
import ErrorBoundary from"./components/ErrorBoundary";
import"./styles/reference.css";

const CommandCenter=lazy(()=>import("./components/CommandCenter"));
const DigitalTwinDeck=lazy(()=>import("./components/DigitalTwinDeck"));
const HealthFaultsDeck=lazy(()=>import("./components/HealthFaultsDeck"));
const MissionDeck=lazy(()=>import("./components/MissionDeck"));
const ReplayDeck=lazy(()=>import("./components/ReplayDeck"));
const DiagnosticsDeck=lazy(()=>import("./components/DiagnosticsDeck"));
const SettingsDeck=lazy(()=>import("./components/SettingsDeck"));
const nav:Array<[ViewName,string,any]>=[["command","Command Center",Home],["digitalTwin","Digital Twin",Box],["healthFaults","Health & Faults",HeartPulse],["mission","Mission Lab",FlaskConical],["replay","Replay",History],["diagnostics","Diagnostics",ScanSearch],["settings","Settings",Settings]];

export default function App(){
 const view=useTwinStore(s=>s.view),setView=useTwinStore(s=>s.setView),twin=useTwinStore(s=>s.twin),online=useTwinStore(s=>s.online),runtime=useTwinStore(s=>s.runtimeValidity),setTwin=useTwinStore(s=>s.setTwin),setOnline=useTwinStore(s=>s.setOnline),setRuntime=useTwinStore(s=>s.setRuntimeValidity),runs=useTwinStore(s=>s.missionRuns),user=useAuthStore(s=>s.user),[clock,setClock]=useState(new Date());
 useEffect(()=>{getTwin().then(setTwin).catch(()=>undefined);return connectTwin(setTwin,setOnline,setRuntime)},[setTwin,setOnline,setRuntime]);
 useEffect(()=>{const id=setInterval(()=>setClock(new Date()),1000);return()=>clearInterval(id)},[]);
 const decisionEligible=online&&runtime?.decision_eligible!==false,last=runs.length?runs[runs.length-1].result:undefined;
 const mission=last?.mission_type?String(last.mission_type).replace(/_/g," "):"Endurance Patrol";
 const screen=view==="command"?<CommandCenter/>:view==="digitalTwin"?<DigitalTwinDeck/>:view==="healthFaults"?<HealthFaultsDeck/>:view==="mission"?<MissionDeck/>:view==="replay"?<ReplayDeck/>:view==="diagnostics"?<DiagnosticsDeck/>:<SettingsDeck/>;
 return <div className="tg-shell">
  <aside className="tg-sidebar">
   <div className="tg-brand"><img src="/assets/twinguard-mark.svg"/><div><strong>TwinGuard AI</strong><small>Mission Reliability. Assured.</small></div></div>
   <nav>{nav.map(([id,label,Icon])=><button key={id} className={view===id?"active":""} onClick={()=>setView(id)}><Icon size={21}/><span>{label}</span></button>)}</nav>
   <div className="tg-sidebar-art"><div className="tg-plane">✈</div><div className="mountain m1"/><div className="mountain m2"/><div className="mountain m3"/></div>
   <div className="tg-sidebar-foot"><b>BUILT FOR<br/>SAFER SKIES</b><span>MONITOR&nbsp;&nbsp;|&nbsp;&nbsp;PREDICT<br/>DECIDE&nbsp;&nbsp;|&nbsp;&nbsp;COMPLETE</span></div>
  </aside>
  <main className="tg-main">
   <header className="tg-topbar">
    <div className="tg-engine-id"><i/><b>ENGINE TG-001</b><span className={decisionEligible?"online":"hold"}>● {decisionEligible?"Online":"Data Hold"}</span></div>
    <div className="tg-top-mission">Mission: <b>{mission}</b></div>
    <div className="tg-clock">{clock.toLocaleTimeString([],{hour:"2-digit",minute:"2-digit",second:"2-digit",timeZone:"UTC"})} UTC</div>
    <div className="tg-top-spacer"/>
    <button className="tg-bell" onClick={()=>setView("diagnostics")}><Bell size={20}/>{(twin?.ai.anomaly||!decisionEligible)&&<i/>}</button>
    <div className="tg-user"><div className="avatar">KT</div><strong>{user?.name||"Krishna Tayal"}</strong><ChevronDown size={16}/></div>
   </header>
   <section className="tg-content"><ErrorBoundary name="TwinGuard page"><Suspense fallback={<div className="tg-loading">Loading TwinGuard…</div>}>{screen}</Suspense></ErrorBoundary></section>
  </main>
 </div>
}
