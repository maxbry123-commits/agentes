---
name: analyze-training-run-iris
description: Detailed health check for a Levanter/executor TRAINING run on the marin Iris cluster (e.g. the delphi midtraining runs) — step progress vs target, loss/throughput, preemption + MAJOR step-gap detection, and checkpoint cadence. Use for an executor coordinator (`<run>-coord`) plus its nested `<run>-coord/checkpoints-<step>-<hash>` training child, which the harbor analyzer (analyze-job-history-iris) does NOT cover (training has no harbor trial sidecars, same as GPU-RL). Reads W&B per-step history + `iris job summary` + GCS checkpoints instead of harbor GCS output.
---

# analyze-training-run-iris

> **📍 Iris orientation — read first.** Before acting on anything in this skill, read the Iris **tools
> catalog** (`.agents/ops/iris/ops.md`) and the Iris **ops directory** (`.agents/ops/iris/` — the
> CoreWeave GPU particulars in `ops.md`, the TPU `marin` particulars in `ops.md`).
> They carry the binding access/preamble/gotchas and the helper-script inventory the steps below rely on.

A Levanter training run launched through the marin **executor** surfaces as **TWO** Iris jobs:

- a tiny CPU **coordinator** — `/<user>/<run>-coord` — the `executor_main` DAG-walker (it submits the
  training job and then blocks); and
- its nested **training child** — `/<user>/<run>-coord/checkpoints-<step>-<hash>` — the multi-task **v5p**
  job where the actual training steps happen (e.g. 8 tasks for a v5p-64).

**Health = the CHILD's step progress + the run's preemption/gap history.** The harbor analyzer
(`analyze-job-history-iris`) does **NOT** apply — a training job has no harbor trial sidecars (just like
GPU-RL). Use the three sources below instead. W&B is primary for step/loss/throughput; `iris job summary`
is primary for preemptions/liveness; GCS is primary for checkpoint cadence.

## Source 1 — `iris job summary`: preemptions, liveness, per-task state (always available)

```bash
IRIS=/Users/benjaminfeuer/Documents/marin/.venv/bin/iris
$IRIS --cluster=marin job summary <child_job_id>
```
Report `preemptions=N failures=N`, tasks `running/completed` (all N tasks should be `running` together —
a v5p job is gang-scheduled), the longest task DURATION, and PEAK MEM. `preemptions>0` is **expected** on a
preemptible v5p — each one means iris restarted the slice and Levanter resumed from the last checkpoint
(every preemption costs a wall-clock gap: re-place + reload weights + XLA recompile). `failures>0`, a
shrinking task count, or a crash-restart loop is a **red flag** → read the child logs for the error.

## Source 2 — W&B per-step history: step / loss / throughput + MAJOR GAP detection (primary)

The run logs to W&B project **`delphi-midtraining`** (entity **`nyu-dice-lab`**); the **run name is the
GCS output-path hash** — the last path segment of `gs://marin-us-east5/checkpoints/<run>-<hash>` (e.g.
`delphi-1e23-p33m67-k0p20-lr0.67-b6607e` → run `delphi-1e23-p33m67-k0p20-lr0.67-b6607e`). Per-step history
is **NOT** mirrored by mum — query the W&B API directly (needs `WANDB_API_KEY` from `$DC_AGENT_SECRET_ENV`; use the
otagent python which has `wandb`):

