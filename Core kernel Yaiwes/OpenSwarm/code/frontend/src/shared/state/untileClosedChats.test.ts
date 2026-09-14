// Run: node --test frontend/src/shared/state/untileClosedChats.test.ts
import { test } from 'node:test';
import assert from 'node:assert/strict';
import { untileClosedChats } from './untileClosedChats.ts';

test('collapsing one chat drops that chat tile and nothing else', () => {
  const tiled: Record<string, string> = { a: 'left', b: 'fullscreen' };
  untileClosedChats(tiled, ['a'], []);
  assert.deepEqual(tiled, { b: 'fullscreen' });
});

test('restoring a saved expansion list untiles every chat missing from it', () => {
  const tiled: Record<string, string> = { a: 'left', b: 'fullscreen', c: 'right' };
  untileClosedChats(tiled, ['a', 'b', 'c'], ['b']);
  assert.deepEqual(tiled, { b: 'fullscreen' });
});

test('non-chat tiles (browsers, apps, windows) are never touched', () => {
  const tiled: Record<string, string> = { chat: 'left', 'browser-1': 'right' };
  untileClosedChats(tiled, ['chat'], []);
  assert.deepEqual(tiled, { 'browser-1': 'right' });
});

test('an open chat keeps its tile', () => {
  const tiled: Record<string, string> = { a: 'fullscreen' };
  untileClosedChats(tiled, ['a'], ['a']);
  assert.deepEqual(tiled, { a: 'fullscreen' });
});
