import test from 'node:test';
import assert from 'node:assert/strict';
import { build } from 'esbuild';
import { mkdtemp, rm } from 'node:fs/promises';
import { tmpdir } from 'node:os';
import { join } from 'node:path';
import { pathToFileURL } from 'node:url';
const dir = await mkdtemp(join(tmpdir(), 'twinguard-test-'));
const file = join(dir, 'runtime.mjs');
await build({entryPoints:['src/demo/demoRuntime.ts'],outfile:file,bundle:true,format:'esm',platform:'node',define:{'import.meta.env.VITE_TWINGUARD_DEMO_MODE':'"1"','import.meta.env.VITE_TWINGUARD_API_ORIGIN':'""'}});
const values = new Map();
globalThis.localStorage = {getItem:k=>values.get(k)??null,setItem:(k,v)=>values.set(k,v),removeItem:k=>values.delete(k)};
globalThis.location = {hostname:'localhost',origin:'http://localhost'};
globalThis.window = {location};
let seq=0;
const fresh = () => import(pathToFileURL(file).href+'?instance='+seq++);
await test('completed recordings survive a fresh runtime without fabricated samples', async () => {
  const runtime = await fresh();
  const recording = await runtime.demoStartReplay('Regression mission');
  assert.equal((await runtime.demoStartReplay('duplicate')).id,recording.id);
  assert.equal((await runtime.demoGetReplaySamples(recording.id)).length,0);
  runtime.buildDemoTwin();runtime.buildDemoTwin();
  const ended = await runtime.demoEndReplay();
  assert.equal(ended.status,'COMPLETED');
  const rows=await runtime.demoGetReplaySamples(recording.id);
  for(const event of ended.summary.events) assert.ok(Date.parse(event.timestamp)>=Date.parse(rows[0].timestamp)&&Date.parse(event.timestamp)<=Date.parse(rows.at(-1).timestamp));
  const reloaded = await fresh();
  assert.equal((await reloaded.demoGetReplay(recording.id)).label,'Regression mission');
  assert.equal((await reloaded.demoGetReplaySamples(recording.id)).length,2);
  await assert.rejects(reloaded.demoGetReplay(-1), /not found/);
  await assert.rejects(reloaded.demoEndReplay(), /No active recording/);
});
await test('fault configuration is shared between workspaces and anomaly requires review',async()=>{
 const a=await fresh(),b=await fresh();
 a.setDemoFault('lubrication',1);
 const config=JSON.parse(values.get('twinguard-demo-scenario-v1'));config.startedAt-=45000;
 values.set('twinguard-demo-scenario-v1',JSON.stringify(config));
 const state=b.buildDemoTwin();assert.equal(state.ai.probable_fault,'lubrication');assert.equal(state.readiness.label,'REVIEW');
 a.resetDemoFault();assert.equal(b.buildDemoTwin().readiness.label,'READY');
});
await test('mission values are validated before synthetic analysis',async()=>{
 const runtime=await fresh();const input={mission_type:'endurance',duration_hours:8,cruise_altitude_m:6000,ambient_temp_c:-5,average_throttle_pct:70};
 assert.ok(Number.isFinite(runtime.demoAnalyzeMission(input).mission_feasibility_index));
 for(const [key,value] of [['duration_hours',0],['duration_hours',Infinity],['cruise_altitude_m',-1],['ambient_temp_c',NaN],['average_throttle_pct',101],['mission_type','unknown']])
 assert.throws(()=>runtime.demoAnalyzeMission({...input,[key]:value}));
});
await test('alternative mission projections agree with reruns and never increase low inputs',async()=>{
 const runtime=await fresh();runtime.resetDemoFault();runtime.buildDemoTwin();
 for(const input of [
  {mission_type:'patrol',duration_hours:0.25,cruise_altitude_m:0,ambient_temp_c:20,average_throttle_pct:10},
  {mission_type:'endurance',duration_hours:8,cruise_altitude_m:5500,ambient_temp_c:35,average_throttle_pct:75},
  {mission_type:'high_altitude',duration_hours:48,cruise_altitude_m:12000,ambient_temp_c:70,average_throttle_pct:100},
 ]){
  const result=runtime.demoAnalyzeMission(input),alt=result.lower_stress_alternative;
  for(const key of ['duration_hours','cruise_altitude_m','average_throttle_pct']) assert.ok(alt[key]<=input[key],key);
  const rerun=runtime.demoAnalyzeMission({...input,...alt});
  assert.equal(alt.projected_stress_index,rerun.stress_index);
  assert.equal(alt.projected_risk,rerun.overall_risk);
  assert.equal(alt.mission_margin_hours,rerun.mission_margin_hours);
  assert.equal(alt.decision_horizon_hours,rerun.decision_horizon_hours);
  assert.ok(alt.projected_stress_index<=result.stress_index);
  assert.ok(alt.mission_margin_hours>=result.mission_margin_hours);
 }
});
await test('exhausted conservative mission reserve requires replan despite low load',async()=>{
 const runtime=await fresh();runtime.resetDemoFault();const twin=runtime.buildDemoTwin();
 twin.ai.rul_hours=1;twin.ai.rul_interval_hours.lower=0.78;runtime.rememberDemoTwin(twin);
 const result=runtime.demoAnalyzeMission({mission_type:'patrol',duration_hours:1,cruise_altitude_m:0,ambient_temp_c:20,average_throttle_pct:10});
 assert.ok(result.mission_margin_hours<0);assert.equal(result.overall_risk,'HIGH');
 assert.equal(result.decision,'REPLAN_OR_RETURN_FOR_REVIEW');assert.equal(result.decision_horizon_hours,0);
});
await test('all demo scenarios provide finite normalized and explicitly uncalibrated scores',async()=>{
 const runtime=await fresh();
 for(const fault of ['normal','lubrication','overheating','cooling_degradation','vibration','sensor_drift','injector','misfire','combustion_instability','alternator_degradation']){
  runtime.setDemoFault(fault,1);
  const config=JSON.parse(values.get('twinguard-demo-scenario-v1'));config.startedAt-=45000;
  values.set('twinguard-demo-scenario-v1',JSON.stringify(config));
  const twin=runtime.buildDemoTwin(),scores=Object.values(twin.ai.fault_probabilities);
  assert.ok(scores.every(x=>Number.isFinite(x)&&x>=0&&x<=1));
  assert.ok(Math.abs(scores.reduce((a,b)=>a+b,0)-1)<1e-9);
  assert.equal(twin.ai.fault_probability_basis,'scenario_conditioned_demo_scores_uncalibrated');
  assert.match(twin.ai.model_warning,/not model inference/);
 }
 assert.throws(()=>runtime.setDemoFault('unknown',1));
 assert.throws(()=>runtime.setDemoFault('normal',NaN));
});
await test('scenario provenance getter reads shared configuration without creating samples or changing storage',async()=>{
 const runtime=await fresh();values.delete('twinguard-demo-scenario-v1');
 const initial=runtime.getDemoScenario();assert.ok(Number.isFinite(Date.parse(initial.started_at)));
 assert.equal(values.has('twinguard-demo-scenario-v1'),false);
 runtime.setDemoFault('sensor_drift',0.7);const saved=values.get('twinguard-demo-scenario-v1');
 const other=await fresh(),scenario=other.getDemoScenario();
 assert.equal(scenario.fault,'sensor_drift');assert.equal(scenario.severity,0.7);
 assert.equal(scenario.started_at,new Date(JSON.parse(saved).startedAt).toISOString());
 assert.equal(values.get('twinguard-demo-scenario-v1'),saved);
 scenario.fault='normal';assert.equal(other.getDemoScenario().fault,'sensor_drift');
 const mission=await other.demoStartReplay('Read-only provenance');other.getDemoScenario();
 assert.equal((await other.demoGetReplaySamples(mission.id)).length,0);await other.demoEndReplay();
});
await rm(dir,{recursive:true,force:true});
