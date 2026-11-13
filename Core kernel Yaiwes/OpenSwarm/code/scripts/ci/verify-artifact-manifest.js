#!/usr/bin/env node
// Builds or compares a SHA-256 manifest of every file under the packaged artifact root. With --write the current state becomes the manifest; without it, drift from the committed manifest fails the build. Catches non-deterministic build steps (zip timestamps, random ids in bundles) that survive even fully-pinned dependencies.

'use strict';
const fs = require('fs');
const path = require('path');
const crypto = require('crypto');
const h = require('./lib/app-harness');

function parseArgs(argv) {
  const out = { app: null, write: false, manifest: null, only: null };
  for (let i = 0; i < argv.length; i++) {
    if (argv[i] === '--app') out.app = argv[++i];
    else if (argv[i] === '--write') out.write = true;
    else if (argv[i] === '--manifest') out.manifest = argv[++i];
    else if (argv[i] === '--only') out.only = argv[++i];
  }
  return out;
}

// Files that legitimately differ run-to-run (timestamped logs, OS metadata).
// Hashing them would force a manifest churn every build for no signal.
const SKIP = [
  /\.DS_Store$/,
  /[\\/]Thumbs\.db$/,
  /[\\/]desktop\.ini$/,
  /\.log$/,
];

function walk(dir, root, out = []) {
  let entries = [];
  try { entries = fs.readdirSync(dir, { withFileTypes: true }); } catch { return out; }
  for (const e of entries) {
    const full = path.join(dir, e.name);
    if (e.isDirectory()) walk(full, root, out);
    else if (e.isFile()) {
      const rel = path.relative(root, full).replace(/\\/g, '/');
      if (SKIP.some((rx) => rx.test(rel))) continue;
      out.push({ rel, full });
    }
  }
  return out;
}

function sha256(file) {
  const hash = crypto.createHash('sha256');
  const buf = fs.readFileSync(file);
  hash.update(buf);
  return { sha: hash.digest('hex'), size: buf.length };
}

function defaultManifestPath() {
  // The manifest lives in-repo under scripts/ci/ so CI compares to the
  // committed snapshot, and we ship one per platform because Mac/Win/Linux
  // produce different file sets.
  return path.join(h.REPO_ROOT, 'scripts', 'ci', `dist-manifest.${process.platform}.json`);
}

function main() {
  const args = parseArgs(process.argv.slice(2));
  const appExe = h.packagedAppPath(args.app);
  const root = process.platform === 'darwin'
    ? path.dirname(path.dirname(path.dirname(appExe)))
    : path.dirname(appExe);
  const manifestPath = args.manifest || defaultManifestPath();

  process.stdout.write(`Artifact root: ${root}\n`);
  process.stdout.write(`Manifest:      ${manifestPath}\n`);

  const files = walk(root, root);
  const filtered = args.only ? files.filter((f) => new RegExp(args.only).test(f.rel)) : files;
  process.stdout.write(`Hashing ${filtered.length} file(s)...\n`);

  const current = {};
  for (const f of filtered) {
    const { sha, size } = sha256(f.full);
    current[f.rel] = { sha, size };
  }

  if (args.write) {
    fs.writeFileSync(manifestPath, JSON.stringify(current, null, 2));
    process.stdout.write(`\nMANIFEST WRITE: ${Object.keys(current).length} entries -> ${manifestPath}\n`);
    process.stdout.write('Commit this file so the next build can compare against it.\n');
    process.exit(0);
  }

  let committed;
  try { committed = JSON.parse(fs.readFileSync(manifestPath, 'utf8')); }
  catch { process.stderr.write(`\nMANIFEST FAIL: no committed manifest at ${manifestPath}. Run once with --write to seed it.\n`); process.exit(1); }

  const added = [];
  const removed = [];
  const changed = [];
  for (const k of Object.keys(current)) {
    if (!committed[k]) added.push(k);
    else if (committed[k].sha !== current[k].sha) changed.push({ k, was: committed[k], now: current[k] });
  }
  for (const k of Object.keys(committed)) {
    if (!current[k]) removed.push(k);
  }

  if (added.length === 0 && removed.length === 0 && changed.length === 0) {
    process.stdout.write('\nMANIFEST PASS: artifact is byte-identical to the committed manifest.\n');
    process.exit(0);
  }

  process.stderr.write(`\nMANIFEST FAIL: artifact diverges from committed manifest.\n`);
  if (added.length) { process.stderr.write(`  added (${added.length}):\n`); for (const a of added.slice(0, 20)) process.stderr.write(`    + ${a}\n`); if (added.length > 20) process.stderr.write(`    ...+${added.length - 20} more\n`); }
  if (removed.length) { process.stderr.write(`  removed (${removed.length}):\n`); for (const r of removed.slice(0, 20)) process.stderr.write(`    - ${r}\n`); if (removed.length > 20) process.stderr.write(`    ...-${removed.length - 20} more\n`); }
  if (changed.length) { process.stderr.write(`  changed (${changed.length}):\n`); for (const c of changed.slice(0, 20)) process.stderr.write(`    ~ ${c.k}\n      was ${c.was.sha.slice(0, 12)}.. (${c.was.size}b), now ${c.now.sha.slice(0, 12)}.. (${c.now.size}b)\n`); if (changed.length > 20) process.stderr.write(`    ...~${changed.length - 20} more\n`); }
  process.stderr.write('\nIf the divergence is intentional, re-run with --write and commit the new manifest.\n');
  process.exit(1);
}

main();
