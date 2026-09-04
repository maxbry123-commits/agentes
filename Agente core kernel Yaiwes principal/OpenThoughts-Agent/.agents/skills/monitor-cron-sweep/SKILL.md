---
name: monitor-cron-sweep
description: >-
  Produce a comprehensive cross-cluster job-status update for a recurring N-hourly cluster sweep. Gather
  squeue/sacct on each cluster (validating against false-drain), bucket every active + recently-terminated
  job by type (RL / SFT / datagen / eval / catch-all), pull each type's signals, render them in the
  job_monitor_table.md formats, and flag completions (→ the matching cleanup skill), genuine failures
  (→ diagnose + agent_logs), and per-type health red-flags. Cluster-AGNOSTIC — ssh strings, code/log/exp
  paths, concurrency caps, gpu-mem ceilings live in `.agents/ops/<cluster>/`. Use for "run a cluster sweep",
  the N-hourly cron, or "give me a status update on all jobs".
---

# monitor-cron-sweep

Deploy each cron sweep to produce ONE comprehensive update across all active clusters.

> **⚠ STEP 0 — READ `.agents/ops/<cluster>/ops.md` FIRST, every sweep, for each cluster you'll touch.**
> It carries the binding gotchas: the **GPFS `find`/`du` ban** (stat-walks stall SSH for minutes — locate
> logs via `scontrol show job <id> -o` `StdOut=`/`%Z` + depth-1 `ls`), the **login01 fork-saturation
> false-drain** (re-check via login02/03/04), **cleanup-isn't-done-until-rm'd**, the **SIF/Ray-actor/NCCL
> debugging tooling** (ptrace blocked → faulthandler; the `opCount dead` false-positive), the
> **sig53/EDQUOT** traps, and shell idioms (`sacct -S now-Nhours`, simple single-string ssh).

> **Local clone = ground truth.** Any code/config fix this sweep performs — or dispatches a subagent to
> perform — is edited in the local Mac checkout → commit → push → `git pull` on the cluster. **NEVER**
> hand-edit, `git commit`, or leave divergent/untracked changes on a cluster; no patch-by-rsync (vLLM
> built from source per-cluster). **Bake this rule into EVERY subagent prompt you dispatch.**

> **Tables → the `monitor-job-tables` skill** (box-drawing `┌─┬─┐`, NOT markdown), bucketed RL · SFT ·
> Datagen · Eval · Catch-all, with the mandatory metric columns, thresholds, and benign-noise-vs-real-fault
> rules per bucket. This skill is the *process* that fills those tables. **Cluster particulars** (ssh,
> paths, RL concurrency cap, gpu-mem ceiling, dotenv) live in `.agents/ops/<cluster>/ops.md` — no
> cluster-specific values inlined here.

## 1. Gather (per cluster)

> **Scope = Leonardo + CoreWeave(iris) + TACC(Vista) — all three each sweep.** Jupiter is SKIPPED (MDC
> downtime until ~2026-07-12 — re-add as a 4th cluster when it returns); Perlmutter DROPPED 2026-06-05
> (do NOT ssh). Leonardo + TACC are SLURM (`squeue`/`sacct`); CoreWeave is a k8s/iris controller backend
> with NO ssh — state-poll the iris lifecycle.

**SLURM clusters (Leonardo, TACC):**
- `squeue -u <user> -t RUNNING` + `sacct -u <user> -S <-Nh> -X` (terminal states since last sweep). TACC
  `<user>`=`penfever` via `ssh TACCVista`; Leonardo `<user>`/ssh → `ops/leonardo`.
- **Validate squeue succeeded before trusting a 0-count.** A slurmctld timeout prints
  `slurm_load_jobs error: Socket timed out` with NO job lines → a naive `grep -c` reads 0 → false
  "drained". Treat an errored squeue as UNKNOWN (keep waiting); prefer a positive done-signal via
  `sacct -j <ids> --format=State` (slurmdbd survives slurmctld outages). login01 fork-saturation is a
  second false-empty cause → re-check via login02/03/04. Mandatory before any destructive datagen
  consolidate+delete.

**Leonardo gather/triage → `ops/leonardo/ops.md` ("Sweep / gather particulars").** The Leonardo layer
(GPFS `find`/`du` ban, `scontrol` log location, eval log-path trap, standard-eval results-JSON shape,
active campaigns, flawed_summ `POLICY.md`/`STATE.md`, HF-upload sbatch-tunnel, step-ca cert, `$WORK` vs
`$SCRATCH_FAST`) lives there. Cross-cluster rules that DO apply: `AgentTimeoutError` /
`ContextLengthExceeded` are EXPECTED passthrough exceptions in agentic eval (still scored) — never the
cause of a hang. **Drive named campaigns (flawed_summ et al.) off their OWN tracker docs — do NOT restate
their rules here (restated rules drift): each sweep READ the campaign's `POLICY.md`/`STATE.md` and drive
off them.** Eval launch/listener mechanics live in **`eval-agentic-launch`** + `.agents/projects/ot-agent/`,
not here.

