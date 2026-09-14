#!/usr/bin/env node
// Asserts the packaged app boots correctly from a TRULY empty user-data dir (no settings.json, no auth.token, no sessions). Catches a class of bugs where the app silently assumes prior state on disk and fails on a first-time user. CI-gated because it deletes the user data dir; never runs on a developer machine without explicit OPENSWARM_E2E_WIPE=1.

'use strict';
const fs = require('fs');
const path = require('path');
const h = require('./lib/app-harness');

function parseArgs(argv) {
  const out = { app: null, timeoutMs: 180000 };
  for (let i = 0; i < argv.length; i++) {
    if (argv[i] === '--app') out.app = argv[++i];
    else if (argv[i] === '--timeout-ms') out.timeoutMs = Number(argv[++i]);
  }
  return out;
}

function rmrf(target) {
  try { fs.rmSync(target, { recursive: true, force: true }); } catch { /* may not exist */ }
}

async function main() {
  if (process.env.CI !== 'true' && process.env.OPENSWARM_E2E_WIPE !== '1') {
    process.stdout.write('SKIP: clean-profile would wipe the user data dir. Set CI=true or OPENSWARM_E2E_WIPE=1 to run.\n');
    process.exit(0);
  }

  const args = parseArgs(process.argv.slice(2));
  const appPath = h.packagedAppPath(args.app);
  const dataDir = path.dirname(h.backendLogPath());
  // The user data dir is one level up from data/ in our layout.
  const appDataRoot = path.dirname(dataDir);

  process.stdout.write(`Wiping user data root: ${appDataRoot}\n`);
  rmrf(appDataRoot);
  if (fs.existsSync(appDataRoot)) { process.stderr.write(`\nCLEAN-PROFILE FAIL: could not wipe ${appDataRoot} (in use?)\n`); process.exit(1); }
  process.stdout.write('  ok user data dir is gone (truly first-launch state)\n');

  process.stdout.write(`Launching from a cold profile: ${appPath}\n`);
  const res = await h.launchAndWait({ appPath, timeoutMs: args.timeoutMs });
  const child = res.child;
  try {
    // Same shape of assertions as verify-packaged-app, but the value is in HAVING WIPED FIRST.
    const headShort = h.gitHeadShort();
    const { failures } = h.bootFailures({ log: res.log, headShort });
    if (failures.length) throw new Error(failures.join('; '));

    if (res.port) {
      let code = 0;
      for (let i = 0; i < 10 && code !== 200; i++) { code = await h.healthCode(res.port); if (code !== 200) await h.sleep(1000); }
      if (code !== 200) throw new Error(`backend on :${res.port} returned ${code} from a clean profile`);
    }

    // Confirm the app populated the basics that a first-time user needs.
    const created = [];
    if (fs.existsSync(h.backendLogPath())) created.push('backend.log');
    if (fs.existsSync(h.authTokenPath())) created.push('auth.token');
    if (created.length === 0) throw new Error('app booted but created no expected files (backend.log/auth.token both absent)');
    process.stdout.write(`  ok app populated: ${created.join(', ')}\n`);

    process.stdout.write('\nCLEAN-PROFILE PASS: app booted, painted, and served from a truly empty user dir.\n');
    process.exit(0);
  } catch (e) {
    process.stderr.write(`\nCLEAN-PROFILE FAIL: ${e && e.message || e}\n`);
    process.exit(1);
  } finally {
    h.killApp(child);
  }
}

main().catch((e) => { process.stderr.write(`\nCLEAN-PROFILE FAIL: ${e && e.message || e}\n`); process.exit(1); });
