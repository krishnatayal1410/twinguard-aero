import{lazy,Suspense,useEffect,useState}from"react";
import type{ReactNode}from"react";
import{Activity,Bell,ChevronDown,FlaskConical,History,Home,LogOut,Menu,Settings,Share2,Stethoscope,Wrench}from"lucide-react";
import{connectTwin,getTwin}from"./services/twinApi";
import{useTwinStore}from"./store/twinStore";
import type{ViewName}from"./types/twin";
import ErrorBoundary from"./components/ErrorBoundary";
import{useAuthStore}from"./store/authStore";import{signOut}from"./services/authApi";
import"./styles/app.css";

const CommandCenter=lazy(()=>import("./components/CommandCenter"));
const DiagnosticsDeck=lazy(()=>import("./components/DiagnosticsDeck"));
const MissionDeck=lazy(()=>import("./components/MissionDeck"));
const ReplayDeck=lazy(()=>import("./components/ReplayDeck"));
const MaintenanceDeck=lazy(()=>import("./components/MaintenanceDeck"));
const SettingsDeck=lazy(()=>import("./components/SettingsDeck"));

const nav:Array<[ViewName,string,any]>=[
 ["command","Command Center",Home],["diagnostics","Diagnostics",Stethoscope],
 ["mission","Mission Lab",FlaskConical],["replay","Mission Replay",History],
 ["maintenance","Maintenance",Wrench],["settings","Settings",Settings]
];

function PageLoader(){return <div className="page-loader"><i/><strong>Loading TwinGuard Aero…</strong></div>}

export default function App(){
 const view=useTwinStore(s=>s.view),setView=useTwinStore(s=>s.setView),twin=useTwinStore(s=>s.twin),
 online=useTwinStore(s=>s.online),setTwin=useTwinStore(s=>s.setTwin),setOnline=useTwinStore(s=>s.setOnline),user=useAuthStore(s=>s.user),token=useAuthStore(s=>s.token),clearAuth=useAuthStore(s=>s.clear),[accountOpen,setAccountOpen]=useState(false);
 useEffect(()=>{getTwin().then(setTwin).catch(()=>undefined);return connectTwin(setTwin,setOnline)},[setTwin,setOnline]);
 const logout=async()=>{await signOut(token);clearAuth()};const share=async()=>{try{if(navigator.share)await navigator.share({title:"TwinGuard Aero",url:location.href});else await navigator.clipboard.writeText(location.href)}catch{}};const initials=(user?.name||"Operator").split(/\s+/).map(x=>x[0]).join("").slice(0,2).toUpperCase();
 const screens:Record<ViewName,ReactNode>={
  command:<CommandCenter/>,diagnostics:<DiagnosticsDeck/>,mission:<MissionDeck/>,
  replay:<ReplayDeck/>,maintenance:<MaintenanceDeck/>,settings:<SettingsDeck/>
 };
 return <div className="app-shell exact-shell">
  <aside className="sidebar exact-sidebar">
   <div className="brand exact-brand"><img src="/assets/twinguard-mark.svg" alt=""/><div><strong>TwinGuard <span>Aero</span></strong></div></div>
   <nav>{nav.map(([id,label,Icon])=><button key={id} className={view===id?"active":""} onClick={()=>setView(id)}><Icon size={18}/><span>{label}</span></button>)}</nav>
   <div className="engine-status-card exact-engine-status">
    <div className="engine-status-head"><i className={online?"":"off"}/><div><strong>ENGINE-01</strong><span>{online?"Connected":"Reconnecting"}</span></div></div>
    <dl><div><dt>Data Source</dt><dd>Twin Telemetry Link</dd></div><div><dt>Uptime</dt><dd>{twin?`${Number(twin.telemetry.operating_hours??0).toFixed(1)} h`:"--"}</dd></div><div><dt>Last Sync</dt><dd>{twin?"Just now":"Waiting"}</dd></div></dl>
   </div>
   <button className="collapse-button"><Menu size={16}/>Collapse</button>
  </aside>

  <main className="main-shell exact-main">
   <header className="topbar exact-topbar">
    <div className="engine-selector"><Activity size={15}/><strong>ENGINE-01</strong><ChevronDown size={13}/></div>
    <div className={`live-chip ${online?"online":"offline"}`}><i/>{online?"Live Telemetry":"Connecting"}</div>
    <div className="topbar-spacer"/>
    <div className="ambient"><span className="sun">☀</span><span>Ambient</span><b>{Number(twin?.telemetry.ambient_temperature??35).toFixed(0)}°C</b></div>
    <button className="alert-button" onClick={()=>setView("diagnostics")}><Bell size={16}/><span>Alerts</span>{twin?.ai.anomaly&&<i/>}</button>
    <button className="share-button" onClick={share}><Share2 size={15}/>Share</button>
    <div className="account-wrap"><button className="operator exact-operator" onClick={()=>setAccountOpen(v=>!v)}><div className="avatar">{initials}</div><div><strong>{user?.name||"Operator"}</strong><span>{user?.role==="admin"?"System Administrator":"Systems Operator"}</span></div><ChevronDown size={13}/></button>{accountOpen&&<div className="account-menu"><div><b>{user?.name}</b><span>{user?.email}</span></div><button onClick={()=>setView("settings")}><Settings size={14}/>Account settings</button><button className="danger" onClick={logout}><LogOut size={14}/>Sign out</button></div>}</div>
   </header>
   <div className="content exact-content">
    <ErrorBoundary name={nav.find(x=>x[0]===view)?.[1]??"Dashboard"} fallback={<div className="dashboard-error"><strong>This dashboard panel failed to load.</strong><span>Open Safari → Develop → Show JavaScript Console for the detailed browser error, or click retry.</span><button onClick={()=>location.reload()}>Reload dashboard</button></div>}>
     <Suspense fallback={<PageLoader/>}>{screens[view]}</Suspense>
    </ErrorBoundary>
   </div>
   <footer><span>All times in UTC · Data latency 120ms</span><span className={online?"online":""}><i/>{online?"Live":"Waiting"}</span></footer>
  </main>
 </div>
}