#!/usr/bin/env node
// Drives a REAL agent turn on the app's own login (gated by OPENSWARM_E2E_AGENT=1; spends quota, else skips). Launches tool-free (no approval-gate hang) and asserts terminal status + tokens.output>0, a live reply the harness cant fake.

'use strict';
const h = require('./lib/app-harness');

function parseArgs(argv) {
  const out = { app: null, prompt: 'Reply with exactly the single word: pong', timeoutMs: 120000 };
  for (let i = 0; i < argv.length; i++) {
    if (argv[i] === '--app') out.app = argv[++i];
    else if (argv[i] === '--prompt') out.prompt = argv[++i];
    else if (argv[i] === '--timeout-ms') out.timeoutMs = Number(argv[++i]);
  }
  return out;
}

function providerForGroup(group) {
  const g = group.toLowerCase();
  if (g.includes('openai')) return 'openai';
  if (g.includes('google') || g.includes('gemini')) return 'google';
  if (g.includes('openrouter')) return 'openrouter';
  return 'anthropic';   // Anthropic / OpenSwarm Pro / Claude / custom default
}

// Pick a model from /api/agents/models, preferring a cheap Anthropic-family one.
function pickModel(modelsByGroup) {
  const groups = Object.entries(modelsByGroup || {});
  const flat = groups.flatMap(([group, ms]) => (ms || []).map((m) => ({ value: m.value, group })));
  if (!flat.length) return null;
  const pref = flat.find((m) => /haiku/i.test(m.value)) || flat.find((m) => /sonnet|claude/i.test(m.value)) || flat[0];
  return { model: pref.value, provider: providerForGroup(pref.group) };
}

async function main() {
  if (process.env.OPENSWARM_E2E_AGENT !== '1') {
    process.stdout.write('SKIP: agent-turn check is gated. Set OPENSWARM_E2E_AGENT=1 to run a real turn (spends LLM quota).\n');
    process.exit(0);
  }
  const args = parseArgs(process.argv.slice(2));

  // Reuse the user's already-running, logged-in app if there is one; else launch.
  let port, token, child = null, ownsApp = false;
  const attached = await h.attachToRunning();
  if (attached) {
    ({ port, token } = attached);
    process.stdout.write(`Attached to running app on :${port}\n`);
  } else {
    const appPath = h.packagedAppPath(args.app);
    process.stdout.write(`Launching: ${appPath}\n`);
    const res = await h.launchAndWait({ appPath, timeoutMs: args.timeoutMs });
    child = res.child; ownsApp = true; port = res.port;
    token = h.readFileSafe(h.authTokenPath()).trim();
  }

  const fail = (msg) => { if (ownsApp) h.killApp(child); process.stderr.write(`\nAGENT FAIL: ${msg}\n`); process.exit(1); };
  if (!port || !token) fail('no backend port / auth token available');

  let sessionId = null;
  try {
    // 1. creds gate
    const models = await h.apiRequest(port, { path: '/api/agents/models', token });
    if (models.status !== 200) fail(`GET /api/agents/models -> ${models.status}`);
    const picked = pickModel(models.json && models.json.models);
    if (!picked) { if (ownsApp) h.killApp(child); process.stdout.write('SKIP: no provider connected on this machine; a real turn is not testable here.\n'); process.exit(0); }
    process.stdout.write(`  using model ${picked.model} (provider ${picked.provider})\n`);

    // 2. launch a tool-free, single-turn session
    const launch = await h.apiRequest(port, {
      method: 'POST', path: '/api/agents/launch', token,
      body: { name: 'e2e-agent-turn', model: picked.model, provider: picked.provider, mode: 'agent', allowed_tools: [], max_turns: 1 },
    });
    if (launch.status !== 200 || !launch.json || !launch.json.session_id) fail(`launch -> ${launch.status} ${launch.text.slice(0, 200)}`);
    sessionId = launch.json.session_id;

    // 3. send the prompt
    const send = await h.apiRequest(port, { method: 'POST', path: `/api/agents/sessions/${sessionId}/message`, token, body: { prompt: args.prompt } });
    if (send.status !== 200) fail(`send message -> ${send.status} ${send.text.slice(0, 200)}`);

    // 4. poll until terminal; a real reply == output tokens with no error
    const TERMINAL = new Set(['completed', 'stopped', 'error']);
    const t0 = Date.now();
    let session = null, status = '';
    while (Date.now() - t0 < args.timeoutMs) {
      const g = await h.apiRequest(port, { path: `/api/agents/sessions/${sessionId}`, token });
      if (g.status === 200 && g.json) { session = g.json; status = session.status; if (TERMINAL.has(status)) break; }
      await h.sleep(1500);
    }
    if (!session) fail('never read session state back');
    if (status === 'error') fail(`turn ended in error: ${JSON.stringify(session.error || session.last_error || 'unknown')}`);
    if (!TERMINAL.has(status)) fail(`turn did not finish within ${Math.round(args.timeoutMs / 1000)}s (status=${status})`);
    const out = (session.tokens && Number(session.tokens.output)) || 0;
    if (out <= 0) fail(`turn completed but produced 0 output tokens (no real model reply)`);

    process.stdout.write(`\nAGENT PASS: real turn completed in ${Math.round((Date.now() - t0) / 1000)}s, ${out} output tokens from ${picked.model}.\n`);
  } finally {
    if (sessionId) {
      await h.apiRequest(port, { method: 'POST', path: `/api/agents/sessions/${sessionId}/stop`, token }).catch(() => {});
      await h.apiRequest(port, { method: 'DELETE', path: `/api/agents/sessions/${sessionId}`, token }).catch(() => {});
    }
    if (ownsApp) h.killApp(child);
  }
  process.exit(0);
}

main().catch((e) => { process.stderr.write(`\nAGENT FAIL: ${e && e.message || e}\n`); process.exit(1); });
