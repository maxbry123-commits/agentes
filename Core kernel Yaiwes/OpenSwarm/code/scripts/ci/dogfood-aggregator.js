#!/usr/bin/env node
// Reads every line of dogfood-manifest.jsonl, computes per-check warn+fail rates, identifies checks that DISAGREE with reality (verdict says fail but boot was fine, or check warned on >2x baseline runs), and emits preflight-tunings.json which the preflight module reads to auto-demote a noisy check (bump its timeout, or downgrade fail->warn). Also emits a release-readiness summary the gate uses.

'use strict';
const fs = require('fs');
const path = require('path');
const h = require('./lib/app-harness');

function parseArgs(argv) {
  const out = { manifest: null, tunings: null, minRuns: 12, falsePositiveTolerance: 0.10 };
  for (let i = 0; i < argv.length; i++) {
    if (argv[i] === '--manifest') out.manifest = argv[++i];
    else if (argv[i] === '--tunings') out.tunings = argv[++i];
    else if (argv[i] === '--min-runs') out.minRuns = Number(argv[++i]);
    else if (argv[i] === '--fp-tolerance') out.falsePositiveTolerance = Number(argv[++i]);
  }
  return out;
}

function readManifest(p) {
  let text = '';
  try { text = fs.readFileSync(p, 'utf8'); } catch { return []; }
  return text.split(/\r?\n/).filter(Boolean).map((l) => { try { return JSON.parse(l); } catch { return null; } }).filter(Boolean);
}

function main() {
  const args = parseArgs(process.argv.slice(2));
  const manifestPath = args.manifest || path.join(h.REPO_ROOT, 'scripts', 'ci', 'dogfood-manifest.jsonl');
  const tuningsPath = args.tunings || path.join(h.REPO_ROOT, 'scripts', 'ci', 'preflight-tunings.json');
  const runs = readManifest(manifestPath);

  process.stdout.write(`Manifest: ${manifestPath}\n`);
  process.stdout.write(`Runs:     ${runs.length}\n`);
  if (runs.length === 0) { process.stdout.write('\nAGGREGATE: no runs yet; nothing to tune.\n'); return; }

  // Per-platform stats so a noisy-on-Windows-only check doesn't get demoted globally.
  const byPlatform = {};
  for (const r of runs) {
    const p = r.platform || 'unknown';
    if (!byPlatform[p]) byPlatform[p] = { runs: [], total: 0, mismatches: 0, falsePositives: 0, falseNegatives: 0, checkStats: {} };
    const slot = byPlatform[p];
    slot.runs.push(r);
    slot.total++;
    if (r.classification && r.classification.mismatch) {
      slot.mismatches++;
      if (r.classification.kind === 'false-positive') slot.falsePositives++;
      if (r.classification.kind === 'false-negative') slot.falseNegatives++;
    }
    for (const [name, info] of Object.entries(r.preflightChecks || {})) {
      if (!slot.checkStats[name]) slot.checkStats[name] = { warn: 0, fail: 0, total: 0 };
      slot.checkStats[name].total++;
      if (info.status === 'warn') slot.checkStats[name].warn++;
      if (info.status === 'fail') slot.checkStats[name].fail++;
    }
  }

  // Identify tuning candidates: checks whose warn-rate on a platform exceeds the
  // tolerance AND the platform's overall boots are mostly successful. These are
  // false-positive sources that need either a longer timeout or a demoted threshold.
  const tunings = { generatedAt: new Date().toISOString(), perPlatform: {}, demote: [] };
  for (const [p, slot] of Object.entries(byPlatform)) {
    tunings.perPlatform[p] = { runs: slot.total, mismatches: slot.mismatches, falsePositiveRate: slot.total ? slot.falsePositives / slot.total : 0, falseNegativeRate: slot.total ? slot.falseNegatives / slot.total : 0 };
    for (const [name, st] of Object.entries(slot.checkStats)) {
      const warnRate = st.warn / Math.max(1, st.total);
      if (warnRate > 2 * args.falsePositiveTolerance && slot.falsePositives / Math.max(1, slot.total) > args.falsePositiveTolerance) {
        tunings.demote.push({ platform: p, check: name, warnRate, action: 'demote-to-warn-only' });
      }
    }
  }

  fs.writeFileSync(tuningsPath, JSON.stringify(tunings, null, 2));
  process.stdout.write(`Tunings written: ${tuningsPath}\n`);
  for (const [p, slot] of Object.entries(byPlatform)) {
    process.stdout.write(`\n  ${p}: ${slot.total} runs, ${slot.mismatches} mismatches (${slot.falsePositives} false-positive, ${slot.falseNegatives} false-negative)\n`);
    for (const [name, st] of Object.entries(slot.checkStats)) {
      const wr = ((st.warn / st.total) * 100).toFixed(1);
      const fr = ((st.fail / st.total) * 100).toFixed(1);
      process.stdout.write(`    ${name.padEnd(20)} warn=${wr}% fail=${fr}% (n=${st.total})\n`);
    }
  }

  // Release readiness: consecutive-clean-runs window per platform. The v* tag
  // gate fails unless every platform has >= minRuns runs with zero mismatches
  // in its tail window.
  let ready = true;
  const readiness = {};
  for (const [p, slot] of Object.entries(byPlatform)) {
    const tail = slot.runs.slice(-args.minRuns);
    const tailMismatches = tail.filter((r) => r.classification && r.classification.mismatch).length;
    const consecutiveClean = tail.length === args.minRuns && tailMismatches === 0;
    readiness[p] = { tailSize: tail.length, tailMismatches, ready: consecutiveClean };
    if (!consecutiveClean) ready = false;
  }
  tunings.releaseReadiness = { ready, perPlatform: readiness, minRuns: args.minRuns };
  fs.writeFileSync(tuningsPath, JSON.stringify(tunings, null, 2));
  process.stdout.write(`\nRelease readiness: ${ready ? 'READY' : 'NOT READY'} (need ${args.minRuns} consecutive clean runs per platform)\n`);
  for (const [p, r] of Object.entries(readiness)) process.stdout.write(`  ${p}: ${r.tailSize}/${args.minRuns} clean=${r.tailMismatches === 0}\n`);
  process.exit(0);
}

main();
