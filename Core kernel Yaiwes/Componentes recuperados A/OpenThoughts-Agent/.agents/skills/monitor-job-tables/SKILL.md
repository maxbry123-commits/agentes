---
name: monitor-job-tables
description: >-
  Format HPC job-status reports as box-drawing tables, bucketed by job type (RL · SFT · Datagen · Eval ·
  Catch-all), with the right metric columns, signal thresholds, and red-flags per bucket. Use whenever
  reporting active/recently-terminated job status — during a cron sweep, an ad-hoc "how are my jobs
  doing", or a single-job progress update. Covers which metrics are mandatory (entropy + collapse
  signals for RL, not just step/reward/grad), where to pull live status (SFT .out vs trainer_log.jsonl),
  the RL collapse-warning rule, and which log lines are benign noise vs real faults. Cluster-agnostic —
  resolve paths, active clusters, and credentials from .agents/ops at execution time.
---

# monitor-job-tables

> **Read `.agents/ops/<cluster>/ops.md` first, every sweep.** It is the source of truth for which
> clusters are active, how to locate logs safely, login-node caveats, and current known log noise. This
> skill deliberately names no cluster as active or down — that changes, and a stale list here produces
> confidently wrong reports.
>
> **Locate logs by cluster type, never by guessing a path:**
> - **SLURM clusters** — resolve the log path from the scheduler (`scontrol show job <id> -o`, fields
>   `StdOut=` / `%Z` workdir). **Never `find`/`du` on a parallel filesystem.**
> - **Kubernetes/iris clusters** — there is no scheduler `.out` and no path to `stat`. **Liveness is a
>   state poll of the job lifecycle, never a log-string grep.** Use the iris job-summary/state helpers
>   documented in the ops file; pull metrics from the job logs. **"running-but-0-pods" or a record that
>   has disappeared is TERMINAL** — that is the silent-wedge signature. Keep iris/kubectl calls
>   synchronous.
>
> **Verify a log path EXISTS before concluding "dead."** A scheduler's `StdOut=` may name a file that
> was never created while the real live log sits in the same workdir under a different name. If the
> scheduler path is absent, `ls` the workdir for any `*_<jobid>.out` and read that. Absence at the
> scheduler path is a path mismatch, not a death.
>
> **A failed log fetch is indistinguishable from an idle job.** An API or kubelet error can land in the
> same stream as the logs and parse as "no metrics". Check the line count before concluding anything
> about a job's state, and retry once against a floor.

Report **every** active and recently-terminated job, **bucketed by type**, in the formats below.
**Unify cross-cluster runs of the same type into ONE table.** Give a separate table for jobs still
filling their generation buffer (no metrics yet). Five buckets: **RL · SFT · Datagen · Eval ·
Catch-all**.

Cross-cutting (every bucket):
- **Chain-restart TIMEOUTs are normal, NOT failures** — when a walltime-limited job TIMEOUTs and its
  `afterany` successor is RUNNING/PENDING, report it as a normal restart and name the successor.
- **Completion → matching cleanup skill**: RL by flavor — agentic → `rl-agentic-job-cleanup`, standard
  non-agentic → `rl-standard-job-cleanup`; SFT → `sft-job-cleanup`; datagen → `datagen-job-cleanup`;
  eval → `eval-agentic-cleanup`. Object-store-backed RL routes the same way but leaves no on-disk trial
  tree to reap. On shared-filesystem clusters, cleanup is not done until the artifact's on-disk trial
  tree is removed and inode reclaim is verified — leaving it is the top inode-leak source.
- **Genuine FAILED (exit≠0, not a wall TIMEOUT) → diagnose + dated `agent_logs/` entry.** Recurring
  identical failures are not transient.

---

## RL

