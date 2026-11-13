/** Plain-English session status for user-facing chips; the raw enum values read as dev-speak. */
export function friendlyStatusLabel(status: string): string {
  switch (status) {
    case 'running': return 'working';
    case 'waiting_approval': return 'needs your OK';
    case 'completed': return 'done';
    case 'error': return 'needs attention';
    default: return status.replace(/_/g, ' ');
  }
}
