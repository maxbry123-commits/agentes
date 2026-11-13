// Run: node --test frontend/src/shared/browserSettle.test.ts
import { test } from 'node:test';
import assert from 'node:assert/strict';
import { shouldStopWaiting, SETTLE_FLOOR_MS, SETTLE_QUIET_MS } from './browserSettle.ts';

test('does not settle before the floor, even when fully quiet', () => {
  assert.equal(shouldStopWaiting(true, 5000, 5000, false, SETTLE_FLOOR_MS - 1), false);
});

test('settles past the floor when the network is quiet', () => {
  assert.equal(shouldStopWaiting(true, SETTLE_QUIET_MS, 0, false, SETTLE_FLOOR_MS), true);
});

test('settles past the floor on DOM-stable even when the network never idles', () => {
  assert.equal(shouldStopWaiting(true, 5, SETTLE_QUIET_MS, false, 1000), true);
});

test('target found short-circuits the floor and a busy network', () => {
  assert.equal(shouldStopWaiting(false, 0, 0, true, 10), true);
});

test('does not settle while the document is still loading', () => {
  assert.equal(shouldStopWaiting(false, 5000, 5000, false, 1000), false);
});

test('does not settle when neither network nor DOM has been quiet long enough', () => {
  assert.equal(shouldStopWaiting(true, SETTLE_QUIET_MS - 1, SETTLE_QUIET_MS - 1, false, 1000), false);
});

test('missing signals are treated as not-quiet, not as settled', () => {
  assert.equal(
    shouldStopWaiting(true, undefined as unknown as number, undefined as unknown as number, false, 1000),
    false,
  );
});