**CoreWeave(iris) — STATE-POLL, not squeue, not a log-string watch:**
- `export KUBECONFIG=~/.kube/coreweave-iris-gpu` in the same shell FIRST (the Mac default kubeconfig points
  at a DIFFERENT cluster → wrong-context "0 pods/not found"). Use the **otagent-env iris binary**
  `/Users/benjaminfeuer/miniconda3/envs/otagent/bin/iris` (the marin `.venv` iris has a broken `kubernetes`
  import). All `iris`/`kubectl` calls SYNCHRONOUS (never background).
- Per active job, poll the authoritative lifecycle:
  `PY=/Users/benjaminfeuer/miniconda3/envs/otagent/bin/python; $PY scripts/iris/iris_ops.py /benjaminfeuer/<job> --once --json`
  and/or `iris --cluster=cw-us-east-02a job summary --json` (authoritative). `iris … query` over the jobs
  table (state 1=PENDING 2=BUILDING 3=RUNNING) lists live jobs. **Treat "running-but-0-pods / record
  disappeared" as TERMINAL** — the silent-wedge signature (a clean kill/eviction/preempt emits no terminal
  log line + reaps pods). Log-content greps (`scripts/iris/analyze_iris_harbor_job.py`, `sel_rows`/`EPDIAG`)
  are for SCIENCE/throughput ONLY, never liveness. Full log: `iris … job logs --since-ms <submitted_at_ms>
  --no-tail` (finelog keeps the whole log; only `--tail` caps lines).
- RL bring-up signals (fresh launches): gang/leafgroup Kueue admission (pods SchedulingGated until
  atomically admitted = normal), `apply_ep`/mesh-load, weights resolving. `shm_broadcast …60s` + a
  transient ghcr-EOF ImagePullBackOff self-heal are BENIGN bring-up noise. `--max-retries ≥1` re-brings-up
  the gang on a transient HF-weight-resolution flake.

**TACC(Vista):** `ssh TACCVista` (ControlMaster live, hardened single-string ssh). `salloc` is BLOCKED →
sbatch; uv/builds go in a CPU `-p gg` sbatch, never the shared login node. Compute nodes have FULL internet
→ **NO proxy/SOCKS/step-ca cert** (contrast Leonardo). GPUs are NOT a SLURM gres (whole-node alloc);
RealMemory misreported. Agentic eval runs through the front door
`python -m hpc.launch --job_type eval_listener --cluster-config tacc`
(`sbatch_script`=`eval/tacc/eval_harbor.sbatch`, `eval_jobs_dir`=`/scratch/10635/penfever/eval_jobs`) —
**newly integrated, currently validated by a canary**, so sanity-check the canary's traces uploaded +
registered before relying on it. Harvest finished TACC evals the same way as Leonardo
(`eval-agentic-cleanup` if auto-register failed).

