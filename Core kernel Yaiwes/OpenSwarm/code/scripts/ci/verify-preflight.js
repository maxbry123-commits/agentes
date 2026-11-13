#!/usr/bin/env node
// Layer 5: hostile-env matrix verifier. Reads OPENSWARM_TEST_NETWORK / _APPDATA / _LANG flags from the environment and asserts the preflight produces the EXPECTED verdict for that scenario. A false positive ('fail' under network=blocked instead of 'warn') is the bug class we are guarding against; this leg fails red when it happens. Pure node, no app launch, runs on every CI leg in under 10s.

'use strict';
const fs = require('fs');
const os = require('os');
const path = require('path');
const pf = require('../../electron/preflight');

function expectVerdict({ network, appdata, lang }) {
  // Encode the matrix: each axis has known-expected ranges. 'fail' means a
  // specific check returns fail; 'warn' means it returns warn (not fail);
  // 'ok' means clean. Network-blocked must be WARN, not fail.
  if (appdata === 'readonly') return { verdictRange: ['fail'], expect: { 'appdata-writable': 'fail' } };
  if (network === 'blocked') return { verdictRange: ['warn'], expect: { network: 'warn', clock: 'warn' } };
  if (lang === 'de-DE') return { verdictRange: ['ok', 'warn'], expect: {} };
  return { verdictRange: ['ok', 'warn'], expect: {} };
}

async function main() {
  const scenario = {
    network: process.env.OPENSWARM_TEST_NETWORK || 'normal',
    appdata: process.env.OPENSWARM_TEST_APPDATA || 'normal',
    lang: process.env.OPENSWARM_TEST_LANG || 'en-US',
  };
  process.stdout.write(`Scenario: network=${scenario.network} appdata=${scenario.appdata} lang=${scenario.lang}\n`);

  const env = pf.defaultEnv();
  // Synthesize the hostile conditions inside env so we don't actually have to
  // poison the runner's filesystem or DNS (and so the gate is hermetic).
  if (scenario.network === 'blocked') {
    // Block egress by routing through a hung local server.
    const http = require('http');
    const blockedSrv = http.createServer(() => { /* never respond */ });
    await new Promise((resolve) => blockedSrv.listen(0, '127.0.0.1', resolve));
    const blockedUrl = `http://127.0.0.1:${blockedSrv.address().port}/`;
    process.on('exit', () => { try { blockedSrv.close(); } catch {} });
    var netOpts = { url: blockedUrl, timeoutMs: 600 };
    var clockOpts = { url: blockedUrl, timeoutMs: 600 };
    var dsOpts = { host: 'invalid-host-that-cannot-resolve.openswarm.local', timeoutMs: 400 };
  }
  if (scenario.appdata === 'readonly') {
    // Synthesize an unwriteable dir by overriding writeFileSync to throw.
    env.fs = Object.assign({}, fs, { writeFileSync: () => { throw new Error('EACCES synthetic'); } });
  }
  if (scenario.lang === 'de-DE') {
    // Pretend Get-MpComputerStatus returned a German antivirus name.
    env.child_process = { execFile: (cmd, args, opts, cb) => setImmediate(() => cb(null, 'Antivirenprogramm aktiviert: True', '')) };
    env.platform = 'win32';
  }

  const dataDir = path.join(os.tmpdir(), `openswarm-pf-scenario-${process.pid}-${Date.now()}`);
  const t0 = Date.now();
  const result = await pf.run(env, {
    dataDir,
    network: typeof netOpts !== 'undefined' ? netOpts : { url: 'https://api.openswarm.com/', timeoutMs: 4000 },
    clock: typeof clockOpts !== 'undefined' ? clockOpts : undefined,
    dualStack: typeof dsOpts !== 'undefined' ? dsOpts : undefined,
  });
  const dt = Date.now() - t0;
  process.stdout.write(`Total runtime: ${dt}ms; verdict: ${result.verdict}\n`);

  let failed = 0;
  const expected = expectVerdict(scenario);
  if (!expected.verdictRange.includes(result.verdict)) {
    process.stderr.write(`  FAIL  verdict ${result.verdict} not in expected ${JSON.stringify(expected.verdictRange)}\n`);
    failed++;
  } else {
    process.stdout.write(`  ok    verdict ${result.verdict} matches expectation\n`);
  }
  for (const [name, expStatus] of Object.entries(expected.expect)) {
    const r = result.results.find((x) => x.name === name);
    if (!r) { process.stderr.write(`  FAIL  no result for check ${name}\n`); failed++; continue; }
    if (r.status !== expStatus) {
      process.stderr.write(`  FAIL  ${name} status=${r.status} expected ${expStatus} (${r.reason})\n`);
      failed++;
    } else {
      process.stdout.write(`  ok    ${name} = ${r.status} (${r.reason})\n`);
    }
  }
  // Belt-and-braces: total runtime stays under a budget regardless of scenario.
  if (dt > 10_000) { process.stderr.write(`  FAIL  preflight took ${dt}ms > 10s budget\n`); failed++; }

  if (failed) { process.stderr.write(`\nPREFLIGHT MATRIX FAIL: ${failed} assertion(s)\n`); process.exit(1); }
  process.stdout.write('\nPREFLIGHT MATRIX PASS: verdict matches the expected envelope for this scenario.\n');
  process.exit(0);
}

main().catch((e) => { process.stderr.write(`\nPREFLIGHT MATRIX FAIL: ${e && e.stack || e}\n`); process.exit(1); });
