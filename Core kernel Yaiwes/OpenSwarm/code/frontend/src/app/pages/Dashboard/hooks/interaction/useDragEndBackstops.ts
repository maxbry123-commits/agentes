import { useEffect } from 'react';

/** Window-level insurance for a card's local drag: a release the drag handle never hears
    (pointercancel, capture lost to a mid-drag remount, mouseup outside the window, app blur)
    still commits the drag. Without this the stuck drag state re-pins the card to the cursor on
    every camera pan, the "card glued to the POV until reload" bug. */
export function useDragEndBackstops(
  active: boolean,
  finalize: (clientX: number, clientY: number, shiftKey: boolean) => void,
  abort: () => void,
): void {
  useEffect(() => {
    if (!active) return undefined;
    const onUp = (e: PointerEvent): void => finalize(e.clientX, e.clientY, e.shiftKey);
    window.addEventListener('pointerup', onUp);
    window.addEventListener('pointercancel', abort);
    window.addEventListener('blur', abort);
    return () => {
      window.removeEventListener('pointerup', onUp);
      window.removeEventListener('pointercancel', abort);
      window.removeEventListener('blur', abort);
    };
  }, [active, finalize, abort]);
}
