// Run: npx tsx --test frontend/src/toolui/parseLeniently.test.ts
// Every case here is a payload shape a real agent emitted (Eric's 2026-08-09 console capture):
// widgets users should see were quietly falling back to classic rendering.
import { test } from 'node:test';
import assert from 'node:assert/strict';
import { parseLeniently } from './parseLeniently.ts';
import { SerializableStatsDisplaySchema } from './components/stats-display/schema.ts';
import { SerializableProgressTrackerSchema } from './components/progress-tracker/schema.ts';
import { SerializableDataTableSchema } from './components/data-table/schema.ts';

test('stats-display: missing key and stringy diff.value repair to a valid payload', () => {
  const gate = parseLeniently(SerializableStatsDisplaySchema, {
    id: 'revenue-stats',
    stats: [
      { label: 'Revenue', value: 1204, diff: { value: '+12%' } },
      { label: 'Churn', value: '2.1%', diff: '-0.4' },
    ],
  });
  assert.equal(gate.state, 'ok');
  const stats = (gate as { parsed: { stats: Array<Record<string, unknown>> } }).parsed.stats;
  assert.equal(stats[0].key, 'revenue');
  assert.deepEqual(stats[0].diff, { value: 12 });
  assert.deepEqual(stats[1].diff, { value: -0.4 });
});

test('progress-tracker: missing step ids, duplicate labels, underscore statuses all repair', () => {
  const gate = parseLeniently(SerializableProgressTrackerSchema, {
    id: 'deploy-progress',
    steps: [
      { label: 'Build', status: 'completed' },
      { label: 'Test', status: 'in_progress' },
      { label: 'Test', status: 'pending' },
    ],
  });
  assert.equal(gate.state, 'ok');
  const steps = (gate as { parsed: { steps: Array<Record<string, unknown>> } }).parsed.steps;
  assert.deepEqual(steps.map((s) => s.status), ['completed', 'in-progress', 'pending']);
  assert.equal(new Set(steps.map((s) => s.id)).size, 3);
});

test('extra invented top-level keys AND repairable steps in the same payload still pass', () => {
  const gate = parseLeniently(SerializableProgressTrackerSchema, {
    id: 'combo',
    caption: 'invented key the schema rejects',
    steps: [{ label: 'Only step', status: 'done' }],
  });
  assert.equal(gate.state, 'ok');
});

test('data-table: a non-ISO receipt.at coerces to ISO; an unparseable one costs only the receipt', () => {
  const base = {
    id: 'orders',
    columns: [{ key: 'name', label: 'Name' }],
    data: [{ name: 'Widget' }],
  };
  const coerced = parseLeniently(SerializableDataTableSchema, {
    ...base,
    receipt: { outcome: 'confirmed', summary: 'ok', at: '2026-08-08 14:30' },
  });
  assert.equal(coerced.state, 'ok');
  const rec = (coerced as { parsed: { receipt: { at: string; outcome: string } } }).parsed.receipt;
  assert.ok(rec.at.endsWith('Z') && !Number.isNaN(Date.parse(rec.at)));
  assert.equal(rec.outcome, 'success');
  const dropped = parseLeniently(SerializableDataTableSchema, {
    ...base,
    receipt: { outcome: 'confirmed', summary: 'ok', at: 'yesterday-ish' },
  });
  assert.equal(dropped.state, 'ok');
  assert.equal((dropped as { parsed: Record<string, unknown> }).parsed.receipt, undefined);
});

test('a valid payload passes through byte-identical, no repair applied', () => {
  const payload = {
    id: 'clean',
    stats: [{ key: 'a', label: 'A', value: 1, diff: { value: 2 } }],
  };
  const gate = parseLeniently(SerializableStatsDisplaySchema, payload);
  assert.equal(gate.state, 'ok');
  assert.deepEqual((gate as { parsed: Record<string, unknown> }).parsed.stats, payload.stats);
});

test('a genuinely wrong shape still fails loudly with a readable problem', () => {
  const gate = parseLeniently(SerializableStatsDisplaySchema, { id: 'nope', stats: [] });
  assert.equal(gate.state, 'bad');
  assert.ok((gate as { problem: string }).problem.length > 0);
});
