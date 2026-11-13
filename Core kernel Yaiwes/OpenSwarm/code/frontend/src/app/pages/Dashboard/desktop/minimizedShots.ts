/** Last visual of a card, frozen while it could still paint; in-memory only, keyed by card id. */
const shots = new Map<string, string>();
const CAP = 40;
const listeners = new Set<() => void>();

/** Readers that render a frozen shot subscribe here; a saved frame is otherwise invisible to them. */
export function subscribeMinimizedShots(fn: () => void): () => void {
  listeners.add(fn);
  return () => { listeners.delete(fn); };
}

export function saveMinimizedShot(cardId: string, dataUrl: string): void {
  if (shots.size >= CAP && !shots.has(cardId)) {
    const oldest = shots.keys().next().value;
    if (oldest) shots.delete(oldest);
  }
  shots.set(cardId, dataUrl);
  listeners.forEach((fn) => fn());
}

export function getMinimizedShot(cardId: string): string | undefined {
  return shots.get(cardId);
}

export function dropMinimizedShot(cardId: string): void {
  if (!shots.delete(cardId)) return;
  listeners.forEach((fn) => fn());
}
