#!/usr/bin/env node
// Phase 0 test: deterministic, hermetic checks of the perf tooling. Builds
// throwaway fixtures in a temp dir with KNOWN file counts and KNOWN timing
// logs, runs file-count.js and parse-timing.js against them, and asserts the
// numbers come back exactly right plus that the failure paths actually fail.
// No packaged build required, so this runs identically on Win, Mac, and CI.
//
//   node scripts/perf/test-perf.js
//
// Exit 0 = all assertions passed. Any failure exits 1 with the first mismatch.

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

function mktmp(prefix) {
  return fs.mkdtempSync(path.join(os.tmpdir(), prefix));
}

function writeFile(p, content) {
  fs.mkdirSync(path.dirname(p), { recursive: true });
  fs.writeFileSync(p, content);
}

// Runs a script, returns { code, stdout, stderr }. Never throws on non-zero.
function run(script, extraArgs) {
  try {
    const stdout = execFileSync(NODE, [path.join(HERE, script), ...extraArgs], { encoding: 'utf8' });
    return { code: 0, stdout, stderr: '' };
  } catch (e) {
    return { code: e.status == null ? -1 : e.status, stdout: e.stdout || '', stderr: e.stderr || '' };
  }
}

// ---- file-count.js -------------------------------------------------------
function testFileCount() {
  const root = mktmp('osw-fc-');
  // Known layout: python-env=3 files, node=2, node_modules=4, mcp-servers=1,
  // plus a stray top-level file that must land in "other"=1. total=11.
  writeFile(path.join(root, 'python-env', 'a.py'), 'x');
  writeFile(path.join(root, 'python-env', 'lib', 'b.py'), 'xx');
  writeFile(path.join(root, 'python-env', 'lib', 'c.so'), 'xxx');
  writeFile(path.join(root, 'node', 'x64', 'node.exe'), 'nn');
  writeFile(path.join(root, 'node', 'arm64', 'node'), 'nn');
  writeFile(path.join(root, 'node_modules', 'pkg', 'index.js'), 'a');
  writeFile(path.join(root, 'node_modules', 'pkg', 'readme.md'), 'a');
  writeFile(path.join(root, 'node_modules', 'dep', 'main.js'), 'a');
  writeFile(path.join(root, 'node_modules', 'dep', 'types.d.ts'), 'a');
  writeFile(path.join(root, 'mcp-servers', 'srv.js'), 'm');
  writeFile(path.join(root, 'app.asar'), 'stray');

  const r = run('file-count.js', ['--root', root, '--json']);
  assert(r.code === 0, `file-count exited ${r.code}: ${r.stderr}`);
  const rep = JSON.parse(r.stdout);
  assert(rep.dirs['python-env'].files === 3, `python-env files=${rep.dirs['python-env'].files} expected 3`);
  assert(rep.dirs['node'].files === 2, `node files=${rep.dirs['node'].files} expected 2`);
  assert(rep.dirs['node_modules'].files === 4, `node_modules files=${rep.dirs['node_modules'].files} expected 4`);
  assert(rep.dirs['mcp-servers'].files === 1, `mcp-servers files=${rep.dirs['mcp-servers'].files} expected 1`);
  assert(rep.dirs['other'].files === 1, `other files=${rep.dirs['other'].files} expected 1`);
  assert(rep.total.files === 11, `total files=${rep.total.files} expected 11`);

  // Total must reconcile with an independent raw walk of the whole tree.
  const independent = countRaw(root);
  assert(rep.total.files === independent, `report total ${rep.total.files} != raw walk ${independent}`);

  // Missing root must exit non-zero (broken-build signal).
  const bad = run('file-count.js', ['--root', path.join(root, 'does-not-exist'), '--json']);
  assert(bad.code !== 0, 'file-count should exit non-zero for a missing root');

  fs.rmSync(root, { recursive: true, force: true });
}

function countRaw(dir) {
  let n = 0;
  for (const ent of fs.readdirSync(dir, { withFileTypes: true })) {
    if (ent.isDirectory()) n += countRaw(path.join(dir, ent.name));
    else n += 1;
  }
  return n;
}

// ---- parse-timing.js -----------------------------------------------------
function logBlock(marks) {
  let s = `\n===== launch ${new Date().toISOString()} (app 1.1.69, win32/x64) =====\n`;
  for (const [k, v] of Object.entries(marks)) s += `[perf] ${k} t=${v}\n`;
  return s;
}

function testParseTimingPass() {
  const dir = mktmp('osw-pt-');
  const log = path.join(dir, 'backend.log');
  // Two launch blocks; the parser must read only the LAST. First block is
  // deliberately broken (missing milestones) to prove staleness is ignored.
  let content = logBlock({ 'app-launch': 5 });
  content += logBlock({ 'app-launch': 3, 'first-paint': 120, 'backend-http-ready': 800, 'first-agent-response': 2500 });
  fs.writeFileSync(log, content);

  const r = run('parse-timing.js', ['--log', log, '--json']);
  assert(r.code === 0, `parse-timing should pass, exited ${r.code}: ${r.stderr}`);
  const rep = JSON.parse(r.stdout);
  assert(rep.ok === true, 'parse-timing ok should be true');
  assert(rep.marks['app-launch'] === 3, `read stale block: app-launch=${rep.marks['app-launch']} expected 3`);
  assert(rep.durations['launch->first-agent-response'] === 2497, `duration=${rep.durations['launch->first-agent-response']} expected 2497`);
  fs.rmSync(dir, { recursive: true, force: true });
}

function testParseTimingFailures() {
  const dir = mktmp('osw-ptf-');

  // (a) missing a milestone -> fail
  const log1 = path.join(dir, 'missing.log');
  fs.writeFileSync(log1, logBlock({ 'app-launch': 0, 'first-paint': 10, 'backend-http-ready': 50 }));
  assert(run('parse-timing.js', ['--log', log1]).code === 1, 'missing milestone should fail');

  // (b) out of order: first-agent-response earlier than backend-ready -> fail
  const log2 = path.join(dir, 'unordered.log');
  fs.writeFileSync(log2, logBlock({ 'app-launch': 0, 'first-paint': 10, 'backend-http-ready': 900, 'first-agent-response': 100 }));
  assert(run('parse-timing.js', ['--log', log2]).code === 1, 'out-of-order should fail (first-agent-response not latest)');

  // (c) app-launch not earliest -> fail
  const log3 = path.join(dir, 'badlaunch.log');
  fs.writeFileSync(log3, logBlock({ 'app-launch': 50, 'first-paint': 10, 'backend-http-ready': 900, 'first-agent-response': 2000 }));
  assert(run('parse-timing.js', ['--log', log3]).code === 1, 'app-launch-not-earliest should fail');

  // (d) nonexistent log -> fail
  assert(run('parse-timing.js', ['--log', path.join(dir, 'nope.log')]).code === 1, 'missing log file should fail');

  fs.rmSync(dir, { recursive: true, force: true });
}

testFileCount();
testParseTimingPass();
testParseTimingFailures();
process.stdout.write(`\nPhase 0 perf tooling: ${passed} assertions passed.\n`);
