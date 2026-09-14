import { useCallback } from 'react';
import { useDispatch, useStore } from 'react-redux';
import { addBrowserCard, clearTiledCard } from '@/shared/state/dashboardLayoutSlice';
import type { RootState } from '@/shared/state/store';

/** Opens a widget link as an in-app browser card, leaving fullscreen first so the card is actually visible (ENG-234). */
export function useOpenUrlInBrowserCard(): (url: string) => void {
  const dispatch = useDispatch();
  const store = useStore<RootState>();
  return useCallback(
    (url: string) => {
      if (!/^https?:\/\//i.test(url)) return;
      // Lazy read, no subscription: this fires on a click, and widgets must not re-render on every tile change.
      const tiled = store.getState().dashboardLayout.tiledCards || {};
      for (const [cardId, zone] of Object.entries(tiled)) {
        if (zone === 'fullscreen') dispatch(clearTiledCard(cardId));
      }
      dispatch(addBrowserCard({ url }));
    },
    [dispatch, store],
  );
}
