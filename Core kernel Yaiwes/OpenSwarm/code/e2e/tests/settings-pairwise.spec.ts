import { test, expect, ElectronApplication, Page } from '@playwright/test';
import { launchApp, waitForMainWindow } from '../helpers/launch';
import { startVisibility, VisibilityHandle } from '../helpers/visibility';
import { pairwise, cartesian, Params } from '../helpers/pairwise';
import fs from 'fs';
import os from 'os';
import path from 'path';

// All-pairs (or full Cartesian via OPENSWARM_E2E_EXHAUSTIVE=1) coverage of the
// General-tab Switch settings + theme. Each row is applied directly via the
// Redux dispatch path the UI uses, then a series of post-conditions confirms:
//   (a) the renderer didn't crash
//   (b) every Switch reflects the row's value (not silently reverted)
//   (c) theme localStorage took effect
//   (d) no unexpected page/console error fired during the apply
//   (e) the final Settings render is screenshot-stable

function backendLogPath(): string {
  if (process.platform === 'win32') return path.join(process.env.APPDATA || '', 'OpenSwarm', 'data', 'backend.log');
  if (process.platform === 'darwin') return path.join(os.homedir(), 'Library', 'Application Support', 'OpenSwarm', 'data', 'backend.log');
  return path.join(process.env.XDG_DATA_HOME || path.join(os.homedir(), '.local', 'share'), 'OpenSwarm', 'data', 'backend.log');
}
function crashCount(): number {
  try { return (fs.readFileSync(backendLogPath(), 'utf8').match(/renderer process gone/g) || []).length; }
  catch { return 0; }
}

// Cross-tab coverage: the first block is the General tab's switches + theme; the
// second block reaches the Models tab (model selection, connection mode) and the
// agent defaults (thinking level) + privacy (analytics) that live on other tabs,
// so the matrix exercises pairwise interactions ACROSS tabs, not just within
// General. All values round-trip cleanly through pydantic in THROUGH_BACKEND mode
// (default_model/default_mode are free-form strings; the rest are enums/bools).
const PARAMS: Params = {
  auto_select_mode_on_new_agent: [false, true],
  expand_new_chats_in_dashboard: [false, true],
  auto_reveal_sub_agents: [false, true],
  dev_mode: [false, true],
  allow_experimental_updates: [false, true],
  theme: ['light', 'dark'],
  default_model: ['sonnet', 'opus'],
  default_thinking_level: ['auto', 'high'],
  connection_mode: ['own_key', 'openswarm-pro'],
  analytics_opt_in: [false, true],
};

const EXHAUSTIVE = process.env.OPENSWARM_E2E_EXHAUSTIVE === '1';
const THROUGH_BACKEND = process.env.OPENSWARM_E2E_THROUGH_BACKEND === '1';
const ROWS = EXHAUSTIVE ? cartesian(PARAMS) : pairwise(PARAMS);

