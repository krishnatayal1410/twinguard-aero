import axios from"axios";
import type{FaultName,MissionResult,ReplayMission,RuntimeValidity,SystemStatus,TwinState}from"../types/twin";
import{storedToken}from"./authApi";
import{buildDemoTwin,demoAnalyzeMission,demoEndReplay,demoGetReplay,demoListReplay,demoStartReplay,demoSystemStatus,isHostedDemo,resetDemoFault,setDemoFault}from"../demo/demoRuntime";

export const http=axios.create({baseURL:"/api/v1",timeout:5000,headers:{"X-Requested-With":"TwinGuard-Aero"}});
http.interceptors.request.use(c=>{const t=storedToken();if(t)c.headers.Authorization=`Bearer ${t}`;return c});

export const getTwin=async()=>isHostedDemo()?buildDemoTwin():(await http.get<TwinState>("/twin/ENGINE-01")).data;
export const setFault=async(fault:FaultName,severity:number)=>{if(isHostedDemo()){setDemoFault(fault,severity);return{ok:true,mode:"hosted-demo"}}return(await http.post("/simulation/fault",{fault,severity})).data};
export const resetFault=async()=>{if(isHostedDemo()){resetDemoFault();return{ok:true,mode:"hosted-demo"}}return(await http.post("/simulation/reset")).data};
export const analyzeMission=async(payload:Record<string,unknown>)=>isHostedDemo()?demoAnalyzeMission(payload):(await http.post<MissionResult>("/mission/analyze",payload)).data;
export const startReplay=async(label?:string)=>isHostedDemo()?demoStartReplay(label):(await http.post<ReplayMission>("/replay/start",{label})).data;
export const endReplay=async()=>isHostedDemo()?demoEndReplay():(await http.post<ReplayMission>("/replay/end")).data;
export const listReplay=async()=>isHostedDemo()?demoListReplay():(await http.get<ReplayMission[]>("/replay/missions")).data;
export const getReplay=async(id:number)=>isHostedDemo()?demoGetReplay(id):(await http.get<ReplayMission>(`/replay/missions/${id}`)).data;
export const getSystemStatus=async()=>isHostedDemo()?demoSystemStatus():(await http.get<SystemStatus>("/system/status")).data;

export function connectTwin(onState:(s:TwinState)=>void,onStatus:(online:boolean)=>void,onValidity?:(v:RuntimeValidity)=>void){
 if(isHostedDemo()){
  let stopped=false;const emit=()=>{if(stopped)return;const x=buildDemoTwin();onState(x);onStatus(true);if(x.runtime_validity)onValidity?.(x.runtime_validity)};emit();const id=window.setInterval(emit,900);return()=>{stopped=true;window.clearInterval(id)};
 }
 const proto=location.protocol==="https:"?"wss":"ws",host=location.port==="5173"?`${location.hostname}:8000`:location.host;
 let ws:WebSocket|undefined,stopped=false,retry=900;
 const open=()=>{const token=storedToken();if(!token){onStatus(false);return}ws=new WebSocket(`${proto}://${host}/api/v1/ws/twin/ENGINE-01?token=${encodeURIComponent(token)}`);ws.onopen=()=>{retry=900;onStatus(true)};ws.onmessage=e=>{try{const x=JSON.parse(e.data);if(x?.telemetry){onState(x);if(x.runtime_validity)onValidity?.(x.runtime_validity)}else if(x?.runtime_validity)onValidity?.(x.runtime_validity)}catch{}};ws.onclose=()=>{onStatus(false);if(!stopped){setTimeout(open,retry);retry=Math.min(6000,retry*1.5)}};ws.onerror=()=>ws?.close()};
 open();return()=>{stopped=true;ws?.close()};
}
