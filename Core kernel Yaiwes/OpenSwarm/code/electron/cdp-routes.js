// Pure helpers for tier-2 shadow-API route capture. No Electron deps so this
// unit-tests under plain node; main.js wires the CDP Network events to it.
//
// The idea: a site's UI is a shell over its own internal HTTP API. While the
// agent drives the UI we passively record the XHR/fetch endpoints the page
// fires, so a later task can replay a safe (GET) one directly instead of
// re-scraping. We NEVER persist secrets: auth/cookie/csrf headers are redacted,
// and only the body's KEY SHAPE is kept (no values).

// Prefix match (no end-anchor) so header variants like x-csrf-token and
// x-auth-token are caught too; over-redacting a secret-shaped header is the
// safe direction.
const REDACT = /^(authorization|cookie|set-cookie|proxy-authorization|x-csrf|x-xsrf|x-api-key|x-auth)/i;
const CAPTURE_RESOURCE_TYPES = new Set(['XHR', 'Fetch']);
const MAX_ROUTES_PER_WC = 200; // bound memory; evict least-recently-seen past this

// Collapse volatile path segments (numeric ids, long hex / uuids) so
// /orders/4821 and /orders/4822 share one route template.
function templateUrl(raw) {
  try {
    const u = new URL(raw);
    const path = u.pathname.replace(
      /\/(\d+|[0-9a-fA-F]{8,}(?:-[0-9a-fA-F]+)*)(?=\/|$)/g,
      '/{id}',
    );
    const keys = [...u.searchParams.keys()].sort().join(',');
    return u.origin + path + (keys ? '?' + keys : '');
  } catch {
    return raw;
  }
}

function redactHeaders(headers) {
  const out = {};
  for (const k of Object.keys(headers || {})) {
    out[k] = REDACT.test(k) ? '<redacted>' : headers[k];
  }
  return out;
}

// A concrete EXAMPLE url (real values) so the agent can see the param shape and
// template its own input in. The template alone (value-stripped) isn't composable
// for multi-param endpoints. We redact token-shaped query VALUES so a session
// token / api key in the query never lands in the agent's context. The user's own
// search terms stay (the agent typed them; not secret). Path stays as-is.
const SECRET_PARAM = /token|secret|sig|session|password|pwd|jwt|bearer|auth|access|refresh|csrf|api[-_]?key/i;
const TOKEN_PREFIX = /^(sk-|ghp_|gho_|pk_|xox[bap]-|AIza|eyJ|Bearer )/;

function looksSecretValue(v) {
  if (!v) return false;
  if (TOKEN_PREFIX.test(v)) return true;
  return v.length >= 20 && /[A-Za-z]/.test(v) && /[0-9]/.test(v) && !/\s/.test(v);
}

function redactExampleUrl(raw) {
  try {
    const u = new URL(raw);
    for (const [k, v] of [...u.searchParams.entries()]) {
      if (SECRET_PARAM.test(k) || looksSecretValue(v)) {
        u.searchParams.set(k, '<redacted>');
      }
    }
    return u.origin + u.pathname + (u.search || '');
  } catch {
    return raw;
  }
}

// Keep the JSON body's key skeleton with value TYPES, never values.
function bodyShape(postData) {
  if (!postData) return null;
  try {
    const skel = (v) =>
      Array.isArray(v)
        ? [v.length ? skel(v[0]) : 'empty']
        : v && typeof v === 'object'
          ? Object.fromEntries(Object.keys(v).map((k) => [k, skel(v[k])]))
          : typeof v;
    return skel(JSON.parse(postData));
  } catch {
    return 'raw';
  }
}

function isSafeMethod(method) {
  const m = String(method || '').toUpperCase();
  return m === 'GET' || m === 'HEAD';
}

function shouldCapture(resourceType) {
  return CAPTURE_RESOURCE_TYPES.has(resourceType);
}

function routeKey(method, template) {
  return String(method || 'GET').toUpperCase() + ' ' + template;
}

// The mutating body WITH values, but secret-shaped string leaves redacted (belt; the backend
// recipe learner redacts again). Only JSON, capped: a write recipe needs the real body (the user's
// payload sits in one leaf), which bodyShape (types only) can't provide. Non-JSON / oversized = null.
const MAX_BODY_CHARS = 65536;

function redactBodyValues(postData) {
  if (!postData || postData.length > MAX_BODY_CHARS) return null;
  try {
    const walk = (v) =>
      typeof v === 'string'
        ? (looksSecretValue(v) ? '<redacted>' : v)
        : Array.isArray(v)
          ? v.map(walk)
          : v && typeof v === 'object'
            ? Object.fromEntries(Object.keys(v).map((k) => [k, walk(v[k])]))
            : v;
    return JSON.stringify(walk(JSON.parse(postData)));
  } catch {
    return null;
  }
}

function makeRouteEntry(request, resourceType) {
  const method = String(request.method || 'GET').toUpperCase();
  const template = templateUrl(request.url);
  const safe = isSafeMethod(method);
  return {
    method,
    template,
    example: redactExampleUrl(request.url),
    resourceType,
    headers: redactHeaders(request.headers),
    bodyShape: bodyShape(request.postData),
    // Only mutating routes carry a replayable body; a GET's body (if any) is never a write recipe.
    lastBody: safe ? null : redactBodyValues(request.postData),
    safe,
    hits: 1,
    lastSeen: Date.now(),
  };
}

// Merge a captured request into a per-wc Map<routeKey, entry>. Dedupes by
// (method, templated url): repeats just bump the hit count. Evicts the
// least-recently-seen entry past the cap.
function recordRoute(routesMap, request, resourceType, now = Date.now()) {
  if (!shouldCapture(resourceType)) return;
  const entry = makeRouteEntry(request, resourceType);
  entry.lastSeen = now;
  const key = routeKey(entry.method, entry.template);
  const existing = routesMap.get(key);
  if (existing) {
    existing.hits += 1;
    existing.lastSeen = now;
    // Refresh the body so a later replay learns from the FRESHEST call (queryId/token rotation
    // lives in the URL/headers, but a stale body could hold an old nonce); keep the latest.
    if (entry.lastBody) existing.lastBody = entry.lastBody;
  } else {
    routesMap.set(key, entry);
    if (routesMap.size > MAX_ROUTES_PER_WC) {
      let oldestKey = null;
      let oldest = Infinity;
      for (const [k, v] of routesMap) {
        if (v.lastSeen < oldest) { oldest = v.lastSeen; oldestKey = k; }
      }
      if (oldestKey) routesMap.delete(oldestKey);
    }
  }
}

module.exports = {
  templateUrl,
  redactExampleUrl,
  looksSecretValue,
  redactHeaders,
  bodyShape,
  isSafeMethod,
  shouldCapture,
  routeKey,
  makeRouteEntry,
  recordRoute,
  CAPTURE_RESOURCE_TYPES,
  MAX_ROUTES_PER_WC,
};
