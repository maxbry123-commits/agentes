import { defineConfig } from '@playwright/test';

// E2E config for driving the PACKAGED Electron app (not a dev server). We launch
// the real built binary via Playwright's _electron API, so there is no webServer
// and no browser project — Electron ships its own Chromium. Runs identically on
// macOS and Windows; CI builds the artifact first, then runs these.
export default defineConfig({
  testDir: './tests',
  // Boot of a cold packaged app (Defender scan + Python cold start) can take a
  // while on first launch, so allow generous per-test time.
  timeout: 180_000,
  expect: { timeout: 30_000 },
  fullyParallel: false,        // one packaged app instance at a time (single-instance lock)
  workers: 1,
  reporter: [['list'], ['json', { outputFile: 'results.json' }]],
  retries: 0,
});
