import { ElectronApplication, Page } from '@playwright/test';
import fs from 'fs';
import os from 'os';
import path from 'path';

// VisibilityRecorder: stream every observable signal from one packaged-app run
// into a single per-test directory so a failing test tells you the full causal
// chain, not just "this assertion didn't match". Layers it stitches together:
//
//   playwright-trace.zip    - built-in trace: action timeline, before/after
//                             screenshots, DOM snapshots, network panel,
//                             console panel, source line per call. Open with
//                             `npx playwright show-trace <path>`.
//   events.jsonl            - unified timestamped stream of EVERY event we
//                             can intercept: console, pageerror, request,
//                             response, requestfailed, websocket open/frame/
//                             close, custom action wrappers, mousemove,
//                             wheel, keypress, perf marks, electron windows.
//   backend.log.tail        - the running app's backend.log captured live
//                             starting at our baseline byte offset so we
//                             see only the slice that belongs to this test.
//   mousepath.jsonl         - cursor positions sampled in the renderer
//                             (mousemove listener), so cursor speed, path
//                             curvature, hover dwell, and pan trajectory are
//                             all reconstructable post-hoc.
//   video.webm + screenshots/  - visual record alongside the timeline.

export interface VisibilityHandle {
  dir: string;
  recordAction<T>(name: string, fn: () => Promise<T>): Promise<T>;
  mark(label: string, payload?: Record<string, unknown>): void;
  // Capture an a11y tree snapshot at a labeled moment (key surfaces).
  snapshotA11y(label: string): Promise<void>;
  // Trigger a heap snapshot mid-run (for memory leak hunts).
  snapshotHeap(label: string): Promise<void>;
  // Dump the failure context for a specific test (call from afterEach when
  // info.status === 'failed'): writes the recent event tail, the current
  // Redux state, and a final screenshot under dir/failures/<test>.
  recordFailure(testTitle: string, status: string, error?: string): Promise<void>;
  stop(): Promise<void>;
}

function backendLogPath(): string {
  if (process.platform === 'win32') return path.join(process.env.APPDATA || '', 'OpenSwarm', 'data', 'backend.log');
  if (process.platform === 'darwin') return path.join(os.homedir(), 'Library', 'Application Support', 'OpenSwarm', 'data', 'backend.log');
  return path.join(process.env.XDG_DATA_HOME || path.join(os.homedir(), '.local', 'share'), 'OpenSwarm', 'data', 'backend.log');
}

function safeName(s: string): string {
  return s.replace(/[^a-z0-9._-]+/gi, '_').slice(0, 120);
}

// Compact view of a Redux state: top-level slice keys + array lengths +
// truncated previews. Avoids dumping 100s of KB while still telling you
// "agents.sessions had 3 entries, settings.loaded was false."
function summarizeRedux(state: unknown): unknown {
  if (!state || typeof state !== 'object') return state;
  const out: Record<string, unknown> = {};
  for (const [k, v] of Object.entries(state as Record<string, unknown>)) {
    if (v == null) out[k] = null;
    else if (Array.isArray(v)) out[k] = { type: 'array', length: v.length };
    else if (typeof v === 'object') out[k] = { type: 'object', keys: Object.keys(v as object).slice(0, 20) };
    else out[k] = { type: typeof v, preview: String(v).slice(0, 80) };
  }
  return out;
}

