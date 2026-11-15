---
name: monitor-cron-sweep-iris
description: >-
  The PROCEDURE for one every-3-hours Iris job-status sweep — primarily the marin TPU datagen/eval jobs
  ("iris" here = the marin TPU cluster), plus CoreWeave GPU-RL as monitor-only. Query both clusters, run the
  harbor analyzer on each active TPU datagen/eval job, classify every job (datagen / eval / other / GPU-RL)
  and apply its treatment, then take the standing DATAGEN-ONLY autonomous actions (auto-rescue, keep-2-in-flight).
  This is the methodology the recurring cron prompt runs; the cron itself is (re)installed via monitor-restore-iris.
  Use for "run an iris sweep / cluster sweep now" or as the reference behind each cron tick.
---

# monitor-cron-sweep-iris

The per-tick procedure for the lightweight Iris monitor: the **marin TPU** datagen/eval pipeline (the autonomous-action surface) plus **CoreWeave** (`cw-us-east-02a`) GPU-RL as **monitor-only**. Distinct from the broader tri-cluster **monitor-cron-sweep** (Leonardo + CoreWeave + TACC). The recurring cron that fires this is installed/restored by **monitor-restore-iris** (holds the verbatim cron prompt); this skill is the methodology behind it and can be run ad-hoc.

> **Iris orientation — read first:** the Iris **tools catalog** (`.agents/ops/iris/ops.md`) + ops directory (`.agents/ops/iris/` — CoreWeave GPU in `ops.md`, TPU `marin` in `ops.md`) carry the binding access/preamble/gotchas + helper-script inventory the steps below rely on.

> Autonomous WRITE actions are **datagen-only** (§4 rescue, §5 keep-2). Eval + GPU-RL + everything else are monitor-only. Never kill/restart a RUNNING job without express permission — the ONE exception is a confirmed zombie DATAGEN job (§4b).

## 1. Query both clusters (active + recently-terminal)
- **marin (TPU):**
  `/Users/benjaminfeuer/Documents/marin/.venv/bin/iris --cluster=marin query "SELECT job_id, state FROM jobs WHERE state IN (1,2,3) AND job_id LIKE '/benjaminfeuer/%' ORDER BY job_id DESC LIMIT 20" -f csv`
- **cw-us-east-02a (CoreWeave GPU)** — the `KUBECONFIG` prefix is REQUIRED (else iris uses the shell-default kubeconfig and errors):
  `KUBECONFIG=~/.kube/coreweave-iris-gpu /Users/benjaminfeuer/Documents/marin/.venv/bin/iris --cluster=cw-us-east-02a query "… same …" -f csv`
- For EACH cluster also query `state IN (4,5,6) LIMIT 8` to catch jobs gone terminal since the last tick.
- If the cw query errors (cluster down / creds), report it and continue with marin — don't fail the whole tick.
- States: 1=PENDING 2=starting 3=RUNNING 4=SUCCEEDED 5=FAILED 6=KILLED.

## 2. Metrics for each ACTIVE marin datagen/eval job → use **analyze-job-history-iris**
Run the harbor analyzer via the **analyze-job-history-iris** skill — do NOT eyeball a `--tail`. That skill is SLOW (paginates the full history, minutes per job — run foreground with a long timeout and WAIT; offload to a patient subagent for big 16k/46k-task jobs). Report from the JSON sidecar: runtime_h, iris_preemption_count, cycles total/served, gen tok/s mean/peak (n), Running mean/peak, non_empty/total trials = productive rate, t_first_serve, top harbor_exception_stats — PLUS two log-only fields that skill extracts (NOT in the sidecar): **mean reward** and **completed/total tasks** (`iris … job logs | grep -aoE '[0-9]+/[0-9]+ Mean: [-0-9.]+'`). The analyzer is harbor-shaped; it does NOT apply to CoreWeave GPU-RL (see class D).

## 3. Report + classify (`## Iris jobs status — <ISO UTC>`)
> **Table formatting → `monitor-job-tables`** (the authority): box-drawing tables (`┌─┬─┐`, NOT markdown), bucketed by type (RL · SFT · Datagen · Eval · Catch-all), with mandatory metric columns, signal thresholds, and benign-noise-vs-real-fault rules per bucket.

One line per job (name + state + CLOSED/PARTIAL/OPEN/DEAD) + a compact metrics block + a survival check (past cold compile? throughput sane vs S1 baseline gen mean~400/peak~1115? traces/results landing on HF?). Classify by job_id prefix:

