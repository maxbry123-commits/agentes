import { closeSession } from '@/shared/state/agentsSlice';
import { removeWorkflowCard, closeWorkflowsHub, closeSettingsCard, recordClosedCard } from '@/shared/state/dashboardLayoutSlice';
import { closeWorkflowCard } from '@/shared/state/workflowsSlice';
import { removeBrowserCardsCleanly } from '@/shared/browserTeardown';
import { removeViewCardCleanly } from '@/shared/viewTeardown';
import type { AppDispatch } from '@/shared/state/store';
import type { CardType } from '../state/useDashboardSelection';

/** Close every selected card, recording each so Cmd+Shift+T can bring it back. */
export function deleteSelectedCards(selectedIds: Map<string, CardType>, dispatch: AppDispatch): void {
  const viewIds: string[] = [];
  const browserIds: string[] = [];
  for (const [id, type] of selectedIds) {
    if (type === 'agent') {
      dispatch(recordClosedCard({ kind: 'agent', id }));
      dispatch(closeSession({ sessionId: id }));
    } else if (type === 'view') {
      dispatch(recordClosedCard({ kind: 'view', id }));
      viewIds.push(id);
    } else if (type === 'browser') {
      dispatch(recordClosedCard({ kind: 'browser', id }));
      browserIds.push(id);
    } else if (type === 'workflow') {
      dispatch(recordClosedCard({ kind: 'workflow', id }));
      dispatch(removeWorkflowCard(id));
      dispatch(closeWorkflowCard(id));
    } else if (type === 'workflows-hub') {
      dispatch(closeWorkflowsHub());
    } else if (type === 'settings') {
      dispatch(closeSettingsCard());
    }
  }
  // Tear webview-backed cards down ONE AT A TIME (each quiesces / CDP-detaches its GPU surface
  // first); ripping several large app OR browser webviews out in one frame is what piles up
  // "non-existent mailbox" errors and SIGSEGVs the GPU/browser process (the mass-delete self-quit).
  void (async () => {
    for (const id of viewIds) await removeViewCardCleanly(id, dispatch);
    await removeBrowserCardsCleanly(browserIds, dispatch);
  })();
}
