import axios from"axios";import type{FaultName,MissionResult,ReplayMission,SystemStatus,TwinState}from"../types/twin";import{storedToken}from"./authApi";
export const http=axios.create({baseURL:"/api/v1",timeout:5000,headers:{"X-Requested-With":"TwinGuard-Aero"}});http.interceptors.request.use(c=>{const t=storedToken();if(t)c.headers.Authorization=`Bearer ${t}`;return c});
export const getTwin=async()=>(await http.get<TwinState>("/twin/ENGINE-01")).data;
export const setFault=async(fault:FaultName,severity:number)=>(await http.post("/simulation/fault",{fault,severity})).data;
export const resetFault=async()=>(await http.post("/simulation/reset")).data;
export const analyzeMission=async(payload:Record<string,unknown>)=>(await http.post<MissionResult>("/mission/analyze",payload)).data;
export const startReplay=async(label?:string)=>(await http.post<ReplayMission>("/replay/start",{label})).data;
export const endReplay=async()=>(await http.post<ReplayMission>("/replay/end")).data;
export const listReplay=async()=>(await http.get<ReplayMission[]>("/replay/missions")).data;
export const getReplay=async(id:number)=>(await http.get<ReplayMission>(`/replay/missions/${id}`)).data;
export const getSystemStatus=async()=>(await http.get<SystemStatus>("/system/status")).data;
export function connectTwin(onState:(s:TwinState)=>void,onStatus:(online:boolean)=>void){const proto=location.protocol==="https:"?"wss":"ws",host=location.port==="5173"?`${location.hostname}:8000`:location.host;let ws:WebSocket|undefined,stopped=false,retry=900;const open=()=>{const token=storedToken();if(!token){onStatus(false);return}ws=new WebSocket(`${proto}://${host}/api/v1/ws/twin/ENGINE-01?token=${encodeURIComponent(token)}`);ws.onopen=()=>{retry=900;onStatus(true)};ws.onmessage=e=>{try{const x=JSON.parse(e.data);if(x?.telemetry)onState(x)}catch{}};ws.onclose=()=>{onStatus(false);if(!stopped){setTimeout(open,retry);retry=Math.min(6000,retry*1.5)}};ws.onerror=()=>ws?.close()};open();return()=>{stopped=true;ws?.close()}}
