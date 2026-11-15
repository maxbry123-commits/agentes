import React, { useEffect, useState } from 'react';
import Box from '@mui/material/Box';
import Dialog from '@mui/material/Dialog';
import Button from '@mui/material/Button';
import { API_BASE } from '@/shared/config';
import { useClaudeTokens } from '@/shared/styles/ThemeContext';
import VendoredToolUi from '@/toolui/VendoredToolUi';

export const APP_TOOL_GRANT_EVENT = 'openswarm:app-tool-grant';

export interface AppToolGrantRequest {
  request_id: string;
  output_id: string;
  app_name: string;
  tool_key: string;
  tool_label: string;
  args_preview: string;
}

/** One global mount that turns backend tool-grant requests (an app asking to use one of the user's
 * connected MCP tools) into an approval dialog. The backend blocks the call until this answers;
 * closing the dialog, denying, and the backend's own timeout ALL read as deny. */
const AppToolGrantHost: React.FC = () => {
  const c = useClaudeTokens();
  // A queue, not a slot: concurrent asks from several apps each get their turn instead of the
  // newest silently replacing a dialog someone was reading (the replaced ask would time out to deny).
  const [queue, setQueue] = useState<AppToolGrantRequest[]>([]);
  useEffect(() => {
    const onGrant = (e: Event): void => {
      const detail = (e as CustomEvent).detail as AppToolGrantRequest | undefined;
      if (!detail || !detail.request_id || !detail.tool_key) return;
      setQueue((prev) => (prev.some((r) => r.request_id === detail.request_id) ? prev : [...prev, detail]));
    };
    window.addEventListener(APP_TOOL_GRANT_EVENT, onGrant);
    return () => window.removeEventListener(APP_TOOL_GRANT_EVENT, onGrant);
  }, []);
  const req = queue[0] ?? null;
  if (!req) return null;
  const answer = (allow: boolean, remember: boolean): void => {
    void fetch(`${API_BASE}/apps-sdk/tools/grant`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ request_id: req.request_id, allow, remember }),
    }).catch(() => { /* backend timeout already reads as deny */ });
    setQueue((prev) => prev.slice(1));
  };
  return (
    <Dialog open onClose={() => answer(false, false)} maxWidth="xs" fullWidth PaperProps={{ sx: { background: 'transparent', boxShadow: 'none' } }}>
      <Box sx={{ background: c.bg.surface, borderRadius: '14px', p: 1.5 }}>
        <VendoredToolUi
          name="approval-card"
          props={{
            id: req.request_id,
            title: `"${req.app_name}" wants to use ${req.tool_label}`,
            description: 'This app is asking to call one of your connected tools. Only allow it if you trust the app with this action.',
            metadata: req.args_preview && req.args_preview !== '{}' ? [{ key: 'input', value: req.args_preview.slice(0, 120) }] : undefined,
            confirmLabel: 'Allow once',
            cancelLabel: 'Deny',
          }}
          extraProps={{
            onConfirm: () => answer(true, false),
            onCancel: () => answer(false, false),
          }}
        />
        {/* The remembered decisions ride outside the vendored card: its contract is confirm/cancel. */}
        <Box sx={{ display: 'flex', gap: 1, justifyContent: 'flex-end', mt: 0.5 }}>
          <Button size="small" color="inherit" onClick={() => answer(false, true)} sx={{ fontSize: '0.75rem', textTransform: 'none', color: c.text.muted }}>Never allow</Button>
          <Button size="small" color="inherit" onClick={() => answer(true, true)} sx={{ fontSize: '0.75rem', textTransform: 'none', color: c.text.secondary, fontWeight: 600 }}>Always allow</Button>
        </Box>
      </Box>
    </Dialog>
  );
};

export default AppToolGrantHost;
