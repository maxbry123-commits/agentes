import { getWebview } from './browserRegistry';

// One place for "get me a picture of a browser card, best effort". Four callers were hand-rolling
// it and three got it wrong in a different way, because capturePage fails in two shapes: it THROWS
// synchronously on a webview that is attached but not yet dom-ready (unguarded, that one took the
// whole dashboard down through AgentCard's ErrorBoundary), and it never settles at all on a guest
// the compositor is not drawing, so the timeout is not optional either.
const DEFAULT_SHOT_TIMEOUT_MS = 1200;

/** A data URL of the card's live page, or null. Never throws, never hangs. */
export async function captureBrowserShot(browserId: string, timeoutMs: number = DEFAULT_SHOT_TIMEOUT_MS): Promise<string | null> {
  try {
    const wv = getWebview(browserId);
    if (!wv?.capturePage) return null;
    const image = await Promise.race([
      wv.capturePage(),
      new Promise<null>((resolve) => { window.setTimeout(() => resolve(null), timeoutMs); }),
    ]);
    return image && !image.isEmpty() ? image.toDataURL() : null;
  } catch {
    return null;
  }
}
