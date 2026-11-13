#!/usr/bin/env node
// Phase 3 test: stand up a fake backend on a real localhost port and prove the
// smoke checker passes a healthy one and fails the failure modes the gate
// exists for (health never ready, agent 401/500). Hermetic; no packaged build.
//
//   node scripts/ci/test-smoke-backend.js

'use strict';
const http = require('http');
const path = require('path');
const { execFile } = require('child_process');

const NODE = process.execPath;
const SCRIPT = path.join(__dirname, 'smoke-backend.js');
let passed = 0;

function assert(cond, msg) {
  if (!cond) { process.stderr.write(`\nASSERT FAILED: ${msg}\n`); process.exit(1); }
  passed++;
}

// Fake backend. behavior() decides the status code per request path so we can
// model healthy / unauthorized / broken-after-health cases.
function startServer(behavior) {
  return new Promise((resolve) => {
    const srv = http.createServer((req, res) => {
      const code = behavior(req);
      res.writeHead(code, { 'content-type': 'application/json' });
      res.end('{}');
    });
    srv.listen(0, '127.0.0.1', () => resolve({ srv, port: srv.address().port }));
  });
}

// Async (not execFileSync): the fake server shares this process's event loop,
// so blocking it synchronously would stop the server answering. Returning a
// promise keeps the loop free to service the smoke child's real TCP requests.
function runSmoke(port, extra) {
  return new Promise((resolve) => {
    execFile(NODE, [SCRIPT, '--port', String(port), '--timeout-ms', '3000', ...extra],
      (err) => resolve(err && err.code != null ? err.code : (err ? -1 : 0)));
  });
}

async function main() {
  // (1) healthy: both endpoints 200 -> pass
  {
    const { srv, port } = await startServer(() => 200);
    assert(await runSmoke(port, ['--agent', '/api/agents/models']) === 0, 'healthy backend should pass');
    srv.close();
  }

  // (2) health ok but agent 401 (auth/origin broken) -> fail
  {
    const { srv, port } = await startServer((req) => (req.url.startsWith('/api/health') ? 200 : 401));
    assert(await runSmoke(port, ['--agent', '/api/agents/models']) === 1, 'agent 401 should fail the smoke');
    srv.close();
  }

  // (3) health ok but agent 500 -> fail
  {
    const { srv, port } = await startServer((req) => (req.url.startsWith('/api/health') ? 200 : 500));
    assert(await runSmoke(port, ['--agent', '/api/agents/models']) === 1, 'agent 500 should fail the smoke');
    srv.close();
  }

  // (4) health never ready (always 503) -> fail within timeout, no hang
  {
    const { srv, port } = await startServer(() => 503);
    const t0 = Date.now();
    assert(await runSmoke(port, []) === 1, 'never-ready health should fail');
    assert(Date.now() - t0 < 15000, 'must fail via timeout, not hang');
    srv.close();
  }

  // (5) nothing listening on the port -> fail
  {
    assert(await runSmoke(59999, []) === 1, 'no server should fail');
  }

  process.stdout.write(`\nPhase 3 backend smoke: ${passed} assertions passed.\n`);
}

main();
