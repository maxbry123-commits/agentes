// Logical cursor position store; rAF-coalesced to ~30fps so popups don't re-render every frame.

import { useSyncExternalStore } from 'react';

interface CursorPos {
  x: number;
  y: number;
  visible: boolean;
  // Windows-only: the motionWin shim strips Framer's spring, so the cursor wrapper eases via CSS transition. `instant` tells it to disable the transition for this update — set true while tracking a (mostly stationary) element so the cursor snaps like Mac's controls.set, false for moveTo/fadeOut so it eases like controls.start. Ignored on Mac (Framer drives the motion).
  instant: boolean;
}

let state: CursorPos = { x: 0, y: 0, visible: false, instant: true };
let pendingState: CursorPos | null = null;
const listeners = new Set<() => void>();

// 1.5px: smooth-feeling threshold that avoids per-sub-pixel React renders.
const COALESCE_PX = 1.5;
let rafScheduled = false;

function flush() {
  rafScheduled = false;
  if (!pendingState) return;
  state = pendingState;
  pendingState = null;
  listeners.forEach((l) => l());
}

export const cursorStore = {
  get: () => state,
  set(next: Partial<CursorPos>) {
    const merged = { ...(pendingState ?? state), ...next };

    // Visibility transitions bypass coalescing (mounts/unmounts must flush immediately).
    const visibilityChanged = merged.visible !== state.visible;
    // `instant` flips the Windows CSS-transition mode (snap vs ease). Commit it immediately, like visibility, so moveTo can arm the eased transition a paint BEFORE it moves the cursor: a same-position arm write is otherwise coalesced silently here, so the move and the none->420ms transition flip land in one recalc and Chromium renders it as an instant jump. No-op on Mac (the wrapper there is Framer-driven and ignores `instant`).
    const instantChanged = merged.instant !== state.instant;
    const dx = Math.abs(merged.x - state.x);
    const dy = Math.abs(merged.y - state.y);
    const significantMove = dx >= COALESCE_PX || dy >= COALESCE_PX;

    if (visibilityChanged || instantChanged) {
      state = merged;
      pendingState = null;
      rafScheduled = false;
      listeners.forEach((l) => l());
      return;
    }

    if (!significantMove) {
      // Below threshold: stash silently; next significant move will pick up these pending values.
      pendingState = merged;
      return;
    }

    pendingState = merged;
    if (!rafScheduled) {
      rafScheduled = true;
      requestAnimationFrame(flush);
    }
  },
  subscribe(listener: () => void) {
    listeners.add(listener);
    return () => listeners.delete(listener);
  },
};

export function useCursorPosition(): CursorPos {
  return useSyncExternalStore(
    cursorStore.subscribe,
    cursorStore.get,
    cursorStore.get,
  );
}
