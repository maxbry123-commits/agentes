// Run: node --test frontend/src/app/pages/Dashboard/hooks/lifecycle/orphanViewCardKeys.test.ts
import { test } from 'node:test';
import assert from 'node:assert/strict';
import { orphanViewCardKeys } from './orphanViewCardKeys.ts';

const app = { id: 'app1', name: 'Calculator' };

test('a live app keeps its primary card', () => {
  const cards = { app1: { output_id: 'app1' } };
  assert.deepEqual(orphanViewCardKeys(cards, { app1: app }), []);
});

test('a second instance of a live app is not an orphan', () => {
  const cards = { app1: { output_id: 'app1' }, 'app1#2': { output_id: 'app1' } };
  assert.deepEqual(orphanViewCardKeys(cards, { app1: app }), []);
});

test('deleting the app orphans every instance of it', () => {
  const cards = {
    app1: { output_id: 'app1' },
    'app1#2': { output_id: 'app1' },
    'app1#3': { output_id: 'app1' },
  };
  assert.deepEqual(orphanViewCardKeys(cards, {}), ['app1', 'app1#2', 'app1#3']);
});

test('one deleted app does not take a surviving app down with it', () => {
  const cards = {
    app1: { output_id: 'app1' },
    'app1#2': { output_id: 'app1' },
    app2: { output_id: 'app2' },
  };
  assert.deepEqual(orphanViewCardKeys(cards, { app2: { id: 'app2' } }), ['app1', 'app1#2']);
});

test('no cards means nothing to prune', () => {
  assert.deepEqual(orphanViewCardKeys({}, { app1: app }), []);
});
