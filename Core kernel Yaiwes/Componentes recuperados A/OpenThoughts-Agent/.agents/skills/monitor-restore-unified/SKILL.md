---
name: monitor-restore-unified
description: >-
  Re-register the every-3-hours UNIFIED OPS TICK cron — the CURRENT operator-owned monitor for the
  qwen3.5-122b-131k-datagen-opencode campaign (keep-3 datagen with autonomous rescue+refill) AND the delphi
  midtrain 1e23_p33m67_k0p20 (monitor-only), plus a marin+CoreWeave sweep and standing Daytona snapshot
  cleanup. The cron is session-only and recurring crons auto-expire after 7 days, so it's routinely lost on a
  session restart. Use at the start of a new session, after a disconnect/restart, or when the user asks to
  restore the monitor cron. Supersedes monitor-restore-iris (which is the OLDER datagen-OUT-of-scope variant);
  use THIS skill when the current session owns the 131k datagen campaign + midtrain. The per-tick sweep
  methodology lives in monitor-cron-sweep-iris; the table format in monitor-job-tables.
---

# monitor-restore-unified

> **Read first:** Iris **tools catalog** (`.agents/ops/iris/ops.md`) and **ops directory**
> (`.agents/ops/iris/` — `ops.md` for TPU `marin` particulars, `ops.md` for GPU)
> carry the binding access/preamble/gotchas + helper-script inventory.

The **UNIFIED OPS TICK** cron is session-only, expires after seven days, and may be lost on restart. Copy the
canonical prompt below verbatim into `CronCreate`. For the per-tick method use `monitor-cron-sweep-iris`; for
tables use `monitor-job-tables`.

## Scope — supersedes monitor-restore-iris

`monitor-restore-iris` installs the older prompt where datagen is out of scope. This skill owns:
- **(B)** the `qwen3.5-122b-131k-datagen-opencode-iris` campaign — keep-3 steady-state, with autonomous
  TERMINAL rescue (→ HF with literals) + refill, and confirmed-wedged kill+refill.
- **(C)** the `delphi` midtrain `1e23_p33m67_k0p20` — monitor-only.
- **(A)** the marin+CoreWeave sweep + native-route check + standing Daytona cleanup.

If both prompts are live, keep only one (`CronDelete` the other).

## When to run
- Start of a new session where the 131k datagen campaign / midtrain are in flight.
- The user says the monitor/cron is gone, down, "not firing," or after a disconnect/restart.
- After ~7 days (expiry).

## Steps
1. **Check if it exists** — `CronList`. If a recurring prompt begins "UNIFIED OPS TICK", do nothing. If this
   session owns datagen and a stale `monitor-restore-iris` variant is present, `CronDelete` it and install the
   prompt below.
2. **If absent, `CronCreate`** with:
   - `cron`: `23 */3 * * *`  (every 3 h at :23 — off the :00/:30 marks)
   - `recurring`: `true`
   - `prompt`: the exact text in the fenced block below.
3. Tell the user the new job id, that it is session-only and expires after seven days. `durable: true` is not
   honored; the cron fires only while the REPL is idle.

## Notes
- **Liveness tooling (operator directive 2026-07-13, memory [[iris_liveness_tooling_not_logtail]]):** judge
  liveness/wedge via `scripts/iris/iris_ops.py` + direct iris SQL, progress via GCS artifacts (checkpoint
  step+ts for training, trial count / output-bucket population for datagen). NEVER diagnose liveness from raw
  `iris job logs` tail (interleaved multi-rank lines; `--no-tail` returns startup lines; a clean preempt emits
  no terminal log line).
- **cgroup memory tracking is RETIRED (2026-07-13):** midtrain (C) reports child state + checkpoint-step delta only.
- **Single-region output migration (OT-Agent `c76dd23a`):** new datagen launches pass NO `--gcs-output-dir`, so
  the launcher's region-pin routes output to a co-located single-region bucket
  (`gs://marin-us-<region>/ot-agent/<job>`). Rescue resolves each job's RECORDED output URI via
  `hpc.iris.job_output_resolver` — legacy jobs stay on multi-region `marin-models-{us,eu}`. NEVER hardcode an output bucket.
