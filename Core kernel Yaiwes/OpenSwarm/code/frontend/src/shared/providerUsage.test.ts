// Run: node --test frontend/src/shared/providerUsage.test.ts
import { test } from 'node:test';
import assert from 'node:assert/strict';
import { summarizeUsage, type ProviderUsage } from './providerUsage.ts';

test('failed or null read yields empty summary', () => {
  assert.equal(summarizeUsage(null), '');
  assert.equal(summarizeUsage({ ok: false, total: 0, titles: [], memories: [] }), '');
});

test('summary leads with memory, names scale, and lists recent topics', () => {
  const u: ProviderUsage = {
    ok: true,
    total: 812,
    titles: ['Swift concurrency', 'Deadlift form check', 'Tax on RSUs'],
    memories: ['Has an Akita', 'Squats 495'],
  };
  const s = summarizeUsage(u);
  assert.match(s, /812 past AI conversations/);
  assert.match(s, /Has an Akita; Squats 495/);
  assert.match(s, /Swift concurrency; Deadlift form check; Tax on RSUs/);
});

test('titles are capped at 150 for breadth, so a heavy user ships a sample not all of them', () => {
  const titles = Array.from({ length: 1000 }, (_, i) => `conversation number ${i} about a very specific topic`);
  const s = summarizeUsage({ ok: true, total: 1000, capped: true, titles, memories: [] });
  assert.match(s, /1000\+ past AI conversations/); // capped => count is shown as an honest "N+" floor
  assert.ok(s.includes('conversation number 0'));
  assert.ok(s.includes('conversation number 149'));
  assert.ok(!s.includes('conversation number 150'), 'only the first 150 titles ship');
});

test('the full-convo payload (the real substance) is bounded by the char budget', () => {
  const convos = Array.from({ length: 60 }, (_, i) => ({ title: `t${i}`, text: 'x'.repeat(5000) }));
  const s = summarizeUsage({ ok: true, total: 60, titles: [], memories: [], convos });
  // Full recent-conversation text is intentionally large (distilled downstream), but never unbounded.
  assert.ok(s.length <= 140000, `convo block should honor the ~130K budget, got ${s.length}`);
});
