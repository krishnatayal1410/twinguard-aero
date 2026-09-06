import{CircleStop,Pause,Play,SkipForward}from"lucide-react";
import{useEffect,useMemo,useState}from"react";
import{endReplay,listReplay,startReplay}from"../services/twinApi";
import{useTwinStore}from"../store/twinStore";
import{MiniLineChart,PageHeader,Panel,PanelTitle}from"./ReferenceUI";

export default function ReplayDeck(){
 const history=useTwinStore(s=>s.history),missions=useTwinStore(s=>s.missions),setMissions=useTwinStore(s=>s.setMissions),[playing,setPlaying]=useState(false),[progress,setProgress]=useState(28),[recording,setRecording]=useState(false),[busy,setBusy]=useState(false);
 useEffect(()=>{listReplay().then(setMissions).catch(()=>undefined)},[setMissions]);
 useEffect(()=>{if(!playing)return;const id=setInterval(()=>setProgress(v=>v>=100?0:v+.3),250);return()=>clearInterval(id)},[playing]);
 const start=async()=>{setBusy(true);try{await startReplay(`TwinGuard Mission ${new Date().toLocaleString()}`);setRecording(true)}finally{setBusy(false)}},stop=async()=>{setBusy(true);try{await endReplay();setRecording(false);setMissions(await listReplay())}finally{setBusy(false)}};
 const latest=missions[0],events=((latest?.summary??{}).events??[]) as Array<Record<string,any>>;
 const markerEvents=events.length?events.slice(0,6):[{type:"Oil pressure started declining",timestamp:"01:02:16",severity:"red"},{type:"Anomaly detected (Lubrication)",timestamp:"02:14:32",severity:"orange"},{type:"Diagnosis: Lubrication degradation",timestamp:"03:06:10",severity:"purple"},{type:"Mission risk changed to MEDIUM",timestamp:"04:28:16",severity:"blue"},{type:"Operator reduced throttle",timestamp:"05:42:31",severity:"green"},{type:"Condition stabilized",timestamp:"07:02:18",severity:"gray"}];
 const trim=(a:number[])=>a.slice(-90);
 return <div className="ref-page replay-ref-page"><PageHeader title="Mission Replay" subtitle="Timeline playback, synchronized telemetry, and event analysis"/>
  <div className="replay-controls-row"><Panel className="replay-controls"><PanelTitle title="Playback Controls"/><div className="player-controls"><button onClick={()=>setPlaying(true)}><Play/></button><button onClick={()=>setPlaying(false)}><Pause/></button><button><SkipForward/></button><div className="replay-progress"><i style={{width:`${progress}%`}}/><b style={{left:`${progress}%`}}/></div><strong>{String(Math.floor(progress/100*8)).padStart(2,"0")}:{String(Math.round(progress%12*5)).padStart(2,"0")}:32 / 08:00:00</strong><select><option>1×</option><option>2×</option><option>4×</option></select><button className="record-btn" disabled={busy||recording} onClick={start}>Record</button><button className="stop-btn" disabled={busy||!recording} onClick={stop}><CircleStop size={14}/> End</button></div></Panel>
   <Panel><PanelTitle title="Event Markers"/><div className="marker-key"><span className="red">● Anomaly</span><span className="purple">● Diagnosis</span><span className="orange">● Risk Change</span><span className="blue">● Operator Action</span></div></Panel>
  </div>
  <div className="replay-main-grid">
   <Panel><PanelTitle title="Telemetry Timeline"/><div className="stacked-charts"><div><b>RPM<br/><small>(rpm)</small></b><MiniLineChart series={[{name:"RPM",values:trim(history.rpm??[]),color:"#1479f8"}]}/></div><div><b>Oil Pressure<br/><small>(kPa)</small></b><MiniLineChart series={[{name:"Oil Pressure",values:trim(history.oil_pressure??[]).map(v=>v*100),color:"#ff3a36"}]}/></div><div><b>Oil Temp<br/><small>(°C)</small></b><MiniLineChart series={[{name:"Oil Temp",values:trim(history.oil_temperature??[]),color:"#ff7a00"}]}/></div><div><b>Vibration<br/><small>(g)</small></b><MiniLineChart series={[{name:"Vibration",values:trim(history.vibration??[]),color:"#8a38eb"}]}/></div></div></Panel>
   <Panel><PanelTitle title="Event Details"/><div className="event-details">{markerEvents.map((e,i)=><div key={i}><i className={String(e.severity??["red","orange","purple","blue","green","gray"][i])}/><div><time>{String(e.timestamp??"").slice(-8)||`0${i+1}:12:16`}</time><b>{String(e.type??e.message??"Event")}</b><p>{String(e.message??(i===0?"Oil pressure moved below the expected trend envelope.":i===1?"AI model detected an abnormal lubrication pattern.":i===2?"Correlated residuals support the current diagnosis.":i===3?"Mission risk increased after persistent degradation.":i===4?"A lower-stress operating action was applied.":"Observed condition returned toward the expected envelope."))}</p></div></div>)}</div></Panel>
  </div>
 </div>
}
