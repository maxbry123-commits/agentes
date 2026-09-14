#!/usr/bin/env node
// Verifies that the Windows and macOS build scripts stage the SAME set of source directories under electron/build-staging/ and that electron/package.json's extraResources lists each as a `from` source. A drift here means one OS ships a directory the other doesn't, which is the classic cross-platform "works on my machine" leak.

'use strict';
const fs = require('fs');
const path = require('path');
const h = require('./lib/app-harness');

const winScript = path.join(h.REPO_ROOT, 'scripts', 'build-app-win.ps1');
const macScript = path.join(h.REPO_ROOT, 'scripts', 'build-app.sh');
const pkgJson = path.join(h.REPO_ROOT, 'electron', 'package.json');

// Pull every literal that mentions a dir under the staging root. Bash uses
// $STAGING_DIR/<name>, PowerShell uses $Staging\<name> or $Staging/<name>,
// and either may write the literal build-staging/<name>.
function extractStagingDirs(text) {
  const dirs = new Set();
  const patterns = [
    // bash: $STAGING_DIR/<name>
    /\$STAGING_DIR[\\/](?<name>[a-zA-Z0-9._-]+)/g,
    // PowerShell: Join-Path $Staging '<name>...' or "<name>..."
    /Join-Path\s+\$Staging\s+['"](?<name>[a-zA-Z0-9._-]+)/g,
    // either: literal build-staging/<name>
    /build-staging[\\/](?<name>[a-zA-Z0-9._-]+)/g,
  ];
  for (const re of patterns) { let m; while ((m = re.exec(text))) if (m.groups.name) dirs.add(m.groups.name); }
  // node directories on both platforms have an arch subdir; normalize.
  if (dirs.has('node')) {
    /* keep `node` as the canonical entry */
  }
  return Array.from(dirs).sort();
}

function extractExtraResourceFroms(pkg) {
  const list = ((pkg.build || {}).extraResources) || [];
  return list.map((e) => e.from).filter(Boolean);
}

function main() {
  const winText = fs.readFileSync(winScript, 'utf8');
  const macText = fs.readFileSync(macScript, 'utf8');
  const pkg = JSON.parse(fs.readFileSync(pkgJson, 'utf8'));
  const winDirs = extractStagingDirs(winText);
  const macDirs = extractStagingDirs(macText);
  const resFroms = extractExtraResourceFroms(pkg);

  process.stdout.write(`Win build-staging dirs : ${winDirs.join(', ')}\n`);
  process.stdout.write(`Mac build-staging dirs : ${macDirs.join(', ')}\n`);
  process.stdout.write(`extraResources from[]  : ${resFroms.join(', ')}\n`);

  // Find directories one script stages that the other doesn't. Document
  // known-intentional differences in EXCEPTIONS; everything else fails.
  const EXCEPTIONS = new Set([
    // Mac-only: webapp-template node_modules archive (build script step 3c). Not yet shipped on Win.
    'webapp-template-node-modules',
  ]);
  const onlyWin = winDirs.filter((d) => !macDirs.includes(d) && !EXCEPTIONS.has(d));
  const onlyMac = macDirs.filter((d) => !winDirs.includes(d) && !EXCEPTIONS.has(d));

  let failed = 0;
  if (onlyWin.length) { process.stderr.write(`  FAIL  staged on Win but not Mac: ${onlyWin.join(', ')}\n`); failed++; }
  if (onlyMac.length) { process.stderr.write(`  FAIL  staged on Mac but not Win: ${onlyMac.join(', ')}\n`); failed++; }
  if (failed === 0) process.stdout.write('  ok   both build scripts stage the same set of source dirs (modulo documented exceptions)\n');

  // Every extraResource from path that references build-staging/X must have X
  // in the union of staged dirs from both scripts. Otherwise electron-builder
  // would fail at package time on one OS but green on the other.
  const stagingResources = resFroms.filter((p) => /^build-staging[\\/]/.test(p));
  for (const r of stagingResources) {
    const sub = r.split(/[\\/]/)[1].replace(/\$\{arch\}/g, ''); // strip arch templating
    const presentBoth = winDirs.includes(sub) && macDirs.includes(sub);
    const presentExcept = EXCEPTIONS.has(sub);
    if (!presentBoth && !presentExcept) {
      process.stderr.write(`  FAIL  extraResources from ${r} - "${sub}" not staged by both scripts\n`);
      failed++;
    } else {
      process.stdout.write(`  ok   extraResources from ${r}\n`);
    }
  }

  if (failed) { process.stderr.write(`\nPACKAGING-PARITY FAIL: ${failed} divergence(s) between build-app.sh and build-app-win.ps1.\n`); process.exit(1); }
  process.stdout.write('\nPACKAGING-PARITY PASS: Mac and Win build the same staged tree (modulo documented exceptions).\n');
  process.exit(0);
}

main();
