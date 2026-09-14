#!/usr/bin/env node
// Dogfood cross-check: launches the packaged app, extracts the [preflight2] verdict from backend.log, then INDEPENDENTLY verifies boot success (provenance == HEAD, perf marks ordered, health 200, no renderer-gone) and asserts the verdict actually correlates with reality. Records every run to dogfood-manifest.jsonl (one line per run) which the aggregator reads to compute false-positive/negative rates per check. The two bug classes this catches:
//   verdict=ok but boot broken     -> a missed check (preflight is theater)
//   verdict=fail but boot fine     -> false positive (will scare real users)
// Either causes a non-zero exit so the dogfood loop goes red and the v* tag is blocked.

'use strict';
const fs = require('fs');
const path = require('path');
const h = require('./lib/app-harness');

function parseArgs(argv) {
  const out = { app: null, timeoutMs: 180000, manifest: null };
  for (let i = 0; i < argv.length; i++) {
    if (argv[i] === '--app') out.app = argv[++i];
    else if (argv[i] === '--timeout-ms') out.timeoutMs = Number(argv[++i]);
    else if (argv[i] === '--manifest') out.manifest = argv[++i];
  }
  return out;
}

function parsePreflight2(log) {
  // [preflight2] verdict=<v> totalMs=<n> <reasons>
  const m = log.match(/\[preflight2\] verdict=(\w+) totalMs=(\d+) (.*)/);
  if (!m) return null;
  const checks = {};
  const reasons = m[3].split(';').map((s) => s.trim()).filter(Boolean);
  for (const r of reasons) {
    const km = r.match(/^([a-z-]+):(\w+)\((.+)\)$/);
    if (km) checks[km[1]] = { status: km[2], reason: km[3] };
  }
  return { verdict: m[1], totalMs: Number(m[2]), checks, raw: m[0] };
}

function bootSuccessSignals(log, headShort, port) {
  // Independent of the preflight: did the app actually paint and serve?
  const { failures, sha, marks } = h.bootFailures({ log, headShort });
  return {
    provenanceMatch: !failures.some((f) => /provenance|HEAD/.test(f)),
    perfMarksOk: !failures.some((f) => /\[perf\]/.test(f)),
    portParsed: !!port,
    rendererCrashed: /renderer process gone/.test(log),
    bootFailures: failures,
    sha,
    marks,
  };
}

function classify(verdict, boot) {
  // boot is "real success" iff provenance matches HEAD, perf marks ordered, port parsed, no renderer crash, no boot failures.
  const realOk = boot.provenanceMatch && boot.perfMarksOk && boot.portParsed && !boot.rendererCrashed && boot.bootFailures.length === 0;
  if (verdict === 'ok' && !realOk) return { mismatch: true, kind: 'false-negative', detail: 'verdict=ok but boot evidence disagrees' };
  if (verdict === 'fail' && realOk) return { mismatch: true, kind: 'false-positive', detail: 'verdict=fail but boot evidence is clean' };
  // warn is allowed in both directions; it's the soft-signal state.
  return { mismatch: false, kind: realOk ? 'true-positive' : 'true-negative', detail: '' };
}

function appendManifest(manifestPath, entry) {
  try {
    fs.mkdirSync(path.dirname(manifestPath), { recursive: true });
    fs.appendFileSync(manifestPath, JSON.stringify(entry) + '\n');
  } catch (e) { process.stderr.write(`  warn could not write manifest: ${e && e.message}\n`); }
}

async function main() {
  const args = parseArgs(process.argv.slice(2));
  const appPath = h.packagedAppPath(args.app);
  const headShort = h.gitHeadShort();
  const manifestPath = args.manifest || path.join(h.REPO_ROOT, 'scripts', 'ci', 'dogfood-manifest.jsonl');

  process.stdout.write(`Dogfood run: ${appPath}\n`);
  const t0 = Date.now();
  const res = await h.launchAndWait({ appPath, timeoutMs: args.timeoutMs });
  const child = res.child;
  let healthCode = 0;
  try {
    if (res.port) { for (let i = 0; i < 10 && healthCode !== 200; i++) { healthCode = await h.healthCode(res.port); if (healthCode !== 200) await h.sleep(1000); } }
    // Wait an extra moment for the [preflight2] line to land (it fires async).
    await h.sleep(3000);
    const log = h.readFileSafe(res.logPath);
    const preflight = parsePreflight2(log);
    const boot = bootSuccessSignals(log, headShort, res.port);
    const totalMs = Date.now() - t0;

    process.stdout.write(`\n  boot.provenanceMatch     = ${boot.provenanceMatch} (sha=${boot.sha})\n`);
    process.stdout.write(`  boot.perfMarksOk         = ${boot.perfMarksOk} (${JSON.stringify(boot.marks)})\n`);
    process.stdout.write(`  boot.portParsed          = ${boot.portParsed} (port=${res.port}, health=${healthCode})\n`);
    process.stdout.write(`  boot.rendererCrashed     = ${boot.rendererCrashed}\n`);
    process.stdout.write(`  boot.failureList         = ${JSON.stringify(boot.bootFailures)}\n`);
    if (preflight) process.stdout.write(`  preflight2.verdict       = ${preflight.verdict} (totalMs=${preflight.totalMs})\n`);
    else process.stdout.write(`  preflight2 line          = ABSENT (no verdict to cross-check)\n`);

    const verdict = preflight ? preflight.verdict : 'absent';
    const cls = classify(verdict, boot);
    const entry = {
      ts: new Date().toISOString(),
      platform: process.platform,
      arch: process.arch,
      sha: headShort,
      verdict,
      preflightChecks: preflight ? preflight.checks : null,
      boot,
      healthCode,
      classification: cls,
      durationMs: totalMs,
    };
    appendManifest(manifestPath, entry);

    if (cls.mismatch) {
      process.stderr.write(`\nDOGFOOD FAIL: ${cls.kind} - ${cls.detail}\n`);
      process.stderr.write(`  This is the bug class the v* tag must NOT ship: verdict and reality disagree.\n`);
      h.killApp(child);
      process.exit(1);
    }
    if (!preflight) {
      // Absent line is a separate failure mode (preflight didn't run or didn't log).
      process.stderr.write(`\nDOGFOOD FAIL: no [preflight2] line in backend.log; the module did not fire or did not log\n`);
      h.killApp(child);
      process.exit(1);
    }
    h.killApp(child);
    process.stdout.write(`\nDOGFOOD PASS: verdict=${verdict} agrees with independent boot evidence (${cls.kind}); recorded to ${manifestPath}\n`);
    process.exit(0);
  } catch (e) {
    h.killApp(child);
    process.stderr.write(`\nDOGFOOD FAIL: ${e && e.stack || e}\n`);
    process.exit(1);
  }
}

main().catch((e) => { process.stderr.write(`\nDOGFOOD FAIL: ${e && e.stack || e}\n`); process.exit(1); });
