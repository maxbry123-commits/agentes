// The card you've clicked INTO, so plain scroll reads its content (chat transcript, scheduled-task
// list) while scroll everywhere else zooms the canvas (Google Maps model). Imperative + read on the
// wheel handler so no re-render. Browser/app cards aren't tracked here: their guest page owns its own
// scroll/zoom (Maps, Figma), so plain wheel always stays in them.
let scrollFocusedCardId: string | null = null;

// Message bubbles carry their own data-select-id, so match the card by walking, not by closest().
function insideFocusedCard(target: EventTarget | null): boolean {
  let el = target as HTMLElement | null;
  while (el) {
    if (el.getAttribute?.('data-select-id') === scrollFocusedCardId) return true;
    el = el.parentElement;
  }
  return false;
}

// Focus follows the cursor: the moment it leaves the card, scroll belongs to the canvas again, so a
// chat you once clicked can't own the wheel forever and make zoom look broken. Listen on pointermove,
// not pointerover: boundary events also fire when a re-render swaps the element under a still cursor.
function releaseOnPointerLeave(e: PointerEvent): void {
  if (insideFocusedCard(e.target)) return;
  setScrollFocusedCard(null);
}

export function setScrollFocusedCard(id: string | null): void {
  if (id === scrollFocusedCardId) return;
  scrollFocusedCardId = id;
  if (id) document.addEventListener('pointermove', releaseOnPointerLeave, true);
  else document.removeEventListener('pointermove', releaseOnPointerLeave, true);
}

export function getScrollFocusedCard(): string | null {
  return scrollFocusedCardId;
}
