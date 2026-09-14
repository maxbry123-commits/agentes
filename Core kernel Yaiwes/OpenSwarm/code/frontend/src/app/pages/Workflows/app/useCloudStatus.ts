import { useCallback, useEffect, useRef, useState } from 'react';
import { useAppDispatch } from '@/shared/hooks';
import { fetchWorkflows } from '@/shared/state/workflowsSlice';
import type { Workflow } from '@/shared/state/workflowsSlice';
import { fetchCloudStatus, setCloudTarget } from './cloudApi';
import type { CloudTarget, TargetOutcome } from './cloudApi';
import type { CloudProbe } from './cloudAvailability';

export interface CloudStatusHandle {
  probe: CloudProbe;
  /** True while a flip is in flight; the control must not accept a second one. */
  pending: boolean;
  /** Set only by a refused flip, and cleared by the next attempt. */
  refusal: string | null;
  retry: () => void;
  choose: (target: CloudTarget, enabled: boolean) => void;
  refresh: () => void;
}

/** The cloud's answer for one workflow, fetched off the render path so the Workflows app paints
 *  and stays usable whether or not there is a cloud, an account, or a network. */
export function useCloudStatus(workflow: Workflow): CloudStatusHandle {
  const dispatch = useAppDispatch();
  const [probe, setProbe] = useState<CloudProbe>({ phase: 'checking' });
  const [pending, setPending] = useState(false);
  const [refusal, setRefusal] = useState<string | null>(null);
  const live = useRef(true);
  const workflowId = workflow.id;
  const dashboardId = workflow.dashboard_id;

  useEffect(() => {
    live.current = true;
    return () => { live.current = false; };
  }, []);

  const refresh = useCallback(() => {
    fetchCloudStatus(workflowId).then((status) => {
      if (!live.current) return;
      setProbe(status ? { phase: 'answered', status } : { phase: 'unreachable' });
    });
  }, [workflowId]);

  // Only a different workflow blanks the answer. Re-asking about the SAME one keeps the last answer on screen while it happens, so an edit does not strobe the card.
  useEffect(() => { setProbe({ phase: 'checking' }); }, [workflowId]);

  // Re-ask when the workflow changes in a way the answer depends on: a different schedule can stop being expressible in the cloud, and edited steps can stop being runnable there.
  useEffect(() => { refresh(); }, [refresh, workflow.updated_at]);

  const choose = useCallback((target: CloudTarget, enabled: boolean) => {
    if (pending) return;
    setPending(true);
    setRefusal(null);
    setCloudTarget(workflowId, { target, enabled }).then((outcome: TargetOutcome) => {
      if (!live.current) return;
      setPending(false);
      if (!outcome.ok) setRefusal(outcome.message);
      // Refresh either way: a refusal usually means the reasons on screen are stale too.
      refresh();
      if (outcome.ok) dispatch(fetchWorkflows(dashboardId ?? undefined));
    });
  }, [dispatch, pending, refresh, workflowId, dashboardId]);

  // refresh() deliberately leaves `refusal` alone: choose() calls it right after setting one, and
  // clearing there would wipe the message before it rendered. A user-driven retry is a different
  // intent, so it gets its own door; without it a refusal outlived the thing that caused it.
  const retry = useCallback(() => { setRefusal(null); refresh(); }, [refresh]);

  return { probe, pending, refusal, choose, refresh, retry };
}
