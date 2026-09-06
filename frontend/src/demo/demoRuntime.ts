import type{FaultName,MissionResult,MissionType,ReplayMission,ReplaySample,SystemStatus,TwinEvent,TwinState}from"../types/twin";

let scenario:FaultName="lubrication";
let severity=.58;
let tick=16;
let latest:TwinState|undefined;
let recording=false;
let activeReplayId:number|undefined;
let replaySeq=2;
const missions:ReplayMission[]=[];
const replaySamples=new Map<number,ReplaySample[]>();

export const isHostedDemo=()=>typeof window!=="undefined"&&(import.meta.env.VITE_TWINGUARD_DEMO_MODE==="1"||window.location.hostname.endsWith(".vercel.app"));
const clamp=(v:number,a=0,b=100)=>Math.max(a,Math.min(b,v));
const human=(s:string)=>s.replace(/_/g," ").replace(/\b\w/g,c=>c.toUpperCase());

export function setDemoFault(fault:FaultName,target:number){scenario=fault;severity=Math.max(0,Math.min(1,target));tick=0}
export function resetDemoFault(){scenario="normal";severity=0;tick=0}
export function rememberDemoTwin(t:TwinState){latest=t}

function evidenceFor(fault:FaultName,f:number){
 const map:Record<FaultName,Array<{feature:string;weight:number;value:number}>>={
  normal:[{feature:"residual_stability",weight:.62,value:.04}],
  lubrication:[{feature:"oil_pressure_residual",weight:.38,value:-1.12*f},{feature:"oil_temperature_residual",weight:.24,value:11*f},{feature:"vibration_residual",weight:.18,value:.11*f},{feature:"persistence",weight:.20,value:28*f}],
  overheating:[{feature:"cht_residual",weight:.40,value:44*f},{feature:"oil_temperature_residual",weight:.22,value:12*f},{feature:"egt_residual",weight:.20,value:22*f},{feature:"persistence",weight:.18,value:25*f}],
  cooling_degradation:[{feature:"cht_residual",weight:.42,value:38*f},{feature:"cht_rate",weight:.24,value:6.2*f},{feature:"oil_temperature_residual",weight:.20,value:9*f},{feature:"persistence",weight:.14,value:24*f}],
  vibration:[{feature:"vibration_residual",weight:.58,value:.34*f},{feature:"vibration_rate",weight:.24,value:.05*f},{feature:"mechanical_health",weight:.18,value:-24*f}],
  sensor_drift:[{feature:"cht_isolated_disagreement",weight:.52,value:58*f},{feature:"cross_sensor_consistency",weight:.30,value:-.72*f},{feature:"cht_sensor_trust",weight:.18,value:38}],
  injector:[{feature:"egt_residual",weight:.34,value:31*f},{feature:"fuel_flow_residual",weight:.30,value:4.6*f},{feature:"rpm_instability",weight:.20,value:88*f},{feature:"combustion_health",weight:.16,value:-20*f}],
  misfire:[{feature:"rpm_instability",weight:.32,value:130*f},{feature:"vibration_residual",weight:.32,value:.20*f},{feature:"egt_imbalance_proxy",weight:.22,value:-24*f},{feature:"persistence",weight:.14,value:20*f}],
  combustion_instability:[{feature:"egt_residual",weight:.30,value:28*f},{feature:"cht_residual",weight:.24,value:17*f},{feature:"vibration_residual",weight:.24,value:.14*f},{feature:"fuel_flow_residual",weight:.22,value:3.8*f}],
  alternator_degradation:[{feature:"alternator_voltage_residual",weight:.44,value:-5.6*f},{feature:"battery_voltage_residual",weight:.34,value:-3.7*f},{feature:"electrical_health",weight:.22,value:-34*f}]
 };
 return map[fault];
}

function demoEvents(timestamp:string,anomaly:boolean,progress:number,fault:FaultName):TwinEvent[]{
 const base: TwinEvent[]=[{timestamp:new Date(Date.parse(timestamp)-60000).toISOString(),type:"TWIN_SYNCHRONIZED",severity:"success",message:"Hosted synthetic Digital Twin synchronized."}];
 if(!anomaly)return base;
 base.push({timestamp:new Date(Date.parse(timestamp)-30000).toISOString(),type:"ANOMALY_DETECTED",severity:"warning",message:"Persistent residual evidence crossed the anomaly threshold."});
 base.push({timestamp:new Date(Date.parse(timestamp)-18000).toISOString(),type:"FAULT_IDENTIFIED",severity:"warning",message:`Probable fault changed to ${fault}.`});
 if(progress>.7)base.push({timestamp:new Date(Date.parse(timestamp)-5000).toISOString(),type:"HEALTH_CAUTION",severity:"critical",message:"Subsystem degradation requires mission-level review."});
 return base;
}

