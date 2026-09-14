import type { CloudRun } from './cloudApi';
import type { RunStatus } from './uiKit';

// A cloud run that never started reports as "dispatch_unavailable: fly_capacity: ...", which is a
// sentence for us, not for the person who was expecting a report at 9am. Every refusal the
// dispatcher can produce gets a plain answer to the only question they have: did it run, and why not.
const REFUSAL_TEXT: Record<string, string> = {
  runner_not_configured: "Cloud runs weren't available on our side, so this didn't start. You weren't charged for it.",
  callback_not_configured: "Cloud runs weren't available on our side, so this didn't start. You weren't charged for it.",
  fly_unauthorized: "Cloud runs weren't available on our side, so this didn't start. You weren't charged for it.",
  fly_rejected: "Cloud runs weren't available on our side, so this didn't start. You weren't charged for it.",
  fly_capacity: "The cloud had no room at that moment, so this didn't start. You weren't charged for it.",
  fly_unreachable: "We couldn't reach the machine meant to run this, so it didn't start. You weren't charged for it.",
  workflow_definition_invalid:
    "The cloud's copy of this workflow was unreadable, so nothing ran. Switch it back to this device and up to the cloud again to resend it.",
  no_cloud_credential:
    "No AI account is connected to the cloud for this workspace, so there was nothing to run this with.",
  slot_already_run: 'This slot had already run, so it was not run a second time.',
};

const STATUS_LABEL: Record<string, string> = {
  pending: 'Starting',
  running: 'Running',
  succeeded: 'Success',
  failed: 'Failed',
  dispatch_unavailable: "Didn't run",
};

const STATUS_TONE: Record<string, RunStatus> = {
  pending: 'running',
  running: 'running',
  succeeded: 'success',
  failed: 'failure',
  dispatch_unavailable: 'skipped',
};

export interface CloudHistoryRow {
  id: string;
  label: string;
  tone: RunStatus;
  summary: string;
  when: Date | null;
  durationText: string;
  costText: string;
}

/** Split "reason: detail" on the FIRST colon only, and only accept a reason we actually know.
 *  An unrecognised prefix falls through to the raw text: showing the truth beats guessing at it. */
export function explainCloudFailure(error: string | null): string {
  if (!error) return '';
  const at = error.indexOf(': ');
  if (at < 0) return error;
  const reason = error.slice(0, at);
  const detail = error.slice(at + 2);
  // The runner-capability detail is already the sentence we would have written.
  if (reason === 'runner_capability') return detail;
  return REFUSAL_TEXT[reason] ?? error;
}

function duration(run: CloudRun): string {
  if (!run.started_at || !run.finished_at) return '';
  const ms = new Date(run.finished_at).getTime() - new Date(run.started_at).getTime();
  if (Number.isNaN(ms) || ms < 0) return '';
  const s = Math.round(ms / 1000);
  return s < 60 ? `${s}s` : `${Math.floor(s / 60)}m ${s % 60}s`;
}

function cost(run: CloudRun): string {
  if (run.cost_usd === null || run.cost_usd === undefined) return '';
  if (run.cost_usd === 0) return '$0.00';
  return run.cost_usd < 0.01 ? '<$0.01' : `$${run.cost_usd.toFixed(2)}`;
}

export function toCloudHistoryRow(run: CloudRun, fallbackTitle: string): CloudHistoryRow {
  const failed = run.status === 'failed' || run.status === 'dispatch_unavailable';
  const explained = explainCloudFailure(run.error);
  return {
    id: run.id,
    label: STATUS_LABEL[run.status] ?? run.status,
    tone: STATUS_TONE[run.status] ?? 'skipped',
    summary: (failed && explained) || run.answer || fallbackTitle,
    when: run.started_at ? new Date(run.started_at) : null,
    durationText: duration(run),
    costText: cost(run),
  };
}
