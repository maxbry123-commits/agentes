#!/usr/bin/env node
// Test-the-tests: feeds broken backend.logs to the boot check and asserts each guard fires (a good log passes); if a break stops going red, the gate is theater. Live-process guards: see GATE_AUDIT.md.

'use strict';
const h = require('./lib/app-harness');

let failed = 0;
function check(name, cond) { process.stdout.write(`  ${cond ? 'ok  ' : 'FAIL'}  ${name}\n`); if (!cond) failed++; }
const caught = (log, head, re) => h.bootFailures({ log, headShort: head }).failures.some((f) => re.test(f));

const HEAD = 'abc123def456';
const GOOD = [
  '[provenance] OpenSwarm 1.1.69 sha=abc123def456 channel=stable builtAt=2026-01-01T00:00:00Z',
  '[perf] app-launch t=100',
  '[perf] first-paint t=400',
  '[perf] backend-http-ready t=4000',
  'Backend ready on port 8324',
].join('\n');

process.stdout.write('boot-check mutation tests:\n');

// Baseline: a good log must PASS (no false positives - the inverse failure mode).
check('good log -> 0 failures (no false alarm)', h.bootFailures({ log: GOOD, headShort: HEAD }).failures.length === 0);

// Each mutation must be CAUGHT:
check('missing [provenance] -> caught', caught(GOOD.replace(/\[provenance\].*/, ''), HEAD, /provenance/));
check('sha != HEAD -> caught', caught(GOOD.replace('abc123def456', '000000000000'), HEAD, /!= git HEAD/));
check('missing first-paint mark -> caught', caught(GOOD.replace(/\[perf\] first-paint t=400\n/, ''), HEAD, /first-paint/));
check('missing backend-http-ready mark -> caught', caught(GOOD.replace(/\[perf\] backend-http-ready t=4000/, ''), HEAD, /backend-http-ready/));
check('out-of-order marks -> caught', caught(GOOD.replace('first-paint t=400', 'first-paint t=9999'), HEAD, /out of order/));
check('degenerate all-zero marks -> caught', caught(
  '[provenance] OpenSwarm 1 sha=abc123def456 channel=stable\n[perf] app-launch t=0\n[perf] first-paint t=0\n[perf] backend-http-ready t=0',
  HEAD, /> 0|degenerate/));

// A stale build (old sha, all marks fine) must still be caught - the case we saw fire live.
check('stale build (every mark fine, wrong sha) -> still caught', caught(GOOD.replace('abc123def456', 'deadbeef0000'), HEAD, /!= git HEAD/));

process.stdout.write('\nparse-function edge cases:\n');
check('parseProvenanceSha reads a real line', h.parseProvenanceSha(GOOD) === 'abc123def456');
check('parseProvenanceSha returns null on no marker', h.parseProvenanceSha('nothing here') === null);
check('parsePerfMarks finds all three', Object.keys(h.parsePerfMarks(GOOD)).length === 3);

process.stdout.write('\ndeps-pinned mutation tests:\n');
const dp = require('./verify-deps-pinned');
check('exact ==X.Y.Z is pinned', dp.isFullyPinned('anthropic==0.97.0') === true);
check('bare name is NOT pinned', dp.isFullyPinned('jsonschema') === false);
check('>= floor is NOT pinned (drift possible)', dp.isFullyPinned('httpx>=0.27.0') === false);
check('~= compat is NOT pinned', dp.isFullyPinned('foo~=1.0') === false);
check('hash-pinned wheel counts as pinned', dp.isFullyPinned('foo --hash=sha256:abc') === true);
check('parseRequirements strips comments + blanks', dp.parseRequirements('# c\n\nanthropic==1\n').length === 1);
check('parseRequirements ignores -r includes', dp.parseRequirements('-r other.txt\nfoo==1\n').length === 1);

process.stdout.write('\nhost-leakage mutation tests:\n');
const hl = require('./verify-host-leakage');
const patterns = ['C:\\Users\\Alice', 'Alice'];
check('a file containing the build-host path -> at least one hit', hl.scanBuffer('something file:///C:\\Users\\Alice/proj/x', patterns).length > 0);
check('a clean file -> zero hits', hl.scanBuffer('nothing host-y in here at all', patterns).length === 0);
check('a file with the bare username also catches', hl.scanBuffer('greetings Alice', ['Alice']).length > 0);
check('DEFAULT_ALLOW skips PEP 610 direct_url.json', hl.DEFAULT_ALLOW.some((rx) => rx.test('Lib/site-packages/foo-0.1.dist-info/direct_url.json')));
check('DEFAULT_ALLOW does NOT skip a random json under site-packages', !hl.DEFAULT_ALLOW.some((rx) => rx.test('Lib/site-packages/foo/data.json')));

process.stdout.write('\nupdate-feed mutation tests:\n');
const uf = require('./verify-update-feed');
const FEED = "version: 1.0.0\nfiles:\n  - url: Setup.exe\n    sha512: AAA==\n    size: 12345\npath: Setup.exe\nsha512: AAA==\n";
const parsed = uf.parseFeed(FEED);
check('parseFeed reads version', parsed.version === '1.0.0');
check('parseFeed reads files[0].url', parsed.files.length === 1 && parsed.files[0].url === 'Setup.exe');
check('parseFeed reads files[0].size as number', parsed.files[0].size === 12345);
check('parseFeed reads top-level path + sha512', parsed.top.path === 'Setup.exe' && parsed.top.sha512 === 'AAA==');
check('parseFeed returns no files on a feed missing the list', uf.parseFeed('version: 1.0.0\n').files.length === 0);

process.stdout.write('\npreflight mutation tests (cross-gate: if withTimeout regresses to fail-on-hang, the boot pipeline gate also fails):\n');
const pf = require('../../electron/preflight');
(async () => {
  // Hang fuzz: a never-resolving fn must yield status=warn within timeoutMs+50ms.
  const t0 = Date.now();
  const w = await pf.withTimeout('sentinel-hang', () => new Promise(() => {}), 100);
  const dt = Date.now() - t0;
  check('withTimeout: hung fn -> warn (NOT fail)', w.status === 'warn');
  check('withTimeout: hung fn returns within budget+slack', dt < 200);
  // Sync throws inside the fn must still produce warn, not crash the gate.
  const t = await pf.withTimeout('sentinel-throw', () => { throw new Error('boom'); }, 500);
  check('withTimeout: thrown fn -> warn', t.status === 'warn');
  check('withTimeout: thrown fn reason carries the message', /boom/.test(t.reason));
  // Cache version-key invariant: any drift here would silently skip preflight on a version mismatch.
  const env = { fs: { readFileSync: () => JSON.stringify({ appVersion: '2.0.0', verdict: 'ok' }) } };
  check('readCache: version mismatch -> null (no stale skip)', pf.readCache(env, '/x', '1.0.0') === null);
  if (failed === 0) process.stdout.write('\nGATE SELFTEST PASS: every boot guard fires on a break and passes on good input.\n');
  else process.stdout.write(`\nGATE SELFTEST FAIL: ${failed} guard(s) did not discriminate - the gate has theater in it.\n`);
  process.exit(failed ? 1 : 0);
})();