- Companion skills: **monitor-cron-sweep-iris** (tick methodology), **monitor-job-tables** (datagen box table
  WITH Mean column), **datagen-job-cleanup** (idempotent rescue for a TERMINAL/wedged arm — dispatch a subagent
  armed with it), **datagen-launch-iris** (refill).

## Canonical cron prompt (copy verbatim into CronCreate)

```
UNIFIED OPS TICK. Source /Users/benjaminfeuer/Documents/secrets.env (never echo secrets). Spawn a general-purpose agent that reads the absolute-path ops docs and reports back; use PATH /Users/benjaminfeuer/miniconda3/envs/otagent/bin for iris+python. Wrap cw kubectl and any recursive gsutil in timeout. Use ABSOLUTE paths everywhere. Format the campaign status as a DATAGEN box-drawing table WITH a Mean-reward column per /Users/benjaminfeuer/Documents/OpenThoughts-Agent/.agents/skills/monitor-job-tables.

LIVENESS TOOLING (operator directive 2026-07-13): judge job liveness/wedge via /Users/benjaminfeuer/Documents/OpenThoughts-Agent/scripts/iris/iris_ops.py + direct iris SQL query, and progress via GCS artifacts (checkpoint step+ts for training, trial count / output-bucket population for datagen). NEVER diagnose liveness from raw `iris job logs` tail (interleaved multi-rank lines; --no-tail returns STARTUP lines not latest; a clean preempt emits no terminal log line). See memory iris_liveness_tooling_not_logtail.

(A) SWEEP both iris clusters (marin GCP + cw-us-east-02a) and the native route (expect 401). Note Daytona snapshot count on the cli org. STANDING CLEANUP: each tick, proactively reclaim idle harbor__ snapshots >120min via /Users/benjaminfeuer/Documents/OpenThoughts-Agent/scripts/daytona/daytona_snapshot_manager.py --api-key-env DAYTONA_API_KEY --stale-days 0.0833 --delete-stale --yes (run from the OT-Agent dir, secrets sourced). Deletes ONLY idle harbor__ env snapshots; the --name-prefix harbor__ default GUARDS base images (daytonaio/sandbox:*, daytona-*, windows-*) — NEVER delete those, never ACTIVE-recent (<120min). Report before/after count.

(B) CAMPAIGN qwen3.5-122b-131k-datagen-opencode-iris — keep-3 steady-state. Box table (arm | dataset | completed/total | Mean | liveness). Confirm each arm RUNNING+serving+advancing (advancing = GCS trial count up vs last tick), single serve dir, no job.py:263.
  MEAN COLUMN IS MANDATORY — pull it from the harbor `<done>/<total> Mean: <X>` progress line in the job logs: `/Users/benjaminfeuer/Documents/marin/.venv/bin/iris --cluster=marin job logs /benjaminfeuer/<job> 2>&1 | grep -aoE '[0-9]+/[0-9]+ Mean: [-0-9.]+' | tail -1` (retry on a transient finelog `dns error`/`StatsError`; that same line ALSO gives the freshest completed/total, more current than result.json). This targeted metric grep is NOT the prohibited liveness-by-log-tail — it is REQUIRED every tick. Mark `—` ONLY when the arm genuinely emits no Mean line (no verifier); do NOT default to `—` because result.json lacks a mean field. (result.json carries no mean — that is expected and is not a reason to drop the column.)
  >=95% KILL-AND-HARVEST (operator directive 2026-07-14): if a state-3 RUNNING arm is past 95% completed/total on ANY tick, KILL the child (autonomously authorized; child only) and HARVEST it as a terminal arm right now — do NOT await the last stragglers (the long tail is not worth the held v5p-8). Treat it exactly like a >=60% terminal arm: rescue via datagen-job-cleanup + refill. (Applies to normal deterministic-verifier arms; a still-cold-compiling or resume-scanning arm that only shows 95% because its total is not yet known is exempt — require real advancing trials.)
  TERMINAL arm (state 4/5/6): if >=60% complete, dispatch a subagent ARMED WITH /Users/benjaminfeuer/Documents/OpenThoughts-Agent/.agents/skills/datagen-job-cleanup (read that SKILL.md, follow its idempotent steps): gs:// rescue of the OUTER recorded output dir (resolve via hpc.iris.job_output_resolver — single-region gs://marin-<region>/ot-agent/<job> for new jobs, multi-region gs://marin-models-{us,eu}/ for legacy; NEVER hardcode) so logs/ literals ride along -> avg_turns realness check -> HF upload via make_and_upload_trace_dataset.py --episodes last with literals AUTO-INCLUDED and --served_model Qwen/Qwen3.5-122B-A10B-FP8 -> verify HF non-empty + Literal yield X/Y (X>0) + count_populated_literal_rows>0 -> report rows+yield. (If <60%, resume instead.) THEN submit a refill (next un-launched tracker dataset) on the newest validated :tpu image --preemptible (no --gcs-output-dir, so the single-region region-pin engages) and let iris schedule; update the tracker with the cleanup (repo+rows) and the refill.
  CONFIRMED-WEDGED datagen (state 3 RUNNING but authoritative-state RUNNING AND 0 trials / empty output bucket for hours with no engine-serving marker, OR harbor frozen >=3h fd-monitor-only per datagen-job-cleanup) -> kill the child + refill (autonomously authorized; child only). Distinguish from a healthy cold-compile/resume-scan (engine bringing up / recompiling) — do NOT kill those.
  If keep-N<3 for any reason, submit refill(s), let iris schedule — do NOT gate on a capacity guess. Preemptible jobs stay preemptible. The LLM-judge-verified datasets (laion/stackexchange-superuser-sandboxes-verified, laion/stackexchange-tezos-sandboxes-verified — tracker rows 120/121) RUN IN THE NORMAL keep-3 SEQUENCE — do NOT skip/hold them: their per-task task.toml propagates OPENAI_API_KEY into the trial verifier sandbox and the standard launch already passes --secrets-env "$DC_AGENT_SECRET_ENV" (which carries OPENAI_API_KEY), so the litellm judge scores real rewards. See datagen-launch-iris (Prerequisites > LLM-judge datasets) for the mechanism.

(C) MIDTRAIN 1e23_p33m67_k0p20 (you OWN this, monitor-only) — ONE-LINE STATUS via iris_ops.py/SQL (NOT log-tail): child state + live step / newest TEMP checkpoint step+ts (gs://marin-us-east5/tmp/ttl=14d/checkpoints-temp/.../delphi-1e23-p33m67-k0p20-lr0.67-b6607e/checkpoints/step-*/metadata.json) + whether the checkpoint step ADVANCED since last tick. NO memory-bounded field (cgroup tracking RETIRED 2026-07-13). A PENDING/re-placing child (preempt/crash-teardown/tier-monotonicity/capacity) is NORMAL — state it, do NOT flag/escalate/bounce; a stale checkpoint under preempt churn is expected. ONLY act on: a confirmed state-3 RUNNING-but-frozen wedge (authoritative state RUNNING + checkpoint stalled across multiple ticks + pod mismatch) -> Option A bounce the WEDGED CHILD only (never coordinator); or a confirmed cgroup OOM.

Relay a tight A/B/C report (campaign as a box-drawing datagen table with Mean).
```

If you change the cadence or scope, update BOTH the `cron`/`prompt` above and the live job (delete + recreate),
and keep **monitor-cron-sweep-iris** in sync — so this skill stays the canonical copy.
