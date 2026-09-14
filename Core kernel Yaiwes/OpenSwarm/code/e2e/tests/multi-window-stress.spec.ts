import { test, expect, ElectronApplication, Page } from '@playwright/test';
import { launchApp, waitForMainWindow } from '../helpers/launch';
import { startVisibility, VisibilityHandle } from '../helpers/visibility';
import fs from 'fs';
import os from 'os';
import path from 'path';

// Multi-window / multi-surface stress: the rest of the suite drives one window
// with one surface at a time, so a webview-mount race, a portal-over-webview
// click-eater, or a modal that steals focus from N live webviews would never
// show up. This spec stacks several Electron <webview> compositor layers plus a
// MUI modal at once and asserts the renderer survives, every webview actually
// attaches, and the modal opens/closes cleanly on top of them.

function backendLogPath(): string {
  if (process.platform === 'win32') return path.join(process.env.APPDATA || '', 'OpenSwarm', 'data', 'backend.log');
  if (process.platform === 'darwin') return path.join(os.homedir(), 'Library', 'Application Support', 'OpenSwarm', 'data', 'backend.log');
  return path.join(process.env.XDG_DATA_HOME || path.join(os.homedir(), '.local', 'share'), 'OpenSwarm', 'data', 'backend.log');
}
function crashCount(): number {
  try { return (fs.readFileSync(backendLogPath(), 'utf8').match(/renderer process gone/g) || []).length; }
  catch { return 0; }
}

const WEBVIEWS = Number(process.env.OPENSWARM_E2E_WEBVIEWS || 3);
// Entirely webview-based. Electron <webview> compositor layers do not attach
// under Playwright-controlled Electron 40 (CastLabs) in a headless/automated
// launch, so this whole spec is gated behind OPENSWARM_E2E_HEAVY=1 and meant to
// run on a real display (or manually). See onboarding-completion.spec.ts for the
// same heavy-surface caveat and the New-Agent renderer-crash finding.
const HEAVY = process.env.OPENSWARM_E2E_HEAVY === '1';