```bash
source "${DC_AGENT_SECRET_ENV:?set DC_AGENT_SECRET_ENV to the secrets file first}"
/Users/benjaminfeuer/miniconda3/envs/otagent/bin/python - <<'PY'
import wandb
ENTITY, PROJECT, RUN = "nyu-dice-lab", "delphi-midtraining", "<run-hash>"   # <-- the ...-b6607e hash
api = wandb.Api()
r = api.run(f"{ENTITY}/{PROJECT}/{RUN}")
total = r.config.get("trainer", {}).get("num_train_steps") or r.config.get("num_train_steps")
h = r.history(keys=["_step", "_timestamp", "_runtime", "train/loss"], pandas=True)
if h is None or len(h) == 0:
    print("state:", r.state, "-> pre-first-step (still setup/HF-download/XLA-compile); no training step yet")
else:
    h = h.dropna(subset=["_step"]).sort_values("_step")
    cur = int(h["_step"].iloc[-1])
    ts = h["_timestamp"].to_numpy()
    deltas = [b - a for a, b in zip(ts[:-1], ts[1:])]
    med = sorted(deltas)[len(deltas)//2] if deltas else 0.0
    thr = max(300.0, 20.0 * med)                       # same MAJOR-GAP rule as compute_time.md
    gaps = [d for d in deltas if d > thr]
    toks = 0
    bs = (r.config.get("trainer", {}) or {}).get("train_batch_size")
    sl = r.config.get("train_seq_len") or (r.config.get("model", {}) or {}).get("max_seq_len")
    if bs and sl and med: toks = bs * sl / med
    loss = h["train/loss"].dropna()
    loss = float(loss.iloc[-1]) if len(loss) else None
    eta_h = ((total - cur) * med / 3600.0) if (total and med) else None
    print(f"state            : {r.state}")
    print(f"step             : {cur}/{total}  ({round(100*cur/total,1) if total else '?'}%)")
    print(f"train/loss       : {loss}")
    print(f"median step dt   : {round(med,2)} s   -> ~{round(toks):,} tok/s" if med else "median step dt: n/a")
    print(f"MAJOR gaps       : count={len(gaps)}  total={round(sum(gaps)/3600,2)} h  (threshold {round(thr)} s)")
    print(f"ETA to {total}   : ~{round(eta_h,1)} h of compute (excludes future preemption gaps)" if eta_h else "ETA: n/a")
PY
```
- **step cur/total** = progress against the K-budget target (e.g. 29,945 for K=0.20). This is the headline
  "progress in steps" number.
- **MAJOR gaps** = consecutive `_timestamp` deltas exceeding `max(300 s, 20 × median step interval)` —
  preemption / idle gaps (the metric the user wants: "note major gaps"). Cross-check `count` against
  `iris job summary preemptions` — they should be the same order (a gap with NO matching preemption is a
  silent stall worth flagging). Report gap **count + total hours**.
- **tok/s** = `batch × seq / median_dt`. Compare across ticks; a sudden drop = contention or a bad slice.
- **Empty history** = the run is still in setup / HF-weight download / first XLA compile — that is **NOT** a
  gap; report it as **pre-first-step** and move on.

## Source 3 — GCS checkpoint cadence: resume safety (always available)

```bash
gsutil ls gs://marin-us-east5/checkpoints/<run>-<hash>/ | grep -E 'step-[0-9]+' | tail -5
gsutil ls -l gs://marin-us-east5/checkpoints/<run>-<hash>/step-<latest>/ 2>/dev/null | tail -2   # timestamp
```
Report the **latest persisted step** + its timestamp (the checkpointer saves on an interval — e.g.
`save_interval 10m`, `keep every 1500`). The latest checkpoint lagging a bit behind the W&B step is fine
(async save). But **no `step-*` checkpoint long after training started** is a red flag — under preemption
the run would lose all un-checkpointed progress. Only `.executor_info` / `.executor_status*` present (no
`step-*`) = still pre-first-checkpoint (early bring-up).

## Don't mistake setup steps for training steps

`iris job logs <child>` early on shows `[iris setup] step N/M` lines — those are **uv-sync SETUP** steps,
NOT training steps. Do **NOT** grep `step N` from the logs for progress. Use the **W&B `_step`** (Source 2)
as the authoritative training-step counter; only fall back to Levanter's own in-log training-step line if
W&B is unreachable.

## The compact cron line (one per training run)

`<run> state=running step=<cur>/<total> (X%) loss=<L> ~<T>tok/s preempts=<P> gaps=<G>/<H>h ckpt=step-<C>`
plus a one-line health read: past setup/compile? step rate sane vs the prior tick? loss finite and trending
down (not NaN/spiking)? preemptions resuming cleanly (checkpoint advancing)? ETA to the K-budget target.

## Running it / offloading to a subagent

The W&B pull is fast (seconds), unlike the harbor analyzer — you usually do NOT need a subagent. If a run
is huge or you are sweeping several, the `analyze-job-history-iris` foreground-and-wait discipline still
applies to any slow `gsutil`/log reads, but the W&B query itself is quick.

## Related skills

- **monitor-cron-sweep-iris** — the every-3-hours sweep; its **class E** (executor/Levanter training)
  invokes this skill, just as class A/B invoke `analyze-job-history-iris`.
- **analyze-job-history-iris** — the harbor (datagen/eval) analyzer; does NOT apply to training runs.
- **rl-job-health-deep-dive** — the GPU-RL equivalent (also no harbor sidecars; uses the finelog).
