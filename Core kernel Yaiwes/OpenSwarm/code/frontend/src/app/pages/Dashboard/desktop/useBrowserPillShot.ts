import { useSyncExternalStore } from 'react';
import { useAppSelector } from '@/shared/hooks';
import { getMinimizedShot, subscribeMinimizedShots } from './minimizedShots';

/**
 * The browser preview under a collapsed agent pill: the session's browser (spawned by it or docked
 * into it) as the frame BrowserCard froze while that card could still paint. Never captures here:
 * a docked card parks off-screen the moment its chat collapses, and capturePage on an unpainted
 * guest never settles (Electron 42), which is what used to leave the pill permanently blank.
 */
export function useBrowserPillShot(sessionId: string, active: boolean): string | null {
  const browserId = useAppSelector((s) => {
    for (const bc of Object.values(s.dashboardLayout.browserCards)) {
      if (bc.spawned_by === sessionId || bc.docked_to === sessionId) return bc.browser_id;
    }
    return null;
  });
  const suspendedShot = useAppSelector(
    (s) => (browserId ? s.dashboardLayout.suspendedBrowserCards[browserId]?.dataUrl || null : null),
  );
  const frozenShot = useSyncExternalStore(
    subscribeMinimizedShots,
    () => (browserId ? getMinimizedShot(browserId) ?? null : null),
  );
  if (!active || !browserId) return null;
  return frozenShot ?? suspendedShot;
}
