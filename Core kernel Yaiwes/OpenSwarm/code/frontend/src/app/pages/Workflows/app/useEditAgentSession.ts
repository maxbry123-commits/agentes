import { useEffect, useRef, useState } from 'react';
import { useAppDispatch } from '@/shared/hooks';
import { fetchSession } from '@/shared/state/agentsSlice';
import { ensureEditAgentSession } from './api';

// Boots (or reattaches) the sticky edit-agent session for a workflow and returns its id once ready. The opener is deterministic: an existing workflow gets a fixed intro message from the backend; a brand-new build starts empty and the compose page shows its own starter prompts.
export function useEditAgentSession(workflowId: string): string | null {
  const dispatch = useAppDispatch();
  const [sessionId, setSessionId] = useState<string | null>(null);
  const didInit = useRef(false);

  useEffect(() => {
    didInit.current = false;
    setSessionId(null);
  }, [workflowId]);

  useEffect(() => {
    if (!workflowId || didInit.current) return;
    didInit.current = true;
    let alive = true;
    (async () => {
      const sid = await ensureEditAgentSession(workflowId);
      if (!sid || !alive) return;
      try { await dispatch(fetchSession(sid)).unwrap(); } catch { /* may hydrate later */ }
      if (alive) setSessionId(sid);
    })();
    return () => { alive = false; };
  }, [workflowId, dispatch]);

  return sessionId;
}
