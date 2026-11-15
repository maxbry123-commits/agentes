// Wall-clock "work time" for an agent session: how long the user actually waited across all turns (prompt -> last assistant/system reply of that turn). Shared so the dashboard chat card timer and the workflow subtitle report the exact same number for the same session.

type WorkMessage = { role: string; timestamp: string; elapsed_ms?: number; hidden?: boolean };

export function getAgentWorkTime(
  messages: WorkMessage[],
  status: string,
): { total: number; last: number } {
  // Covers thinking + every tool call + assistant text generation + any subagent/MCP work, anything that consumed user attention. NOT the sum of thinking.elapsed_ms (that misses tool execution). For each user message we find the LAST adjacent assistant/system message before the next user message, that's the turn boundary. In-flight turns extrapolate to now while running. Hidden messages (auto-continuation prompts) are skipped.
  const visible = messages.filter((m) => !m.hidden);
  let totalMs = 0;
  let lastMs = 0;
  for (let i = 0; i < visible.length; i++) {
    const msg = visible[i];
    if (msg.role !== 'user') continue;

    let nextUserIdx = visible.length;
    for (let k = i + 1; k < visible.length; k++) {
      if (visible[k].role === 'user') {
        nextUserIdx = k;
        break;
      }
    }

    let turnEndMs: number | null = null;
    for (let k = nextUserIdx - 1; k > i; k--) {
      const r = visible[k].role;
      if (r === 'assistant' || r === 'system') {
        turnEndMs = new Date(visible[k].timestamp).getTime();
        break;
      }
    }

    if (turnEndMs == null) {
      if (status === 'running' || status === 'waiting_approval') {
        turnEndMs = Date.now();
      } else {
        continue;
      }
    }

    const dur = Math.max(0, turnEndMs - new Date(msg.timestamp).getTime());
    totalMs += dur;
    lastMs = dur;
  }

  return {
    total: Math.max(0, Math.round(totalMs / 1000)),
    last: Math.max(0, Math.round(lastMs / 1000)),
  };
}

export function fmtSeconds(seconds: number): string {
  if (seconds < 60) return `${seconds}s`;
  const minutes = Math.floor(seconds / 60);
  if (minutes < 60) return `${minutes}m ${seconds % 60}s`;
  const hours = Math.floor(minutes / 60);
  return `${hours}h ${minutes % 60}m`;
}
