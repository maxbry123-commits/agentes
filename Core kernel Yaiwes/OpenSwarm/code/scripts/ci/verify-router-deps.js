#!/usr/bin/env node
// Guards the "subscription service hangs forever" failure. The bundled 9Router is
// a Next.js standalone server whose server.js does require('next'), so it needs
// router/node_modules (and router/.next) present in the packaged app. electron-
// builder 26 special-excludes node_modules from extraResources (25 did not), and
// drops the .next dotdir unless the filter opts dotfiles in - either way the
// router dies with "Cannot find module 'next'", 9Router never binds :20128, and
// the Models tab spins on "Starting subscription service..." indefinitely. Assert
// the deps are actually in the package.

'use strict';
const fs = require('fs');
const path = require('path');
const h = require('./lib/app-harness');

function parseArgs(argv) {
  const out = { app: null };
  for (let i = 0; i < argv.length; i++) if (argv[i] === '--app') out.app = argv[++i];
  return out;
}

function routerDir(exe) {
  if (process.platform === 'darwin') {
    const appRoot = exe.slice(0, exe.indexOf('.app') + 4);
    return path.join(appRoot, 'Contents', 'Resources', 'router');
  }
  return path.join(path.dirname(exe), 'resources', 'router');
}

function main() {
  const args = parseArgs(process.argv.slice(2));
  const exe = h.packagedAppPath(args.app);
  const dir = routerDir(exe);
  const checks = {
    'server.js': path.join(dir, 'server.js'),
    'node_modules/next': path.join(dir, 'node_modules', 'next'),
    '.next': path.join(dir, '.next'),
  };
  const missing = [];
  for (const [label, p] of Object.entries(checks)) {
    const ok = fs.existsSync(p);
    process.stdout.write(`  ${ok ? 'ok ' : 'MISSING'}  ${label}\n`);
    if (!ok) missing.push(label);
  }
  if (missing.length === 0) {
    process.stdout.write(`PASS  9Router deps present in ${dir}\n`);
    process.exit(0);
  }
  process.stderr.write(
    `FAIL  bundled 9Router is missing ${missing.join(', ')} in ${dir}\n` +
    `      server.js does require('next'); without node_modules/.next the 9Router\n` +
    `      never starts, port 20128 stays dead, and the subscription service hangs.\n` +
    `      Fix: ensure the build copies router/node_modules + .next into the package\n` +
    `      (electron-builder 26 drops node_modules from extraResources; build-app-win.ps1\n` +
    `      copies it back post-build, and the package.json filter opts the .next dotdir in).\n`);
  process.exit(1);
}

main();