function toReplaySample(t:TwinState):ReplaySample{return{timestamp:t.timestamp,health:t.health.overall,rul:t.ai.rul_hours,cht:t.telemetry.cht,oil_pressure:t.telemetry.oil_pressure,vibration:t.telemetry.vibration,anomaly:t.ai.anomaly,fault:t.ai.probable_fault,maintenance:t.maintenance.priority}}

export function buildDemoTwin():TwinState{
 tick+=1;
 const phase=tick/5,progress=scenario==="normal"?0:Math.min(1,tick/34)*severity;
 const wave=Math.sin(phase*.75),tiny=Math.sin(phase*2.1);
 let rpm=2450+wave*16,throttle=68+Math.sin(phase*.22)*2,cht=182+wave*1.4,egt=645+tiny*2.5,oilP=3.28+wave*.025,oilT=93+wave*.5,fuel=32.1+wave*.25,vib=.22+Math.abs(tiny)*.012,batt=28.1,altV=28.3;
 if(scenario==="lubrication"){oilP-=1.18*progress;oilT+=12*progress;vib+=.12*progress}
 if(scenario==="overheating"){cht+=47*progress;egt+=24*progress;oilT+=13*progress}
 if(scenario==="cooling_degradation"){cht+=40*progress;oilT+=10*progress;egt+=13*progress}
 if(scenario==="vibration")vib+=.38*progress;
 if(scenario==="sensor_drift")cht+=62*progress;
 if(scenario==="injector"){egt+=34*progress;fuel+=4.8*progress;rpm+=Math.sin(phase*4)*80*progress}
 if(scenario==="misfire"){rpm-=110*progress+Math.abs(Math.sin(phase*5))*70*progress;vib+=.22*progress;egt-=22*progress}
 if(scenario==="combustion_instability"){egt+=29*progress;cht+=18*progress;fuel+=3.4*progress;vib+=.15*progress}
 if(scenario==="alternator_degradation"){altV-=6.2*progress;batt-=4.1*progress}
 const injectionTiming=22.5;
 const expected={cht:182,egt:645,oil_pressure:3.28,oil_temperature:93,fuel_flow:32.1,vibration:.22,battery_voltage:28.1,alternator_voltage:28.3,injection_timing:22.5};
 const residuals={cht_residual:cht-expected.cht,egt_residual:egt-expected.egt,oil_pressure_residual:oilP-expected.oil_pressure,oil_temperature_residual:oilT-expected.oil_temperature,fuel_flow_residual:fuel-expected.fuel_flow,vibration_residual:vib-expected.vibration,battery_voltage_residual:batt-expected.battery_voltage,alternator_voltage_residual:altV-expected.alternator_voltage,injection_timing_residual:injectionTiming-expected.injection_timing};
 const thermal=clamp(96-progress*(scenario==="overheating"||scenario==="cooling_degradation"?40:scenario==="combustion_instability"?18:5));
 const lubrication=clamp(96-progress*(scenario==="lubrication"?48:6));
 const mechanical=clamp(96-progress*(scenario==="vibration"||scenario==="misfire"?38:scenario==="lubrication"?16:6));
 const combustion=clamp(96-progress*(["injector","misfire","combustion_instability"].includes(scenario)?40:7));
 const electrical=clamp(97-progress*(scenario==="alternator_degradation"?55:3));
 const sensor=clamp(98-progress*(scenario==="sensor_drift"?62:2));
 const overall=(thermal+lubrication+mechanical+combustion+electrical+sensor)/6;
 const anomaly=progress>.16,confidencePct=anomaly?clamp(64+progress*38):96,rul=Math.max(6,38-progress*24),timestamp=new Date().toISOString();
 const sensorTrust={rpm:97,cht:scenario==="sensor_drift"?clamp(96-progress*70):96,egt:96,oil_pressure:scenario==="lubrication"?94:97,oil_temperature:95,vibration:94,battery_voltage:96,alternator_voltage:scenario==="alternator_degradation"?91:97};
 const state:TwinState={
  engine_id:"ENGINE-01",timestamp,
  telemetry:{engine_id:"ENGINE-01",timestamp,rpm,throttle,cht,egt,oil_pressure:oilP,oil_temperature:oilT,fuel_flow:fuel,vibration:vib,battery_voltage:batt,alternator_voltage:altV,altitude:4250+wave*18,ambient_temperature:31,operating_hours:486.2,injection_timing:injectionTiming},
  expected,residuals,
  trends:{oil_pressure_per_min:scenario==="lubrication"?-.041*progress:0,oil_temperature_per_min:scenario==="lubrication"||scenario==="overheating"?1.8*progress:0,cht_per_min:(scenario==="overheating"||scenario==="cooling_degradation")?5.8*progress:.1,egt_per_min:["injector","combustion_instability"].includes(scenario)?3.2*progress:0,vibration_per_min:["vibration","misfire","combustion_instability"].includes(scenario)?.04*progress:0,battery_voltage_per_min:scenario==="alternator_degradation"?-.45*progress:0,alternator_voltage_per_min:scenario==="alternator_degradation"?-.72*progress:0,health_index_per_min:anomaly?-2.4*progress:0},
  events:demoEvents(timestamp,anomaly,progress,scenario),
  sensor_trust:sensorTrust,data_quality:{overall:98,status:"GOOD",source:"VERCEL_DEMO_SIMULATOR"},runtime_validity:{telemetry_age_seconds:.2,stale:false,freshness_limit_seconds:5,data_quality:98,minimum_data_quality:70,decision_eligible:true},
  health:{thermal,lubrication,mechanical,combustion,electrical,sensor,overall},
  ai:{anomaly,anomaly_score:anomaly?Math.min(1,.2+progress*.8):.04,probable_fault:anomaly?scenario:"normal",fault_confidence:confidencePct/100,fault_probabilities:{[scenario]:anomaly?confidencePct/100:.04,normal:anomaly?.08:.96},rul_hours:rul,rul_interval_hours:{lower:rul*.78,estimate:rul,upper:rul*1.18,basis:"synthetic engineering uncertainty band",calibrated_probability_interval:false},rul_uncertainty_hours:rul*.20,evidence:evidenceFor(anomaly?scenario:"normal",Math.max(.1,progress)),model_state:"ENGINEERING_FALLBACK",validation_scope:"SYNTHETIC_PROOF_OF_CONCEPT",rul_basis:"simulation-derived degradation surrogate",rul_interval_basis:"engineering uncertainty band",feature_contract:"aero-piston-v2",anomaly_persistence_samples:anomaly?Math.round(progress*42):0,model_warning:"Hosted demo uses deterministic synthetic telemetry. Real-engine calibration is not claimed."},
  confidence:{ai:confidencePct,sensor:Object.values(sensorTrust).reduce((a,b)=>a+b,0)/Object.values(sensorTrust).length,physics_agreement:anomaly?clamp(92-progress*12):97,data_quality:98,temporal_persistence:anomaly?clamp(progress*100):8,decision:anomaly?clamp(70+progress*26):94},
  maintenance:{priority:anomaly?(progress>.7?"HIGH":"MONITOR"):"ROUTINE",affected_subsystem:anomaly?human(scenario):"None",recommended_checks:anomaly?[`Review ${human(scenario)} evidence and trend persistence`,`Verify related sensor channels and operating context`,`Reassess next mission profile using Mission Lab`]:["Continue normal monitoring","Review scheduled maintenance interval"],reason:anomaly?`${human(scenario)} evidence is persistent and corroborated in the synthetic demonstrator.`:"No persistent abnormal residual pattern is present.",next_mission_suitability:anomaly?"REVIEW":"SUITABLE",validation_scope:"SYNTHETIC_PROOF_OF_CONCEPT"},
  readiness:{status:anomaly&&progress>.72?"CAUTION":"READY",label:anomaly&&progress>.72?"REVIEW":"READY",reason:anomaly?"Twin synchronized; degradation evidence requires mission-level review.":"Twin synchronized with nominal residual behavior."},
  twin_meta:{physics_model:"generic-aero-piston-surrogate-v2",telemetry_source:"HOSTED_SYNTHETIC_DEMO",validation_scope:"SYNTHETIC_PROOF_OF_CONCEPT",freshness_gate_seconds:5,mission_min_data_quality:70}
 };
 if(recording&&activeReplayId!==undefined){const arr=replaySamples.get(activeReplayId)??[];arr.push(toReplaySample(state));replaySamples.set(activeReplayId,arr.slice(-5000))}
 rememberDemoTwin(state);return state;
}

