import{Activity,Clock3,Fuel,Gauge,Mountain,ShieldCheck,Thermometer}from"lucide-react";
import{useTwinStore}from"../store/twinStore";
import EngineTwin from"./EngineTwin";
import{fmt}from"./ui";
import{MiniLineChart,PageHeader,Panel,PanelTitle,StatusPill}from"./ReferenceUI";

export default function DigitalTwinDeck(){
 const twin=useTwinStore(s=>s.twin),history=useTwinStore(s=>s.history),t=twin?.telemetry??{},e=twin?.expected??{},r=twin?.residuals??{},tr=twin?.trends??{};
 const rows=[
  ["RPM (rpm)",Number(t.rpm??0),Number(e.rpm??t.rpm??0),Number(r.rpm??Number(t.rpm??0)-Number(e.rpm??t.rpm??0))],
  ["CHT (°C)",Number(t.cht??0),Number(e.cht??0),Number(r.cht??0)],
  ["EGT (°C)",Number(t.egt??0),Number(e.egt??0),Number(r.egt??0)],
  ["Oil Pressure (kPa)",Number(t.oil_pressure??0)*100,Number(e.oil_pressure??0)*100,Number(r.oil_pressure??0)*100],
  ["Oil Temp (°C)",Number(t.oil_temperature??0),Number(e.oil_temperature??0),Number(r.oil_temperature??0)],
  ["Vibration (g)",Number(t.vibration??0),Number(e.vibration??0),Number(r.vibration??0)]
 ];
 return <div className="ref-page digital-page">
  <PageHeader title="Digital Twin" subtitle="Engine state, expected model, residuals, and temporal analysis"/>
  <div className="ref-tabs"><button className="active">State Overview</button><button>Expected Model</button><button>Residuals</button><button>Trends</button><button>Model Details</button></div>
  <div className="dt-top-grid">
   <Panel><PanelTitle title="Engine Operating State"/><div className="state-list">
    <div><Gauge/><span>RPM</span><b>{fmt(t.rpm,0)} rpm</b></div><div><Activity/><span>Throttle</span><b>{fmt(t.throttle,0)} %</b></div><div><Mountain/><span>Altitude</span><b>{fmt(t.altitude,0)} m</b></div><div><Thermometer/><span>Ambient Temp</span><b>{fmt(t.ambient_temp,0)} °C</b></div><div><Fuel/><span>Fuel Flow</span><b>{fmt(t.fuel_flow,1)} L/h</b></div><div><ShieldCheck/><span>Mission Profile</span><b>Patrol</b></div>
   </div></Panel>
   <Panel className="blueprint-panel"><div className="blueprint-stage"><EngineTwin compact focus="all" autoRotate/></div></Panel>
   <Panel><PanelTitle title="Twin Status"/><div className="twin-status"><div className="sync"><ShieldCheck/><b>Synchronized</b></div><div><Clock3/><span>Last Update</span><b>{new Date(twin?.timestamp??Date.now()).toLocaleTimeString([],{hour12:false})} UTC</b><small>Real-time, 1s interval</small></div><div><Activity/><span>Model Type</span><b>Hybrid (Physics + AI)</b></div><div><ShieldCheck/><span>Data Validity</span><b>{Math.round(Number(twin?.confidence.data_quality??98))}%</b></div><div><Gauge/><span>Engine Type</span><b>Aero-Piston (MALE UAV)</b></div></div></Panel>
  </div>
  <div className="dt-bottom-grid">
   <Panel><PanelTitle title="Actual vs Expected"/><div className="ref-table-wrap"><table className="ref-table"><thead><tr><th>Parameter</th><th>Actual</th><th>Expected</th><th>Residual</th><th>Trend</th></tr></thead><tbody>{rows.map(([name,a,x,res])=>{const n=Number(res),trend=name.toString().includes("Oil Pressure")&&n<0?"Falling":Math.abs(n)<3?"Stable":n>0?"Rising":"Falling";return <tr key={String(name)}><td>{name}</td><td>{typeof a==="number"?fmt(a,String(name).includes("Vibration")?2:0):a}</td><td>{typeof x==="number"?fmt(x,String(name).includes("Vibration")?2:0):x}</td><td className={n>0?"res-pos":n<0?"res-neg":""}>{n>0?"+":""}{fmt(n,String(name).includes("Vibration")?2:0)}</td><td><span className={`trend ${trend==="Stable"?"stable":"warn"}`}>● {trend}</span></td></tr>})}</tbody></table></div></Panel>
   <Panel><PanelTitle title="Residual Trends" right={<StatusPill tone="blue">Last 60 minutes</StatusPill>}/><MiniLineChart series={[{name:"Oil Pressure",values:(history.oil_pressure??[]).map(v=>v*100-(Number(e.oil_pressure??v)*100)),color:"#0d72f4"},{name:"CHT",values:(history.cht??[]).map(v=>v-Number(e.cht??v)),color:"#8b35ee"},{name:"Vibration",values:(history.vibration??[]).map(v=>(v-Number(e.vibration??v))*100),color:"#ff7a00"}]} labels={["-60m","-50m","-40m","-30m","-20m","-10m","0m"]}/></Panel>
  </div>
 </div>
}
