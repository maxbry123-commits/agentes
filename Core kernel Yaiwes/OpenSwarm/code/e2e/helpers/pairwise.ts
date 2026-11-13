// Pairwise (all-pairs) covering array generator. For N binary parameters, the
// full cross is 2^N; pairwise guarantees every (param_i = v_a, param_j = v_b)
// combination appears in at least one test row while typically using O(N log N)
// rows. Greedy in-parameter-order algorithm: build rows one at a time, for each
// row pick values that cover the most uncovered pairs.
//
// Output rows are deterministic for a given (paramNames, values) input. Pure
// function so the spec's selftest can mutation-check it without touching the
// DOM or running Playwright.

export type Params = Record<string, ReadonlyArray<unknown>>;
export type Row = Record<string, unknown>;

function pairKey(a: string, av: unknown, b: string, bv: unknown): string {
  return `${a}=${JSON.stringify(av)}|${b}=${JSON.stringify(bv)}`;
}

function allPairs(params: Params): Set<string> {
  const out = new Set<string>();
  const names = Object.keys(params);
  for (let i = 0; i < names.length; i++) {
    for (let j = i + 1; j < names.length; j++) {
      for (const av of params[names[i]]) for (const bv of params[names[j]]) out.add(pairKey(names[i], av, names[j], bv));
    }
  }
  return out;
}

function coveredByRow(row: Row, params: Params): Set<string> {
  const out = new Set<string>();
  const names = Object.keys(params);
  for (let i = 0; i < names.length; i++) {
    for (let j = i + 1; j < names.length; j++) {
      if (row[names[i]] === undefined || row[names[j]] === undefined) continue;
      out.add(pairKey(names[i], row[names[i]], names[j], row[names[j]]));
    }
  }
  return out;
}

// IPO-style all-pairs generator: each row is SEEDED from an uncovered pair so
// every row makes progress (a pure greedy without seeding never explores the
// non-default branch when ties default to first-value). Then fill remaining
// parameters greedily to maximize newly-covered pairs.
function decodePairKey(k: string): { a: string; av: unknown; b: string; bv: unknown } {
  const [left, right] = k.split('|');
  const [a, avJson] = [left.slice(0, left.indexOf('=')), left.slice(left.indexOf('=') + 1)];
  const [b, bvJson] = [right.slice(0, right.indexOf('=')), right.slice(right.indexOf('=') + 1)];
  return { a, av: JSON.parse(avJson), b, bv: JSON.parse(bvJson) };
}

export function pairwise(params: Params): Row[] {
  const names = Object.keys(params);
  if (names.length === 0) return [];
  if (names.length === 1) return params[names[0]].map((v) => ({ [names[0]]: v }));

  const remaining = allPairs(params);
  const rows: Row[] = [];
  const totalPairs = remaining.size;

  while (remaining.size > 0) {
    // Seed: take any still-uncovered pair and lock those two parameters first.
    const seedKey = remaining.values().next().value!;
    const { a, av, b, bv } = decodePairKey(seedKey);
    const row: Row = { [a]: av, [b]: bv };
    // Fill the rest greedily.
    for (const name of names) {
      if (name in row) continue;
      let bestVal: unknown = params[name][0];
      let bestScore = -1;
      for (const v of params[name]) {
        const candidate: Row = { ...row, [name]: v };
        let score = 0;
        for (const k of coveredByRow(candidate, params)) if (remaining.has(k)) score++;
        if (score > bestScore) { bestScore = score; bestVal = v; }
      }
      row[name] = bestVal;
    }
    for (const k of coveredByRow(row, params)) remaining.delete(k);
    rows.push(row);
    if (rows.length > totalPairs) break;   // safety; should never reach
  }
  return rows;
}

// Helper for tests: returns true iff every cross-pair is covered by at least one row.
export function isCovering(rows: Row[], params: Params): { covering: boolean; missing: string[] } {
  const must = allPairs(params);
  const have = new Set<string>();
  for (const r of rows) for (const k of coveredByRow(r, params)) have.add(k);
  const missing: string[] = [];
  for (const k of must) if (!have.has(k)) missing.push(k);
  return { covering: missing.length === 0, missing };
}

// Full Cartesian product, exposed for opt-in exhaustive mode.
export function cartesian(params: Params): Row[] {
  const names = Object.keys(params);
  if (names.length === 0) return [{}];
  const rest = cartesian(Object.fromEntries(names.slice(1).map((n) => [n, params[n]])) as Params);
  const out: Row[] = [];
  for (const v of params[names[0]]) for (const r of rest) out.push({ [names[0]]: v, ...r });
  return out;
}
