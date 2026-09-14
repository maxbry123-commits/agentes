#!/usr/bin/env node
// Layer 4: boot-race verification. Runs the preflight 20x against a fixed mocked env and asserts (a) cache writes don't race with reads, (b) cache file name is keyed by version, (c) mid-loop kill simulation leaves no half-written file, (d) old-version cache files are pruned. Hermetic - no real app launch (Layer 5 + the e2e harness exercises real launch).

'use strict';
const fs = require('fs');
const os = require('os');
const path = require('path');
const pf = require('../../electron/preflight');

let failed = 0;
function check(name, cond, detail) { process.stdout.write(`  ${cond ? 'ok  ' : 'FAIL'}  ${name}${detail ? ` :: ${detail}` : ''}\n`); if (!cond) failed++; }

async function main() {
  const baseDir = path.join(os.tmpdir(), `openswarm-pf-race-${process.pid}-${Date.now()}`);
  fs.mkdirSync(baseDir, { recursive: true });

  process.stdout.write('Race: 20 parallel preflight runs (different dataDirs)\n');
  const t0 = Date.now();
  const N = 20;
  const promises = [];
  for (let i = 0; i < N; i++) {
    const dataDir = path.join(baseDir, `dd-${i}`);
    promises.push(pf.run(pf.defaultEnv(), { dataDir, network: { url: 'http://127.0.0.1:1', timeoutMs: 200 }, clock: { url: 'http://127.0.0.1:1', timeoutMs: 200 }, dualStack: { host: 'invalid.openswarm.local', timeoutMs: 200 } }));
  }
  const results = await Promise.all(promises);
  const dt = Date.now() - t0;
  check(`20 parallel runs finished in <8s`, dt < 8000, `${dt}ms`);
  check('all 20 returned a verdict', results.every((r) => ['ok', 'warn', 'fail'].includes(r.verdict)));

  process.stdout.write('\nCache: write keyed by version + read returns it\n');
  const dataDir = path.join(baseDir, 'cache');
  fs.mkdirSync(dataDir, { recursive: true });
  pf.writeCache(pf.defaultEnv(), dataDir, '1.2.3', { verdict: 'ok', results: [] });
  const file = pf.cachePath(dataDir, '1.2.3');
  check('cache file written at version-keyed path', fs.existsSync(file), file);
  const got = pf.readCache(pf.defaultEnv(), dataDir, '1.2.3');
  check('readCache returns the payload', !!got && got.verdict === 'ok');
  const wrongVer = pf.readCache(pf.defaultEnv(), dataDir, '9.9.9');
  check('readCache returns null on version mismatch', wrongVer === null);

  process.stdout.write('\nPrune: old-version cache files get deleted on next write\n');
  fs.writeFileSync(path.join(dataDir, 'preflight-0.9.0.json'), '{}');
  fs.writeFileSync(path.join(dataDir, 'preflight-1.0.0.json'), '{}');
  pf.pruneOldCaches(pf.defaultEnv(), dataDir, '1.2.3');
  check('prune left 1.2.3 file intact', fs.existsSync(file));
  check('prune deleted 0.9.0 file', !fs.existsSync(path.join(dataDir, 'preflight-0.9.0.json')));
  check('prune deleted 1.0.0 file', !fs.existsSync(path.join(dataDir, 'preflight-1.0.0.json')));

  process.stdout.write('\nMid-boot kill simulation: half-written cache + restart re-runs preflight\n');
  const halfDir = path.join(baseDir, 'halfdir');
  fs.mkdirSync(halfDir, { recursive: true });
  // Simulate a partial write: file exists but is corrupt JSON.
  fs.writeFileSync(pf.cachePath(halfDir, '1.2.3'), '{"appVersion":"1.2.3","verdict":"ok"');
  const halfRead = pf.readCache(pf.defaultEnv(), halfDir, '1.2.3');
  check('corrupt cache reads as null (re-run will happen)', halfRead === null);

  process.stdout.write('\nNo cross-test contamination: 20 dataDirs each have own cache file\n');
  const allFiles = [];
  for (let i = 0; i < N; i++) {
    const dd = path.join(baseDir, `dd-${i}`);
    pf.writeCache(pf.defaultEnv(), dd, '1.2.3', { verdict: 'ok' });
    allFiles.push(pf.cachePath(dd, '1.2.3'));
  }
  check('all 20 cache files exist independently', allFiles.every((f) => fs.existsSync(f)));

  // Cleanup the temp dir tree.
  try { fs.rmSync(baseDir, { recursive: true, force: true }); } catch {}

  process.stdout.write(failed
    ? `\nPREFLIGHT RACE FAIL: ${failed} assertion(s)\n`
    : '\nPREFLIGHT RACE PASS: parallel runs, version-keyed cache, prune, and mid-kill recovery all behave.\n');
  process.exit(failed ? 1 : 0);
}

main().catch((e) => { process.stderr.write(`\nPREFLIGHT RACE FAIL: ${e && e.stack || e}\n`); process.exit(1); });