// Renderer-side instrumentation. Runs in EVERY frame of the app before any
// page script, captures mousemove/wheel/keydown with high-res timestamps,
// and forwards to the test side via window.__visibility_log__ which the test
// reads on a poll. No frontend code changes; this is test-only init script.
const INIT_SCRIPT = `
(() => {
  // Set BEFORE any bundle code runs so frontend code that gates on this flag
  // (e.g. store.ts exposing the Redux store) sees it during module load.
  (window).__OPENSWARM_E2E__ = true;
  if ((window).__visibility_installed__) return;
  (window).__visibility_installed__ = true;
  const buf = [];
  (window).__visibility_drain__ = () => { const out = buf.splice(0); return out; };

  // Redux state diffs: subscribe once the store is exposed, push a shallow
  // top-level slice-key diff each time. Full state can be 100s of KB; logging
  // every dispatch flat would saturate the JSONL. We log shallow changes only.
  const installReduxHook = () => {
    const s = (window).__OPENSWARM_STORE__;
    if (!s) return false;
    let prev = s.getState();
    s.subscribe(() => {
      const next = s.getState();
      const changed = [];
      for (const k of Object.keys(next)) {
        if (next[k] !== prev[k]) changed.push(k);
      }
      if (changed.length) buf.push({ ts: performance.now(), kind: 'redux', payload: { slices: changed } });
      prev = next;
    });
    return true;
  };
  if (!installReduxHook()) {
    // Bundle hasn't created the store yet; poll briefly.
    let tries = 0;
    const id = setInterval(() => { if (installReduxHook() || ++tries > 200) clearInterval(id); }, 50);
  }

  // NOTE: page-side IPC wrapping is NOT possible. window.openswarm is exposed via
  // contextBridge.exposeInMainWorld, which deep-freezes the object in the main
  // world, so reassigning api[key] from here is a silent no-op (verified: it
  // captured 0 events on every run). We deliberately do NOT instrument IPC here
  // rather than ship code that pretends to. IPC's observable effects ARE captured
  // through the channels that do work: page.on('request'/'response') for HTTP
  // round-trips, page.on('websocket') for the agent protocol, and the live
  // backend.log tail for server-side handling. Real per-call IPC timing would
  // need a preload-side wrapper gated on __OPENSWARM_E2E__ (a packaged-build
  // change), tracked as a follow-up.
  const push = (kind, payload) => {
    try { buf.push({ ts: performance.now(), kind, payload }); }
    catch (e) { /* never throw out of an event listener */ }
  };
  let lastMove = 0;
  document.addEventListener('mousemove', (e) => {
    // Sample at most every 8ms to keep the buffer tractable on long tests.
    const now = performance.now();
    if (now - lastMove < 8) return;
    lastMove = now;
    push('mousemove', { x: e.clientX, y: e.clientY, btn: e.buttons });
  }, { capture: true, passive: true });
  document.addEventListener('wheel', (e) => {
    push('wheel', { dx: e.deltaX, dy: e.deltaY, mode: e.deltaMode, ctrl: e.ctrlKey });
  }, { capture: true, passive: true });
  document.addEventListener('keydown', (e) => {
    push('keydown', { key: e.key, code: e.code, mod: { c: e.ctrlKey, s: e.shiftKey, a: e.altKey, m: e.metaKey } });
  }, { capture: true, passive: true });
  document.addEventListener('click', (e) => {
    // Walk up to the nearest identifiable control: a raw click usually lands on
    // an inner text node (SPAN/P) that carries no id, so reading attributes off
    // e.target alone records "SPAN" instead of the button that was hit.
    const t = e.target;
    const ctrl = (t && t.closest) ? t.closest('[data-onboarding],[aria-label],[data-select-id],button,[role="button"],a') : null;
    const id =
      (ctrl && (ctrl.getAttribute('data-onboarding') || ctrl.getAttribute('aria-label') || ctrl.getAttribute('data-select-id'))) ||
      (ctrl && ctrl.tagName) ||
      (t && t.tagName);
    push('click', { x: e.clientX, y: e.clientY, target: id, raw: t && t.tagName });
  }, { capture: true, passive: true });
  // Surface any long task (>50ms blocking the main thread) so we see where
  // input responsiveness craters.
  try {
    const po = new PerformanceObserver((list) => {
      for (const entry of list.getEntries()) push('longtask', { dur: entry.duration, name: entry.name });
    });
    po.observe({ entryTypes: ['longtask'] });
  } catch {}
})();
`;

