// Run: node --test frontend/src/shared/typeChars.test.ts
import { test } from 'node:test';
import assert from 'node:assert/strict';
import { typeChars } from './typeChars.ts';
import type { CdpDispatch } from './typeChars.ts';

interface Call { method: string; params: Record<string, any> }

function recorder(): { calls: Call[]; dispatch: CdpDispatch } {
  const calls: Call[] = [];
  const dispatch: CdpDispatch = async (method, params) => {
    calls.push({ method, params: params as Record<string, any> });
    return {};
  };
  return { calls, dispatch };
}

test('every character goes out as a CDP keyDown then keyUp, in order', async () => {
  const { calls, dispatch } = recorder();
  const r = await typeChars(dispatch, 'hi');
  assert.deepEqual(r, { dispatched: true, skipped: '' });
  assert.equal(calls.length, 4);
  assert.deepEqual(calls.map((c) => c.params.type), ['keyDown', 'keyUp', 'keyDown', 'keyUp']);
  assert.deepEqual(calls.map((c) => c.params.key), ['h', 'h', 'i', 'i']);
});

test('the transport is CDP, never Electron sendInputEvent', async () => {
  // The whole point of this module. sendInputEvent goes to whatever the OS thinks has focus, which
  // is how the agent once typed into the user's notes app, and it is unawaitable, which is why the
  // read-back after it always lost the race. If this ever regresses, the fill tier goes dead silent
  // again: it fails with "did not register even as real keystrokes" and nobody sees a reason.
  const { calls, dispatch } = recorder();
  await typeChars(dispatch, 'abc');
  assert.ok(calls.length > 0);
  assert.ok(calls.every((c) => c.method === 'Input.dispatchKeyEvent'), 'every event must go over CDP');
});

test('each dispatch is awaited, so a read-back after this cannot outrun the text', async () => {
  // A fire-and-forget loop would let a slow first character land after a fast last one. Resolve in
  // reverse-latency order and check the sequence still comes out forward.
  const seen: string[] = [];
  let delay = 30;
  const dispatch: CdpDispatch = async (_m, params) => {
    const wait = (delay -= 5);
    await new Promise((res) => setTimeout(res, Math.max(0, wait)));
    if (params.type === 'keyDown') seen.push(String(params.key));
    return {};
  };
  await typeChars(dispatch, 'abc');
  assert.deepEqual(seen, ['a', 'b', 'c']);
});

test('only the keyDown carries text, or every character types twice', async () => {
  const { calls, dispatch } = recorder();
  await typeChars(dispatch, 'x');
  const [down, up] = calls;
  assert.equal(down.params.text, 'x');
  assert.equal(down.params.unmodifiedText, 'x');
  assert.equal(up.params.text, undefined);
});

test('letters, digits, space and punctuation get the right code and key code', async () => {
  const { calls, dispatch } = recorder();
  await typeChars(dispatch, 'a7 !');
  const downs = calls.filter((c) => c.params.type === 'keyDown');
  assert.deepEqual(downs.map((c) => c.params.code), ['KeyA', 'Digit7', 'Space', undefined]);
  assert.deepEqual(downs.map((c) => c.params.windowsVirtualKeyCode), [65, 55, 32, 33]);
});

test('multi-line text dispatches NOTHING, because Enter in a composer sends the message', async () => {
  const { calls, dispatch } = recorder();
  for (const text of ['line one\nline two', 'trailing\n', 'carriage\rreturn']) {
    assert.deepEqual(await typeChars(dispatch, text), { dispatched: false, skipped: 'multiline' });
  }
  assert.equal(calls.length, 0, 'a refused fill must not type a partial draft');
});

test('empty text is a no-op, not an empty keystroke', async () => {
  const { calls, dispatch } = recorder();
  assert.deepEqual(await typeChars(dispatch, ''), { dispatched: false, skipped: 'empty' });
  assert.equal(calls.length, 0);
});

test('a strict editor that ignores synthetic input still receives the whole string', async () => {
  // Twitch's chat box, Reddit's Lexical, and X's composer are this shape: they own their state and
  // commit only on a real key event, dropping Input.insertText and execCommand on the floor. This
  // is the case the fill ladder's third tier exists for, and the case it silently failed for as
  // long as it used sendInputEvent. The model below accepts nothing else on purpose.
  let value = '';
  const strictEditor: CdpDispatch = async (method, params) => {
    if (method === 'Input.insertText') return {};
    if (method === 'Runtime.callFunctionOn') return {};
    if (method === 'Input.dispatchKeyEvent' && params.type === 'keyDown' && params.text) {
      value += String(params.text);
    }
    return {};
  };
  await typeChars(strictEditor, 'coverage probe alpha');
  assert.equal(value, 'coverage probe alpha');
});
