#!/usr/bin/env node
// Phase 5a test: hermetic checks of the promotion gate. Builds throwaway
// latest*.yml fixtures and asserts the gate promotes a good release and blocks
// the two failures the gate exists for: a missing feed and a version mismatch.
// No network (URL checking is exercised separately in CI with --base-url).
//
//   node scripts/release/test-verify-release.js

'use strict';
const fs = require('fs');
const os = require('os');
const path = require('path');
const { execFileSync } = require('child_process');

const HERE = __dirname;
const NODE = process.execPath;
let passed = 0;

function assert(cond, msg) {
  if (!cond) { process.stderr.write(`\nASSERT FAILED: ${msg}\n`); process.exit(1); }
  passed++;
}

function run(args) {
  try {
    const stdout = execFileSync(NODE, [path.join(HERE, 'verify-release.js'), ...args], { encoding: 'utf8' });
    return { code: 0, stdout };
  } catch (e) {
    return { code: e.status == null ? -1 : e.status, stdout: e.stdout || '', stderr: e.stderr || '' };
  }
}

function feed(version, asset) {
  return `version: ${version}\nfiles:\n  - url: ${asset}\n    sha512: deadbeef\n    size: 123\npath: ${asset}\nsha512: deadbeef\nreleaseDate: '2026-05-27T00:00:00.000Z'\n`;
}

function mkdir() { return fs.mkdtempSync(path.join(os.tmpdir(), 'osw-rel-')); }

// (1) good release: both feeds, same version, matches expected -> promotable
(() => {
  const d = mkdir();
  fs.writeFileSync(path.join(d, 'latest.yml'), feed('1.2.3', 'OpenSwarm-Setup-x64.exe'));
  fs.writeFileSync(path.join(d, 'latest-mac.yml'), feed('1.2.3', 'OpenSwarm-arm64.dmg'));
  const r = run(['--dir', d, '--expect-version', '1.2.3', '--json']);
  assert(r.code === 0, `good release should pass, got ${r.code}`);
  assert(JSON.parse(r.stdout).version === '1.2.3', 'should report version 1.2.3');
  // tolerate a leading v on expected
  assert(run(['--dir', d, '--expect-version', 'v1.2.3', '--json']).code === 0, 'leading-v expected should pass');
  fs.rmSync(d, { recursive: true, force: true });
})();

// (2) missing latest-mac.yml -> blocked
(() => {
  const d = mkdir();
  fs.writeFileSync(path.join(d, 'latest.yml'), feed('1.2.3', 'OpenSwarm-Setup-x64.exe'));
  const r = run(['--dir', d, '--expect-version', '1.2.3']);
  assert(r.code === 1, 'missing mac feed should block');
  fs.rmSync(d, { recursive: true, force: true });
})();

// (3) version mismatch across feeds -> blocked
(() => {
  const d = mkdir();
  fs.writeFileSync(path.join(d, 'latest.yml'), feed('1.2.3', 'OpenSwarm-Setup-x64.exe'));
  fs.writeFileSync(path.join(d, 'latest-mac.yml'), feed('1.2.2', 'OpenSwarm-arm64.dmg'));
  const r = run(['--dir', d, '--expect-version', '1.2.3']);
  assert(r.code === 1, 'version mismatch should block');
  fs.rmSync(d, { recursive: true, force: true });
})();

// (4) feeds agree with each other but not with expected version -> blocked
(() => {
  const d = mkdir();
  fs.writeFileSync(path.join(d, 'latest.yml'), feed('1.2.0', 'OpenSwarm-Setup-x64.exe'));
  fs.writeFileSync(path.join(d, 'latest-mac.yml'), feed('1.2.0', 'OpenSwarm-arm64.dmg'));
  const r = run(['--dir', d, '--expect-version', '1.2.3']);
  assert(r.code === 1, 'expected-version mismatch should block');
  fs.rmSync(d, { recursive: true, force: true });
})();

process.stdout.write(`\nPhase 5a promotion gate: ${passed} assertions passed.\n`);
