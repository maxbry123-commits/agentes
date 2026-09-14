#!/usr/bin/env node
// Drives a real HTTP request against the bundled 9router, not just a TCP probe. /api/providers is the same endpoint the backend itself polls at startup (see backend/apps/agents/providers/registry.py); if it 200s with parseable JSON, the router is actually routing. A misconfigured router can listen on :20128 and 500 every real request, which the TCP-only check in verify-network would silently green.

'use strict';
const http = require('http');
const h = require('./lib/app-harness');

function parseArgs(argv) {
  const out = { app: null, timeoutMs: 120000 };
  for (let i = 0; i < argv.length; i++) {
    if (argv[i] === '--app') out.app = argv[++i];
    else if (argv[i] === '--timeout-ms') out.timeoutMs = Number(argv[++i]);
  }
  return out;
}

function getJson(port, path, timeoutMs = 8000) {
  return new Promise((resolve) => {
    const req = http.get({ host: '127.0.0.1', port, path }, (res) => {
      let buf = '';
      res.on('data', (c) => { buf += c; });
      res.on('end', () => { let json = null; try { json = JSON.parse(buf); } catch {} resolve({ status: res.statusCode, json, text: buf }); });
    });
    req.on('error', () => resolve({ status: 0, json: null, text: '' }));
    req.setTimeout(timeoutMs, () => { req.destroy(); resolve({ status: 0, json: null, text: '' }); });
  });
}

async function pollUntil(fn, ok, timeoutMs) {
  const deadline = Date.now() + timeoutMs;
  let last = null;
  while (Date.now() < deadline) {
    last = await fn();
    if (ok(last)) return last;
    await h.sleep(1000);
  }
  return last;
}

async function main() {
  const args = parseArgs(process.argv.slice(2));
  const appPath = h.packagedAppPath(args.app);
  process.stdout.write(`Launching: ${appPath}\n`);
  const res = await h.launchAndWait({ appPath, timeoutMs: args.timeoutMs });
  const child = res.child;
  try {
    // Wait for the router to answer /api/providers with 200 + JSON. Until then
    // either the port isn't open or the framework hasn't bound the routes yet.
    const final = await pollUntil(
      () => getJson(20128, '/api/providers'),
      (r) => r && r.status === 200 && r.json && typeof r.json === 'object',
      30_000,
    );
    if (!final || final.status !== 200) throw new Error(`/api/providers returned ${final && final.status}, expected 200`);
    if (!final.json) throw new Error(`/api/providers returned non-JSON body: ${(final.text || '').slice(0, 200)}`);
    process.stdout.write(`  ok 9router GET /api/providers -> 200 (${JSON.stringify(final.json).slice(0, 100)}...)\n`);
    process.stdout.write('\n9ROUTER PASS: bundled router is actually routing, not just listening.\n');
  } catch (e) {
    process.stderr.write(`\n9ROUTER FAIL: ${e && e.message || e}\n`);
    h.killApp(child);
    process.exit(1);
  }
  h.killApp(child);
  process.exit(0);
}

main().catch((e) => { process.stderr.write(`\n9ROUTER FAIL: ${e && e.message || e}\n`); process.exit(1); });