export function demoAnalyzeMission(payload:Record<string,unknown>):MissionResult{
 const twin=latest??buildDemoTwin(),type=(payload.mission_type??"endurance") as MissionType,duration=Math.max(.25,Number(payload.duration_hours??8)),altitude=Number(payload.cruise_altitude_m??5500),temp=Number(payload.ambient_temp_c??35),throttle=Number(payload.average_throttle_pct??75);
 const health=twin.health.overall,rul=twin.ai.rul_hours,lower=twin.ai.rul_interval_hours?.lower??rul*.8;
 const typeStress:Record<MissionType,number>={endurance:10,high_altitude:16,hot_weather:15,rapid_throttle:18,patrol:8};
 const stress=clamp(typeStress[type]+duration*2.2+Math.max(0,altitude-3500)/450+Math.max(0,temp-30)*.7+Math.max(0,throttle-60)*.55+(100-health)*.8,0,100);
 const feasibility=clamp(100-stress*.68-(100-health)*.32,4,98),risk=stress<34?"LOW":stress<62?"MEDIUM":"HIGH";
 const postHealth=clamp(health-duration*(stress/100)*1.6),postRul=Math.max(0,rul-duration*(.7+stress/75));
 const reserve=Math.max(0,lower*.14),margin=lower-duration-reserve,horizon=Math.max(0,lower-reserve-duration*.55);
 const alt={cruise_altitude_m:Math.max(2500,Math.round((altitude-900)/100)*100),duration_hours:Math.max(.5,Number((duration*.88).toFixed(2))),average_throttle_pct:Math.max(50,Math.round(throttle-12))};
 const altStress=clamp(stress-18,0,100),altRisk=altStress<34?"LOW":altStress<62?"MEDIUM":"HIGH";
 return{mission_type:type,profile_modifier_description:`${human(type)} duty-cycle modifier`,profile_modifiers:{duty_cycle:typeStress[type]/10},overall_risk:risk,decision:risk==="LOW"?"CONTINUE_WITH_MONITORING":risk==="MEDIUM"?"REVIEW_OR_REDUCE_LOAD":"REPLAN_OR_RETURN_FOR_REVIEW",stress_index:stress/100,thermal_risk:(type==="hot_weather"||type==="high_altitude")&&stress>45?"MEDIUM":risk==="HIGH"?"MEDIUM":"LOW",mechanical_risk:type==="rapid_throttle"&&stress>48?"MEDIUM":risk==="HIGH"?"MEDIUM":"LOW",lubrication_risk:twin.health.lubrication<75?"HIGH":twin.health.lubrication<88?"MEDIUM":"LOW",combustion_risk:twin.health.combustion<78?"HIGH":twin.health.combustion<90?"MEDIUM":"LOW",electrical_risk:twin.health.electrical<78?"HIGH":twin.health.electrical<90?"MEDIUM":"LOW",current_health:health,post_mission_health:postHealth,current_rul_hours:rul,current_rul_interval_hours:twin.ai.rul_interval_hours,post_mission_rul_hours:postRul,post_mission_rul_interval_hours:{lower:postRul*.78,estimate:postRul,upper:postRul*1.18,basis:"synthetic engineering uncertainty band",calibrated_probability_interval:false},rul_margin_ratio:rul/duration,conservative_rul_margin_ratio:lower/duration,projected_profile_endurance_hours:Math.max(0,lower-reserve),mission_margin_hours:margin,engineering_reserve_hours:reserve,decision_horizon_hours:horizon,decision_horizon_status:horizon<1?"IMMEDIATE_REVIEW":horizon<3?"REVIEW_SOON":"MARGIN_AVAILABLE",lower_stress_alternative:{...alt,projected_stress_index:altStress/100,projected_risk:altRisk,projected_profile_endurance_hours:Math.max(0,lower-reserve),mission_margin_hours:margin+duration*.24,decision_horizon_hours:horizon+duration*.22,engineering_reserve_hours:reserve},explanation:`Current ${human(type)} profile is evaluated against the synchronized synthetic Twin state. The alternative reduces throttle, altitude and exposure to demonstrate counterfactual decision support.`,mission_feasibility_index:feasibility,risk_factors:[`Current engine health index ${health.toFixed(0)}/100`,`Conservative RUL lower bound ${lower.toFixed(1)} h`,`Planned mission duration ${duration.toFixed(1)} h`,`Average throttle ${throttle.toFixed(0)}%`,`Duty-cycle profile: ${human(type)}`],validation_scope:"SYNTHETIC_PROOF_OF_CONCEPT"};
}