```
┌─────────────────────────┬───────┬────────┬─────────────┬───────────┬─────────────────────────────────────────┐
│           Job           │ Step  │ Reward │ Policy Loss │ Grad Norm │                  Trend                  │
├─────────────────────────┼───────┼────────┼─────────────┼───────────┼─────────────────────────────────────────┤
│ <run> (shaped)          │ 15/80 │ 0.619  │ -0.0040     │ 0.006     │ Checkpoint saved. Slight dip from 0.652 │
│ <run> (base)            │ 26/80 │ 0.451  │ -0.0930     │ 0.021     │ Stable, gradients strong                │
└─────────────────────────┴───────┴────────┴─────────────┴───────────┴─────────────────────────────────────────┘
```
Box-drawing tables (┌─┬─┐), **not** markdown — hard user preference for RL. Columns: Job, Step
(`cur/max`), Reward, Policy Loss, Grad Norm, Trend. **Entropy + collapse signals are mandatory**:
include `policy_entropy`, TIS `log_ratio`, and `grad_norm` (in Trend or as extra columns) — without
entropy you cannot apply the collapse rule. A metric not emitted yet → mark `—`. A fresh launch still
in bring-up (gang/queue admission, mesh load, shared-memory broadcast waits, transient image-pull
self-heal — all BENIGN) goes in the buffer-filling table with `—` until its first step lands.

**Rewards from different shaping regimes are not comparable.** Confirm the shaper state from
integrality of `reward × rollouts_per_step` (fractional ⇒ shaping active) before putting two arms in
the same column and drawing a conclusion.

**New/untested RL run? → deep-probe it, don't trust the row.** A row can read "healthy" on a silently
dead run (weight-sync garbage, engine starvation, zero trials completing). For any RL job in a new
setting — new config/geometry/model/image, a smoke test, or the first launch after a code or config
change — dispatch a subagent with **`rl-job-health-deep-dive`**; it reads the literal rollouts and
returns a KILL/NO-KILL recommendation.

**Standard (non-agentic) RL has no Harbor trial artifacts.** Its gates cannot be scored from trial
evidence and must not be marked ERROR for lacking it. Substitute `reward/avg_raw_reward`, banked-step
cadence plus durable checkpoints, `timing/*`, and `generate/avg_num_tokens`.

**Banked steps come from durable evidence, not a progress line.** Take the max `global_step_N` under
the run's checkpoint prefix, and **search every location the launcher may have written to** — a run
that resumed and a run that started fresh can bank to different paths. Corroborate with a
purity-checked log parse. An `exports/global_step_N` signals completion only on a finished run; a
running job also writes periodic saves there.

### Metrics to track per RL run (priority order)
**Core 5 (always):** `reward/avg_raw_reward` (primary), `reward/avg_pass_at_N` (less noisy),
`policy/policy_loss`, `policy/policy_entropy` (direction and magnitude both matter — pre-collapse),
`policy/raw_grad_norm` (most predictive; healthy < 1.0; > 1.0 for ≥2 steps has predicted collapse 2–5
steps early). Under **seqnorm global-denom**, grad/policy_loss/log_ratio are genuinely ~1e-5 or
smaller — that is the regime, NOT vanishing gradient.
**Clip ratio (if tracked):** `policy/ppo_clip_ratio` ≈0 normally; >1 % indicates an LR↔eps_clip
mismatch. Also `policy/z_clip/triggered` for clip-variant ablations.
**TIS:** `tis/imp_ratio_mean` (~0.84–1.56 healthy), `tis/imp_ratio_capped_fraction` (~0 healthy).
**Per-token log-ratio diagnostics, where the trainer emits them:** `log_ratio_abs_{mean,p99,max}`,
`n_tokens_dp_gt_{1,10,50}pct`, positional buckets. Healthy: `mean` ~0.005–0.02, `max` < 0.5,
`gt_50pct` ≈ 0, position buckets even.

### NOT a collapse signal — `rollout_train_prob_diff_mean`
`policy/rollout_train_prob_diff_mean` = `exp(rollout_lp − train_recompute_lp).abs().mean()` — the mean
per-token importance ratio, **dominated by outlier tokens** (a single ~20-nat disagreement gives
`exp(20)≈5e8`). **Millions or billions are NORMAL** on healthy dense arms. Reward is verifier-computed
and independent of logprobs, so this can never "hit the reward". For a per-token divergence read use
the **capped** `tis/imp_ratio_mean` / `imp_ratio_capped_fraction`, the median, or `log_ratio_abs_*` —
not this mean.

