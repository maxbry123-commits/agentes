---
name: monitor-restore-iris
description: Re-register the every-3-hours Iris job-monitor cron (status check + datagen auto-rescue/keep-2-in-flight) if it has been lost. Primarily the marin TPU datagen/eval jobs ("iris" = the marin TPU cluster); also queries CoreWeave (cw-us-east-02a) GPU-RL as monitor-only. The cron is session-only and recurring crons auto-expire after 7 days, so it's routinely lost on a session restart. Use at the start of a new session, after a restart, or when the user asks to restore/check the iris monitoring cron. The sweep PROCEDURE the cron runs lives in monitor-cron-sweep-iris.
---

# monitor-restore-iris

> **📍 Iris orientation — read first.** Read the Iris **tools catalog** (`.agents/ops/iris/ops.md`) and the Iris **ops directory** (`.agents/ops/iris/` — `ops.md` for CoreWeave GPU, `ops.md` for TPU `marin`) for binding access/preamble/gotchas and the helper-script inventory.

The recurring cron watching all `benjaminfeuer` Iris jobs is **session-only** and recurring crons **auto-expire after 7 days** — routinely lost on a session restart. This skill is the durable source of truth for re-creating it: the **canonical cron prompt below is what gets (re-)installed — copy it verbatim into `CronCreate`.** The per-tick sweep *methodology* is **monitor-cron-sweep-iris**. (The separate broader tri-cluster monitor — Leonardo + CoreWeave + TACC — is **monitor-restore** / **monitor-cron-sweep**.)

## When to run
- Start of a new session where Iris jobs are in flight.
- The user says the monitor/cron is gone, down, or "not firing."
- After ~7 days (expiry).

## Steps
1. **Check if it already exists** — call `CronList`. If a recurring job whose prompt mentions "status check on ALL Iris jobs for user benjaminfeuer" is present, do nothing (a duplicate causes redundant SQL/tunnel load). If a stale **datagen-only** variant exists (prompt mentions only `qwen3.5-122b-32k-%`), `CronDelete` it and recreate with the all-jobs prompt below.
2. **If absent, call `CronCreate`** with:
   - `cron`: `23 */3 * * *`  (every 3 h at :23 — off the :00/:30 marks)
   - `recurring`: `true`
   - `prompt`: the exact text in the fenced block below.
3. Tell the user the new job id + the two caveats: **session-only** (dies when this Claude session exits — re-run this skill next session) and **7-day auto-expiry**.

## Notes
- `durable: true` is NOT honored in this harness (still creates a session-only job) — this skill IS the persistence layer.
- The cron only fires while the REPL is idle (not mid-task). If it reliably misses, fallback is the user pasting the prompt manually or an external launchd monitor (out of scope).
- It tracks ALL `/benjaminfeuer/%` jobs but the autonomous write actions (auto-rescue, keep-2-in-flight) are **datagen-only**; eval jobs are monitor-only (self-sync to Supabase+HF). See **datagen-launch-iris** (launch/refill), **datagen-job-cleanup** (canonical idempotent post-run cleanup for a TERMINAL datagen arm), and **eval-agentic-launch-iris**.
- **Two clusters.** The cron queries both the **marin** TPU cluster and the **`cw-us-east-02a`** CoreWeave GPU cluster. The marin `.venv` iris carries the `[controller]` deps so it drives CoreWeave too — but the CoreWeave query MUST be prefixed `KUBECONFIG=~/.kube/coreweave-iris-gpu`, else iris falls back to the shell-default kubeconfig (`~/.kube/lambdaconfig`) and errors with `Invalid kube-config file … Expected object with name`. GPU-RL jobs on CoreWeave are **monitor-only** (no rescue, no keep-2); pods GC on terminal, so logs come from the persistent finelog server. Other CoreWeave GPU configs (`coreweave*` = US-WEST-04A, CI/smoke) are NOT in scope unless the user runs jobs there.
- **The methodology each step encodes** (how to run the analyzer, classify, rescue, refill) is **monitor-cron-sweep-iris** — read it when actually executing a tick; this skill is just the (re)install wrapper + the canonical prompt.

## Canonical cron prompt (copy verbatim into CronCreate)