- **A. Datagen** (`qwen3.5-122b-32k-%`): HF repo `penfever/<slug>-qwen3.5-122b-32k-traces`; image `ae085bc8`+ auto-uploads on state-4 — verify the repo self-created before rescuing. Short-task datasets run lower gen tok/s — judge by productive trial rate. Watch the heavy-dataset OOM-fix + stuck-PENDING (unpinned relaunch). **§4-5 standing actions apply to datagen ONLY.**
- **B. Eval** (`eval-%`): auto-syncs to Supabase + HF on completion (`--upload_to_database`); NO rescue, NO keep-2, NEVER auto-relaunch. ALWAYS report the leading metric — the `<done>/<total> Mean: <X>` harbor progress line from `iris --cluster=marin job logs <job_id>` — plus productive rate + harness exceptions; on a terminal job, whether results landed. (See eval-agentic-launch-iris.)
- **C. Other** (matches none of A/B/D/E — e.g. `serve-%` inference jobs): report state + a one-line health read; no autonomous write action.
- **E. Executor/Levanter training** (a marin-executor training run — a CPU coordinator `<run>-coord` PLUS its nested v5p training child `<run>-coord/checkpoints-<step>-<hash>`; e.g. `delphi-%`/`iris-run-midtrain_*`):
  **monitor-only — NO rescue, NO keep-2, NO auto-relaunch, NEVER kill.** The §2 harbor analyzer does NOT apply (no harbor trial sidecars, like GPU-RL). Run **analyze-training-run-iris** on the CHILD job and report its compact line: `step=<cur>/<total> (X%) loss=<L> ~<T>tok/s preempts=<P> gaps=<G>/<H>h ckpt=step-<C>` + a health read (past setup/compile? step rate sane vs last tick? loss finite & trending down? preemptions resuming cleanly — checkpoint advancing? ETA to the K-budget target). That skill reads W&B per-step history (`nyu-dice-lab/delphi-midtraining`, run = the GCS output-path hash) + `iris job summary` (preemptions) + GCS `step-*` checkpoints; empty W&B history = **pre-first-step** (still HF-download/XLA-compile), not a gap.
- **D. GPU-RL** (CoreWeave, `rl-%` / `rl-iris-%` / MarinSkyRL GRPO on H100×8, possibly multi-node `replicas>1`):
  **monitor-only — NO rescue, NO keep-2, NO auto-relaunch, NEVER kill/relaunch.** The §2 analyzer does NOT apply (no harbor trial sidecars). Report state + latest RL progress from the persistent finelog (pods GC on terminal):
  `KUBECONFIG=~/.kube/coreweave-iris-gpu iris --cluster=cw-us-east-02a job logs <job_id> --max-lines 100000 --no-tail`
  then grep `WANDB_MIRROR kind=train step=` for the latest `trainer/global_step`, `loss/avg_raw_reward`, `generate/num_failed_trajectories`/`errors`; for multi-node confirm `All N Ray node(s) joined`. On terminal, report exit state. For a NEW/untested RL run, deep-probe via **rl-job-health-deep-dive** (KILL/NO-KILL). (Finelog retention is finite — report what survives.)

