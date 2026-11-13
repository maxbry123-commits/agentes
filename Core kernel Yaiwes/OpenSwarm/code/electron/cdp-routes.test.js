// Run: node --test electron/cdp-routes.test.js
const { test } = require('node:test');
const assert = require('node:assert/strict');
const R = require('./cdp-routes');

test('templateUrl collapses numeric ids', () => {
  assert.equal(R.templateUrl('https://x.com/api/orders/4821'), 'https://x.com/api/orders/{id}');
  assert.equal(R.templateUrl('https://x.com/api/orders/4821/items/9'), 'https://x.com/api/orders/{id}/items/{id}');
});

test('templateUrl collapses hex/uuid ids', () => {
  assert.equal(
    R.templateUrl('https://x.com/u/3f9a8b7c6d5e4f3a/profile'),
    'https://x.com/u/{id}/profile',
  );
  assert.equal(
    R.templateUrl('https://x.com/r/550e8400-e29b-41d4-a716-446655440000'),
    'https://x.com/r/{id}',
  );
});

test('templateUrl keeps sorted query keys, drops values', () => {
  assert.equal(R.templateUrl('https://x.com/search?q=shoes&page=2'), 'https://x.com/search?page,q');
  assert.equal(R.templateUrl('https://x.com/search?q=hats'), 'https://x.com/search?q');
});

test('templateUrl returns input unchanged on garbage', () => {
  assert.equal(R.templateUrl('not a url'), 'not a url');
});

test('redactHeaders scrubs secret headers, keeps the rest', () => {
  const out = R.redactHeaders({
    Authorization: 'Bearer abc', Cookie: 'sid=xyz', 'X-CSRF-Token': 't',
    'Content-Type': 'application/json', Accept: '*/*',
  });
  assert.equal(out.Authorization, '<redacted>');
  assert.equal(out.Cookie, '<redacted>');
  assert.equal(out['X-CSRF-Token'], '<redacted>');
  assert.equal(out['Content-Type'], 'application/json');
  assert.equal(out.Accept, '*/*');
});

test('bodyShape keeps key skeleton with value TYPES, never values', () => {
  const shape = R.bodyShape(JSON.stringify({ id: 7, name: 'secret-name', tags: ['a'], nested: { x: true } }));
  assert.deepEqual(shape, { id: 'number', name: 'string', tags: ['string'], nested: { x: 'boolean' } });
  // crucially the real value "secret-name" is not present anywhere
  assert.ok(!JSON.stringify(shape).includes('secret-name'));
});

test('bodyShape handles non-JSON and empty', () => {
  assert.equal(R.bodyShape('<xml/>'), 'raw');
  assert.equal(R.bodyShape(null), null);
});

test('isSafeMethod only GET/HEAD', () => {
  assert.equal(R.isSafeMethod('get'), true);
  assert.equal(R.isSafeMethod('HEAD'), true);
  assert.equal(R.isSafeMethod('POST'), false);
  assert.equal(R.isSafeMethod('DELETE'), false);
});

test('shouldCapture only XHR/Fetch', () => {
  assert.equal(R.shouldCapture('XHR'), true);
  assert.equal(R.shouldCapture('Fetch'), true);
  assert.equal(R.shouldCapture('Document'), false);
  assert.equal(R.shouldCapture('Image'), false);
  assert.equal(R.shouldCapture('Script'), false);
});

test('recordRoute dedupes by (method,template) and counts hits', () => {
  const m = new Map();
  R.recordRoute(m, { method: 'GET', url: 'https://x.com/api/orders/1', headers: {} }, 'XHR');
  R.recordRoute(m, { method: 'GET', url: 'https://x.com/api/orders/2', headers: {} }, 'XHR');
  assert.equal(m.size, 1);
  assert.equal([...m.values()][0].hits, 2);
  assert.equal([...m.values()][0].safe, true);
});

test('recordRoute marks non-GET unsafe and skips non-XHR resource types', () => {
  const m = new Map();
  R.recordRoute(m, { method: 'POST', url: 'https://x.com/api/cart', headers: {}, postData: '{"id":1}' }, 'Fetch');
  R.recordRoute(m, { method: 'GET', url: 'https://x.com/page.css', headers: {} }, 'Stylesheet');
  assert.equal(m.size, 1);
  const e = [...m.values()][0];
  assert.equal(e.method, 'POST');
  assert.equal(e.safe, false);
  assert.deepEqual(e.bodyShape, { id: 'number' });
});

