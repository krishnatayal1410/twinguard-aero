import test from 'node:test';
import assert from 'node:assert/strict';
import { build } from 'esbuild';
import { mkdtemp, rm } from 'node:fs/promises';
import { tmpdir } from 'node:os';
import { join } from 'node:path';
import { pathToFileURL } from 'node:url';
const dir=await mkdtemp(join(tmpdir(),'twin-connection-'));
globalThis.window={location:{hostname:'twinguard-aero.vercel.app',origin:'https://twinguard-aero.vercel.app'}};
await test('explicit cloud backend overrides hostname demo and websocket uses same backend',async()=>{
 for(const [mode,origin,expected] of [['','',true],['0','',false],['','https://api.example.com',false],['1','https://api.example.com',true]]){
  const file=join(dir,`config-${Math.random()}.mjs`);
  await build({entryPoints:['src/services/runtimeConfig.ts'],outfile:file,bundle:true,format:'esm',platform:'node',define:{'import.meta.env.VITE_TWINGUARD_DEMO_MODE':JSON.stringify(mode),'import.meta.env.VITE_TWINGUARD_API_ORIGIN':JSON.stringify(origin)}});
  const config=await import(pathToFileURL(file));
  assert.equal(config.isDemo(),expected);
  const url=new URL(config.twinSocketUrl('token+with/slashes'));
  assert.equal(url.host,origin?'api.example.com':'twinguard-aero.vercel.app');
  assert.equal(url.protocol,'wss:');assert.equal(url.searchParams.get('token'),'token+with/slashes');
 }
});
await rm(dir,{recursive:true,force:true});
