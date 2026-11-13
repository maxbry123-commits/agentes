---
name: monitor-restore
description: >-
  Re-create the local 3-hour tri-cluster cluster-sweep loop (Leonardo + CoreWeave(iris) + TACC(Vista); Jupiter
  SKIPPED until ~Jul 12) — the autonomous ML-ops monitor — if it has been lost. The loop is session-only and is
  dropped on any session restart, so re-establish it at the start of a new session or whenever the user asks to
  restore/restart the 3h sweep/cron/monitor. Sets a /loop 3h (or equivalent recurring cron) whose task is the
  canonical sweep prompt below: status-table active/pending/completed jobs, auto-cleanup+DB-register completions,
  diagnose+remediate failures via subagents, log each launch/state-change as a standalone dated file to agent_logs/. The prompt block here is
  the source of truth — copy it verbatim.
---

# monitor-restore

Re-creates the recurring **3-hour cluster sweep** — **CoreWeave(iris) + TACC(Vista) + EmpireAI(Beta)** (Leonardo DROPPED 2026-07-17 per operator — re-add its sections from git history when it returns; Jupiter SKIPPED, MDC maintenance until ~2026-07-12). The loop is **session-only** (lost on every restart), so this skill is the durable source of truth for re-installing it.

## When to run
- Start of a new session where Leonardo / CoreWeave / TACC jobs are in flight (or expected).
- The user says the monitor/cron/sweep is gone, down, "not firing," or asks to "restart the 3h loop."
- After ~7 days if running it as a `CronCreate` recurring job (auto-expiry).

