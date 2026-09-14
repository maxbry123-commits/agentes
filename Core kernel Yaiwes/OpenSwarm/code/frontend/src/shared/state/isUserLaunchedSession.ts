// Plumbing chats the UI spins up for itself: a workflow card's Edit Agent, a workflow run, a browser
// or sub agent working for a parent. They are real sessions, they just aren't things the user started.
const PLUMBING_MODES: ReadonlySet<string> = new Set(['browser-agent', 'invoked-agent', 'sub-agent']);

export interface SessionOrigin {
  mode: string;
  workflow_run_id?: string | null;
  workflow_edit_id?: string | null;
}

/** True for a chat the user started themselves, which is the only kind that earns a card or a notification. */
export function isUserLaunchedSession(session: SessionOrigin): boolean {
  return !session.workflow_run_id && !session.workflow_edit_id && !PLUMBING_MODES.has(session.mode);
}
