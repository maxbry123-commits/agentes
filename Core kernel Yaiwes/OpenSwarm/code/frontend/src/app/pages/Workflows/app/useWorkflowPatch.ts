import { useCallback } from 'react';
import { useAppDispatch } from '@/shared/hooks';
import { updateWorkflow, fetchWorkflows } from '@/shared/state/workflowsSlice';
import type { Workflow } from '@/shared/state/workflowsSlice';

// Patch a workflow with optimistic concurrency. The PATCH carries If-Match on updated_at; if the record changed underneath us (409 → 'stale'), resync from the server so the next edit starts from truth instead of stomping it.
export function useWorkflowPatch() {
  const dispatch = useAppDispatch();
  return useCallback((wf: Workflow, patch: Partial<Workflow>) => {
    dispatch(updateWorkflow({ id: wf.id, patch, ifMatch: wf.updated_at }))
      .unwrap()
      .catch((err: { kind?: string } | undefined) => {
        if (err?.kind === 'stale') dispatch(fetchWorkflows(wf.dashboard_id ?? undefined));
      });
  }, [dispatch]);
}
