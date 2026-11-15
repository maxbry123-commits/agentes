import type { Dispatch } from '@reduxjs/toolkit';
import { removeViewCard } from '@/shared/state/dashboardLayoutSlice';
import { getViewWebview } from '@/shared/viewWebviewRegistry';

// A wedged app must never hold a card open; cap the whole quiesce so delete stays responsive. The
// old 250ms timer was fail-OPEN: on a loaded machine the about:blank commit takes longer, the timer
// won, and the destroy ripped a LIVE GPU surface mid-composite, which is the whole-app crash family
// (ENG-228, Haik's close-crashes). Now we wait for the commit EVENT with a generous ceiling; the
// UI already hid the card, so the extra wait costs nothing visible.
const QUIESCE_BUDGET_MS = 1500;

// Navigate a doomed card's webview to about:blank so the running app's heavy GPU surfaces are released BEFORE React destroys the <webview>, leaving only a trivial surface to tear down.
export async function quiesceViewWebview(outputId: string): Promise<void> {
  const wv = getViewWebview(outputId);
  if (!wv) return;
  try {
    const committed = new Promise<void>((resolve) => {
      const done = (): void => { wv.removeEventListener('did-navigate', done); resolve(); };
      wv.addEventListener('did-navigate', done);
    });
    void wv.loadURL('about:blank').catch(() => {});
    await Promise.race([
      committed,
      new Promise<void>((resolve) => setTimeout(resolve, QUIESCE_BUDGET_MS)),
    ]);
    // One settle frame after commit so the compositor lets go of the old surface before React unmounts the element.
    await new Promise<void>((resolve) => requestAnimationFrame(() => resolve()));
  } catch {
    // webview already torn down; nothing to quiesce
  }
}

// Quiesce a card's live preview surface, THEN remove it. Every view-card delete path routes through here so none rips a live <webview> GPU surface out mid-composite. Awaited in a loop (multi-select Delete, orphan prune) the teardowns SERIALIZE, which is what stops the simultaneous "non-existent mailbox" pile-up that kills the GPU process.
export async function removeViewCardCleanly(outputId: string, dispatch: Dispatch): Promise<void> {
  await quiesceViewWebview(outputId);
  dispatch(removeViewCard(outputId));
}
