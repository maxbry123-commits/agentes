#!/usr/bin/env node
// Phase 0 baseline: walk the packaged output and report a per-directory file
// count and byte size for the heavy resource dirs we ship, plus a grand total.
// This is the number we measure Phase 6 (python-env/node_modules slimming) and
// Phase 7 (Squirrel vs NSIS) against, so it must be deterministic: same tree in
// => same numbers out, regardless of OS or which arch was packaged.
//
// Usage:
//   node scripts/perf/file-count.js [--root <dir>] [--json]
//
// With no --root it auto-detects the packaged resources dir for this platform,
// falling back to build-staging/ (the pre-package staging tree). Exits non-zero
// if it can't find anything to count so a CI gate notices a broken build.

'use strict';
const fs = require('fs');
const path = require('path');

// Top-level resource dirs we care about. Anything else in the root is folded
// into "other" so the grand total always reconciles with a raw walk.
const DIRS_OF_INTEREST = ['python-env', 'node', 'node_modules', 'mcp-servers', 'backend', 'frontend', 'router', 'debugger'];

function parseArgs(argv) {
  const out = { root: null, json: false };
  for (let i = 0; i < argv.length; i++) {
    if (argv[i] === '--root') out.root = argv[++i];
    else if (argv[i] === '--json') out.json = true;
  }
  return out;
}

// Candidate locations for the packaged tree, most-specific first. We resolve
// relative to the repo root (two levels up from this file) so it works from any
// cwd. The mac .app Resources and the Windows win-unpacked/resources are the
// real shipped trees; build-staging is the pre-electron-builder snapshot.
function autodetectRoot(repoRoot) {
  const dist = path.join(repoRoot, 'electron', 'dist');
  const candidates = [
    path.join(dist, 'win-unpacked', 'resources'),
    path.join(dist, 'mac-arm64', 'OpenSwarm.app', 'Contents', 'Resources'),
    path.join(dist, 'mac', 'OpenSwarm.app', 'Contents', 'Resources'),
    path.join(dist, 'mac-universal', 'OpenSwarm.app', 'Contents', 'Resources'),
    path.join(repoRoot, 'electron', 'build-staging'),
    path.join(repoRoot, 'build-staging'),
  ];
  return candidates.find((c) => safeIsDir(c)) || null;
}

function safeIsDir(p) {
  try { return fs.statSync(p).isDirectory(); } catch { return false; }
}

// Recursive walk. Counts regular files (not directories), sums byte size.
// Symlinks are counted as files without following them, so a symlink loop can
// never hang the walk and the count stays deterministic.
function walk(dir) {
  let files = 0;
  let bytes = 0;
  let entries;
  try { entries = fs.readdirSync(dir, { withFileTypes: true }); } catch { return { files, bytes }; }
  for (const ent of entries) {
    const full = path.join(dir, ent.name);
    if (ent.isDirectory()) {
      const sub = walk(full);
      files += sub.files;
      bytes += sub.bytes;
    } else {
      files += 1;
      try { bytes += fs.statSync(full).size; } catch { /* vanished mid-walk */ }
    }
  }
  return { files, bytes };
}

function fmtBytes(n) {
  const units = ['B', 'KB', 'MB', 'GB'];
  let i = 0;
  let v = n;
  while (v >= 1024 && i < units.length - 1) { v /= 1024; i++; }
  return `${v.toFixed(i === 0 ? 0 : 1)} ${units[i]}`;
}

function main() {
  const args = parseArgs(process.argv.slice(2));
  const repoRoot = path.resolve(__dirname, '..', '..');
  const root = args.root ? path.resolve(args.root) : autodetectRoot(repoRoot);

  if (!root || !safeIsDir(root)) {
    process.stderr.write('file-count: no packaged tree found. Build first or pass --root.\n');
    process.exit(2);
  }

  const report = { root, dirs: {}, total: { files: 0, bytes: 0 }, generatedAt: new Date().toISOString() };
  const topEntries = fs.readdirSync(root, { withFileTypes: true });
  const seen = new Set();

  for (const name of DIRS_OF_INTEREST) {
    const full = path.join(root, name);
    if (safeIsDir(full)) {
      report.dirs[name] = walk(full);
      seen.add(name);
    } else {
      report.dirs[name] = { files: 0, bytes: 0, absent: true };
    }
  }

  // "other" = everything in the root not already counted, so the printed total
  // is the real total of the tree and can be cross-checked by an independent walk.
  let other = { files: 0, bytes: 0 };
  for (const ent of topEntries) {
    if (seen.has(ent.name)) continue;
    const full = path.join(root, ent.name);
    if (ent.isDirectory()) { const s = walk(full); other.files += s.files; other.bytes += s.bytes; }
    else { other.files += 1; try { other.bytes += fs.statSync(full).size; } catch { /* gone */ } }
  }
  report.dirs.other = other;

  for (const k of Object.keys(report.dirs)) {
    report.total.files += report.dirs[k].files;
    report.total.bytes += report.dirs[k].bytes;
  }

  if (args.json) {
    process.stdout.write(JSON.stringify(report, null, 2) + '\n');
    return;
  }

  process.stdout.write(`\nPackaged file count  (root: ${root})\n`);
  process.stdout.write('  ' + '-'.repeat(52) + '\n');
  const rows = Object.keys(report.dirs).sort((a, b) => report.dirs[b].files - report.dirs[a].files);
  for (const name of rows) {
    const d = report.dirs[name];
    const note = d.absent ? '  (absent)' : '';
    process.stdout.write(`  ${name.padEnd(16)} ${String(d.files).padStart(8)} files  ${fmtBytes(d.bytes).padStart(10)}${note}\n`);
  }
  process.stdout.write('  ' + '-'.repeat(52) + '\n');
  process.stdout.write(`  ${'TOTAL'.padEnd(16)} ${String(report.total.files).padStart(8)} files  ${fmtBytes(report.total.bytes).padStart(10)}\n\n`);
}

main();