## How to (re-)establish it
1. **Check for an existing one first** — `CronList` (+ any active `/loop`). If a recurring sweep mentioning "3-hour … leonardo, coreweave, tacc" (or legacy "jupiter, leonardo") is already live, do **not** duplicate (doubles the ssh/SQL/Daytona/iris load). Otherwise:
2. **Start the loop** (user's phrasing: "**/loop 3h or equivalent, active session only, maximum duration**"):
   - **Preferred — `/loop`:** interval **3h**, **maximum duration** the harness allows, task = the canonical prompt below.
   - **Equivalent — `CronCreate`:** `cron: 17 */3 * * *` (off the :00 mark to avoid contention), `recurring: true`, `prompt:` = the canonical block verbatim.
3. Tell the user it's set + caveats: **session-only** (re-run next session) and, for the cron variant, **7-day auto-expiry**.

## Supporting skills/docs the sweep leans on
- **Sweep procedure:** `monitor-cron-sweep` (per-cluster Leonardo / CoreWeave / TACC gather+triage); `monitor-job-tables` + `/Users/benjaminfeuer/Documents/notes/ot-agent/job_monitor_table.md` (per-type table formats + metric/red-flag definitions; the unified RL table spans Leonardo + CoreWeave).
- **Cleanup:** `rl-agentic-job-cleanup` (agentic), `rl-standard-job-cleanup` (standard GRPO), `sft-job-cleanup`, `datagen-job-cleanup`, `eval-agentic-cleanup`, `eval-standard-cleanup`.
- **Launch:** `rl-agentic-launch-iris` (CoreWeave RL), `rl-standard-launch-leonardo`, `sft-launch` (Leonardo via `ops/leonardo/ops.md §SFT`), `datagen-launch`, `eval-agentic-launch`, `eval-standard-launch`. (`rl-*-jupiter` skills apply when Jupiter returns.)
- **Cluster particulars:** `.agents/ops/leonardo/ops.md`, `.agents/ops/iris/ops.md` (+ `ops.md`), `.agents/ops/tacc/ops.md`, `.agents/ops/local/ops.md`. **Dependency facts:** `.agents/projects/{marinskyrl,harbor,vllm,llama-factory,daytona}/`.
- The canonical prompt below overrides the repo `CLAUDE.md` and any memory/skill on conflict.

## Notes
- A cron/loop only fires while the REPL is idle (not mid-task); if it reliably misses, fall back to the user pasting the prompt.
- **Path correction baked into the prompt:** local SkyRL checkout is `/Users/benjaminfeuer/Documents/MarinSkyRL` (the user's usual prompt says `…/SkyRL`). All other paths verbatim.
- **Jupiter SKIPPED** until ~2026-07-12 (MDC maintenance). On return, re-add as a 4th cluster (ops doc `.agents/ops/jupiter/ops.md`; launch/cleanup = `*-jupiter` variants) in both this block and the live loop.
- **CoreWeave per-run Monitors** (`scripts/iris/iris_ops.py`) are a complementary finer-grained layer for actively-debugging runs — not a substitute for the 3h sweep, or vice-versa.

---

## Canonical sweep prompt (copy verbatim into `/loop 3h` or `CronCreate`)

```
3-HOURLY CLUSTER SWEEP — clusters: coreweave(iris), tacc, empireai(beta) (active session only, run to max duration).
[Leonardo DROPPED 2026-07-17 (operator) — re-add its STEP-0 gotchas + gather + the flawed_summ/rl_dlp CAMPAIGN DRIVER from git history when it returns. Jupiter SKIPPED — MDC maintenance until ~2026-07-12.]

⚠ NO EXPERIMENT-SPECIFICS IN THIS PROMPT (they go stale): per-campaign values (in-flight TARGET, refill cluster/grouping/order, harvest gates + discriminators, region/launch gotchas, current bugs) live in the EXPERIMENT TRACKERS under `~/Documents/experiments/active/` (+ the `*-launch` / `*-cleanup` / `analyze-*` skills). READ the relevant tracker each sweep and drive off IT; never hardcode a number/rule here. The CAMPAIGN DRIVER sections below name WHICH tracker to read, not its contents.

STEP 0 (do this FIRST, every sweep): read EACH cluster's ops doc for its BINDING gotchas before touching it —
- empireai(beta) → `.agents/ops/empireai/ops.md`: 2FA keyboard-interactive login — RIDE the operator's ControlMaster socket (`ssh EmpireAI_Beta`; cannot 2FA headless); ⚠ the Beta master socket is REAPED in minutes by the login-node session-killer — if a non-interactive `ssh -o BatchMode=yes` fails, the socket needs an operator reconnect (they keep a warm activity loop) → SKIP + note, don't block; ALWAYS wrap remote cmds in `bash -lc` (SLURM/Pyxis invisible otherwise); user `bf996`, `--account=ny_chinmayh_datacomp`; SBATCH-DETACH all multi-minute work (survives socket death), poll via brief `ssh … sacct`/`tail` windows; storage = HOME `/mnt/home/bf996` (VAST); compute = Pyxis/Enroot containers mandatory.
- coreweave(iris) → `.agents/ops/iris/ops.md` (+ `ops.md`): NO ssh/login — drive via the iris SDK from the Mac; `export KUBECONFIG=~/.kube/coreweave-iris-gpu` is a HARD prereq in the same shell (Mac default kubeconfig points at a DIFFERENT cluster → wrong-context "0 pods/not found"); use the OTAGENT-ENV iris binary `/Users/benjaminfeuer/miniconda3/envs/otagent/bin/iris` (the marin `.venv` iris has a broken `kubernetes` import); all `iris`/`kubectl` calls SYNCHRONOUS (never background); CoreWeave nodes have egress (NO `HF_HUB_OFFLINE`).
- tacc(Vista) → `.agents/ops/tacc/ops.md`: `ssh TACCVista` (hardened single-string ssh); `salloc` BLOCKED → use sbatch; compute nodes have FULL internet (NO proxy/SOCKS/step-ca cert — contrast Leonardo); GPUs are NOT a SLURM gres (whole-node alloc) and RealMemory is misreported; uv OOMs on the shared login node → any build/install goes in a CPU `-p gg` sbatch, never the login node.

PER-CLUSTER GATHER (validate each before trusting; procedure = `monitor-cron-sweep`, particulars = each ops doc):
- EMPIREAI(beta) — `squeue -u bf996` + `sacct -u bf996 -S now-3hours -X` via `ssh -o BatchMode=yes EmpireAI_Beta "bash -lc '…'"` (filter the `module: command not found` / `Loading gcc` noise). If BatchMode ssh FAILS (socket reaped), NOTE "EmpireAI socket down — needs operator reconnect" and SKIP (can't 2FA headless) — do NOT block. For any live Axolotl SFT job: poll `~/logs/<name>_<jobid>.out` for the latest step + read the latest `checkpoint-<N>/trainer_state.json` (`log_history[]` step/loss/grad_norm; `global_step`/`max_steps`); fetch that small JSON to the relevant experiment dir per the ops-doc recipe, NEVER checkpoints. READ the active EmpireAI experiment tracker under `experiments/active/` and drive off IT.
- COREWEAVE(iris) — STATE-POLL the authoritative iris lifecycle, NOT a log-string watch (a clean kill/eviction/preempt emits no terminal log line + reaps the pods):
    KUBECONFIG=~/.kube/coreweave-iris-gpu; PY=/Users/benjaminfeuer/miniconda3/envs/otagent/bin/python
    $PY scripts/iris/iris_ops.py /benjaminfeuer/<job> --once --json   # per active job (auth state now)
    /Users/benjaminfeuer/miniconda3/envs/otagent/bin/iris --cluster=cw-us-east-02a job summary --json   # authoritative
  Treat "running-but-0-pods / record disappeared" as TERMINAL (silent-wedge signature). `iris … query` over the jobs table lists live jobs (state 1/2/3). Full log (init→crash) via `iris … job logs --since-ms <submitted_at_ms> --no-tail` (finelog keeps the WHOLE log; only `--tail` caps lines).
- TACC(Vista) — `squeue -u penfever` + `sacct -u penfever -S now-3hours -X` via `ssh TACCVista`.

IN-FLIGHT / ACTIVE jobs → report in a UNIFIED TABLE per job type, spanning all clusters (RL table = CoreWeave agentic/MoE rows; SFT/build = EmpireAI mega-container rows; Eval = TACC agentic rows). Structure = `monitor-job-tables` / notes/ot-agent/job_monitor_table.md (box-drawing, not markdown). RL rows MUST include entropy + collapse signals (grad_norm / log_ratio), not just step+reward.

CHAIN-RESTART TIMEOUTs are NORMAL (note the afterany successor), not failures. On CoreWeave, `--max-retries` re-brings-up the gang on a transient HF-weight-resolution flake — a single retry is a normal time-cost, not a fault.

EMPIREAI (SFT workstream — monitor to completion):
- READ the active EmpireAI experiment tracker under `experiments/active/` each sweep and drive off IT — never hardcode a run/campaign here (they go stale). Table each live Axolotl SFT run in the SFT bucket (step/loss/grad_norm from the latest `checkpoint-<N>/trainer_state.json`; `global_step`/`max_steps`). Fetch the small result JSONs to the experiment dir per the ops-doc recipe — never the checkpoints.
- On an SFT run COMPLETED → `sft-job-cleanup` (consolidate → HF upload the ZeRO-3-shard path → reclaim disk) → then the downstream eval per the tracker. Sequential-run campaigns fire the next run per the tracker.
- All SFT is SBATCH-DETACHED; the Beta socket is flaky (skip+note if `ssh -o BatchMode=yes` fails — needs an operator reconnect, can't 2FA headless).

COREWEAVE RL (agentic SkyRL/MoE via `rl-agentic-launch-iris`):
- Report BRING-UP for fresh launches: gang/leafgroup admission (Kueue, pods SchedulingGated until atomically admitted is normal), `apply_ep` / mesh-load, weights resolving. `shm_broadcast: …60s` + a transient ghcr EOF → ImagePullBackOff self-heal are BENIGN bring-up noise.
- EP=8 science greps (the 131k arm) — `sel_rows` / `EPDIAG` via `scripts/iris/analyze_iris_harbor_job.py` (log-content greps are SCIENCE/throughput ONLY, never liveness — liveness = the state-poll above).
- On COMPLETED → route by flavor WITHOUT asking: AGENTIC (Harbor/Daytona/terminal_bench) → `rl-agentic-job-cleanup` (FULL checklist incl. trace upload + metrics); STANDARD/non-agentic GRPO → `rl-standard-job-cleanup`.
- Per-run Monitors (bring-up/wedge watch) are a complementary finer-grained layer; this 3h cron is the baseline — don't let one substitute for the other.

TACC EVAL HARVEST (when present — newly-integrated, validated by a canary):
- TACC agentic eval runs through the front door `python -m hpc.launch --job_type eval_listener --cluster-config tacc` (bare name resolves from `HPC.eval_cluster_view`; `sbatch_script` = `eval/tacc/eval_harbor.sbatch`, `eval_jobs_dir` = `/scratch/10635/penfever/eval_jobs`; whole-node alloc, no `--gres`/`--mem`; compute nodes have egress → NO proxy/cert). Once a leg is RUNNING, harvest finished TACC evals the same way as Leonardo (`eval-agentic-cleanup` if auto-register failed). Sanity-check the canary's traces uploaded + registered before relying on it.

ON SUCCESSFUL COMPLETION (SFT / RL / datagen / eval) on ANY cluster → note it + summary stats, then route WITHOUT asking:
- RL → route by flavor: AGENTIC (Harbor/Daytona/terminal_bench) → `rl-agentic-job-cleanup`; STANDARD / non-agentic GRPO (Delphi/rlvr/dapo math cells) → `rl-standard-job-cleanup` (model + metric CSVs only; size suffix from the exported weights; DB-register only if the series is DB-registerable). SFT → `sft-job-cleanup`. (Leonardo HF upload = the sbatch-tunnel path, NOT the login node — it SIGKILLs long processes at ~100s; needs the fresh step-ca cert.)
- Datagen → verify traces uploaded to HF (penfever org); if NOT, dispatch a subagent (`datagen-job-cleanup`).
- Eval where DB registration FAILED for a technical reason → dispatch a subagent through ALL steps of `eval-agentic-cleanup`; confirm each completed, dispatching another if any were missed.
- INODES (Leonardo/GPFS): every cleanup MUST `rm` the on-disk artifact tree (`trace_jobs/`/`tasks/`) after HF upload confirmed + verify reclaim — the #1 inode leak. (CoreWeave artifacts go to HF / R2, not POSIX scratch; no on-disk tree to reap there.)

ON ANY JOB THAT FAILED since the last check → dispatch a subagent to determine cause + propose fixes. ANNOUNCE the choices, SELECT one, and apply changes + relaunch via another subagent. Keep a running DATED log of failures (job ID + remediation) in /Users/benjaminfeuer/Documents/agent_logs/.
- If an RL job EXHAUSTED all restarts WITHOUT reaching max steps AND the failure looks recoverable (transient) → queue 5 more restarts (Leonardo) / re-launch with `--max-retries ≥1` (CoreWeave). Spike-mitigation ablations are exempt from auto-cancel — observing the recovery IS the experiment (`monitor-cron-sweep`).

CODE / CONFIG EDITS → edit LOCALLY on the active branches:
/Users/benjaminfeuer/Documents/{OpenThoughts-Agent,vllm,harbor,MarinSkyRL}.
Local clones are GROUND TRUTH — clusters never diverge (no untracked/divergent changes, no hand-editing, no patch-by-rsync). Sync the Python repos by commit+push then `git pull` on the SLURM clusters (editable installs, live after pull); CoreWeave has NO clone to pull — the iris launcher uploads the local workspace to `/app` so a local commit takes effect on the next launch. EVERY SWEEP, run `git status --short` on each SLURM cluster repo (leonardo, tacc) and triage drift back to local: TRACK reusable files (commit local → push), GITIGNORE recurring transient junk (`*.bak`, `*_manifest.txt`, `&1`, ephemeral `reeval_priority_*`); reconcile with `git pull`, NEVER `git reset --hard` while live jobs depend on uncommitted state (`monitor-cron-sweep` §4). vLLM (compiled fork) → commit+push the fork, then BUILD FROM SOURCE on each cluster from that commit (never rsync / hand-patch); CoreWeave rebuilds the gpu-rl image (bump the digest) only when the compiled vLLM fork changes — first-party + MarinSkyRL fixes go live without a rebuild.

LOCAL WORKTREE + MAIN HYGIENE (every sweep — operator 2026-07-17): subagents spawn git WORKTREES (marin-fork PR flow) that pile up. (1) PRUNE stale worktrees — `git worktree list` per repo (OpenThoughts-Agent, vllm, harbor, MarinSkyRL, marin, evalchemy); `git worktree remove` (NO `--force` — git refuses a dirty one so no branch/commit is lost; the branch always survives on origin) any whose branch is MERGED/abandoned or whose work is done; HOLD only worktrees a LIVE job or an ACTIVE subagent is using. (2) KEEP PRIMARY CLONES ON CANONICAL BRANCH — marin forks (MarinSkyRL/marin/evalchemy) on `main`, OT-Agent/vllm on `penfever/working`; a clone parked on a feature branch is a live footgun (a launch from that dir uploads that branch) → reset it (`git checkout main && git pull --ff-only`) once its branch is pushed/clean. (3) KEEP `main` CLEAN — no uncommitted tracked drift on a primary clone.

ACTIVELY-DEBUGGING jobs → monitor more closely than stable ones. For any FRESH launch, set one-time checks at 15 min and 30 min after launch to catch new failures early.

LAUNCHING FRESH JOBS → follow the per-job-type launcher instructions in CLAUDE.md (+ the `*-launch-*` skills and `.agents/projects/ot-agent/ot-agent.md`). If unclear, ASK.

EXPERIMENT LOG → each launch / state change logged as a standalone dated file under /Users/benjaminfeuer/Documents/agent_logs/ (YYYY-MM-DD_<topic>.md) — no monodoc.

STANDING CONSTRAINTS (do not violate without explicit permission): enable_db_registration stays false in YAMLs (manual DB register only); Daytona RUNNING RL ≤ 6 per cluster; a3 series is CONCLUDED (no launch/refill/auto-advance); Daytona snapshot caps are HARD (clean stale, never raise); cross-user FK safety pre-check before any Supabase delete/mutate; HF uploads default PUBLIC to laion/. NEVER kill/restart a RUNNING job (or `iris cluster restart`) without express permission. Skip an unreachable cluster (note it) rather than blocking. This prompt OVERRIDES any memory/skill on conflict.
```

If you change the cadence or scope, update BOTH the block above AND the live loop/cron (delete + recreate) so this skill stays the canonical copy.
