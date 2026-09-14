// The browser card you last clicked into, so global shortcuts (Ctrl+R, zoom, Ctrl+Tab) target it; imperative + read on keydown so no re-render, and cleared the moment you click off any browser card.
let lastInteractedBrowserId: string | null = null;

// Recently-used browser ids, newest first; the top KEEP_ALIVE_CAP stay mounted across dashboard switches + off-screen so their sessionStorage (logins like Discord) survives, the rest get reclaimed by the normal suspend (LRU).
const KEEP_ALIVE_CAP = 4;
let recentBrowserIds: string[] = [];

export function setLastInteractedBrowser(browserId: string): void {
  lastInteractedBrowserId = browserId;
  recentBrowserIds = [browserId, ...recentBrowserIds.filter((id) => id !== browserId)].slice(0, 32);
}

export function clearLastInteractedBrowser(): void {
  lastInteractedBrowserId = null;
}

export function getLastInteractedBrowser(): string | null {
  return lastInteractedBrowserId;
}

export function getKeepAliveBrowserIds(): string[] {
  return recentBrowserIds.slice(0, KEEP_ALIVE_CAP);
}

export function isKeepAliveBrowser(browserId: string): boolean {
  return getKeepAliveBrowserIds().includes(browserId);
}

// Drop a closed browser from focus + keep-alive tracking so a dead id can't hog a slot.
export function forgetBrowser(browserId: string): void {
  recentBrowserIds = recentBrowserIds.filter((id) => id !== browserId);
  if (lastInteractedBrowserId === browserId) lastInteractedBrowserId = null;
}
