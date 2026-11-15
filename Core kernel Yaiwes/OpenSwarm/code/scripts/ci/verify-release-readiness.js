#!/usr/bin/env node
// The v* tag gate. Reads preflight-tunings.json (produced by the aggregator) and asserts every platform has the required number of consecutive clean dogfood runs AND zero outstanding tuning candidates. Exits non-zero if any platform isn't ready, blocking the release workflow from publishing.

'use strict';
const fs = require('fs');
const path = require('path');
const h = require('./lib/app-harness');

function parseArgs(argv) {
  // Windows-only by default: the macOS dogfood legs were removed (runner
  // starvation + untriageable mac-only failures), so darwin never accrues runs
  // and requiring it would block every v* tag forever. Re-add a Mac leg to
  // dogfood and pass --require win32,darwin once a maintainer owns it.
  const out = { tunings: null, requirePlatforms: ['win32'] };
  for (let i = 0; i < argv.length; i++) {
    if (argv[i] === '--tunings') out.tunings = argv[++i];
    else if (argv[i] === '--require') out.requirePlatforms = argv[++i].split(',');
  }
  return out;
}

function main() {
  const args = parseArgs(process.argv.slice(2));
  const tuningsPath = args.tunings || path.join(h.REPO_ROOT, 'scripts', 'ci', 'preflight-tunings.json');
  let tunings;
  try { tunings = JSON.parse(fs.readFileSync(tuningsPath, 'utf8')); }
  catch (e) { process.stderr.write(`\nRELEASE-READINESS FAIL: cannot read ${tuningsPath}: ${e && e.message}\n  Run dogfood-aggregator first to generate it.\n`); process.exit(1); }

  process.stdout.write(`Release readiness check: ${tuningsPath}\n`);
  process.stdout.write(`Tunings generated at:    ${tunings.generatedAt}\n`);

  let failed = 0;
  const r = tunings.releaseReadiness || {};
  if (!r.perPlatform) { process.stderr.write('  FAIL no perPlatform block in tunings\n'); process.exit(1); }

  for (const p of args.requirePlatforms) {
    const slot = r.perPlatform[p];
    if (!slot) { process.stderr.write(`  FAIL  required platform "${p}" has no runs yet\n`); failed++; continue; }
    if (!slot.ready) { process.stderr.write(`  FAIL  ${p}: ${slot.tailSize}/${r.minRuns} runs in tail, ${slot.tailMismatches} mismatch(es)\n`); failed++; }
    else process.stdout.write(`  ok    ${p}: ${slot.tailSize}/${r.minRuns} consecutive clean runs\n`);
  }

  // No outstanding demotion candidates (each is an unresolved false-positive source).
  const demoteCount = (tunings.demote || []).length;
  if (demoteCount > 0) {
    process.stderr.write(`  FAIL  ${demoteCount} check(s) flagged for demotion - resolve before tagging:\n`);
    for (const d of tunings.demote) process.stderr.write(`    - ${d.platform}/${d.check}: warnRate=${(d.warnRate * 100).toFixed(1)}%\n`);
    failed++;
  } else {
    process.stdout.write('  ok    no demotion candidates outstanding\n');
  }

  if (failed) { process.stderr.write(`\nRELEASE-READINESS FAIL: ${failed} blocker(s); do not tag v*.\n`); process.exit(1); }
  process.stdout.write('\nRELEASE-READINESS PASS: every platform has the required consecutive clean dogfood runs; tagging is unblocked.\n');
  process.exit(0);
}

main();
