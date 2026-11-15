import React from 'react';

// Mission Control's spaces rail: a vertical wheel scrolls it sideways, a press-drag pans it, and the
// active space is always kept in view. Lives apart from SpacesStrip so the strip stays about tiles.
const DRAG_THRESHOLD_PX = 4;
const EDGE_EPSILON_PX = 2;
const MIN_PAGE_PX = 220;

export const ACTIVE_TILE_ATTR = 'data-space-active';

export interface StripScroll {
  scrollRef: React.MutableRefObject<HTMLDivElement | null>;
  atStart: boolean;
  atEnd: boolean;
  overflowing: boolean;
  dragging: boolean;
  scrollByPage: (dir: -1 | 1) => void;
}

const wantsMotion = (): boolean => !window.matchMedia?.('(prefers-reduced-motion: reduce)').matches;

export function useStripScroll(activeId: string | null, itemCount: number, animate: boolean): StripScroll {
  const scrollRef = React.useRef<HTMLDivElement | null>(null);
  const [edges, setEdges] = React.useState({ atStart: true, atEnd: true, overflowing: false });
  const [dragging, setDragging] = React.useState(false);

  const syncEdges = React.useCallback((): void => {
    const el = scrollRef.current;
    if (!el) return;
    const max = el.scrollWidth - el.clientWidth;
    const next = {
      atStart: el.scrollLeft <= EDGE_EPSILON_PX,
      atEnd: el.scrollLeft >= max - EDGE_EPSILON_PX,
      overflowing: max > EDGE_EPSILON_PX,
    };
    setEdges((prev) => (
      prev.atStart === next.atStart && prev.atEnd === next.atEnd && prev.overflowing === next.overflowing ? prev : next
    ));
  }, []);

  React.useEffect(() => {
    const el = scrollRef.current;
    if (!el) return undefined;
    // The canvas zooms on wheel, so anything this rail consumes must stop here and never bubble onward.
    const onWheel = (e: WheelEvent): void => {
      if (el.scrollWidth - el.clientWidth <= EDGE_EPSILON_PX) return;
      const delta = Math.abs(e.deltaX) > Math.abs(e.deltaY) ? e.deltaX : e.deltaY;
      if (delta === 0) return;
      el.scrollLeft += delta;
      e.preventDefault();
      e.stopPropagation();
    };
    el.addEventListener('wheel', onWheel, { passive: false });
    el.addEventListener('scroll', syncEdges, { passive: true });
    const ro = new ResizeObserver(syncEdges);
    ro.observe(el);
    return () => {
      el.removeEventListener('wheel', onWheel);
      el.removeEventListener('scroll', syncEdges);
      ro.disconnect();
    };
  }, [syncEdges]);

  React.useEffect(() => { syncEdges(); }, [syncEdges, itemCount]);

  React.useEffect(() => {
    const el = scrollRef.current;
    if (!el) return undefined;
    let startX = 0;
    let startLeft = 0;
    let moved = false;
    let swallowClick = false;

    const onMove = (e: PointerEvent): void => {
      const dx = e.clientX - startX;
      if (!moved) {
        if (Math.abs(dx) < DRAG_THRESHOLD_PX) return;
        moved = true;
        setDragging(true);
      }
      el.scrollLeft = startLeft - dx;
      e.preventDefault();
    };
    const onUp = (): void => {
      window.removeEventListener('pointermove', onMove);
      window.removeEventListener('pointerup', onUp);
      window.removeEventListener('pointercancel', onUp);
      if (!moved) return;
      swallowClick = true;
      setDragging(false);
    };
    const onDown = (e: PointerEvent): void => {
      if (e.button !== 0) return;  // right-click belongs to the tile context menu
      if ((e.target as HTMLElement).closest('input')) return;  // the inline rename field keeps its own caret
      swallowClick = false;
      startX = e.clientX;
      startLeft = el.scrollLeft;
      moved = false;
      window.addEventListener('pointermove', onMove);
      window.addEventListener('pointerup', onUp);
      window.addEventListener('pointercancel', onUp);
    };
    // A pan that ends on a tile still fires a click, so eat exactly that one and let real clicks through.
    const onClickCapture = (e: MouseEvent): void => {
      if (!swallowClick) return;
      swallowClick = false;
      e.preventDefault();
      e.stopPropagation();
    };

    el.addEventListener('pointerdown', onDown);
    el.addEventListener('click', onClickCapture, true);
    return () => {
      el.removeEventListener('pointerdown', onDown);
      el.removeEventListener('click', onClickCapture, true);
      window.removeEventListener('pointermove', onMove);
      window.removeEventListener('pointerup', onUp);
      window.removeEventListener('pointercancel', onUp);
    };
  }, []);

  React.useEffect(() => {
    const el = scrollRef.current;
    if (!el || !activeId) return;
    const target = el.querySelector<HTMLElement>(`[${ACTIVE_TILE_ATTR}="true"]`);
    if (!target) return;
    const max = el.scrollWidth - el.clientWidth;
    if (max <= EDGE_EPSILON_PX) return;
    const left = target.offsetLeft;
    if (left >= el.scrollLeft && left + target.offsetWidth <= el.scrollLeft + el.clientWidth) return;
    const centered = Math.max(0, Math.min(max, left - (el.clientWidth - target.offsetWidth) / 2));
    el.scrollTo({ left: centered, behavior: animate && wantsMotion() ? 'smooth' : 'auto' });
  }, [activeId, itemCount, animate]);

  const scrollByPage = React.useCallback((dir: -1 | 1): void => {
    const el = scrollRef.current;
    if (!el) return;
    const step = Math.max(MIN_PAGE_PX, el.clientWidth * 0.8);
    el.scrollBy({ left: dir * step, behavior: wantsMotion() ? 'smooth' : 'auto' });
  }, []);

  return { scrollRef, ...edges, dragging, scrollByPage };
}
