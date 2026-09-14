#!/usr/bin/env node
// One green button for every hermetic phase test in this plan. These run with no
// packaged build, no network, and no platform assumptions, so they are safe in
// CI and on any dev machine. Phase tests that REQUIRE a packaged artifact, CI,
// macOS hardware, or a real device fleet are intentionally not here (they can't
// be hermetic); see docs/RELEASE_CHECKLIST.md for those.
//
//   node scripts/run-phase-tests.js
//
// Exit 0 only if every suite passes.

'use strict';
const path = require('path');
const { execFileSync } = require('child_process');

const SUITES = [
  ['Phase 0  boot timing + file count', 'perf/test-perf.js'],
  ['Phase 3  backend artifact smoke',   'ci/test-smoke-backend.js'],
  ['Phase 5a release promotion gate',   'release/test-verify-release.js'],
];

let failures = 0;
for (const [label, rel] of SUITES) {
  process.stdout.write(`\n=== ${label} ===\n`);
  try {
    const out = execFileSync(process.execPath, [path.join(__dirname, rel)], { encoding: 'utf8' });
    process.stdout.write(out.trim() + '\n');
  } catch (e) {
    failures++;
    process.stdout.write((e.stdout || '') + (e.stderr || '') + `  -> SUITE FAILED (${rel})\n`);
  }
}

process.stdout.write(`\n${failures === 0 ? 'ALL PHASE TEST SUITES PASSED' : failures + ' SUITE(S) FAILED'}\n`);
process.exit(failures === 0 ? 0 : 1);
