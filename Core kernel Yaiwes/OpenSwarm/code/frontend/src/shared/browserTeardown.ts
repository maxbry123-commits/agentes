import type { Dispatch } from '@reduxjs/toolkit';
import { removeBrowserCard } from '@/shared/state/dashboardLayoutSlice';
import { getBrowserWebviews } from '@/shared/browserRegistry';
import { forgetBrowser } from '@/shared/browserFocus';

interface CdpBridge {
  cdpDetachClean?: (wcId: number) => Promise<unknown>;
}

// A wedged CDP pipe must never hold a card open; cap the whole detach round-trip.
const DETACH_BUDGET_MS = 600;

// Detach the CDP debugger from every webview of a browser card BEFORE React unmounts them. Otherwise a late DevTools notification (a Target child-session message or Network.responseReceivedExtraInfo) lands on a session Chromium has already freed and SIGSEGVs the whole browser process. Bounded + fail-open.
export async function detachBrowserCdp(browserId: string): Promise<void> {
  const ow = (window as unknown as { openswarm?: CdpBridge }).openswarm;
  if (!ow?.cdpDetachClean) return;
  const detaches: Promise<unknown>[] = [];
  for (const wv of getBrowserWebviews(browserId)) {
    try {
      detaches.push(ow.cdpDetachClean(wv.getWebContentsId()).catch(() => {}));
    } catch {
      // webview already torn down; nothing to detach
    }
  }
  if (!detaches.length) return;
  await Promise.race([
    Promise.allSettled(detaches),
    new Promise<void>((resolve) => setTimeout(resolve, DETACH_BUDGET_MS)),
  ]);
}

// Park each doomed webview at about:blank and wait for the COMMIT EVENT (plus one settle frame), so
// React never unmounts a live GPU surface mid-composite; browser cards are the heaviest surfaces and
// had no quiesce at all while app cards did (ENG-228). Bounded generously; the card is already gone
// from the user's view, so the wait costs nothing visible.
const QUIESCE_BUDGET_MS = 1500;
export async function quiesceBrowserWebviews(browserId: string): Promise<void> {
  const waits: Promise<void>[] = [];
  for (const wv of getBrowserWebviews(browserId)) {
    try {
      const committed = new Promise<void>((resolve) => {
        const done = (): void => { wv.removeEventListener('did-navigate', done); resolve(); };
        wv.addEventListener('did-navigate', done);
      });
      void (wv as unknown as { loadURL: (u: string) => Promise<void> }).loadURL('about:blank').catch(() => {});
      waits.push(Promise.race([committed, new Promise<void>((r) => setTimeout(r, QUIESCE_BUDGET_MS))]));
    } catch {
      // webview already torn down; nothing to quiesce
    }
  }
  if (waits.length) {
    await Promise.allSettled(waits);
    await new Promise<void>((resolve) => requestAnimationFrame(() => resolve()));
  }
}

// Clean-detach a browser card's CDP, quiesce its GPU surfaces, THEN remove it. All three card-removal paths (the X button, the agent-finish timer, and keyboard delete) route through here so none of them tears the webview down with the debugger still attached or a live surface still compositing. Every step is bounded, so removal is never blocked by a dead pipe.
export async function removeBrowserCardCleanly(
  browserId: string,
  dispatch: Dispatch,
): Promise<void> {
  await detachBrowserCdp(browserId);
  await quiesceBrowserWebviews(browserId);
  forgetBrowser(browserId);
  dispatch(removeBrowserCard(browserId));
}

// Detach many browsers' CDP concurrently but CAPPED (order-independent, the only invariant is all
// debuggers gone before any unmount). Serial cost ~72ms/browser (a 20-card teardown lagged >1s);
// unbounded parallel risks flooding the debugger host at pathological counts and leaving one
// attached at unmount. Batches of DETACH_CONCURRENCY are the middle: flat-ish latency, no flood.
const DETACH_CONCURRENCY = 10;
export async function detachBrowsersCdpBounded(browserIds: string[]): Promise<void> {
  for (let i = 0; i < browserIds.length; i += DETACH_CONCURRENCY) {
    await Promise.allSettled(browserIds.slice(i, i + DETACH_CONCURRENCY).map((id) => detachBrowserCdp(id)));
  }
}

// Batch remove: bounded-parallel detach, THEN remove. Keeps the crash-safe ordering but flat.
export async function removeBrowserCardsCleanly(
  browserIds: string[],
  dispatch: Dispatch,
): Promise<void> {
  await detachBrowsersCdpBounded(browserIds);
  // Same batching rationale as detach: a mass close (multi-select delete) quiesces in bounded waves, so the surfaces release before any unmount without flooding the compositor.
  for (let i = 0; i < browserIds.length; i += DETACH_CONCURRENCY) {
    await Promise.allSettled(browserIds.slice(i, i + DETACH_CONCURRENCY).map((id) => quiesceBrowserWebviews(id)));
  }
  for (const id of browserIds) {
    forgetBrowser(id);
    dispatch(removeBrowserCard(id));
  }
}