## 4. AUTO-RESCUE — DATAGEN ONLY (autonomous; overrides read-only)
- **4a. TERMINAL rescue:** a datagen job terminal (4/5/6) with productive GCS trials that did NOT auto-upload (HF repo missing/stale) → rescue automatically, no need to ask.
- **4b. ZOMBIE kill-then-rescue (datagen only):** state 3 AND harbor frozen ≥3h (`harbor_updated_at` stale) AND the task log shows ONLY `[fd-monitor]` heartbeats in that window (no vLLM/harbor/trial activity) → confirmed zombie: `iris --cluster=marin job stop <job>`, then rescue per 4a. The fd-monitor-ONLY clause is the safety gate (a healthy cold-compiling/preempt-recompiling job emits XLA/vLLM logs, so it won't match). Unsure wedge vs slow long-task cycle → do NOT kill; report and ask. Before killing, ALSO rule out the §4c resume-scan (a healthy vLLM engine ⇒ NOT a zombie).
- **4c. RESUME-SCAN check (report, NEVER kill) — the benign twin of §4b:** a datagen job can match §4b's signals (state 3, harbor frozen, fd-monitor-only) yet be healthy — it's mid harbor GCS-`jobs_dir` resume after a preempt, emitting only `[fd-monitor]` while the vLLM engine is already up. **DISCRIMINATOR:** a recent engine-ready marker with NO serving yet ⇒ resume-scan, not zombie. Detect + report per active datagen job:
  1. engine-ready ts: `iris --cluster=marin job logs <job> --max-lines 20000 | grep -aE "Application startup complete|Starting vLLM API server" | tail -1`
  2. progress advancing? compare the harbor `<done>/<total> Mean:` line across the tick (or `harbor_updated_at` from the §2 sidecar). Frozen + recent-tail fd-monitor-only (`iris ... job logs --max-lines 300 | grep -aoE 'fd-monitor|Mean:|serving|vllm' | sort | uniq -c`) ⇒ in a resume scan.
  Report it explicitly: `RESUME-SCAN ~<Nh> (engine up @<T>, harbor idle, <done>/<total> trials)` — this is EXPECTED on pre-fix builds and self-resolves; do NOT kill and do NOT count it as a stall. The durable fix is the harbor O(existing) resume speedup (harbor `7010e48c`, in the `:tpu` image rebuilt 2026-07-02) — jobs on the current image resume in minutes; surface "relaunch on the current image to eliminate the resume tax" for a job that keeps paying it. ESCALATE (report as an OUTLIER, still NO auto-kill) only if the resume exceeds ~8h with a still-healthy engine (beyond the observed max); if there is NO healthy engine, it is the §4b zombie path.
- **Rescue mechanics (both):** resolve the job's RECORDED output prefix — never hardcode a bucket (jobs now pin to single-region `gs://marin-<region>`, older jobs to the multi-region mirror):
  `OUT=$(…/otagent/bin/python -m hpc.iris.job_output_resolver "$JOB" --cluster …/marin.yaml)` — then
  `gsutil rsync` the OUTER `$OUT/` (`.../ot-agent/<job>/`) → `/tmp/<job>_traces`
  (the OUTER `<job>/` — carries the trial dirs AND the sibling `logs/<slug>_literal.jsonl`; do NOT rsync only the inner `<job>/<job>/`, which drops `logs/` and silently loses the literals for a `--record_literal` job),
  then `make_and_upload_trace_dataset.py --job_dir /tmp/<job>_traces --repo_id penfever/<slug>-qwen3.5-122b-32k-traces --episodes last --filter none --skip_register` (source `$DC_AGENT_SECRET_ENV` first). Literals AUTO-INCLUDE when a `logs/*_literal.jsonl` is present (`--no_literal_tokens` to force text-only; FAILS LOUD on a present-literal / 0-bind). Report row count AND the `Literal yield: X/Y` line (X>0 for a `--record_literal` job); update the tracker. (Full launch/rescue detail: **datagen-launch-iris**.)

## 5. KEEP TWO DATAGEN IN-FLIGHT (datagen only)
If active datagen (`qwen3.5-122b-32k-%`, state 1/2/3) < 2, auto-launch the next `pending` dataset from `/Users/benjaminfeuer/Documents/experiments/active/datagen/qwen3.5-122b-tt/tracker.md` via the datagen launch template (S1, `ctx32k_verified.yaml`, `--tpu v5p-8 --preemptible`; **omit `--gcs-output-dir`** so the launcher auto-pins a co-located **single-region** output bucket for the chosen region — passing it explicitly opts OUT of the region pin and forces that exact bucket, so only pass it to deliberately override; repo `penfever/<slug>-qwen3.5-122b-32k-traces`) — see **datagen-launch-iris**. Flip its tracker row to RUNNING. Eval jobs do NOT count toward the 2 and are never auto-launched.

**Snapshot-cap hygiene — PROACTIVE every tick (2026-07-10 operator directive):** every tick, unconditionally **reclaim idle `harbor__` snapshots** on the cli-org (`DAYTONA_API_KEY`) via `daytona_snapshot_manager.py --api-key-env DAYTONA_API_KEY --delete-stale --yes` (run from the OT-Agent dir, secrets sourced) — at the stale threshold defined in `.agents/projects/daytona/daytona.md` § "How to clean stale snapshots" (GT — don't restate the value). Do NOT wait for a refill to be blocked or the org to hit ~58/60; keep the org clean by default. Report before/after count. This deletes ONLY idle `harbor__` env snapshots (rebuilt on demand by harbor `auto_snapshot`) — the `--name-prefix harbor__` default guards the shared base images (`daytonaio/sandbox:*`, `daytona-*`, `windows-*`), which must never be deleted, and the idle threshold never hits an ACTIVE-recent snapshot in use by a running job. Full procedure: **utils-reclaim-stale-snapshots**.

## 6. No-kill guardrail
Never kill/restart/bounce a RUNNING job or the cluster without express permission — the ONLY exception is the §4b confirmed-zombie DATAGEN kill. Autonomous write actions = datagen rescue (incl. §4b) + datagen refill. GPU-RL and everything else stay strictly no-touch (flag, never kill). Stuck PENDING (no capacity) → report + surface the unpinned-relaunch option; don't kill a placed job unprompted.

## Related skills
- **monitor-job-tables** — the §3 report FORMATTING authority.
- **monitor-restore-iris** — (re)installs the recurring 3-hour cron that runs this procedure (holds the verbatim prompt).
- **analyze-job-history-iris** — the §2 analyzer recipe for class A/B datagen+eval (foreground-and-wait; mean-reward + completed/total extraction).
- **analyze-training-run-iris** — the class-E recipe for executor/Levanter training runs (step progress + major-gap detection via W&B + `iris job summary` + GCS checkpoints).
- **datagen-launch-iris** — launch / rescue / snapshot-cleanup mechanics for §4–§5.
- **rl-job-health-deep-dive** — deep per-RL-job KILL/NO-KILL probe for class-D GPU-RL in new/untested settings.
- **monitor-cron-sweep** / **monitor-restore** — the separate broader tri-cluster (Leonardo+CoreWeave+TACC) campaign.
