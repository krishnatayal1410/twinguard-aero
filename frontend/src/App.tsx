import{lazy,Suspense,useEffect,useState}from"react";
import type{ReactNode}from"react";
import{Activity,Bell,Box,ChevronDown,FlaskConical,HeartPulse,History,Home,LogOut,Menu,ScanSearch,Settings,Share2}from"lucide-react";
import{connectTwin,getTwin}from"./services/twinApi";
import{useTwinStore}from"./store/twinStore";
import type{ViewName}from"./types/twin";
import ErrorBoundary from"./components/ErrorBoundary";
import{useAuthStore}from"./store/authStore";
import{signOut}from"./services/authApi";
import{isHostedDemo}from"./demo/demoRuntime";
import"./styles/app.css";
import"./styles/premium.css";

const CommandCenter=lazy(()=>import("./components/CommandCenter"));
const DigitalTwinDeck=lazy(()=>import("./components/DigitalTwinDeck"));
const HealthFaultsDeck=lazy(()=>import("./components/HealthFaultsDeck"));
const DiagnosticsDeck=lazy(()=>import("./components/DiagnosticsDeck"));
const MissionDeck=lazy(()=>import("./components/MissionDeck"));
const ReplayDeck=lazy(()=>import("./components/ReplayDeck"));
const MaintenanceDeck=lazy(()=>import("./components/MaintenanceDeck"));
const SettingsDeck=lazy(()=>import("./components/SettingsDeck"));

const nav:Array<[ViewName,string,any]>=[
 ["command","Command Center",Home],["digitalTwin","Digital Twin",Box],["healthFaults","Health & Faults",HeartPulse],
 ["mission","Mission Lab",FlaskConical],["replay","Replay",History],["diagnostics","Diagnostics",ScanSearch],["settings","Settings",Settings]
];
function PageLoader(){return <div className="page-loader"><i/><strong>Loading TwinGuard AI…</strong></div>}

