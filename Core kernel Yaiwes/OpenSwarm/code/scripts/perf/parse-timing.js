#!/usr/bin/env node
// Phase 0 baseline: parse the four boot milestones out of backend.log and prove
// they are present and correctly ordered. main.js emits one line per milestone:
//   [perf] <name> t=<ms-since-launch>
// We read the most recent launch block (delimited by "===== launch ... =====")
// so a re-run measures the latest boot, not a stale one.
//
// Usage:
//   node scripts/perf/parse-timing.js [--log <path>] [--json]
//
// Exit 0 if all four present and ordered, 1 otherwise. Designed to be the
// assertion step of the Phase 0 test: launch the packaged app, then run this.

'use strict';
const fs = require('fs');
const os = require('os');
const path = require('path');

// Canonical order. app-launch must be first and first-agent-response last;
// first-paint and backend-http-ready sit between and may swap (lazy backend
// paints the shell before Python answers, eager backend does the reverse), so
// we only require they fall between the bookends, not a fixed order vs each other.
const REQUIRED = ['app-launch', 'first-paint', 'backend-http-ready', 'first-agent-response'];

function parseArgs(argv) {
  const out = { log: null, json: false };
  for (let i = 0; i < argv.length; i++) {
    if (argv[i] === '--log') out.log = argv[++i];
    else if (argv[i] === '--json') out.json = true;
  }
  return out;
}

// Mirrors getAuthTokenFilePath()/getBackendLogPath() in electron/main.js.
function defaultLogPath() {
  if (process.platform === 'darwin') {
    return path.join(os.homedir(), 'Library', 'Application Support', 'OpenSwarm', 'data', 'backend.log');
  } else if (process.platform === 'win32') {
    return path.join(process.env.APPDATA || os.homedir(), 'OpenSwarm', 'data', 'backend.log');
  }
  const xdg = process.env.XDG_DATA_HOME || path.join(os.homedir(), '.local', 'share');
  return path.join(xdg, 'OpenSwarm', 'data', 'backend.log');
}

function fail(msg, report) {
  if (report && report.json) { process.stdout.write(JSON.stringify({ ok: false, error: msg, ...report.data }, null, 2) + '\n'); }
  else process.stderr.write(`FAIL: ${msg}\n`);
  process.exit(1);
}

function main() {
  const args = parseArgs(process.argv.slice(2));
  const logPath = args.log ? path.resolve(args.log) : defaultLogPath();

  let raw;
  try { raw = fs.readFileSync(logPath, 'utf8'); }
  catch { fail(`cannot read log at ${logPath} (launch the packaged app first)`, { json: args.json, data: { logPath } }); return; }

  // Take only the last launch block so we measure the most recent boot.
  const marker = '===== launch';
  const lastIdx = raw.lastIndexOf(marker);
  const block = lastIdx >= 0 ? raw.slice(lastIdx) : raw;

  const marks = {};
  const re = /\[perf\]\s+(\S+)\s+t=(\d+)/g;
  let m;
  while ((m = re.exec(block)) !== null) {
    // First occurrence wins (matches main.js one-shot guard); ignore later dupes.
    if (!(m[1] in marks)) marks[m[1]] = Number(m[2]);
  }

  const report = { json: args.json, data: { logPath, marks } };
  const missing = REQUIRED.filter((k) => !(k in marks));
  if (missing.length) fail(`missing milestone(s): ${missing.join(', ')}`, report);

  // Bookends: app-launch earliest, first-agent-response latest.
  const t = marks;
  if (t['app-launch'] !== Math.min(...REQUIRED.map((k) => t[k]))) fail('app-launch is not the earliest milestone', report);
  if (t['first-agent-response'] !== Math.max(...REQUIRED.map((k) => t[k]))) fail('first-agent-response is not the latest milestone', report);
  for (const k of REQUIRED) if (!Number.isFinite(t[k]) || t[k] < 0) fail(`milestone ${k} has invalid t=${t[k]}`, report);

  const ordered = [...REQUIRED].sort((a, b) => t[a] - t[b]);
  const result = {
    ok: true,
    logPath,
    marks,
    order: ordered.map((k) => `${k}@${t[k]}ms`),
    durations: {
      'launch->first-paint': t['first-paint'] - t['app-launch'],
      'launch->backend-ready': t['backend-http-ready'] - t['app-launch'],
      'launch->first-agent-response': t['first-agent-response'] - t['app-launch'],
    },
  };

  if (args.json) { process.stdout.write(JSON.stringify(result, null, 2) + '\n'); return; }
  process.stdout.write('\nPASS: all four boot milestones present and ordered.\n');
  process.stdout.write(`  log: ${logPath}\n`);
  for (const k of ordered) process.stdout.write(`  ${k.padEnd(22)} ${String(t[k]).padStart(8)} ms\n`);
  process.stdout.write(`\n  launch -> first-agent-response: ${result.durations['launch->first-agent-response']} ms\n\n`);
}

main();