test('recordRoute evicts least-recently-seen past the cap', () => {
  const m = new Map();
  let t = 1000;
  for (let i = 0; i < R.MAX_ROUTES_PER_WC + 5; i++) {
    R.recordRoute(m, { method: 'GET', url: `https://x.com/p${i}/a`, headers: {} }, 'XHR', t++);
  }
  assert.equal(m.size, R.MAX_ROUTES_PER_WC);
  // the earliest few paths should have been evicted
  assert.ok(!m.has('GET https://x.com/p0/a'));
});

test('redactExampleUrl keeps normal search terms (agent typed them)', () => {
  assert.equal(
    R.redactExampleUrl('https://x.com/api/search?q=design+engineer&page=2'),
    'https://x.com/api/search?q=design+engineer&page=2',
  );
});

test('redactExampleUrl redacts token-shaped param VALUES', () => {
  // sensitive param name
  assert.equal(
    R.redactExampleUrl('https://x.com/api/feed?access_token=abc123xyz&q=cats'),
    'https://x.com/api/feed?access_token=%3Credacted%3E&q=cats',
  );
  // high-entropy value even under a benign key
  assert.equal(
    R.redactExampleUrl('https://x.com/api?sid=aB3xK9mQ2pL7wR4tY8nZ&q=hi'),
    'https://x.com/api?sid=%3Credacted%3E&q=hi',
  );
  // known token prefix
  assert.ok(
    R.redactExampleUrl('https://x.com/api?key=sk-ant-api03-abc').includes('redacted'),
  );
});

test('looksSecretValue: tokens yes, plain words no', () => {
  assert.ok(R.looksSecretValue('eyJhbGciOiJIUzI1NiIsInR5cCI6'));
  assert.ok(R.looksSecretValue('aB3xK9mQ2pL7wR4tY8nZ'));
  assert.ok(!R.looksSecretValue('shoes'));
  assert.ok(!R.looksSecretValue('design engineer'));
  assert.ok(!R.looksSecretValue('2'));
});

test('makeRouteEntry carries a redacted example url', () => {
  const e = R.makeRouteEntry({ method: 'GET', url: 'https://x.com/api/p?q=ada&token=secretAbc123Long', headers: {} }, 'XHR');
  assert.ok(e.example.includes('q=ada'));
  assert.ok(e.example.includes('redacted'));
  assert.ok(!e.example.includes('secretAbc123Long'));
});

test('makeRouteEntry: mutating route keeps a body, GET does not, secrets redacted', () => {
  const post = R.makeRouteEntry({
    method: 'POST',
    url: 'https://x.com/i/api/graphql/AbC123/CreateTweet',
    headers: { 'x-csrf-token': 'ct0secret' },
    postData: JSON.stringify({ variables: { tweet_text: 'hello world' }, authToken: 'aB3xK9mQ2pL7wR4tY8nZ' }),
  }, 'Fetch');
  assert.equal(post.safe, false);
  const body = JSON.parse(post.lastBody);
  assert.equal(body.variables.tweet_text, 'hello world');      // payload survives
  assert.equal(body.authToken, '<redacted>');                  // secret leaf redacted
  assert.equal(post.headers['x-csrf-token'], '<redacted>');    // header redacted

  const get = R.makeRouteEntry({ method: 'GET', url: 'https://x.com/i/api/graphql/AbC123/Home', headers: {}, postData: '' }, 'XHR');
  assert.equal(get.lastBody, null);                            // no body on a safe route
});

test('recordRoute: repeat write refreshes lastBody to the freshest call', () => {
  const m = new Map();
  const mk = (text) => ({ method: 'POST', url: 'https://x.com/i/api/graphql/AbC/CreateTweet', headers: {}, postData: JSON.stringify({ variables: { tweet_text: text } }) });
  R.recordRoute(m, mk('first'), 'Fetch');
  R.recordRoute(m, mk('second'), 'Fetch');
  const entry = [...m.values()][0];
  assert.equal(entry.hits, 2);
  assert.equal(JSON.parse(entry.lastBody).variables.tweet_text, 'second');
});