export async function startVisibility(
  app: ElectronApplication,
  page: Page,
  testId: string,
  rootDir = path.resolve(__dirname, '..', 'traces'),
): Promise<VisibilityHandle> {
  const dir = path.join(rootDir, safeName(testId));
  fs.mkdirSync(dir, { recursive: true });
  fs.mkdirSync(path.join(dir, 'screenshots'), { recursive: true });

  const eventsPath = path.join(dir, 'events.jsonl');
  const mousePath = path.join(dir, 'mousepath.jsonl');
  const backendTailPath = path.join(dir, 'backend.log.tail');
  const eventsStream = fs.createWriteStream(eventsPath, { flags: 'a' });
  const mouseStream = fs.createWriteStream(mousePath, { flags: 'a' });
  const backendTailStream = fs.createWriteStream(backendTailPath, { flags: 'a' });

  const log = (kind: string, payload: unknown) => {
    eventsStream.write(JSON.stringify({ ts: Date.now(), kind, payload }) + '\n');
  };

  // 1) Playwright tracing - the heavy lifter. Captures every action, network
  //    request, console message, and produces snapshot timeline. Saved as a
  //    .zip viewable in `npx playwright show-trace`.
  const ctx = app.context();
  await ctx.tracing.start({ screenshots: true, snapshots: true, sources: true, title: testId });

  // 2) Renderer-side hooks: input timing, long tasks, Redux subscribe, IPC wrap.
  //    The init script runs on every NEW page; we also eval against the current
  //    page so the already-open main window picks it up.
  await ctx.addInitScript({ content: INIT_SCRIPT });
  await page.evaluate(INIT_SCRIPT).catch(() => { /* page may be navigating */ });

  // 3) JS + CSS coverage. Chromium-only on Playwright. Saved at stop.
  try { await page.coverage.startJSCoverage({ resetOnNavigation: false }); } catch (e) { log('coverage-skip', { reason: 'js', error: String(e) }); }
  try { await page.coverage.startCSSCoverage({ resetOnNavigation: false }); } catch (e) { log('coverage-skip', { reason: 'css', error: String(e) }); }

  // 4) Chromium perf tracing via CDP. Categories chosen to capture paint /
  //    layout / scripting / raf cadence without exploding trace size.
  const cdp = await ctx.newCDPSession(page).catch(() => null);
  let tracingActive = false;
  if (cdp) {
    try {
      await cdp.send('Tracing.start', {
        categories: 'devtools.timeline,disabled-by-default-devtools.timeline.frame,blink.user_timing,latencyInfo,toplevel',
        transferMode: 'ReturnAsStream',
      });
      tracingActive = true;
    } catch (e) { log('cdp-tracing-skip', { error: String(e) }); }
  }

  // 5) Electron main-process stdout/stderr piped into the unified stream.
  //    Catches main-process crashes and Electron-internal warnings that never
  //    reach the renderer log.
  try {
    const proc: any = (app as any).process?.();
    proc?.stdout?.on?.('data', (b: Buffer) => log('main-stdout', String(b).slice(0, 800)));
    proc?.stderr?.on?.('data', (b: Buffer) => log('main-stderr', String(b).slice(0, 800)));
  } catch (e) { log('main-pipe-skip', { error: String(e) }); }

  // 3) Page-level event listeners. Console + errors + every network round-trip.
  page.on('console', (m) => log('console', { type: m.type(), text: m.text(), location: m.location() }));
  page.on('pageerror', (e) => log('pageerror', { message: String(e?.message ?? e), stack: e?.stack }));
  page.on('request', (r) => log('request', { url: r.url(), method: r.method(), resourceType: r.resourceType() }));
  page.on('response', (r) => log('response', { url: r.url(), status: r.status(), fromCache: r.fromServiceWorker() }));
  page.on('requestfailed', (r) => log('requestfailed', { url: r.url(), failure: r.failure()?.errorText }));
  page.on('crash', () => log('crash', { url: page.url() }));

  // 4) WebSocket frame capture - the agent protocol streams over this; without
  //    it you see UI changes but not what message arrived.
  page.on('websocket', (ws) => {
    log('ws-open', { url: ws.url() });
    ws.on('framereceived', (f) => log('ws-recv', { url: ws.url(), preview: String(f.payload).slice(0, 400) }));
    ws.on('framesent', (f) => log('ws-send', { url: ws.url(), preview: String(f.payload).slice(0, 400) }));
    ws.on('close', () => log('ws-close', { url: ws.url() }));
    ws.on('socketerror', (e) => log('ws-error', { url: ws.url(), error: String(e) }));
  });

  // 5) Backend log live tail. Capture only the suffix from our start offset so
  //    interleaving with the test timeline stays exact.
  const startOffset = (() => {
    try { return fs.statSync(backendLogPath()).size; } catch { return 0; }
  })();
  let backendOffset = startOffset;
  const backendTimer = setInterval(() => {
    try {
      const stat = fs.statSync(backendLogPath());
      if (stat.size <= backendOffset) return;
      const fd = fs.openSync(backendLogPath(), 'r');
      const buf = Buffer.alloc(stat.size - backendOffset);
      fs.readSync(fd, buf, 0, buf.length, backendOffset);
      fs.closeSync(fd);
      backendOffset = stat.size;
      backendTailStream.write(buf);
      // Also project each line into the unified events stream so a single grep
      // across events.jsonl recovers everything ordered.
      for (const line of buf.toString('utf8').split(/\r?\n/)) {
        if (line) log('backend', line.slice(0, 800));
      }
    } catch { /* file may not exist yet; keep polling */ }
  }, 500);

  // 6) Drain the renderer-side buffer (mousemove etc.) on a tick.
  const drainTimer = setInterval(async () => {
    try {
      const drained: Array<{ ts: number; kind: string; payload: unknown }> = await page.evaluate(() => (window as any).__visibility_drain__?.() || []);
      for (const e of drained) {
        if (e.kind === 'mousemove' || e.kind === 'wheel') mouseStream.write(JSON.stringify(e) + '\n');
        log(e.kind, e.payload);
      }
    } catch { /* renderer may be busy; pick up next tick */ }
  }, 200);

  // 7) Video. Electron context recording isn't always supported; if it isn't,
  //    skip silently - the snapshots in the trace zip are the fallback.
  // (Playwright's electron.launch does not currently expose recordVideo; we
  // capture frequent screenshots in tests instead, plus the trace's snapshots.)

  log('start', { testId, platform: process.platform, pid: process.pid });

  const handle: VisibilityHandle = {
    dir,
    async recordAction<T>(name, fn) {
      const t0 = Date.now();
      log('action-start', { name });
      try {
        const result = await fn();
        log('action-end', { name, durationMs: Date.now() - t0, ok: true });
        return result;
      } catch (e: any) {
        log('action-end', { name, durationMs: Date.now() - t0, ok: false, error: String(e?.message ?? e) });
        throw e;
      }
    },
    mark(label, payload) { log('mark', { label, ...(payload || {}) }); },
    async snapshotA11y(label) {
      try {
        const snap = await page.accessibility.snapshot({ interestingOnly: true });
        const p = path.join(dir, `a11y-${safeName(label)}.json`);
        fs.writeFileSync(p, JSON.stringify(snap, null, 2));
        log('a11y-snapshot', { label, path: p });
      } catch (e) { log('a11y-snapshot-skip', { label, error: String(e) }); }
    },
    async recordFailure(testTitle, status, error) {
      const failDir = path.join(dir, 'failures');
      fs.mkdirSync(failDir, { recursive: true });
      const base = path.join(failDir, safeName(testTitle));
      // Take a final screenshot for visual context.
      try { await page.screenshot({ path: `${base}.png`, fullPage: true }); }
      catch (e) { log('failure-screenshot-skip', { error: String(e) }); }
      // Pull current Redux state if available - tells us the slice that was
      // wrong at the moment of failure.
      let reduxState: unknown = null;
      try { reduxState = await page.evaluate(() => (window as any).__OPENSWARM_STORE__?.getState?.() ?? null); }
      catch (e) { reduxState = { error: String(e) }; }
      // Read the tail of events.jsonl as the action breadcrumb. The user reads
      // this top-down to localize the failure to a step.
      let eventTail = '';
      try {
        const stat = fs.statSync(eventsPath);
        const fd = fs.openSync(eventsPath, 'r');
        const tailSize = Math.min(stat.size, 256 * 1024);
        const buf = Buffer.alloc(tailSize);
        fs.readSync(fd, buf, 0, tailSize, stat.size - tailSize);
        fs.closeSync(fd);
        eventTail = buf.toString('utf8');
      } catch (e) { eventTail = `(events tail read failed: ${String(e)})`; }
      fs.writeFileSync(`${base}.json`, JSON.stringify({
        test: testTitle,
        status,
        error: error || null,
        atMs: Date.now(),
        reduxStateSummary: summarizeRedux(reduxState),
        eventTailLines: eventTail.split(/\r?\n/).slice(-200),
      }, null, 2));
      log('failure-report', { test: testTitle, status, path: `${base}.json` });
    },
    async snapshotHeap(label) {
      if (!cdp) { log('heap-skip', { label, reason: 'no cdp' }); return; }
      try {
        // CDP HeapProfiler.takeHeapSnapshot streams chunks via event.
        const chunks: string[] = [];
        const onChunk = (e: any) => chunks.push(e.chunk);
        cdp.on('HeapProfiler.addHeapSnapshotChunk' as any, onChunk);
        await cdp.send('HeapProfiler.takeHeapSnapshot' as any, { reportProgress: false } as any);
        cdp.off('HeapProfiler.addHeapSnapshotChunk' as any, onChunk);
        const p = path.join(dir, `heap-${safeName(label)}.heapsnapshot`);
        fs.writeFileSync(p, chunks.join(''));
        log('heap-snapshot', { label, path: p, sizeBytes: chunks.join('').length });
      } catch (e) { log('heap-snapshot-skip', { label, error: String(e) }); }
    },
    async stop() {
      log('stop', {});
      clearInterval(backendTimer);
      clearInterval(drainTimer);
      // Flush JS/CSS coverage before tracing stops (Playwright requires it).
      try {
        const js = await page.coverage.stopJSCoverage();
        fs.writeFileSync(path.join(dir, 'coverage-js.json'), JSON.stringify(js));
      } catch (e) { log('coverage-stop-skip', { reason: 'js', error: String(e) }); }
      try {
        const css = await page.coverage.stopCSSCoverage();
        fs.writeFileSync(path.join(dir, 'coverage-css.json'), JSON.stringify(css));
      } catch (e) { log('coverage-stop-skip', { reason: 'css', error: String(e) }); }
      // Stop CDP Chromium tracing and drain stream to disk. The stream handle is
      // delivered by the Tracing.tracingComplete EVENT, not the Tracing.end
      // response (which is empty); reading result.stream off end() was always
      // undefined, so nothing was ever written. Listen for the event instead.
      if (cdp && tracingActive) {
        try {
          const completed: any = await new Promise((resolve, reject) => {
            const to = setTimeout(() => reject(new Error('tracingComplete timed out')), 20000);
            cdp.once('Tracing.tracingComplete' as any, (e: any) => { clearTimeout(to); resolve(e); });
            cdp.send('Tracing.end' as any).catch((e) => { clearTimeout(to); reject(e); });
          });
          const streamHandle = completed?.stream;
          if (streamHandle) {
            const out = fs.createWriteStream(path.join(dir, 'chromium-trace.json'));
            for (;;) {
              const piece: any = await cdp.send('IO.read' as any, { handle: streamHandle, size: 256 * 1024 } as any);
              if (piece?.data) out.write(piece.base64Encoded ? Buffer.from(piece.data, 'base64') : piece.data);
              if (piece?.eof) break;
            }
            await new Promise<void>((r) => out.end(() => r()));
            await cdp.send('IO.close' as any, { handle: streamHandle } as any).catch(() => {});
          } else {
            log('cdp-tracing-stop-skip', { reason: 'tracingComplete carried no stream handle' });
          }
        } catch (e) { log('cdp-tracing-stop-skip', { error: String(e) }); }
      }
      try { await ctx.tracing.stop({ path: path.join(dir, 'playwright-trace.zip') }); } catch {}
      await new Promise<void>((r) => eventsStream.end(() => r()));
      await new Promise<void>((r) => mouseStream.end(() => r()));
      await new Promise<void>((r) => backendTailStream.end(() => r()));
    },
  };
  return handle;
}