```
Every-3-hours status check on ALL Iris jobs for user benjaminfeuer (datagen + eval + GPU-RL + anything else), across BOTH the marin TPU cluster and the CoreWeave GPU cluster.

**⚠ NO EXPERIMENT-SPECIFICS IN THIS PROMPT (they go stale): the per-campaign values — in-flight TARGET, refill cluster/grouping/order, harvest gates, repo/image patterns, and current bugs — live in the EXPERIMENT TRACKERS under `~/Documents/experiments/active/` (and the `*-launch` / `*-cleanup` / `analyze-*` skills). READ the relevant tracker each tick and drive off IT; never rely on a number hardcoded here.**

**⛔ DATAGEN IS OUT OF SCOPE: a DIFFERENT agent manages ALL datagen (`tracegen-iris-%` / `qwen3.5-122b-%`). Do NOT analyze, rescue, keep-N, or take any action on datagen jobs. This monitor covers EVAL (§3B) + Levanter TRAINING (§3C) + CoreWeave GPU-RL (§3D) only.**

1. Active jobs (query BOTH clusters):
   1a. marin (TPU):
       /Users/benjaminfeuer/Documents/marin/.venv/bin/iris --cluster=marin query "SELECT job_id, state FROM jobs WHERE state IN (1,2,3) AND job_id LIKE '/benjaminfeuer/%' ORDER BY job_id DESC LIMIT 20" -f csv
   1b. cw-us-east-02a (CoreWeave GPU) — KUBECONFIG prefix REQUIRED (else iris uses the wrong shell-default kubeconfig):
       KUBECONFIG=~/.kube/coreweave-iris-gpu /Users/benjaminfeuer/Documents/marin/.venv/bin/iris --cluster=cw-us-east-02a query "SELECT job_id, state FROM jobs WHERE state IN (1,2,3) AND job_id LIKE '/benjaminfeuer/%' ORDER BY job_id DESC LIMIT 20" -f csv
   For EACH cluster also query state IN (4,5,6) LIMIT 8 to catch jobs that went terminal since the last tick. If the cw query errors (cluster down / creds), report that and continue with marin.

2. For each ACTIVE marin (TPU) datagen/eval job, run the harbor analyzer (does NOT apply to CoreWeave GPU-RL — handle per class D). Use the analyze-job-history-iris skill:
   /Users/benjaminfeuer/miniconda3/envs/otagent/bin/python /Users/benjaminfeuer/Documents/OpenThoughts-Agent/scripts/iris/analyze_iris_harbor_job.py <job_id> --output /tmp/$(basename <job_id>)_history.md --resync
   Report from the .json sidecar: runtime_h, iris_preemption_count, cycles total/served, samples (serving_summary.gen_tps.n), gen tok/s mean/peak, Running mean/peak, non_empty/total trials = rate, t_first_serve, top harbor_exception_stats. ALSO report mean reward + completed/total tasks from the harbor progress line (NOT in the sidecar): /Users/benjaminfeuer/Documents/marin/.venv/bin/iris --cluster=marin job logs <job_id> --max-lines 8000 | grep -aoE '[0-9]+/[0-9]+ Mean: [-0-9.]+' | tail -1

3. Print `## Iris jobs status — <ISO UTC>`: one line per job (name + state + CLOSED/PARTIAL/OPEN/DEAD), a compact metrics block, and a survival check (past cold compile? throughput sane? traces/results landing on HF?). Classify each job by job_id prefix and apply the right treatment:

   A. **Datagen** (`qwen3.5-122b-%` / `tracegen-iris-%`): **⛔ OUT OF SCOPE — a DIFFERENT agent manages ALL datagen.** Do NOT query, analyze (§2), rescue (§4), keep-N (§5), or take ANY action on datagen jobs. If one appears in the state query, note its existence in ONE line at most and move on. §4 + §5 are BOTH retired for this monitor.

   B. **Eval** (`eval-%`): auto-sync to Supabase + HF on completion (`--upload_to_database`); build sandboxes at runtime (MAIN Daytona org). **ALWAYS report the leading metric (`<done>/<total> Mean: <X>`) per in-flight eval** (from `iris … job logs <job_id>`; not in the analyzer sidecar) + productive rate + exceptions; on terminal, whether results landed. A **one-off** eval is monitor-only (no rescue/relaunch). **⚠ EXCEPTION — an eval CAMPAIGN with a tracker in `active/` (e.g. `~/Documents/experiments/active/flawed_summ_evals/reeval_tracker.md`) DOES run an active harvest+refill loop: drive it PER THAT TRACKER each tick — its in-flight TARGET, refill cluster/grouping/order, harvest gate + discriminator, and gotchas ALL live in the tracker's TOP BLOCK (never hardcode them here). Route harvest via the `eval-agentic-cleanup` skill, refill via the `eval-*-launch` skill.**

   C. **Other** job types (e.g. Levanter training `iris-run-…` — health via `analyze-training-run-iris`; source of truth = its `active/` experiment dir): report state + a one-line health read; take no autonomous write action.

   D. **GPU-RL** (CoreWeave `cw-us-east-02a`, e.g. `rl-iris-%` / `rl-%` — MarinSkyRL GRPO on whole H100x8 nodes, possibly gang-scheduled multi-node `replicas>1`): **monitor-only — NO rescue, NO keep-2-in-flight, NO auto-relaunch.** The harbor analyzer in §2 does NOT apply (no harbor trial sidecars). For each in-flight GPU-RL job report state + the latest RL progress by reading the persistent finelog (pods GC on terminal): `KUBECONFIG=~/.kube/coreweave-iris-gpu /Users/benjaminfeuer/Documents/marin/.venv/bin/iris --cluster=cw-us-east-02a job logs <job_id> --max-lines 100000 --no-tail` then grep `WANDB_MIRROR kind=train step=` for the latest `trainer/global_step`, `loss/avg_raw_reward`, and `generate/num_failed_trajectories`/`generate/errors`. For multi-node confirm `All N Ray node(s) joined`. On a terminal job report exit state (4=SUCCEEDED). NEVER kill/relaunch GPU-RL jobs.

6. NEVER kill/restart/bounce a RUNNING job or the cluster without express user permission. GPU-RL and all other RUNNING jobs stay strictly no-touch (flag for the user, never kill). If a job is stuck PENDING (no capacity), report it and surface the unpinned-relaunch option — do not kill a running/placed job unprompted. (Datagen zombie-kill+rescue authority, when datagen WAS in scope: state 3 + harbor progress frozen ≥3h + task log ONLY `[fd-monitor]` heartbeats in that window with no recent healthy vLLM engine marker. But datagen is now §A out of scope — a different agent owns it.)
```

If you change the cadence or scope, update BOTH the `cron`/`prompt` above and the live job (delete + recreate), and keep **monitor-cron-sweep-iris** (the procedure) in sync — so this skill stays the canonical copy.
