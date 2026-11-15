import { test, expect, ElectronApplication, Page } from '@playwright/test';
import { launchApp, waitForMainWindow, hasAnyProviderKey } from '../helpers/launch';
import { startVisibility, VisibilityHandle } from '../helpers/visibility';
import fs from 'fs';
import os from 'os';
import path from 'path';

// Real provider round-trip: types a tiny prompt into a new agent, sends it, and
// asserts an assistant message bubble arrives with non-empty text and no
// renderer crash. Auto-skips entirely when no provider key is in env, so CI
// legs without Actions Secrets stay green. Keys come from process.env only;
// nothing is read from or written to a committed file.

function backendLogPath(): string {
  if (process.platform === 'win32') return path.join(process.env.APPDATA || '', 'OpenSwarm', 'data', 'backend.log');
  if (process.platform === 'darwin') return path.join(os.homedir(), 'Library', 'Application Support', 'OpenSwarm', 'data', 'backend.log');
  return path.join(process.env.XDG_DATA_HOME || path.join(os.homedir(), '.local', 'share'), 'OpenSwarm', 'data', 'backend.log');
}
function crashCount(): number {
  try { return (fs.readFileSync(backendLogPath(), 'utf8').match(/renderer process gone/g) || []).length; }
  catch { return 0; }
}

test.describe.configure({ mode: 'serial' });
test.describe('real agent round-trip', () => {
  let app: ElectronApplication;
  let page: Page;
  let baselineCrashes = 0;
  let vis: VisibilityHandle;

  // Whole describe skips with a clear reason when no key is wired, so we
  // never silently green this on a leg that can't actually test it.
  test.beforeAll(async () => {
    test.skip(!hasAnyProviderKey(), 'no provider env key set; pass ANTHROPIC_API_KEY or OPENAI_API_KEY etc. to enable');
    test.skip(process.env.CI !== 'true' && process.env.OPENSWARM_E2E_SEED !== '1', 'seed gate not enabled; set OPENSWARM_E2E_SEED=1 for local runs');
    app = await launchApp();
    page = await waitForMainWindow(app);
    vis = await startVisibility(app, page, 'real-agent-roundtrip');
    baselineCrashes = crashCount();
  });
  test.afterAll(async () => {
    try { await vis?.stop(); } catch {}
    await app?.close().catch(() => {});
  });

  test('compose, send, and receive an assistant reply', async ({}, info) => {
    // Find the New Agent button on the dashboard toolbar.
    const newAgentBtn = page.locator('[data-onboarding="new-agent-button"]');
    await expect(newAgentBtn).toBeVisible({ timeout: 15_000 });
    await newAgentBtn.click();

    const editor = page.locator('[data-onboarding="chat-input"]').first();
    await expect(editor, 'EditorSurface did not mount').toBeVisible({ timeout: 15_000 });
    await editor.click();
    await page.keyboard.type('reply with the single word: pong', { delay: 10 });
    await expect.poll(async () => (await editor.innerText()).trim(), { timeout: 5_000 }).toContain('pong');

    const sendBtn = page.locator('[data-onboarding="chat-send-button"]');
    await expect(sendBtn, 'send button never enabled; provider likely unconfigured').toBeVisible({ timeout: 10_000 });
    await sendBtn.click();
    await page.screenshot({ path: info.outputPath('after-send.png') });

    // Wait for an assistant bubble to appear with non-empty text. Bubbles tag
    // themselves via data-select-meta JSON; matching on substring is enough.
    const assistantBubble = page.locator('[data-select-type="message"][data-select-meta*="\\"role\\":\\"assistant\\""]');
    await expect.poll(async () => assistantBubble.count(), { timeout: 120_000 }).toBeGreaterThan(0);

    // Allow the streaming bubble a moment to accumulate text past zero chars.
    await expect.poll(async () => {
      const n = await assistantBubble.count();
      if (n === 0) return 0;
      const text = (await assistantBubble.first().innerText()).trim();
      return text.length;
    }, { timeout: 60_000 }).toBeGreaterThan(0);

    const finalText = (await assistantBubble.first().innerText()).trim();
    expect(finalText.length, 'assistant bubble appeared but text never populated').toBeGreaterThan(0);
    await page.screenshot({ path: info.outputPath('assistant-replied.png') });

    expect(crashCount(), 'renderer crashed during real round-trip').toBe(baselineCrashes);
  });
});
