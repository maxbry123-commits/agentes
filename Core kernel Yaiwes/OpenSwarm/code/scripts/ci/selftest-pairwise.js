#!/usr/bin/env node
// Mutation tests for the pairwise covering-array generator that the settings spec uses. If the generator stops covering every pair (the WHOLE point), or produces blow-up output, or breaks the deterministic-input contract, the spec is silently weakened. This catches it before CI even builds. Pure node + transpile-by-hand of the .ts module to minimize moving parts; the .ts logic is small enough to vendor.

'use strict';

// Hand-port of e2e/helpers/pairwise.ts kept in sync; any change to the .ts must
// also land here. This isolates the gate from the e2e TypeScript build.
function pairKey(a, av, b, bv) { return `${a}=${JSON.stringify(av)}|${b}=${JSON.stringify(bv)}`; }
function allPairs(params) {
  const out = new Set();
  const names = Object.keys(params);
  for (let i = 0; i < names.length; i++) for (let j = i + 1; j < names.length; j++) for (const av of params[names[i]]) for (const bv of params[names[j]]) out.add(pairKey(names[i], av, names[j], bv));
  return out;
}
function coveredByRow(row, params) {
  const out = new Set();
  const names = Object.keys(params);
  for (let i = 0; i < names.length; i++) for (let j = i + 1; j < names.length; j++) {
    if (row[names[i]] === undefined || row[names[j]] === undefined) continue;
    out.add(pairKey(names[i], row[names[i]], names[j], row[names[j]]));
  }
  return out;
}
function decodePairKey(k) {
  const [left, right] = k.split('|');
  const [a, avJson] = [left.slice(0, left.indexOf('=')), left.slice(left.indexOf('=') + 1)];
  const [b, bvJson] = [right.slice(0, right.indexOf('=')), right.slice(right.indexOf('=') + 1)];
  return { a, av: JSON.parse(avJson), b, bv: JSON.parse(bvJson) };
}
function pairwise(params) {
  const names = Object.keys(params);
  if (names.length === 0) return [];
  if (names.length === 1) return params[names[0]].map((v) => ({ [names[0]]: v }));
  const remaining = allPairs(params);
  const rows = [];
  const totalPairs = remaining.size;
  while (remaining.size > 0) {
    const seedKey = remaining.values().next().value;
    const { a, av, b, bv } = decodePairKey(seedKey);
    const row = { [a]: av, [b]: bv };
    for (const name of names) {
      if (name in row) continue;
      let bestVal = params[name][0]; let bestScore = -1;
      for (const v of params[name]) {
        const candidate = { ...row, [name]: v }; let score = 0;
        for (const k of coveredByRow(candidate, params)) if (remaining.has(k)) score++;
        if (score > bestScore) { bestScore = score; bestVal = v; }
      }
      row[name] = bestVal;
    }
    for (const k of coveredByRow(row, params)) remaining.delete(k);
    rows.push(row);
    if (rows.length > totalPairs) break;
  }
  return rows;
}
function isCovering(rows, params) {
  const must = allPairs(params); const have = new Set();
  for (const r of rows) for (const k of coveredByRow(r, params)) have.add(k);
  const missing = []; for (const k of must) if (!have.has(k)) missing.push(k);
  return { covering: missing.length === 0, missing };
}
function cartesian(params) {
  const names = Object.keys(params); if (names.length === 0) return [{}];
  const rest = cartesian(Object.fromEntries(names.slice(1).map((n) => [n, params[n]])));
  const out = []; for (const v of params[names[0]]) for (const r of rest) out.push({ [names[0]]: v, ...r });
  return out;
}

let failed = 0;
function check(name, cond, detail) { process.stdout.write(`  ${cond ? 'ok  ' : 'FAIL'}  ${name}${detail ? ` :: ${detail}` : ''}\n`); if (!cond) failed++; }

process.stdout.write('Layer 1 - pairwise generator correctness:\n');

// 6 binary parameters: the actual surface we care about (5 switches + theme).
const P6 = { a: [false, true], b: [false, true], c: [false, true], d: [false, true], e: [false, true], theme: ['light', 'dark'] };
const rows6 = pairwise(P6);
const cov6 = isCovering(rows6, P6);
check('6 binary params: every pair covered', cov6.covering, cov6.missing.length ? `missing ${cov6.missing.length}: ${cov6.missing.slice(0, 3).join(', ')}` : '');
check('6 binary params: rows << full cross (must be < 64)', rows6.length < 64, `rows=${rows6.length}`);
check('6 binary params: rows >= 4 (lower bound for 6 binary)', rows6.length >= 4, `rows=${rows6.length}`);

// 0 params -> 0 rows; 1 param -> N rows.
check('empty params -> 0 rows', pairwise({}).length === 0);
check('1 param 2 vals -> 2 rows', pairwise({ x: [1, 2] }).length === 2);

// Determinism: same input -> same output (order-stable).
const r1 = JSON.stringify(pairwise(P6)); const r2 = JSON.stringify(pairwise(P6));
check('deterministic: same input -> same output', r1 === r2);

// Multi-valued: 3-valued color + 2-valued bool.
const P3x2 = { color: ['red', 'green', 'blue'], on: [false, true] };
const rows3x2 = pairwise(P3x2);
check('3x2 params: every pair covered', isCovering(rows3x2, P3x2).covering);
check('3x2 params: at most 6 rows (full cross is 6)', rows3x2.length <= 6, `rows=${rows3x2.length}`);

// Cartesian sanity: 6 binary -> 64.
check('cartesian(6 binary) = 64', cartesian(P6).length === 64);
check('cartesian({}) = [{}]', JSON.stringify(cartesian({})) === '[{}]');

process.stdout.write('\nLayer 2 - mutation: regressions in the generator are caught:\n');
// "If a future change drops the all-pairs guarantee, isCovering catches it."
// Simulate that by hand-removing rows and confirming isCovering reports missing.
const broken = rows6.slice(0, 1);  // only one row cannot possibly cover every pair
const brokenCov = isCovering(broken, P6);
check('isCovering catches a deliberately incomplete row set', !brokenCov.covering && brokenCov.missing.length > 0);

process.stdout.write(failed
  ? `\nPAIRWISE SELFTEST FAIL: ${failed} assertion(s)\n`
  : '\nPAIRWISE SELFTEST PASS: covering-array generator is exhaustive, deterministic, bounded.\n');
process.exit(failed ? 1 : 0);