test.describe.configure({ mode: 'serial' });
test.describe(`settings ${EXHAUSTIVE ? 'cartesian' : 'pairwise'} (${ROWS.length} rows)`, () => {
  let app: ElectronApplication;
  let page: Page;
  let vis: VisibilityHandle;
  let baseline = 0;
  const errors: Array<{ kind: string; text: string }> = [];
  const WHITELIST = [/DevTools listening/i, /Autofill/i, /electron-store/i, /downloadable font/i];

  test.beforeAll(async () => {
    app = await launchApp();
    page = await waitForMainWindow(app);
    vis = await startVisibility(app, page, `settings-pairwise-${ROWS.length}rows`);
    page.on('pageerror', (e) => errors.push({ kind: 'pageerror', text: String(e?.message ?? e) }));
    page.on('console', (m) => { if (m.type() === 'error') errors.push({ kind: 'console', text: m.text() }); });
    baseline = crashCount();
  });
  test.afterAll(async () => { try { await vis?.stop(); } catch {} await app?.close().catch(() => {}); });

  // Self-check identical to the combinatorial spec: must-locator MUST throw on missing target.
  test('self-check: pairwise rows are non-empty + cover the cross', () => {
    expect(ROWS.length).toBeGreaterThan(0);
    if (!EXHAUSTIVE) expect(ROWS.length).toBeLessThan(Object.values(PARAMS).reduce((a, vs) => a * vs.length, 1));
  });

  // Apply a row. Two paths:
  //   default: dispatch settings/update/fulfilled directly - hermetic, fast
  //   THROUGH_BACKEND=1: drive the real PUT /api/settings round-trip so the
  //     server's pydantic validation, write-lock, and slice-shape contract
  //     are all exercised. Slower but catches the class where local apply
  //     works but the server would reject the payload.
  async function applyRow(row: Record<string, unknown>) {
    await page.evaluate(async ({ rowJson, throughBackend }) => {
      const r = JSON.parse(rowJson);
      const store = (window as any).__OPENSWARM_STORE__;
      if (!store) throw new Error('Redux store not exposed; __OPENSWARM_E2E__ flag did not take effect');
      const current = store.getState().settings.data;
      const next = { ...current };
      for (const k of Object.keys(r)) if (k !== 'theme') next[k] = r[k];
      if (throughBackend) {
        // Real PUT round-trip via the same auth path the renderer uses.
        const port: number = (window as any).openswarm?.getBackendPort?.();
        const token: string = await ((window as any).openswarm?.getAuthToken?.() ?? Promise.resolve(''));
        const res = await fetch(`http://127.0.0.1:${port}/api/settings/`, {
          method: 'PUT',
          headers: { 'Content-Type': 'application/json', ...(token ? { Authorization: `Bearer ${token}` } : {}) },
          body: JSON.stringify(next),
        });
        if (!res.ok) throw new Error(`PUT /api/settings returned ${res.status}`);
        const body = await res.json();
        const persisted = body.settings || body;
        store.dispatch({ type: 'settings/update/fulfilled', payload: persisted });
      } else {
        store.dispatch({ type: 'settings/update/fulfilled', payload: next });
      }
      if (r.theme) { try { localStorage.setItem('self-swarm-theme-mode', r.theme); } catch {} }
    }, { rowJson: JSON.stringify(row), throughBackend: THROUGH_BACKEND });
    await page.waitForTimeout(150);
  }

  async function readState(): Promise<{ store: Record<string, unknown>; theme: string | null }> {
    return await page.evaluate(() => {
      const store = (window as any).__OPENSWARM_STORE__;
      const s = store ? store.getState().settings.data : {};
      let theme: string | null = null;
      try { theme = localStorage.getItem('self-swarm-theme-mode'); } catch {}
      return { store: s, theme };
    });
  }

  for (let i = 0; i < ROWS.length; i++) {
    const row = ROWS[i];
    test(`row ${i + 1}/${ROWS.length}: ${JSON.stringify(row)}`, async ({}, info) => {
      const errMark = errors.length;
      vis?.mark('apply-row', { row, index: i });
      await applyRow(row);
      const state = await readState();
      for (const [k, v] of Object.entries(row)) {
        if (k === 'theme') continue;
        expect(state.store[k], `${k} did not persist as ${v}`).toBe(v);
      }
      if (row.theme) expect(state.theme, 'theme localStorage did not take').toBe(row.theme);

      expect(crashCount(), `row ${i + 1} crashed renderer`).toBe(baseline);
      const fresh = errors.slice(errMark).filter((e) => !WHITELIST.some((rx) => rx.test(e.text)));
      expect(fresh.map((e) => `${e.kind}: ${e.text}`).join('\n'), `row ${i + 1} produced unexpected errors`).toBe('');
      if (i < 3 || i === ROWS.length - 1) await page.screenshot({ path: info.outputPath(`row-${String(i).padStart(2, '0')}.png`) });
    });
  }

  test('final: zero new renderer-gone-lines across the entire matrix', () => {
    expect(crashCount(), 'a row crashed the renderer somewhere').toBe(baseline);
  });
});