test.describe.configure({ mode: 'serial' });
(HEAVY ? test.describe : test.describe.skip)(`multi-window stress (${WEBVIEWS} webviews + modal)`, () => {
  let app: ElectronApplication;
  let page: Page;
  let vis: VisibilityHandle;
  let baseline = 0;
  const errors: Array<{ kind: string; text: string }> = [];
  const WHITELIST = [/DevTools listening/i, /Autofill/i, /electron-store/i, /downloadable font/i, /ERR_INTERNET_DISCONNECTED/i, /net::ERR_/i];

  test.beforeAll(async () => {
    app = await launchApp();
    page = await waitForMainWindow(app);
    vis = await startVisibility(app, page, `multi-window-stress-${WEBVIEWS}`);
    page.on('pageerror', (e) => errors.push({ kind: 'pageerror', text: String(e?.message ?? e) }));
    page.on('console', (m) => { if (m.type() === 'error') errors.push({ kind: 'console', text: m.text() }); });
    baseline = crashCount();
  });
  test.afterAll(async () => { try { await vis?.stop(); } catch {} await app?.close().catch(() => {}); });

  const must = async (sel: string, label: string) => {
    const loc = page.locator(sel);
    expect(await loc.count(), `${label}: no element matched ${sel}`).toBeGreaterThan(0);
    await expect(loc.first(), `${label}: ${sel} not visible`).toBeVisible({ timeout: 8000 });
    return loc.first();
  };
  const mustClick = async (sel: string, label: string) => { const el = await must(sel, label); await el.click({ timeout: 8000 }); return el; };
  const freshErrors = (mark: number) => errors.slice(mark).filter((e) => !WHITELIST.some((rx) => rx.test(e.text))).map((e) => `${e.kind}: ${e.text}`).join('\n');
  const webviewCount = () => page.locator('webview').count();

  const ensureSidebarExpanded = async () => {
    const toggle = page.locator('[data-onboarding="sidebar-toggle"]');
    if ((await toggle.getAttribute('aria-expanded')) === 'false') await toggle.click({ timeout: 5000 });
    await expect(toggle, 'sidebar never expanded').toHaveAttribute('aria-expanded', 'true', { timeout: 5000 });
  };
  const ensureDashboardActive = async () => {
    await ensureSidebarExpanded();
    await mustClick('[data-onboarding="sidebar-dashboards"]', 'dashboards');
    const newAgent = page.locator('[data-onboarding="new-agent-button"]').first();
    if (await newAgent.isVisible().catch(() => false)) return;
    const createBtn = page.locator('[data-onboarding="sidebar-dashboards"] button').first();
    await expect(createBtn, 'no create-dashboard "+" button').toBeVisible({ timeout: 5000 });
    await createBtn.click({ timeout: 5000 });
    await expect.poll(() => page.url(), { timeout: 8000 }).toMatch(/\/dashboard\//);
    await expect(newAgent, 'dashboard toolbar never mounted').toBeVisible({ timeout: 12_000 });
  };

  test('self-check: must() fails loudly on a missing target', async () => {
    let threw = false;
    try { await must('#__not_in_dom_mws__', 'sentinel'); } catch { threw = true; }
    expect(threw, 'must() did NOT fail on a missing element').toBe(true);
  });

  test(`stack ${WEBVIEWS} browser webviews; every one attaches, renderer survives`, async ({}, info) => {
    const mark = errors.length;
    await ensureDashboardActive();
    const before = await webviewCount();
    for (let i = 0; i < WEBVIEWS; i++) {
      vis?.mark('open-webview', { i });
      await mustClick('[data-onboarding="browser-button"]', `browser #${i + 1}`);
      // Each click must add exactly one more attached webview (mount race guard).
      await expect.poll(webviewCount, { message: `webview ${i + 1} never attached`, timeout: 15_000 }).toBeGreaterThanOrEqual(before + i + 1);
      expect(crashCount(), `opening webview ${i + 1} crashed the renderer`).toBe(baseline);
    }
    await page.screenshot({ path: info.outputPath('stacked-webviews.png') });
    expect(await webviewCount(), 'final webview count short').toBeGreaterThanOrEqual(before + WEBVIEWS);
    expect(freshErrors(mark), 'stacking webviews produced errors').toBe('');
  });

  test('open Settings modal ON TOP of the live webviews, then close it', async () => {
    const mark = errors.length;
    const wvBefore = await webviewCount();
    await ensureSidebarExpanded();
    await mustClick('[data-onboarding="sidebar-settings-button"]', 'settings (over webviews)');
    // Modal renders and is interactable even with N webview compositor layers behind it.
    await expect(page.getByRole('tab', { name: 'General' }), 'settings modal did not open over webviews').toBeVisible({ timeout: 8000 });
    await mustClick('[data-onboarding="settings-models-tab"]', 'models tab over webviews');
    await expect(page.locator('[data-onboarding="settings-api-keys"]')).toBeVisible({ timeout: 8000 });
    await mustClick('[data-onboarding="settings-close-button"]', 'close settings');
    await expect(page.getByRole('tab', { name: 'General' }), 'settings modal did not close').toHaveCount(0, { timeout: 5000 });
    // Webviews must survive the modal open/close (no teardown side effect).
    expect(await webviewCount(), 'webviews were torn down by the modal').toBeGreaterThanOrEqual(wvBefore);
    expect(crashCount(), 'settings-over-webviews crashed the renderer').toBe(baseline);
    expect(freshErrors(mark), 'settings-over-webviews produced errors').toBe('');
  });

  test('rapid settings open/close x5 over webviews does not leak or crash', async () => {
    const mark = errors.length;
    await ensureSidebarExpanded();
    for (let i = 0; i < 5; i++) {
      await mustClick('[data-onboarding="sidebar-settings-button"]', `rapid open ${i}`);
      await expect(page.getByRole('tab', { name: 'General' })).toBeVisible({ timeout: 6000 });
      await mustClick('[data-onboarding="settings-close-button"]', `rapid close ${i}`);
      await expect(page.getByRole('tab', { name: 'General' })).toHaveCount(0, { timeout: 5000 });
      expect(crashCount(), `rapid cycle ${i} crashed renderer`).toBe(baseline);
    }
    expect(freshErrors(mark), 'rapid open/close produced errors').toBe('');
  });

  test('final: zero new renderer-gone-lines across the whole stress run', () => {
    expect(crashCount(), 'a step crashed the renderer somewhere').toBe(baseline);
  });
});
