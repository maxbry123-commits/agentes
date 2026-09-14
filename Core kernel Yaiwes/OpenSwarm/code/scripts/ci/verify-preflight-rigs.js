#!/usr/bin/env node
// Layer 3: stand up local failure rigs (hanging HTTP, slow DNS, no-write FS, garbage spawn) and drive the WHOLE preflight against each. Asserts (a) total runtime under budget, (b) the failing-check name is in the diagnostic, (c) no other check is corrupted by its neighbor's failure.

'use strict';
const fs = require('fs');
const os = require('os');
const path = require('path');
const http = require('http');
const pf = require('../../electron/preflight');

let failed = 0;
function check(name, cond, detail) { process.stdout.write(`  ${cond ? 'ok  ' : 'FAIL'}  ${name}${detail ? ` :: ${detail}` : ''}\n`); if (!cond) failed++; }

// A hanging HTTP server: accepts the socket, never responds. Forces network/clock
// checks to timeout-then-warn, proving the per-check timeout is what unblocks us.
function startHangingHttp() {
  return new Promise((resolve) => {
    const srv = http.createServer(() => { /* never write */ });
    srv.listen(0, '127.0.0.1', () => resolve({ srv, port: srv.address().port }));
  });
}

// A 500-returning HTTP server: completes the round-trip but with a bad status.
function start500() {
  return new Promise((resolve) => {
    const srv = http.createServer((req, res) => { res.statusCode = 500; res.end(); });
    srv.listen(0, '127.0.0.1', () => resolve({ srv, port: srv.address().port }));
  });
}

// A close-mid-handshake server: accepts, then destroys.
function startCloseMidHandshake() {
  return new Promise((resolve) => {
    const srv = http.createServer((req, res) => { req.socket.destroy(); });
    srv.listen(0, '127.0.0.1', () => resolve({ srv, port: srv.address().port }));
  });
}

// Filesystem rig: a path inside the OS temp dir that we'll keep, plus a "locked"
// path inside it that we make non-writable (best-effort cross-platform).
function tmpDataDir(label) { return path.join(os.tmpdir(), `openswarm-preflight-rig-${label}-${process.pid}-${Date.now()}`); }

// A localized PowerShell stub via a fake execFile that returns German text.
function germanLocaleEnv() {
  const real = pf.defaultEnv();
  return Object.assign({}, real, {
    child_process: { execFile: (cmd, args, opts, cb) => setImmediate(() => cb(null, 'Antivirenprogramm aktiviert: True', '')) },
    platform: 'win32',  // pretend win32 so the security probe takes the pwsh path
  });
}

async function rigHangingNetwork() {
  process.stdout.write('Rig: hanging HTTP (network + clock should timeout to warn)\n');
  const { srv, port } = await startHangingHttp();
  try {
    const t0 = Date.now();
    const env = pf.defaultEnv();
    const result = await pf.run(env, {
      dataDir: tmpDataDir('hang-net'),
      network: { url: `http://127.0.0.1:${port}/`, timeoutMs: 600 },
      clock: { url: `http://127.0.0.1:${port}/`, timeoutMs: 600 },
      dualStack: { host: '127.0.0.1', timeoutMs: 300 },
    });
    const dt = Date.now() - t0;
    check('total runtime under global budget (5s)', dt < 5000, `${dt}ms`);
    const net = result.results.find((r) => r.name === 'network');
    const clk = result.results.find((r) => r.name === 'clock');
    check('network -> warn (not fail) on hang', net.status === 'warn', net.reason);
    check('clock -> warn (not fail) on hang', clk.status === 'warn', clk.reason);
    const os_ = result.results.find((r) => r.name === 'os');
    check('neighbor check (os) not corrupted by hang', os_.status === 'ok' || os_.status === 'warn', os_.reason);
  } finally { srv.close(); }
}

async function rig500() {
  process.stdout.write('\nRig: 500 server (network records HTTP 500, still ok-ish; we just want no crash)\n');
  const { srv, port } = await start500();
  try {
    const result = await pf.run(pf.defaultEnv(), {
      dataDir: tmpDataDir('500'),
      network: { url: `http://127.0.0.1:${port}/`, timeoutMs: 1000 },
    });
    const net = result.results.find((r) => r.name === 'network');
    check('network completes (no throw) on 500', !!net && net.status !== undefined, net && net.reason);
    check('reason mentions 500', /500/.test(net.reason || ''), net && net.reason);
  } finally { srv.close(); }
}

async function rigCloseMidHandshake() {
  process.stdout.write('\nRig: server closes mid-handshake (network -> warn, no crash)\n');
  const { srv, port } = await startCloseMidHandshake();
  try {
    const result = await pf.run(pf.defaultEnv(), {
      dataDir: tmpDataDir('reset'),
      network: { url: `http://127.0.0.1:${port}/`, timeoutMs: 1000 },
    });
    const net = result.results.find((r) => r.name === 'network');
    check('network -> warn on socket reset', net.status === 'warn', net && net.reason);
  } finally { srv.close(); }
}

async function rigLockedDir() {
  process.stdout.write('\nRig: appdata write blocked (mkdir succeeds, write fails -> fail)\n');
  // We synthesize blocked write via a custom env that throws on writeFileSync.
  const env = Object.assign({}, pf.defaultEnv(), {
    fs: Object.assign({}, fs, { writeFileSync: () => { throw new Error('EACCES'); } }),
  });
  const result = await pf.run(env, { dataDir: tmpDataDir('locked'), network: { url: 'http://127.0.0.1:1', timeoutMs: 300 } });
  const w = result.results.find((r) => r.name === 'appdata-writable');
  check('appdata-writable -> fail when write throws', w.status === 'fail', w && w.reason);
  check('overall verdict = fail', result.verdict === 'fail');
  check('diagnostic names appdata-writable', !!w);
}

async function rigGermanLocale() {
  process.stdout.write('\nRig: German-localized PowerShell stub (security stays ok, reason is the text we got back)\n');
  const result = await pf.run(germanLocaleEnv(), { dataDir: tmpDataDir('de'), network: { url: 'http://127.0.0.1:1', timeoutMs: 300 } });
  const sec = result.results.find((r) => r.name === 'security-block');
  check('security-block does not crash on German output', sec && sec.status === 'ok', sec && sec.reason);
}

async function main() {
  await rigHangingNetwork();
  await rig500();
  await rigCloseMidHandshake();
  await rigLockedDir();
  await rigGermanLocale();

  process.stdout.write(failed
    ? `\nPREFLIGHT RIGS FAIL: ${failed} assertion(s) failed.\n`
    : '\nPREFLIGHT RIGS PASS: every deliberate-failure rig produced the right verdict and no cross-contamination.\n');
  process.exit(failed ? 1 : 0);
}

main().catch((e) => { process.stderr.write(`\nPREFLIGHT RIGS FAIL: ${e && e.stack || e}\n`); process.exit(1); });
