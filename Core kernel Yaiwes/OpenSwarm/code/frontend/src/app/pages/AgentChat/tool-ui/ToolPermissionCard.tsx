import React, { useMemo } from 'react';
import Box from '@mui/material/Box';
import Button from '@mui/material/Button';
import VendoredToolUi from '@/toolui/VendoredToolUi';
import { ApprovalRequest } from '@/shared/state/agentsSlice';
import { useClaudeTokens } from '@/shared/styles/ThemeContext';

interface Props {
  request: ApprovalRequest;
  title: string;
  description?: string;
  onApprove: (requestId: string, updatedInput?: Record<string, any>, trustPattern?: boolean, alwaysAllow?: boolean) => void;
  onDeny: (requestId: string, message?: string) => void;
}

const METADATA_ROW_CAP = 5;

function metadataRows(toolInput: Record<string, unknown>): Array<{ key: string; value: string }> {
  const rows: Array<{ key: string; value: string }> = [];
  for (const [key, val] of Object.entries(toolInput)) {
    if (key.startsWith('_') || val == null) continue;
    const text = typeof val === 'string' ? val : JSON.stringify(val);
    if (!text || text === '{}' || text === '[]') continue;
    rows.push({ key, value: text.length > 120 ? `${text.slice(0, 117)}...` : text });
    if (rows.length >= METADATA_ROW_CAP) break;
  }
  return rows;
}

/** Tool permission asks rendered through the vendored tool-ui approval-card (the modern surface),
 * with the persistent "Always allow" escalation as a slim host-side row: the vendored contract is
 * confirm/cancel, and widening it would fork the upstream component. */
const ToolPermissionCard: React.FC<Props> = ({ request, title, description, onApprove, onDeny }) => {
  const c = useClaudeTokens();
  const metadata = useMemo(() => metadataRows(request.tool_input), [request.tool_input]);
  return (
    <Box sx={{ mx: 2, mb: 1 }}>
      <VendoredToolUi
        name="approval-card"
        props={{
          id: request.id,
          title,
          description: description || undefined,
          metadata: metadata.length ? metadata : undefined,
          confirmLabel: 'Approve',
          cancelLabel: 'Deny',
        }}
        extraProps={{
          onConfirm: () => onApprove(request.id),
          onCancel: () => onDeny(request.id),
        }}
      />
      <Button
        variant="text"
        size="small"
        color="inherit"
        onClick={() => onApprove(request.id, undefined, false, true)}
        sx={{ mt: 0.25, fontSize: '0.75rem', textTransform: 'none', color: c.text.muted, '&:hover': { color: c.text.secondary } }}
      >
        Always allow {title}
      </Button>
    </Box>
  );
};

export default ToolPermissionCard;
