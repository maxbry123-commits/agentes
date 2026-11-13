import { test, expect, ElectronApplication, Page } from '@playwright/test';
import { launchApp, waitForMainWindow, readBuildInfo } from '../helpers/launch';

// End-to-end smoke of the PACKAGED app. Everything here runs unchanged on macOS
// and Windows; CI builds the artifact for the OS, then runs this. It deliberately
// avoids anything needing a provider API key (no agent turn) so it is hermetic
// and deterministic on a clean machine.
test.describe('packaged app boot', () => {
  let app: ElectronApplication;
  let win: Page;

  test.beforeAll(async () => {
    app = await launchApp();
    win = await waitForMainWindow(app);
  });

  test.afterAll(async () => {
    await app?.close().catch(() => {});
  });

  test('main window paints the React shell', async () => {
    // waitForMainWindow already required a mounted #root; assert it explicitly.
    const childCount = await win.evaluate(() => document.getElementById('root')!.childElementCount);
    expect(childCount).toBeGreaterThan(0);
  });

  test('preload bridge is exposed', async () => {
    const hasBridge = await win.evaluate(() => ({
      port: typeof (window as any).openswarm?.getBackendPort === 'function',
      buildInfo: typeof (window as any).openswarm?.getBuildInfo === 'function',
    }));
    expect(hasBridge.port).toBe(true);
    expect(hasBridge.buildInfo).toBe(true);
  });

  test('backend reaches HTTP-ready (health 200)', async () => {
    const port: number = await win.evaluate(() => (window as any).openswarm.getBackendPort());
    expect(port).toBeGreaterThan(0);
    // Poll the real backend the packaged app spawned, from inside the renderer
    // (same origin/path the app itself uses), until it answers 200.
    await expect.poll(
      async () =>
        win.evaluate(
          (p) => fetch(`http://127.0.0.1:${p}/api/health/check`).then((r) => r.status).catch(() => 0),
          port,
        ),
      { timeout: 150_000, intervals: [1000] },
    ).toBe(200);
  });

  test('provenance: running app reports the built commit', async () => {
    const info = await win.evaluate(() => (window as any).openswarm.getBuildInfo());
    const onDisk = readBuildInfo();
    expect(info.sha).toBe(onDisk.sha);
    expect(info.shortSha).toMatch(/^[0-9a-f]{12}$/);
    expect(info.version).toBe(onDisk.version);
  });

  test('app version is reported', async () => {
    const version = await win.evaluate(() => (window as any).openswarm.getAppVersion());
    expect(version).toMatch(/^\d+\.\d+\.\d+/);
  });
});
