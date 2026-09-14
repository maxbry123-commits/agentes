import type { Workflow, ScheduleConfig, WorkflowStep } from '@/shared/state/workflowsSlice';

export const WEEKDAY_LABEL = ['S', 'M', 'T', 'W', 'T', 'F', 'S'];
export const WEEKDAY_LABEL_SHORT = ['SUN', 'MON', 'TUE', 'WED', 'THU', 'FRI', 'SAT'];
export const WEEKDAY_FULL = ['Sun', 'Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat'];

export function defaultSchedule(): ScheduleConfig {
  // Pick the host's IANA tz so new schedules start with an explicit zone instead of the legacy "local" sentinel. Backend storage still coerces "local" if a record predates this default; new records skip that path.
  let tz = 'local';
  try { tz = Intl.DateTimeFormat().resolvedOptions().timeZone || 'local'; } catch { /* keep 'local' */ }
  return {
    enabled: false,
    repeat_every: 1,
    repeat_unit: 'week',
    on_days: [],
    hour: 9,
    minute: 0,
    day_of_month: null,
    timezone: tz,
    ends_at: null,
    max_runs: null,
    runs_count: 0,
  };
}

export function isScheduleConfigured(sched: ScheduleConfig | null | undefined): boolean {
  if (!sched) return false;
  if (sched.repeat_unit === 'week') return sched.on_days.length > 0;
  return true;
}

export function isScheduleActive(sched: ScheduleConfig | null | undefined): boolean {
  return !!sched?.enabled && isScheduleConfigured(sched);
}

export function isWorkflowSchedulable(workflow: Workflow): boolean {
  return isScheduleConfigured(workflow.schedule);
}

// Stable fingerprint of the steps that actually drive behavior (order + id + text). label is just the at-a-glance headline, so it's left out. Computed only here so the backend stores exactly what the FE compares: no cross- language hashing drift.
export function stepsSignature(steps: WorkflowStep[] | null | undefined): string {
  return JSON.stringify((steps || []).map((s) => [s.id, s.text]));
}

// True when the current steps haven't been validated by a test run (or seeded at chat conversion) since they were last edited. Drives the test-first warning before scheduling.
export function needsScheduleTestWarning(workflow: Workflow): boolean {
  const steps = workflow.draft_steps ?? workflow.steps;
  if (!steps || steps.length === 0) return false;
  return stepsSignature(steps) !== (workflow.tested_signature ?? '');
}

export function formatTime(hour: number, minute: number): string {
  const h12 = ((hour + 11) % 12) + 1;
  const suffix = hour < 12 ? 'am' : 'pm';
  const mm = String(minute).padStart(2, '0');
  return minute === 0 ? `${h12}${suffix}` : `${h12}:${mm}${suffix}`;
}

// Used in the roomy hub calendar: "10 AM", "12 PM", "1 PM"... Matches Figma image #8 styling for the left-column time labels.
export function formatHourLabel(hour: number): string {
  const h12 = ((hour + 11) % 12) + 1;
  const suffix = hour < 12 ? 'AM' : 'PM';
  return `${h12} ${suffix}`;
}

export function describeSchedule(sched: ScheduleConfig): string {
  if (!sched.enabled || !isScheduleConfigured(sched)) return 'Not scheduled';
  const time = formatTime(sched.hour, sched.minute);
  if (sched.repeat_unit === 'minute') {
    return `Every ${sched.repeat_every} minutes`;
  }
  if (sched.repeat_unit === 'hour') {
    const at = sched.minute === 0 ? '' : ` at :${String(sched.minute).padStart(2, '0')}`;
    return sched.repeat_every === 1 ? `Every hour${at}` : `Every ${sched.repeat_every} hours${at}`;
  }
  if (sched.repeat_unit === 'day') {
    return sched.repeat_every === 1 ? `Every day at ${time}` : `Every ${sched.repeat_every} days at ${time}`;
  }
  if (sched.repeat_unit === 'month') {
    const day = sched.day_of_month ? ` on day ${sched.day_of_month}` : '';
    return sched.repeat_every === 1 ? `Every month${day} at ${time}` : `Every ${sched.repeat_every} months${day} at ${time}`;
  }
  const days = sched.on_days.length === 0 ? 'week' : sched.on_days
    .slice()
    .sort()
    .map((d) => WEEKDAY_FULL[d])
    .join(', ');
  const cadence = sched.repeat_every === 1 ? `Every ${days}` : `Every ${sched.repeat_every} weeks on ${days}`;
  return `${cadence} at ${time}`;
}

export function describePermissions(workflow: Workflow): string {
  if (!workflow.permissions || workflow.permissions.length === 0) return 'Notify only';
  const labels: string[] = [];
  for (const p of workflow.permissions) {
    if (p.kind === 'notify') labels.push('notify in app');
    else if (p.kind === 'text') labels.push('text');
    else if (p.kind === 'call') labels.push('call');
  }
  return `First ${labels.join(', then ')}`;
}

export function startOfWeek(date: Date): Date {
  const d = new Date(date);
  d.setHours(0, 0, 0, 0);
  d.setDate(d.getDate() - d.getDay());
  return d;
}

export function startOfMonthGrid(date: Date): Date {
  const d = new Date(date.getFullYear(), date.getMonth(), 1);
  d.setDate(d.getDate() - d.getDay());
  return d;
}

export function sameDay(a: Date, b: Date): boolean {
  return a.getFullYear() === b.getFullYear() && a.getMonth() === b.getMonth() && a.getDate() === b.getDate();
}

export function addDays(date: Date, n: number): Date {
  const d = new Date(date);
  d.setDate(d.getDate() + n);
  return d;
}