function summarize(samples:ReplaySample[]){
 if(!samples.length)return{sample_count:0,duration_seconds:0,events:[]};
 const first=samples[0],last=samples[samples.length-1];
 return{sample_count:samples.length,duration_seconds:Math.max(0,(Date.parse(last.timestamp)-Date.parse(first.timestamp))/1000),start_health:first.health,end_health:last.health,rul_change_hours:last.rul-first.rul,max_cht:Math.max(...samples.map(x=>x.cht)),min_oil_pressure:Math.min(...samples.map(x=>x.oil_pressure)),max_vibration:Math.max(...samples.map(x=>x.vibration)),anomaly_samples:samples.filter(x=>x.anomaly).length,faults_observed:[...new Set(samples.filter(x=>x.fault!=="normal").map(x=>x.fault))],events:(latest?.events??[])}
}

function seedReplaySamples(id:number){
 if(replaySamples.has(id))return;
 const base=latest??buildDemoTwin(),start=Date.now()-53*60000,samples:ReplaySample[]=[];
 for(let i=0;i<120;i++){
  const p=i/119,w=Math.sin(i/8),degrade=Math.max(0,(p-.38)/.62);
  samples.push({timestamp:new Date(start+i*26_000).toISOString(),health:96-degrade*18,rul:38-degrade*10,cht:182+w*1.4+degrade*16,oil_pressure:3.28+w*.02-degrade*.78,vibration:.22+Math.abs(w)*.01+degrade*.1,anomaly:degrade>.22,fault:degrade>.22?"lubrication":"normal",maintenance:degrade>.68?"HIGH":"MONITOR"});
 }
 replaySamples.set(id,samples);
}

