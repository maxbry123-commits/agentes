import { getAllViewOutputIds } from '@/shared/viewWebviewRegistry';
import { getAllBrowserIds } from '@/shared/browserRegistry';
import { quiesceViewWebview } from '@/shared/viewTeardown';
import { detachBrowsersCdpBounded } from '@/shared/browserTeardown';

// Switching dashboards clears every card from the store in ONE reducer (resetLayout), so React
// unmounts all the outgoing app + browser <webview>s in a single frame. Ripping several live GPU
// surfaces out at once (app previews) or unmounting a browser with its CDP debugger still attached
// piles up "non-existent mailbox" errors and SIGSEGVs the GPU/browser process, taking the whole app
// down with no crash dump (the "navigate away and it quits itself" bug). We ready the outgoing
// webviews before the reset so only trivial surfaces are left to tear down; keep-alive browsers are
// skipped so they survive the switch with their session intact. Fail-open + bounded (the helpers
// self-cap), so a wedged webview can never block the switch.
export async function prepareDashboardSwitch(keepBrowserIds: string[]): Promise<void> {
  const keep = new Set(keepBrowserIds);
  // Views release their heavy GPU SharedImage surface ONE AT A TIME (parallel surface teardown is
  // the "non-existent mailbox" pile-up); browser CDP detaches are order-independent (the crash is
  // unmounting with a debugger ATTACHED, and all we need is every debugger gone before the reset),
  // so they run in PARALLEL: serial detach added ~72ms/browser and made a 20-card switch lag 1.4s.
  for (const outputId of getAllViewOutputIds()) {
    await quiesceViewWebview(outputId);
  }
  await detachBrowsersCdpBounded(getAllBrowserIds().filter((b) => !keep.has(b)));
}
