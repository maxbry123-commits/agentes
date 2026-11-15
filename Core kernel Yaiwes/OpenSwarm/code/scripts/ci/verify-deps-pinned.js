#!/usr/bin/env node
// Audits backend/requirements.txt for fully-pinned versions. Header comment says reproducible builds, so any "no-version" or ">=" entry means two builds from the same git sha could resolve different package versions - the classic invisible "works on my machine" drift.

'use strict';
const fs = require('fs');
const path = require('path');
const h = require('./lib/app-harness');

const REQ_FILE = path.join(h.REPO_ROOT, 'backend', 'requirements.txt');

function parseRequirements(text) {
  const items = [];
  for (let raw of text.split(/\r?\n/)) {
    const line = raw.replace(/#.*$/, '').trim();
    if (!line) continue;
    if (/^-r\s/.test(line)) continue;             // file include, treated separately
    if (/^(--|-)/.test(line)) continue;           // pip flags
    items.push(line);
  }
  return items;
}

// A line is "fully pinned" if it carries an exact-version operator (==) OR
// a hash-pinned wheel via --hash (treated as canonical pin). Floors (>=, ~=,
// >, <, <=) and bare names all FAIL because they leave room for drift.
function isFullyPinned(line) {
  if (line.includes('==')) return true;
  if (line.includes(' --hash=')) return true;
  return false;
}

module.exports = { parseRequirements, isFullyPinned };

function main() {
  const text = fs.readFileSync(REQ_FILE, 'utf8');
  const reqs = parseRequirements(text);
  const unpinned = reqs.filter((r) => !isFullyPinned(r));

  process.stdout.write(`Audit: ${REQ_FILE}\n`);
  process.stdout.write(`  ${reqs.length} requirement(s) parsed, ${reqs.length - unpinned.length} fully pinned\n`);

  if (unpinned.length === 0) {
    process.stdout.write('\nDEPS-PINNED PASS: every backend requirement is exact-version (==X.Y.Z) or hash-pinned.\n');
    process.exit(0);
  }

  process.stderr.write(`\nDEPS-PINNED FAIL: ${unpinned.length} requirement(s) are NOT fully pinned:\n`);
  for (const r of unpinned) process.stderr.write(`  - ${r}\n`);
  process.stderr.write('\nThe header of requirements.txt promises reproducible builds, but pip will resolve these\n');
  process.stderr.write('to latest-matching at install time, so a build on Monday can ship different bytes than\n');
  process.stderr.write('Tuesday from the same git sha. Pin to ==X.Y.Z (run `pip freeze` against the working env\n');
  process.stderr.write('to capture the current resolved versions, then commit them).\n');
  process.exit(1);
}

if (require.main === module) main();