### NOT a failure/hang cause — context-overflow + passthrough-exception lines
Engine `... N input tokens > M max`, `ContextLengthExceededError`, and `AgentTimeoutError` are **benign
and expected** in agentic rollouts — they are harbor `passthrough_exceptions`, the verifier still
scores, the rollout completes, and they appear in successful runs. **Never the reason a job hangs or
fails.** Find the real terminal signal: a `Traceback`, OOM / raylet death / SIGKILL, an RPC or sampling
timeout, a `RuntimeError`, or a hung actor/trial that never returns.

### Collapse rule (≥2 fire same step → cancel + salvage)
`raw_grad_norm` > 1.0 (or > 2× its window); `policy_entropy` off its 10-step trend by > 30 %;
`log_ratio_abs_mean` > 2× its window while `max` stays bounded; trial pass-rate < 10 % over the last
100. **Exception:** spike-mitigation ablations are NEVER auto-cancelled on this rule — observing the
recovery IS the experiment.

**Where a no-kill instruction is in force, this rule gates a RECOMMENDATION, not an action.** Capture
the evidence that disappears at termination, record it, report it, and leave the job running.

---

## SFT

```
┌──────────────────────────────┬─────────┬────────┬───────────┬───────────────────────────────────┐
│             Job              │  Step   │  Loss  │ Grad Norm │               Trend               │
├──────────────────────────────┼─────────┼────────┼───────────┼───────────────────────────────────┤
│ <run> cold-start 2ep         │ 320/916 │ 1.21   │ 0.84      │ Loss descending; healthy          │
└──────────────────────────────┴─────────┴────────┴───────────┴───────────────────────────────────┘
```
Columns: Job, Step (`cur/total`), Loss, Grad Norm, Trend. **No reward.**

**For multi-cell SFT grids, also give a grid-completion rollup each sweep:**
- Per RUNNING cell: progress % (step/total) and a rough ETA, plus a one-line running / pending-unique /
  done tally.
- **Dedupe the PENDING count — restart-chain resume copies inflate it several-fold.** Count *distinct*
  cells: list pending job names, strip to the cell name, `sort -u`, then subtract running cells' own
  resume backups.
- **Name the long pole.** In a mixed-scale grid the largest cells gate completion; small cells clear
  fast and their progress is not the campaign's progress.
- **Grep the TRAINING progress bar, not the packing bar.** Verify the denominator matches the cell's
  total optimization steps, not an example count.
- **A single tailed `s/it` is NOT the rate.** Checkpoint-save spikes inflate one line at the save
  cadence. Use a trailing-window rate (average several step lines, or Δwall/Δstep).

**Pull live status from the training `.out`, not `trainer_log.jsonl`.** The `.out` carries the
per-step dicts and is richer (live grad_norm, per-rank loss spread, token coverage, epoch). The JSONL
is unreliable mid-run — sparse, empty, or frozen — and produces false "stale/dead" readings. Use it
only for the completion check before consolidate/upload. Total steps come from the rendered config or
the trainer banner.

**Red flags:** `ChildFailedError` / non-zero exit (read the FIRST real traceback above the elastic
summary — it is usually masked), CUDA OOM at the first forward/backward, `SIGTERM` (node fault or a
masked rank crash — a recurring death at a fixed interval is NOT transient), loss → NaN, grad
explosion.

---

## Datagen

