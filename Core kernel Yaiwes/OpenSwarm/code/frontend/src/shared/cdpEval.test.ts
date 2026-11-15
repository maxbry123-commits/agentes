// Run: node --test frontend/src/shared/cdpEval.test.ts
import { test } from 'node:test';
import assert from 'node:assert/strict';
import { unwrapCdpEval } from './cdpEval.ts';

test('returns the serialized value on success', () => {
  assert.equal(unwrapCdpEval({ result: { value: 'hello', type: 'string' } }), 'hello');
});

test('returns an object value untouched (returnByValue serialized)', () => {
  const v = unwrapCdpEval({ result: { value: { found: true, filled: false } } }) as any;
  assert.equal(v.found, true);
  assert.equal(v.filled, false);
});

test('undefined result value comes back as undefined, not a throw', () => {
  assert.equal(unwrapCdpEval({ result: { type: 'undefined' } }), undefined);
});

test('a page-side throw surfaces as an Error with the exception description', () => {
  assert.throws(
    () => unwrapCdpEval({ exceptionDetails: { exception: { description: 'ReferenceError: x is not defined' } } }),
    /x is not defined/,
  );
});

test('falls back to exceptionDetails.text when no exception description', () => {
  assert.throws(
    () => unwrapCdpEval({ exceptionDetails: { text: 'Uncaught' } }),
    /Uncaught/,
  );
});

test('exceptionDetails wins even if a result is also present', () => {
  assert.throws(
    () => unwrapCdpEval({ result: { value: 'partial' }, exceptionDetails: { text: 'boom' } }),
    /boom/,
  );
});
