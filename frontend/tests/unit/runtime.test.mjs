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
await rm(dir,{recursive:true,force:true});