export async function demoStartReplay(label?:string){
 recording=true;const id=replaySeq++,m:ReplayMission={id,engine_id:"ENGINE-01",label:label??"Hosted Demo Mission",status:"RECORDING",started_at:new Date().toISOString()};activeReplayId=id;replaySamples.set(id,[]);missions.unshift(m);return m
}
export async function demoEndReplay(){
 const m=missions.find(x=>x.id===activeReplayId)??missions[0]??await demoStartReplay("Hosted Demo Mission");recording=false;activeReplayId=undefined;const samples=replaySamples.get(m.id)??[];const done:ReplayMission={...m,status:"COMPLETED",ended_at:new Date().toISOString(),summary:summarize(samples)};const index=missions.findIndex(x=>x.id===m.id);if(index>=0)missions[index]=done;return done
}
export async function demoListReplay(){
 if(!missions.length){const id=1;seedReplaySamples(id);const sample:ReplayMission={id,engine_id:"ENGINE-01",label:"Endurance Patrol · Demo",status:"COMPLETED",started_at:new Date(Date.now()-53*60000).toISOString(),ended_at:new Date().toISOString(),summary:summarize(replaySamples.get(id)??[])};missions.push(sample)}return [...missions]
}
export async function demoGetReplay(id:number){const all=await demoListReplay();return all.find(x=>x.id===id)??all[0]}
export async function demoGetReplaySamples(id:number){await demoListReplay();seedReplaySamples(id);return[...(replaySamples.get(id)??[])]}

export function demoSystemStatus():SystemStatus{return{service:"TwinGuard Aero Hosted Demo",version:"3.2.0",environment:"vercel-demo",engine_id:"ENGINE-01",database:"Hosted demo memory",models:{anomaly:false,fault:false,rul:false},integrations:{mqtt:false,unreal_udp:false,can:false},telemetry:{available:true,age_seconds:.2,stale:false,freshness_limit_seconds:5,data_quality:98,minimum_data_quality:70,decision_eligible:true},security:{cors_origins:[location.origin],trusted_hosts:[location.hostname],ingest_key_required:false,authentication:false}}}
