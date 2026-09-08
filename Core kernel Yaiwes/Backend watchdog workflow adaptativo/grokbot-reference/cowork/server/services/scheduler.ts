import cron from "node-cron";
import { exec } from "child_process";
import { getTasks, saveTasks, ScheduledTask, getSettings } from "./data";
import { runAutoSkillUpdate } from "./skillAutoUpdater";

const activeJobs = new Map<string, cron.ScheduledTask>();
let autoSkillJob: cron.ScheduledTask | null = null;

export async function initScheduler(): Promise<void> {
  const tasks = await getTasks();
  tasks.filter((t) => t.enabled).forEach((t) => scheduleTask(t));
}

export function scheduleTask(task: ScheduledTask): boolean {
  if (!cron.validate(task.cron)) return false;

  // Stop existing job if any
  stopTask(task.id);

  const job = cron.schedule(task.cron, () => {
    exec(task.command, { timeout: 60000 }, async (err, stdout, stderr) => {
      const tasks = await getTasks();
      const idx = tasks.findIndex((t) => t.id === task.id);
      if (idx >= 0) {
        tasks[idx].lastRun = new Date().toISOString();
        tasks[idx].lastResult = err ? `Error: ${stderr}` : stdout.slice(0, 1000);
        await saveTasks(tasks);
      }
    });
  });

  activeJobs.set(task.id, job);
  return true;
}

export function stopTask(id: string): void {
  const job = activeJobs.get(id);
  if (job) {
    job.stop();
    activeJobs.delete(id);
  }
}

export function stopAllTasks(): void {
  activeJobs.forEach((job) => job.stop());
  activeJobs.clear();
}

/**
 * Reconcile the skill auto-update cron job with the current Settings.
 * Called at boot and after Settings PUT so toggling takes effect immediately.
 */
export async function reconcileAutoSkillJob(): Promise<void> {
  const settings = await getSettings();
  if (autoSkillJob) {
    autoSkillJob.stop();
    autoSkillJob = null;
  }
  if (!settings.skillAutoUpdateEnabled) return;
  const minutes = Math.max(5, Math.min(1440, settings.skillAutoUpdateIntervalMinutes ?? 60));
  // node-cron supports m h dom mon dow. */N m runs at minute 0,N,2N... every hour.
  // For intervals > 60, fall back to running once at the top of each Nth hour.
  const expr = minutes <= 60 ? `*/${minutes} * * * *` : `0 */${Math.ceil(minutes / 60)} * * *`;
  if (!cron.validate(expr)) {
    console.error(`[skillAutoUpdate] invalid cron expression: ${expr}`);
    return;
  }
  autoSkillJob = cron.schedule(expr, () => {
    runAutoSkillUpdate().catch((err) => console.error("[skillAutoUpdate] tick failed:", err));
  });
  console.log(`[skillAutoUpdate] scheduled (${expr})`);
}

