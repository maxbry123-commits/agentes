// How far the camera is allowed to pull back when a new card appears.
//
// The reveal takes min(current, fit) so a spawn never zooms IN, which is right. But that made the
// camera monotonically decreasing: every spawn that did not fit ratcheted it out and nothing ever
// brought it back. Measured over one ordinary session: 100% -> 88% -> 79% -> 61% -> 36% -> 18%, at
// which point the workspace is a fifth of the viewport and not one word is readable.
//
// So the reveal gets a floor. Fitting every card on screen is not the goal; seeing the new one is.
// A hand-driven zoom is untouched and can still go to the hard minimum.

export const REVEAL_MIN_ZOOM = 0.5;

export function revealZoom(currentZoom: number, fitZoom: number, minZoom: number, maxZoom: number): number {
  // Floor the FIT, not the result. Flooring the result would drag a user who had deliberately zoomed
  // out back IN, which breaks the one rule this function already had: a reveal never zooms in.
  const floor = Math.max(minZoom, REVEAL_MIN_ZOOM);
  return Math.min(Math.min(currentZoom, Math.max(fitZoom, floor)), maxZoom);
}