export default function App(){
 const view=useTwinStore(s=>s.view),setView=useTwinStore(s=>s.setView),twin=useTwinStore(s=>s.twin),online=useTwinStore(s=>s.online),setTwin=useTwinStore(s=>s.setTwin),setOnline=useTwinStore(s=>s.setOnline),runtimeValidity=useTwinStore(s=>s.runtimeValidity),setRuntimeValidity=useTwinStore(s=>s.setRuntimeValidity),missionRuns=useTwinStore(s=>s.missionRuns),user=useAuthStore(s=>s.user),token=useAuthStore(s=>s.token),clearAuth=useAuthStore(s=>s.clear),[accountOpen,setAccountOpen]=useState(false),[clock,setClock]=useState(new Date()),demo=isHostedDemo();
 useEffect(()=>{getTwin().then(setTwin).catch(()=>undefined);return connectTwin(setTwin,setOnline,setRuntimeValidity)},[setTwin,setOnline,setRuntimeValidity]);
 useEffect(()=>{const id=window.setInterval(()=>setClock(new Date()),1000);return()=>window.clearInterval(id)},[]);
 const logout=async()=>{if(demo)return;await signOut(token);clearAuth()};
 const share=async()=>{try{if(navigator.share)await navigator.share({title:"TwinGuard AI",url:location.href});else await navigator.clipboard.writeText(location.href)}catch{}};
 const initials=demo?"TG":(user?.name||"Operator").split(/\s+/).map(x=>x[0]).join("").slice(0,2).toUpperCase();
 const decisionLive=online&&runtimeValidity?.decision_eligible!==false,dataState=!online?"Reconnecting":runtimeValidity?.stale?"Data Hold":runtimeValidity?.decision_eligible===false?"Quality Hold":"Online",age=runtimeValidity?.telemetry_age_seconds,lastSync=age==null?(twin?"Received":"Waiting"):age<1?"<1 s ago":`${age.toFixed(age<10?1:0)} s ago`,lastMission=missionRuns.length?missionRuns[missionRuns.length-1].result:undefined;
 const screens:Record<ViewName,ReactNode>={command:<CommandCenter/>,digitalTwin:<DigitalTwinDeck/>,healthFaults:<HealthFaultsDeck/>,diagnostics:<DiagnosticsDeck/>,mission:<MissionDeck/>,replay:<ReplayDeck/>,maintenance:<MaintenanceDeck/>,settings:<SettingsDeck/>};
 return <div className="app-shell exact-shell premium-shell">
  <aside className="sidebar exact-sidebar premium-sidebar">
   <div className="brand exact-brand premium-brand"><img src="/assets/twinguard-mark.svg" alt=""/><div><strong>TwinGuard</strong><span>AI</span><small>Mission Reliability. Assured.</small></div></div>
   <nav>{nav.map(([id,label,Icon])=><button key={id} className={view===id?"active":""} onClick={()=>setView(id)}><Icon size={17}/><span>{label}</span></button>)}</nav>
   <div className="sidebar-spacer"/>
   <div className="engine-status-card exact-engine-status premium-engine-status"><div className="engine-status-head"><i className={decisionLive?"":"off"}/><div><strong>ENGINE TG-001</strong><span>{dataState}</span></div></div><dl><div><dt>Validation</dt><dd>{demo?"Hosted Demo":"Synthetic POC"}</dd></div><div><dt>Operating Hours</dt><dd>{twin?`${Number(twin.telemetry.operating_hours??0).toFixed(1)} h`:"--"}</dd></div><div><dt>Last Sync</dt><dd>{lastSync}</dd></div></dl></div>
   <button className="collapse-button"><Menu size={16}/>Compact Navigation</button>
  </aside>
  <main className="main-shell exact-main premium-main">
   <header className="topbar exact-topbar premium-topbar">
    <div className="engine-selector"><Activity size={15}/><strong>ENGINE TG-001</strong><span className="engine-online">{decisionLive?"Online":"Hold"}</span></div>
    <div className="mission-top-label"><span>Mission:</span><b>{lastMission?.mission_type?String(lastMission.mission_type).replace(/_/g," "):demo?"Endurance Patrol":"Not Evaluated"}</b></div>
    <div className="utc-clock">{clock.toLocaleTimeString([],{hour:"2-digit",minute:"2-digit",second:"2-digit",timeZone:"UTC"})} UTC</div>
    <div className="topbar-spacer"/>
    <button className="alert-button" onClick={()=>setView("diagnostics")}><Bell size={16}/>{(twin?.ai.anomaly||runtimeValidity?.decision_eligible===false)&&<i/>}</button>
    <button className="share-button" onClick={share}><Share2 size={15}/><span>Share</span></button>
    <div className="account-wrap"><button className="operator exact-operator" onClick={()=>setAccountOpen(v=>!v)}><div className="avatar">{initials}</div><div><strong>{demo?"TwinGuard Demo":user?.name||"Operator"}</strong><span>{demo?"Public SIH Demonstrator":user?.role==="admin"?"System Administrator":"Systems Operator"}</span></div><ChevronDown size={13}/></button>{accountOpen&&<div className="account-menu"><div><b>{demo?"TwinGuard AI":user?.name}</b><span>{demo?"Synthetic hosted demonstration":user?.email}</span></div><button onClick={()=>setView("settings")}><Settings size={14}/>System settings</button>{!demo&&<button className="danger" onClick={logout}><LogOut size={14}/>Sign out</button>}</div>}</div>
   </header>
   <div className="content exact-content premium-content"><ErrorBoundary name={nav.find(x=>x[0]===view)?.[1]??"Dashboard"} fallback={<div className="dashboard-error"><strong>This TwinGuard panel failed to load.</strong><span>Reload the dashboard or inspect the local verification log.</span><button onClick={()=>location.reload()}>Reload dashboard</button></div>}><Suspense fallback={<PageLoader/>}>{screens[view]}</Suspense></ErrorBoundary></div>
   <footer className="premium-footer"><span>SIH26054 · Aero-Piston Digital Twin · {demo?"Hosted synthetic demonstrator":"Local engineering demonstrator"}</span><span className={decisionLive?"online":""}><i/>{!online?"Waiting":decisionLive?"Decision-eligible":"Data hold"}</span></footer>
  </main>
 </div>
}
