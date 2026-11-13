import { useCallback, useEffect, useLayoutEffect, useMemo, useRef, useState } from 'react';

// Generic list windowing, lifted from AgentChat's transcript virtualizer so a long schedule list mounts only the rows near the viewport (off-screen rows unmount, replaced by measured-height spacers). Rows can be any height; the hook measures them once on screen and estimates the rest. Top-anchored: the list reads from the top, no bottom-following like the chat does.

// Keep this many screens of real content mounted on EACH side of the viewport.
const BUFFER_SCREENS_PER_SIDE = 3;
// Floor on mounted count so one very tall row can't strand an empty window.
const MIN_BUFFER_ITEMS = 2;

// Pure solver: given scroll position and a per-index height accessor (measured where known, estimated otherwise), return the [start, end) slice to mount. Buffer is in PIXELS (N screens per side), so a few tall rows can't blow the mounted set up to the whole list.
export function computeDesiredWindow(
  scrollTop: number,
  clientHeight: number,
  total: number,
  heightOf: (index: number) => number,
  bufferPx: number,
): { start: number; end: number } {
  if (total <= 0) return { start: 0, end: 0 };
  const keepTop = scrollTop - bufferPx;
  const keepBottom = scrollTop + clientHeight + bufferPx;
  let offset = 0;
  let start = -1;
  let end = total;
  for (let i = 0; i < total; i++) {
    const h = heightOf(i);
    const itemTop = offset;
    const itemBottom = offset + h;
    if (start === -1 && itemBottom > keepTop) start = i;
    if (itemTop < keepBottom) {
      end = i + 1;
    } else {
      break;
    }
    offset += h;
  }
  if (start === -1) start = Math.max(0, total - 1);
  end = Math.min(total, Math.max(end, start + 1));
  if (end - start < MIN_BUFFER_ITEMS) {
    start = Math.max(0, Math.min(start, end - MIN_BUFFER_ITEMS));
  }
  return { start: Math.max(0, start), end };
}

interface UseWindowedListArgs {
  // Stable id per row, in render order. Heights are cached by id so a measured row keeps its height across re-renders even as the window slides.
  ids: string[];
  estimateHeight: (index: number) => number;
  // Off below this gates windowing entirely: render all, no spacers. Short lists don't benefit and the spacer recompute just fights the scrollbar.
  enabled: boolean;
}

interface UseWindowedListResult {
  setScrollEl: (el: HTMLDivElement | null) => void;
  onScroll: () => void;
  start: number;
  end: number;
  topSpacer: number;
  bottomSpacer: number;
}

export function useWindowedList({ ids, estimateHeight, enabled }: UseWindowedListArgs): UseWindowedListResult {
  const total = ids.length;
  const [scrollEl, setScrollEl] = useState<HTMLDivElement | null>(null);

  const heightsRef = useRef<Map<string, number>>(new Map());
  const [heightVersion, setHeightVersion] = useState(0);

  const [start, setStart] = useState(0);
  const [end, setEnd] = useState(total);
  const startRef = useRef(0);
  const endRef = useRef(total);

  const idsRef = useRef(ids);
  idsRef.current = ids;
  const estimateRef = useRef(estimateHeight);
  estimateRef.current = estimateHeight;

  const heightOf = useCallback((index: number): number => {
    const id = idsRef.current[index];
    if (id == null) return 0;
    const measured = heightsRef.current.get(id);
    if (measured != null) return measured;
    return estimateRef.current(index);
  }, []);

  const applyWindow = useCallback(() => {
    const el = scrollEl;
    if (!el || !enabled) return;
    const count = idsRef.current.length;
    const clientHeight = Math.max(1, el.clientHeight);
    const tightPx = BUFFER_SCREENS_PER_SIDE * clientHeight;
    const loosePx = tightPx + clientHeight;
    const tight = computeDesiredWindow(el.scrollTop, clientHeight, count, heightOf, tightPx);
    const loose = computeDesiredWindow(el.scrollTop, clientHeight, count, heightOf, loosePx);
    const curStart = startRef.current;
    const curEnd = endRef.current;
    // Hysteresis: must-mount the tight band, but keep already-mounted edges until they drift past the looser band, so rows on the boundary don't flip-flop mount/unmount on every scroll tick.
    let next = Math.max(loose.start, Math.min(curStart, tight.start));
    let nextEnd = Math.min(loose.end, Math.max(curEnd, tight.end));
    next = Math.max(0, Math.min(next, Math.max(0, nextEnd - 1)));
    if (next === curStart && nextEnd === curEnd) return;
    startRef.current = next;
    endRef.current = nextEnd;
    setStart(next);
    setEnd(nextEnd);
  }, [scrollEl, enabled, heightOf]);

  const rafRef = useRef<number | null>(null);
  const onScroll = useCallback(() => {
    if (rafRef.current != null) return;
    rafRef.current = requestAnimationFrame(() => {
      rafRef.current = null;
      applyWindow();
    });
  }, [applyWindow]);

  useEffect(() => {
    if (!scrollEl) return;
    applyWindow();
    const obs = new ResizeObserver(() => applyWindow());
    obs.observe(scrollEl);
    return () => {
      obs.disconnect();
      if (rafRef.current != null) {
        cancelAnimationFrame(rafRef.current);
        rafRef.current = null;
      }
    };
  }, [scrollEl, enabled, total, heightVersion, applyWindow]);

  // Measure mounted rows after paint; a real height replaces its estimate and nudges the window + spacers to the truth on the next frame.
  useLayoutEffect(() => {
    if (!scrollEl) return;
    let changed = false;
    scrollEl.querySelectorAll<HTMLElement>('[data-wl-id]').forEach((node) => {
      const id = node.dataset.wlId;
      if (!id) return;
      const h = node.offsetHeight;
      if (h <= 0) return;
      const prev = heightsRef.current.get(id);
      if (prev === undefined || Math.abs(prev - h) > 1) {
        heightsRef.current.set(id, h);
        changed = true;
      }
    });
    if (changed) setHeightVersion((v) => v + 1);
  });

  const safeStart = enabled ? Math.min(Math.max(0, start), Math.max(0, total - 1)) : 0;
  const safeEnd = enabled ? Math.min(Math.max(safeStart + 1, end), total) : total;

  const { topSpacer, bottomSpacer } = useMemo(() => {
    if (!enabled) return { topSpacer: 0, bottomSpacer: 0 };
    let top = 0;
    for (let i = 0; i < safeStart; i++) top += heightOf(i);
    let bottom = 0;
    for (let i = safeEnd; i < total; i++) bottom += heightOf(i);
    return { topSpacer: top, bottomSpacer: bottom };
    // heightVersion: spacers depend on the measured-height map (a ref the dep checker can't see), recompute when a measurement lands. eslint-disable-next-line react-hooks/exhaustive-deps
  }, [enabled, safeStart, safeEnd, total, heightVersion, heightOf]);

  return { setScrollEl, onScroll, start: safeStart, end: safeEnd, topSpacer, bottomSpacer };
}
