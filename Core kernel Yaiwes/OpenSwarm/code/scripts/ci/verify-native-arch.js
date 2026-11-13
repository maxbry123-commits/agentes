#!/usr/bin/env node
// Guards against shipping a native module built for the WRONG architecture.
// prebuildify packages (uiohook-napi, the dictation hotkey tap) ship one .node per platform+arch
// they support: seven dirs, of which exactly one is ours. Six are dead weight, and on macOS an
// x86_64 Mach-O inside an arm64 bundle is what makes the OS raise its Intel-deprecation dialog at
// the user. electron/build/after-pack.js prunes them; this asserts the prune actually happened,
// because an afterPack hook that silently no-ops (layout changed, module moved into the asar) would
// otherwise ship the same bundle it always did with nobody the wiser.

'use strict';
const fs = require('fs');
const path = require('path');
const { execFileSync } = require('child_process');
const h = require('./lib/app-harness');

function parseArgs(argv) {
  const out = { app: null };
  for (let i = 0; i < argv.length; i++) if (argv[i] === '--app') out.app = argv[++i];
  return out;
}

function findNodeFiles(root) {
  const found = [];
  (function walk(dir, depth) {
    if (depth > 14) return;
    let ents = [];
    try { ents = fs.readdirSync(dir, { withFileTypes: true }); } catch { return; }
    for (const e of ents) {
      const full = path.join(dir, e.name);
      if (e.isDirectory()) walk(full, depth + 1);
      else if (e.isFile() && e.name.endsWith('.node')) found.push(full);
    }
  })(root, 0);
  return found;
}

// `file` names every slice in a Mach-O, so a fat binary reports both and a wrong-arch one reports
// only the wrong slice. On Windows/Linux there is no equivalent worth the dependency, so the gate
// there just asserts no foreign prebuild DIRS survived.
function machoArches(file) {
  try {
    return execFileSync('file', [file], { encoding: 'utf8' }).trim();
  } catch (err) {
    return `file failed: ${err && err.message}`;
  }
}

function main() {
  const args = parseArgs(process.argv.slice(2));
  const exe = h.packagedAppPath(args.app);
  const root = process.platform === 'darwin' ? exe.slice(0, exe.indexOf('.app') + 4) : path.dirname(exe);
  const want = process.arch === 'arm64' ? 'arm64' : 'x86_64';

  const nodes = findNodeFiles(root);
  process.stdout.write(`  ${nodes.length} .node file(s) under ${path.basename(root)}\n`);

  const offenders = [];
  for (const n of nodes) {
    // A prebuilds dir for another OS is wrong no matter what `file` says about it.
    const tuple = path.basename(path.dirname(n));
    const platformOk = !tuple.includes('-') || tuple.startsWith(process.platform);
    const desc = process.platform === 'darwin' ? machoArches(n) : '';
    const archOk = process.platform !== 'darwin' || desc.includes(want);
    if (!platformOk || !archOk) offenders.push(`${path.relative(root, n)}  [${tuple}]  ${desc.split(':').slice(1).join(':').trim()}`);
  }

  if (!offenders.length) {
    process.stdout.write(`PASS  every bundled .node targets ${process.platform}/${want}\n`);
    process.exit(0);
  }
  process.stderr.write(
    `FAIL  packaged build ships ${offenders.length} native module(s) for the WRONG target:\n` +
    offenders.map((o) => `      ${o}\n`).join('') +
    `      An x86_64 .node inside an arm64 bundle makes macOS show its Intel-deprecation\n` +
    `      dialog, and every foreign prebuild is dead weight the user downloads.\n` +
    `      Fix: electron/build/after-pack.js pruneForeignPrebuilds() should have deleted these.\n` +
    `      If they now live inside app.asar rather than app.asar.unpacked, the prune needs to\n` +
    `      run before the asar is built (beforePack) instead.\n`);
  process.exit(1);
}

main();
