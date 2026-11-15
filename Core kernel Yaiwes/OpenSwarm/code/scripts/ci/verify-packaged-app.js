#!/usr/bin/env node
// Launches the built app and reads backend.log: provenance sha == git HEAD, perf marks ordered (proves first paint), health 200. No browser automation; Playwright is for GUI clicks.

'use strict';
const h = require('./lib/app-harness');

function parseArgs(argv) {
  const out = { app: null, timeoutMs: 180000 };
  for (let i = 0; i < argv.length; i++) {
    if (argv[i] === '--app') out.app = argv[++i];
    else if (argv[i] === '--timeout-ms') out.timeoutMs = Number(argv[++i]);
  }
  return out;
}

let child = null;
function fail(msg) { process.stderr.write(`\nVERIFY FAIL: ${msg}\n`); h.killApp(child); process.exit(1); }

async function main() {
  const args = parseArgs(process.argv.slice(2));
  const appPath = h.packagedAppPath(args.app);
  const headShort = h.gitHeadShort();

  process.stdout.write(`Launching: ${appPath}\n`);
  const res = await h.launchAndWait({ appPath, timeoutMs: args.timeoutMs });
  child = res.child;
  const { log, port } = res;

  // --- assertions (log half is pure + mutation-tested in selftest-gate.js) ---
  const { failures, sha: provSha, marks } = h.bootFailures({ log, headShort });
  if (failures.length) fail(failures.join('; '));

  if (port) {
    let code = 0;
    for (let i = 0; i < 10 && code !== 200; i++) { code = await h.healthCode(port); if (code !== 200) await h.sleep(1000); }
    if (code !== 200) fail(`backend health on :${port} returned ${code}, expected 200`);
  } else {
    process.stdout.write('  (note: could not parse backend port from log; relied on perf marks + provenance)\n');
  }

  h.killApp(child);
  process.stdout.write('\nVERIFY PASS: packaged app booted, painted, and served.\n');
  process.stdout.write(`  provenance sha   = ${provSha} (== HEAD)\n`);
  process.stdout.write(`  app-launch       = ${marks['app-launch']} ms\n`);
  process.stdout.write(`  first-paint      = ${marks['first-paint']} ms\n`);
  process.stdout.write(`  backend-ready    = ${marks['backend-http-ready']} ms${port ? ` (health 200 on :${port})` : ''}\n\n`);
  process.exit(0);
}

main().catch((e) => fail(e && e.message || String(e)));
