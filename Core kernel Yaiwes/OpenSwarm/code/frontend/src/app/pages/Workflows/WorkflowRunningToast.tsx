// Clickable "your {workflow} is running now" nudge for scheduled runs that fire while the user isn't looking. Detection lives in the upsertRun reducer (it owns the into-running edge); this just renders the redux toast state and, on View, opens the Workflows app to that workflow's live detail.

import React from 'react';
import Snackbar from '@mui/material/Snackbar';
import Alert from '@mui/material/Alert';
import Button from '@mui/material/Button';
import { useClaudeTokens } from '@/shared/styles/ThemeContext';
import { useAppDispatch, useAppSelector } from '@/shared/hooks';
import { dismissRunningToast } from '@/shared/state/workflowsSlice';
import { openWorkflowsApp } from '@/shared/state/dashboardLayoutSlice';

export default function WorkflowRunningToast() {
  const c = useClaudeTokens();
  const dispatch = useAppDispatch();
  const toast = useAppSelector((s) => s.workflows.runningToast);

  const onView = React.useCallback(() => {
    if (!toast) return;
    dispatch(openWorkflowsApp({ workflowId: toast.workflowId }));
    dispatch(dismissRunningToast());
  }, [toast, dispatch]);

  return (
    <Snackbar
      open={Boolean(toast)}
      autoHideDuration={10000}
      onClose={(_, reason) => { if (reason !== 'clickaway') dispatch(dismissRunningToast()); }}
      anchorOrigin={{ vertical: 'bottom', horizontal: 'left' }}
    >
      <Alert
        icon={false}
        severity="info"
        onClose={() => dispatch(dismissRunningToast())}
        sx={{
          bgcolor: c.bg.surface,
          color: c.text.primary,
          border: `1px solid ${c.border.medium}`,
          '& .MuiAlert-action': { alignItems: 'center', pt: 0 },
        }}
        action={
          <Button size="small" onClick={onView} sx={{ color: c.accent.primary, fontWeight: 700 }}>
            View
          </Button>
        }
      >
        {toast ? `${toast.workflowTitle} is running now` : ''}
      </Alert>
    </Snackbar>
  );
}
