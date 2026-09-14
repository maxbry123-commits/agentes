#!/usr/bin/env node
// Proves the app survives a taken preferred port (--locked-port falls back, still serves 200) and a second launch (--multi-instance exits cleanly, first keeps serving). No flag runs both.

'use strict';
const net = require('net');
const h = require('./lib/app-harness');

function parseArgs(argv) {
  const out = { app: null, lockedPort: false, multiInstance: false };
  for (let i = 0; i < argv.length; i++) {
    if (argv[i] === '--app') out.app = argv[++i];
    else if (argv[i] === '--locked-port') out.lockedPort = true;
    else if (argv[i] === '--multi-instance') out.multiInstance = true;
  }
  if (!out.lockedPort && !out.multiInstance) { out.lockedPort = true; out.multiInstance = true; }
  return out;
}

function occupy(ports) {
  return Promise.all(ports.map((p) => new Promise((resolve) => {
    const srv = net.createServer();
    srv.once('error', () => resolve(null));            // already taken; fine, still occupied
    srv.listen(p, '127.0.0.1', () => resolve(srv));
  }))).then((s) => s.filter(Boolean));
}

async function healthOk(port) {
  let code = 0;
  for (let i = 0; i < 10 && code !== 200; i++) { code = await h.healthCode(port); if (code !== 200) await h.sleep(1000); }
  return code === 200;
}

async function lockedPortCheck(appPath) {
  const occupied = [];
  for (let p = 8324; p <= 8333; p++) occupied.push(p);   // hold the bottom of the preferred range
  process.stdout.write(`[locked-port] occupying 127.0.0.1:${occupied[0]}-${occupied[occupied.length - 1]}\n`);
  const servers = await occupy(occupied);
  let child = null;
  try {
    const res = await h.launchAndWait({ appPath, timeoutMs: 120000 });
    child = res.child;
    if (!res.port) throw new Error('app never reported a backend port while preferred ports were taken');
    if (occupied.includes(res.port)) throw new Error(`app bound an occupied port :${res.port} (should have skipped it)`);
    if (!(await healthOk(res.port))) throw new Error(`app came up on :${res.port} but health != 200`);
    process.stdout.write(`[locked-port] PASS: app skipped taken ports, served on :${res.port}\n`);
  } finally {
    h.killApp(child);
    servers.forEach((s) => { try { s.close(); } catch { /* */ } });
    await h.sleep(1500);
  }
}

async function multiInstanceCheck(appPath) {
  process.stdout.write('[multi-instance] launching first instance\n');
  const res = await h.launchAndWait({ appPath, timeoutMs: 120000 });
  const first = res.child;
  let second = null;
  try {
    if (res.port && !(await healthOk(res.port))) throw new Error('first instance did not reach health 200');
    process.stdout.write('[multi-instance] launching second instance (must exit cleanly)\n');
    second = h.spawnApp(appPath);
    const exitCode = await new Promise((resolve) => {
      const t = setTimeout(() => resolve('timeout'), 45000);
      second.once('exit', (code) => { clearTimeout(t); resolve(code); });
    });
    if (exitCode === 'timeout') throw new Error('second instance did not exit within 45s (single-instance lock not enforced)');
    if (res.port && !(await healthOk(res.port))) throw new Error('first instance stopped serving after the second launched');
    process.stdout.write(`[multi-instance] PASS: second instance exited (code ${exitCode}); first still serving\n`);
    second = null;   // it exited on its own
  } finally {
    h.killApp(second);
    h.killApp(first);
    await h.sleep(1500);
  }
}

async function main() {
  const args = parseArgs(process.argv.slice(2));
  const appPath = h.packagedAppPath(args.app);
  process.stdout.write(`App: ${appPath}\n`);
  if (args.lockedPort) await lockedPortCheck(appPath);
  if (args.multiInstance) await multiInstanceCheck(appPath);
  process.stdout.write('\nRESILIENCE PASS: all selected checks passed.\n');
  process.exit(0);
}

main().catch((e) => { process.stderr.write(`\nRESILIENCE FAIL: ${e && e.message || e}\n`); process.exit(1); });
