// The server's own words when it refuses something the user asked for. Today that is a delete the
// cloud would not let go of; without it the card simply stays put and the click looks broken.

import React from 'react';
import Snackbar from '@mui/material/Snackbar';
import Alert from '@mui/material/Alert';
import { useClaudeTokens } from '@/shared/styles/ThemeContext';
import { useAppDispatch, useAppSelector } from '@/shared/hooks';
import { dismissNoticeToast } from '@/shared/state/workflowsSlice';

export default function WorkflowNoticeToast() {
  const c = useClaudeTokens();
  const dispatch = useAppDispatch();
  const notice = useAppSelector((s) => s.workflows.noticeToast);

  return (
    <Snackbar
      open={Boolean(notice)}
      autoHideDuration={9000}
      onClose={(_, reason) => { if (reason !== 'clickaway') dispatch(dismissNoticeToast()); }}
      anchorOrigin={{ vertical: 'bottom', horizontal: 'left' }}
    >
      <Alert
        icon={false}
        severity="warning"
        onClose={() => dispatch(dismissNoticeToast())}
        sx={{
          bgcolor: c.bg.surface,
          color: c.text.primary,
          border: `1px solid ${c.border.medium}`,
          maxWidth: 420,
        }}
      >
        {notice}
      </Alert>
    </Snackbar>
  );
}
