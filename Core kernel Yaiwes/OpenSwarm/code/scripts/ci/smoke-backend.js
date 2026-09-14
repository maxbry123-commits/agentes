#!/usr/bin/env node
// Phase 3 artifact smoke: drive the real backend the packaged app spawns and
// prove it actually serves. Polls the health endpoint until it answers 200 (or
// a hard timeout), then hits an authenticated agent-subapp endpoint and asserts
// 200. This is the check that turns "works on our machine" into "the artifact
// boots and answers" — break the http origin/CORS or auth and it goes red.
//
// Usage:
//   node scripts/ci/smoke-backend.js --port 8324 [--token <bearer>] \
//        [--token-file <path>] [--health /api/health/check] \
//        [--agent /api/agents/models] [--timeout-ms 120000] [--origin <url>]
//
// Exit 0 = backend booted and both endpoints answered 200. Exit 1 = failed
// (prints reason). Always exits (never hangs): the poll has a wall-clock cap.

'use strict';
const fs = require('fs');
const http = require('http');

function parseArgs(argv) {
  const out = {
    port: null, token: null, tokenFile: null,
    health: '/api/health/check', agent: '/api/agents/models',
    timeoutMs: 120000, origin: null, host: '127.0.0.1',
  };
  for (let i = 0; i < argv.length; i++) {
    const a = argv[i];
    if (a === '--port') out.port = Number(argv[++i]);
    else if (a === '--token') out.token = argv[++i];
    else if (a === '--token-file') out.tokenFile = argv[++i];
    else if (a === '--health') out.health = argv[++i];
    else if (a === '--agent') out.agent = argv[++i];
    else if (a === '--timeout-ms') out.timeoutMs = Number(argv[++i]);
    else if (a === '--origin') out.origin = argv[++i];
    else if (a === '--host') out.host = argv[++i];
  }
  return out;
}

function getOnce(host, port, path, headers) {
  return new Promise((resolve) => {
    let req;
    try {
      // http.get throws synchronously (not via 'error') on a malformed path or
      // header value. A CI smoke tool must degrade to "not answering" (0), never
      // crash, so the wait loop / failure message stays in control.
      req = http.get({ host, port, path, headers }, (res) => {
        res.on('data', () => {}); // drain so the socket frees
        res.on('end', () => resolve(res.statusCode));
      });
    } catch {
      resolve(0);
      return;
    }
    req.on('error', () => resolve(0));
    req.setTimeout(4000, () => { req.destroy(); resolve(0); });
  });
}

function sleep(ms) { return new Promise((r) => setTimeout(r, ms)); }

async function main() {
  const args = parseArgs(process.argv.slice(2));
  if (!args.port) { process.stderr.write('FAIL: --port is required\n'); process.exit(1); }

  let token = args.token || '';
  if (!token && args.tokenFile) {
    try { token = fs.readFileSync(args.tokenFile, 'utf8').trim(); } catch { /* leave empty */ }
  }
  const headers = {};
  if (token) headers.Authorization = `Bearer ${token}`;
  // The backend rejects cross-origin localhost callers; CI can pass --origin to
  // prove the origin check is wired (a wrong origin must NOT 200 the agent call).
  if (args.origin) headers.Origin = args.origin;

  // 1) Wait for health to answer 200, capped by wall clock.
  const deadline = Date.now() + args.timeoutMs;
  let healthCode = 0;
  while (Date.now() < deadline) {
    healthCode = await getOnce(args.host, args.port, args.health, headers);
    if (healthCode === 200) break;
    await sleep(500);
  }
  if (healthCode !== 200) {
    process.stderr.write(`FAIL: health ${args.health} never returned 200 within ${args.timeoutMs}ms (last=${healthCode})\n`);
    process.exit(1);
  }

  // 2) Authenticated agent-subapp endpoint must answer 200.
  const agentCode = await getOnce(args.host, args.port, args.agent, headers);
  if (agentCode !== 200) {
    process.stderr.write(`FAIL: agent ${args.agent} returned ${agentCode} (expected 200; auth/origin/CORS broken?)\n`);
    process.exit(1);
  }

  process.stdout.write(`SMOKE PASS: health 200, agent 200 on :${args.port}\n`);
  process.exit(0);
}

main();
