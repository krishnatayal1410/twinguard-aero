import test from 'node:test';
import assert from 'node:assert/strict';
import { build } from 'esbuild';
import { mkdtemp, rm } from 'node:fs/promises';
import { tmpdir } from 'node:os';
import { join } from 'node:path';
import { pathToFileURL } from 'node:url';

const dir = await mkdtemp(join(tmpdir(), 'twinguard-auth-'));
const file = join(dir, 'auth.mjs');
await build({
  entryPoints: ['src/services/authApi.ts'], outfile: file, bundle: true,
  format: 'esm', platform: 'browser',
  define: {'import.meta.env.VITE_TWINGUARD_DEMO_MODE': '"1"', 'import.meta.env.VITE_TWINGUARD_API_ORIGIN': '""'},
});
const values = new Map();
globalThis.localStorage = {
  getItem: key => values.get(key) ?? null,
  setItem: (key, value) => values.set(key, value),
  removeItem: key => values.delete(key),
};
globalThis.window = {location: {hostname: 'localhost', origin: 'http://localhost'}};
const auth = await import(pathToFileURL(file));
const accountsKey = 'twinguard_demo_accounts';

await test('local account round trip normalizes identity and stores only salted password derivatives', async () => {
  values.clear();
  const created = await auth.signUp(' Demo Operator ', ' DEMO.Operator@example.com ', 'TwinGuard2026');
  assert.equal(created.user.name, 'Demo Operator');
  assert.equal(created.user.email, 'demo.operator@example.com');
  assert.equal(created.user.role, 'demo_operator');
  const [saved] = JSON.parse(values.get(accountsKey));
  assert.match(saved.passwordSalt, /^[0-9a-f]{32}$/);
  assert.match(saved.passwordHash, /^[0-9a-f]{64}$/);
  assert.ok(!values.get(accountsKey).includes('TwinGuard2026'));
  assert.deepEqual(await auth.currentUser(created.token), created.user);
  assert.deepEqual((await auth.signIn('DEMO.OPERATOR@example.com', 'TwinGuard2026')).user, created.user);
  await assert.rejects(auth.signIn(created.user.email, 'WrongPassword1'), /incorrect/);
  await assert.rejects(auth.signUp('Duplicate', 'DEMO.OPERATOR@example.com', 'TwinGuard2026'), /already exists/);
  await assert.rejects(auth.currentUser('demo:1234:other@example.com'), /not found/);
});

await test('malformed persisted session and account data cannot crash application startup or signup', async () => {
  for (const stored of ['null', '{}', '[null]', '{"token":7}', '{"token":"stale","user":{"name":7}}', '{']) {
    values.set(auth.AUTH_KEY, stored);
    assert.equal(auth.readStoredSession(), null);
    assert.equal(auth.storedToken(), undefined);
  }
  for (const stored of ['null', '{}', '[null,{"id":1}]', '{']) {
    values.set(accountsKey, stored);
    const created = await auth.signUp('Recovery Operator', 'recovery@example.com', 'TwinGuard2026');
    assert.equal((await auth.currentUser(created.token)).name, 'Recovery Operator');
  }
});

await test('demo signup enforces the backend identity and password requirements', async () => {
  for (const [name, email, password] of [
    ['  ', 'valid@example.com', 'TwinGuard2026'],
    ['Operator', 'invalid-email', 'TwinGuard2026'],
    ['Operator', 'valid@example.com', 'short'],
    ['Operator', 'valid@example.com', 'alllowercase1'],
    ['Operator', 'valid@example.com', 'ALLUPPERCASE1'],
    ['Operator', 'valid@example.com', 'MissingNumbers'],
    ['Operator', 'valid@example.com', 'A1' + 'a'.repeat(127)],
  ]) await assert.rejects(auth.signUp(name, email, password));
});

await test('simultaneous account creation preserves both identities', async () => {
  values.clear();
  const [first, second] = await Promise.all([
    auth.signUp('First Operator', 'first@example.com', 'TwinGuard2026'),
    auth.signUp('Second Operator', 'second@example.com', 'TwinGuard2026'),
  ]);
  assert.notEqual(first.user.id, second.user.id);
  assert.equal(JSON.parse(values.get(accountsKey)).length, 2);
  assert.deepEqual(await auth.currentUser(first.token), first.user);
  assert.deepEqual(await auth.currentUser(second.token), second.user);
});

await test('blocked browser storage reports an actionable local profile error', async () => {
  const original = localStorage.setItem;
  localStorage.setItem = () => { throw new Error('QuotaExceededError'); };
  try {
    await assert.rejects(auth.signUp('Storage Operator', 'storage@example.com', 'TwinGuard2026'), /browser storage/);
  } finally {
    localStorage.setItem = original;
  }
});

await rm(dir, {recursive: true, force: true});
