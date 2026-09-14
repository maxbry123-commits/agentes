import { useEffect, useState, useCallback } from 'react';
import { useLocation } from 'react-router-dom';
import { setLastDashboardId } from '@/shared/lastDashboardId';

const STORAGE_KEY = 'openswarm_last_dashboard_id';

/** Sticky last-visited dashboard id so Dashboard stays mounted across non-dashboard nav. */
export function useLastDashboardId(): [string | null, (id: string | null) => void] {
  const location = useLocation();
  const [lastId, setLastIdState] = useState<string | null>(() => {
    try {
      return localStorage.getItem(STORAGE_KEY);
    } catch {
      return null;
    }
  });

  // The id from the CURRENT url, read synchronously in render: a dashboard switch must update dashboardId on the SAME render the route changes. Deferring it to the effect below left a one-frame window where the OLD dashboard was still the active id, so a kept-alive browser card from it flashed onto the new dashboard before parking off-screen (the cross-dashboard bleed).
  const routeId = location.pathname.match(/^\/dashboard\/([^/]+)/)?.[1] ?? null;
  const effectiveId = routeId ?? lastId;

  // Persist the route id so it stays sticky when the url stops matching a dashboard (settings etc.). Do NOT clear when it stops matching.
  useEffect(() => {
    if (routeId && routeId !== lastId) {
      setLastIdState(routeId);
      try {
        localStorage.setItem(STORAGE_KEY, routeId);
      } catch {}
      setLastDashboardId(routeId);
    }
  }, [routeId, lastId]);

  const setLastId = useCallback((id: string | null) => {
    setLastIdState(id);
    try {
      if (id) {
        localStorage.setItem(STORAGE_KEY, id);
      } else {
        localStorage.removeItem(STORAGE_KEY);
      }
    } catch {}
    setLastDashboardId(id);
  }, []);

  return [effectiveId, setLastId];
}
