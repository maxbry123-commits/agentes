export interface AgentTodoItem {
  content: string;
  status: 'pending' | 'in_progress' | 'completed';
}

function isTodoStatus(v: unknown): v is AgentTodoItem['status'] {
  return v === 'pending' || v === 'in_progress' || v === 'completed';
}

/** Latest TodoWrite payload in the transcript = the agent's live plan; null when it never wrote one. */
export function extractLatestTodos(messages: Array<{ role: string; content: unknown }>): AgentTodoItem[] | null {
  for (let i = messages.length - 1; i >= 0; i--) {
    const msg = messages[i];
    if (msg.role !== 'tool_call') continue;
    const body = (typeof msg.content === 'object' && msg.content !== null ? msg.content : {}) as { tool?: unknown; input?: unknown };
    if (!/todowrite$/i.test(String(body.tool || ''))) continue;
    const raw = (typeof body.input === 'object' && body.input !== null ? (body.input as { todos?: unknown }).todos : undefined);
    if (!Array.isArray(raw)) continue;
    const items: AgentTodoItem[] = [];
    for (const entry of raw) {
      const t = (typeof entry === 'object' && entry !== null ? entry : {}) as { content?: unknown; activeForm?: unknown; status?: unknown };
      const content = typeof t.content === 'string' ? t.content : (typeof t.activeForm === 'string' ? t.activeForm : '');
      if (!content) continue;
      items.push({ content, status: isTodoStatus(t.status) ? t.status : 'pending' });
    }
    if (items.length > 0) return items;
  }
  return null;
}