```
┌─────────────────────────────┬──────────────┬─────────┬───────────┬──────┬──────┬──────────────────────────┐
│         Datagen run         │    Chunks    │ Trials  │ avg_turns │ Mean │ exc% │           Trend          │
├─────────────────────────────┼──────────────┼─────────┼───────────┼──────┼──────┼──────────────────────────┤
│ <run> (tracker row #N)      │ 18/20 done   │ ~8.6k   │ 5.1       │ 0.53 │ 19%  │ 2 chunks running         │
└─────────────────────────────┴──────────────┴─────────┴───────────┴──────┴──────┴──────────────────────────┘
```
Columns: run (+ tracker row), Chunks (`done/total`), Trials (`result.json` count), avg_turns, **Mean**
(mean reward, from harbor's `<done>/<total> Mean: <X>` line; mark `—` if there is no verifier), exc%,
Trend. **avg_turns is the realness gate** — `>1` is real multi-step; **`≈1.0` is a dead-engine run, do
NOT consolidate.** An exc% of ~20–25 % AgentTimeout is normal for hard sets.
**Red flags:** a `TIMEOUT` **strands the traces** (the terminal upload is killed — traces are on disk
but not uploaded, so consolidate manually); a hung chunk (log silent for hours with a stalled trial
count while still RUNNING); avg_turns ≈ 1.0.

---

## Eval

```
┌──────────────────────────────┬───────────┬───────────┬───────────┬────────────────────────────────┐
│   Eval (model × benchmark)   │  Trials   │ pass-rate │  top exc  │         Infra / Trend          │
├──────────────────────────────┼───────────┼───────────┼───────────┼────────────────────────────────┤
│ <model> × <benchmark>        │ 142/300   │ 0.21      │ AgentTO   │ tunnel✓ engine✓ ; healthy      │
└──────────────────────────────┴───────────┴───────────┴───────────┴────────────────────────────────┘
```
Columns: model×benchmark, Trials (`result.json`/total), pass-rate (fraction with reward > 0), top
exception type, Infra/Trend. The Infra column is the launch-check set from `eval-agentic-launch`:
tunnel auth and traffic, sandbox `api_base` pointing at the public URL rather than an internal IP,
engine POSTs growing and returning 200, trial progression.
**Red flags:** no `result.json` for 60+ min while RUNNING → stall; engine showing zero running requests
for 10+ min → agents not generating; **all trials done but job RUNNING → zombie, cancel**; instant-fail
(null output tokens, `finished_at` ≈ `started_at`) → tunnel not carrying traffic; repeated auth
failures → sandbox-provider degradation.
**Before calling an eval dead, confirm the RIGHT log and a CURRENT window.** Count `result.json` over
the whole run, not just the tail. A burst of timeouts in the last window is usually the hard-trial tail
of a nearly-done run. Verify the engine is actually down (no recent 200s) before blaming it.

### NOT a reliability problem — a high `AgentTimeoutError` fraction
A large timeout share — **even a majority of trials** — is EXPECTED on hard, long-horizon benchmarks
and does NOT make the eval unreliable. The timeout is a passthrough exception: the trial is still
scored, an unfinished task scores as not-solved, and that reflects genuine capability. If the baseline
ran the same harness, the score and delta stand. The only timeout red flag is the infra case:
essentially every trial failing with zero completions and no `result.json` is a stall, not a score.

---

## Catch-all / other (ad-hoc)

Anything that is not one of the four majors — consolidate, pretokenize, uploads, image builds, feature
smoke tests, GPU-CI runs, measurement and grid probes. **Don't force a metric table** — one line each:

| Job | Type | State | Elapsed | Note |
|---|---|---|---|---|
| `<id>` | datagen-consolidate | running | 12m | pushing N rows → `<dataset>` |
| `<id>` | gpu-ci | COMPLETED | 6m | 2 passed |
| `<id>` | RL upload | running | 3m | `<model>` |

State, elapsed, and a human note: what it is, the one signal that matters, and any follow-up. Flag
terminal COMPLETED/FAILED and whether it needs action.

---

## Benign log-noise (do NOT chase as faults)

- **Shared-memory broadcast "no available block found in N seconds"** is an informational heartbeat,
  not a kill signal. It re-fires on a fixed cadence while the engine waits with nothing scheduled. It
  is fault-indicative **only when co-firing with** a real NCCL hang (a `WorkNCCL(...)` timeout line, a
  "preparing to dump debug info", or a SIGABRT). Alone, look upstream for the engine-idle cause; do not
  relaunch or patch the ring buffer.
- **`rollout_train_prob_diff_mean` in the millions or billions** — outlier-dominated, normal. See RL §.
- **Debug-token and `opCount` chatter** — check the cluster's ops file for the current benign set rather
  than assuming any given line is a fault.