**Cross-cluster liveness + inode checks (apply per cluster):**
- **LIVENESS — `RUNNING` is NOT proof of progress (catches silent wedges).** A job can hold its allocation
  for hours while hung (engine deadlock, NCCL stall, generation-buffer wedge) — squeue still says RUNNING.
  For EVERY RUNNING job, `stat -c%y <StdOut>` and compare log mtime to "now": if a job has emitted NOTHING
  materially longer than its expected cadence (RL step / SFT log interval / eval trial — minutes, not
  hours), treat as a **suspected silent hang** → investigate (tail the log, grep ray-worker logs for
  EngineDead/NCCL-timeout/Watchdog/RPC-timeout around the last-output timestamp). A multi-hour-stale log on
  a multi-node job is a wedge burning nodes → diagnose + (with permission, since it's RUNNING) kill+relaunch.
  **Never report a RUNNING job as "healthy" without confirming its log is live.** Put the log-mtime ("last
  output N min ago") in the table.
- **INODE HEADROOM (each sweep) — `jutil project dataquota -p <project>` + `df -i`.** Inodes (file COUNT),
  not bytes, are the binding constraint; the shared `datasets` project on `/e/data1/datasets` (where
  `…/playground/ot-baf` lives) runs chronically near/over its soft limit. (DORMANT while Jupiter is down,
  re-arm when it returns; Leonardo's bind is disk quota, not inodes → `ops/leonardo`; CoreWeave artifacts
  go to HF/R2, no POSIX tree to reap.) See `ops/jupiter/ops.md` → "Inode allocations" (`#inode-allocations`).
  At/over the inode soft limit → sweep red-flag → trigger the cleanup-reclaim step (§4).

## 2. Bucket every job by type
By job-name prefix / run-tag: `rl__*` → **RL**, `sft__*` → **SFT**, `datagen__*` → **Datagen**,
`eval-*` / eval run-tags → **Eval**, everything else (consolidate, pretokenize, hf_upload, SIF build,
DCP/CP/GPU-CI smoke, measurement/grid probes) → **Catch-all**.

## 3. Render per `monitor-job-tables` (unify cross-cluster per type)
**Unify all clusters' runs of a type into ONE table.** Extraction pointers:
- **RL** — Step (`.out` tqdm `Training Step Progress: N/M` or `trainer/global_step`) + reward/grad/entropy/
  TIS from the WANDB_MIRROR lines (chain-restart logs may have step but not the dict — scan the chain's
  logs). Apply the collapse-signal rule. **For any RL job in a NEW/UNTESTED setting** (new
  config/geometry/model/image, a "debug"/"smoke-test" run, or the first launch after a code/config change),
  the table row is NOT enough — **dispatch a subagent armed with `rl-job-health-deep-dive`** this tick to
  deep-probe it (sync trace_jobs + logs, live-poll GPUs vs the serving LUT, read the literal rollouts) → a
  **KILL/NO-KILL recommendation**. State-poll + metrics can read "healthy" on a run that is silently dead
  (weight-sync garbage, engine-starvation wedge, all-reward-0). Carry the verdict into §4; the supervisor
  owns the actual kill.
- **SFT** — Step + `{'loss','grad_norm'}` from the `.out` (NOT trainer_log.jsonl); total steps from the
  config/banner.
- **Datagen** — chunks done/total (squeue+sacct) + `result.json` count + avg_turns (realness gate: ≈1.0 =
  dead) + exc%.
- **Eval** — `result.json`/total + pass-rate + top exception + the 4 infra checks (`eval-agentic-launch` §4
  for greps).
- **Catch-all** — one line each: State / Elapsed / human note.

## 4. Flag + hand off
- **Completion → the matching cleanup skill:** RL by flavor — **agentic** (Harbor/Daytona/terminal_bench)
  → **`rl-agentic-job-cleanup`**; **standard / non-agentic GRPO** (the Delphi/rlvr/dapo math cells from
  `rl-standard-launch-leonardo`; no `trace_jobs/`) → **`rl-standard-job-cleanup`** (model + metric CSVs
  only, no trace dataset). SFT → **`sft-job-cleanup`** (upload + DB register). datagen (all chunks done) →
  **`datagen-job-cleanup`** (consolidate + advance the tracker). eval → **`eval-agentic-cleanup`** (only
  if auto-upload/register failed). For RL, recognize **resume-overshoot**: a clean COMPLETED at `max_steps`
  means done → cleanup; spurious past-max chain links should be cancelled.
  **CLEANUP IS NOT DONE UNTIL THE ARTIFACT DIR IS `rm`'d.** Uploading to HF then leaving the experiment's
  `trace_jobs/`/`tasks/`/already-pushed-`exports/` subtrees on disk is the #1 inode leak. Every cleanup
  handoff (and every cleanup subagent prompt) MUST: confirm the artifact is on HF, then **delete the
  on-disk trees** (detached `rm` per the GPFS-delete discipline in `ops/jupiter/ops.md`), and **verify inode
  reclaim** (`df -i` / `jutil`).
- **HF-only SFT chain (Delphi #6279 + any `enable_db_registration: false` series) — "move the chains", 3
  legs, autonomous every sweep, no asking:**
  1. **SFT completes → HF upload** via `sft-cleanup-hf-only` (NOT `sft-job-cleanup`; upload, **no DB**).
  2. **upload completes → `eval-standard-launch`** for the newly-uploaded cell(s).
  3. **eval completes → record scores** in the tracker — Delphi midtrained-cell grid →
     `main_sft_evals/SCORES.md`; **base-model SFT grid (#6279 rows 2&4) → `base_sft_evals/grid.md`** (one
     row per base×recipe cell).
  Each sweep advance whichever leg is pending (catch up backlog). Idempotent — skip done legs. Applies to
  BOTH `main_sft_evals` (27 midtrained cells) AND `base_sft_evals` (9 base × 2 recipes = 18 cells).
- **Standalone eval-grid trackers (self-describing — harvest pending rows every sweep):** any tracker
  markdown holding `⏳ pending` rows with a recorded `eval job` id — e.g.
  `experiments/active/delphi/rl-scaling-laws-6279/baseline_evals/grid.md`, `…/base_sft_evals/grid.md`,
  `…/pass_at_k_sft_evals/grid.md`, `…/main_sft_evals/SCORES.md`. For each pending row:
  `sacct -j <jobid> --format=State` → on `COMPLETED`, harvest per `EVAL_CONVENTION.md` §5.2 D/E (rsync the
  per-task `results_*.json` to the tracker's `<RUN>/` dir, **verify the JSON has numeric scores — a
  COMPLETED job can carry an empty `results:{}`**, extract MATH500/AIME24-mean±se/gsm8k, fill the row, flip
  to ✅). On failure, diagnose per `EVAL_CONVENTION.md` §3.3 + log. The tracker carries the jobids — read
  the grid each sweep.
- **Cluster working-tree hygiene (every sweep, Leonardo + TACC only — CoreWeave has NO clone: the iris
  launcher uploads the local Mac workspace to `/app` per launch, so a local commit takes effect on the next
  launch with no push/pull and no on-cluster tree to drift):** run `git -C <cluster repo> status --short`.
  If untracked/modified files have piled up (ad-hoc launch scripts, priority lists, configs, `.bak`s,
  manifests, stray `&1` junk), **triage them back to the local ground-truth clone**: rsync local, **TRACK**
  the reusable/canonical ones (commit locally → supervisor pushes; place at the path matching tracked
  siblings, e.g. `eval/lists/*.txt`, `sft/lf_configs/`, launchers under `scripts/`), **GITIGNORE** the
  recurring transient/generated set (`*.bak`, `*_manifest.txt`, `&1`, ephemeral `reeval_priority_*`). Diff
  any tracked-but-modified vs origin first (identical → stale HEAD). Reconcile the cluster with **`git pull`
  (fast-forward) — NEVER `git reset --hard`** while live jobs depend on uncommitted working-tree state.
  Dispatch a triage subagent if the set is large.
- **Chain-restart TIMEOUT** (12h/24h wall) with a successor RUNNING/PENDING → **normal, not a failure** —
  note the successor.
- **Genuine FAILED** (exit≠0, not a wall TIMEOUT) → diagnose (read the first real traceback, often masked
  by the elastic summary) + a dated **`agent_logs/`** entry; recurring identical failures ≠ transient.
- **RL collapse rule** (≥2 signals fire same step) → flag for cancel+salvage per `rl-agentic-job-cleanup`.
  **Spike-mitigation ablations OVERRIDE this:** a job_name containing `zclip`/`staleclip`/`stale_clip`/
  `z_clip`/`maxgn09_hint`/`shaped_entropy` (or any spike-mitigation tag) is NOT auto-scancelled on 2/4
  collapse signals — observing whether the mechanism damps the spike IS the experiment (still REPORT the
  signals, marked "ablation observation, not actionable"). Standard runs (a3/a2/a1-base, no tag) DO follow
  cancel+salvage. A real crash/NaN/SIGSEGV is still a genuine failure → diagnose.
- **New/untested RL → act on the `rl-job-health-deep-dive` verdict:** **NO-KILL** → note it + the
  watch-signal that would flip it; **KILL** → it's our own doomed/wedged job, so (with the standing
  kill-permission in mind) the supervisor cancels + relaunches on the corrected setting per
  `rl-agentic-launch-iris`/`rl-*-launch-*`, logging the probe + verdict to a dated `agent_logs/` entry.
  Don't sit on a confirmed-garbage run for another 3h.
- **Eval** stall/zombie/instant-fail red-flags → act per the `monitor-job-tables` Eval section;
  **`DCAgent2/*` measurement runs are EXEMPT** (report as calibration, not production).
- **Writing discipline (agent_logs + ops edits):** lead with WHAT (the fact/state/change), concise, no
  speculation. Ops docs hold validated ground truth only — a doubted/unvalidated claim goes to a dated
  `agent_logs/` entry with a ⚠ pointer in the ops doc, NOT asserted as fact.

## 5. Respect the standing constraints (reference, don't relitigate)
- **RL concurrency cap per cluster** (value in `ops/<cluster>`); **a3 series CONCLUDED** — do NOT
  launch/refill a3 rows; **`enable_db_registration: false`** in YAMLs → DB registration is the manual
  cleanup step only; **Daytona snapshot org cap is HARD** — at the cap clean STALE snapshots, never raise
  it; **cross-user FK safety** before ANY Supabase delete/mutate (restrict to rows you own). Full policy →
  the cron sweep directive + the cleanup skills.

## 6. Output + record
Post the bucketed tables (RL/SFT/datagen/eval/catch-all) + a short **"actions taken / flagged"** summary
(completions cleaned/handed off, failures diagnosed, health flags, anything launched). Log a standalone
dated file under `~/Documents/agent_logs/` (`YYYY-MM-DD_<topic>.md`) + update the relevant tracker (a3 /
MiniMax datagen / Delphi). Skip unreachable clusters (note it) rather than blocking.
