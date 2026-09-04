# Daytona — dependency-specific operating notes

Daytona is the cloud sandbox backend Harbor uses for agentic RL rollouts and datagen trials. These are
the service-side constraints that shape how we launch and monitor jobs.

**⚠ Two DISTINCT resources — never conflate them (separate count, cap, and cleanup tool each):**
- **Snapshots** = the unique Docker *builds* (one per sandbox-environment hash, keyed by the task set), **reused across many sandboxes**. The **HARD org cap (40 RL / 60 default)** is on these — it's what BLOCKS a launch that needs a new env. Clean stale ones with **`scripts/daytona/daytona_snapshot_manager.py`** (audit → `--delete-stale`).
- **Sandboxes** = the actual *compute instances* that host the running trials. They accumulate as trials run and are left behind after jobs finish. Clean stale ones (idle >60 min, across all 3 orgs) with **`scripts/daytona/cleanup_stale_sandboxes.py`**.
- Cleaning **sandboxes does NOT free snapshot-cap headroom**, and reclaiming snapshots does NOT reduce running sandboxes — use the right tool for the resource you're actually freeing.

---

## Concurrency caps

### RL — ≤ 6 RUNNING RL jobs **per cluster**

Cap **concurrently RUNNING** RL jobs at **6 per cluster** (Jupiter, Leonardo, NYU Torch, … each have their own headroom — **NOT** a cross-cluster aggregate). Each RL job spawns ~hundreds of concurrent Daytona sandboxes per training step; the rate-limit horizon is about **per-source-cluster connection count**, not total org load.

- **PENDING restart-chain jobs (`afterany` deps) don't count** — they're SLURM-queued, not creating sandboxes. Only RUNNING counts.
- Before launching an RL batch on a cluster, count `squeue --me -t RUNNING` RL jobs **on that cluster only**. If adding more would exceed 6, either chain behind existing runs (`--dependency afterany:<last>`) or defer.
- Eval jobs count as a *fraction* of an RL job — a few evals alongside 6 RL is OK.
- This is a Daytona service-side concern scoped per-cluster, **NOT** a SLURM cap and **NOT** a cross-cluster aggregate.

### Datagen — per-job ceiling ~100–128 (NOT aggregate)

A datagen job's effective trial concurrency (vLLM `Running:` reqs) tops out at **~100–128 PER JOB**, regardless of requested `--trace-n-concurrent` / `max_num_seqs`. This is a **per-job ceiling, NOT multi-job contention** — running several datagen jobs in parallel is fine.

- **Don't set `max_num_seqs`/`--trace-n-concurrent` much above ~128 per job** — wasted (the job won't be fed beyond ~100–128 effective Running). Per-job pattern: req 32→Running~25, 64→~56, 128→~100, 256→~100 (256 buys nothing over 128).
- **Run datagen jobs in parallel freely** up to aggregate Daytona supply (≥~400 concurrent sustained on Jupiter); serializing grids is unnecessary.
- Throughput tracks effective Running ~linearly (~7 gen tok/s/req MiniMax-M2.7, ~5 GLM-5.1-AWQ @32k). If Running caps at ~100, the lever is **prefix-caching** (shared prompts) or the real production target (131k, where KV finally binds), NOT more seqs. At 32k the engine is rarely KV-bound at Running ~100 (KV <40%).

---

## Snapshot caps are HARD limits — never bypass the gate

The safety gates in `hpc/rl_launch_utils.py:prebuild_daytona_snapshots` are intentional hard limits:
- `max_new_snapshots: int = 10` — per-launch cap
- `max_org_snapshots: int = 60` — total org cap
- Both `raise ValueError(...)` when exceeded.

**NEVER** raise these defaults, pass a larger `max_new_snapshots`, or convert the `ValueError`s to a warning-and-skip. Mass snapshot creation is expensive and starves other org users.

### Two distinct over-cap cases — handle them differently

1. **Org total cap full** (org at quota, next dataset needs a new env) → **AUTONOMOUS: clean STALE/orphaned snapshots to make room**, then launch (it fits under the unchanged cap). Do NOT block/ask. Reclaim only orphaned `harbor__<hash>` envs from completed/cancelled work — snapshots are keyed by sandbox-ENVIRONMENT hash and **shared across every run using those tasks**, so never delete an env a running/queued job depends on ("do NOT reclaim per-dataset; leave the shared env snapshot").

**⚠ "Sandbox not found. Please build the environment first." has TWO distinct causes — DIAGNOSE, don't assume.** From the job state it is INDISTINGUISHABLE from a never-built env OR a GIL/throughput stall (the vLLM engine can show `Running:N/Waiting:M` reqs while the `RolloutCoordinator` fails EVERY trial). Before acting, check BOTH: the snapshot CREATE→DELETE timeline AND the concurrency-vs-decode-slots ratio.

- **Cause 1 — harbor idle-reap under opencode oversubscription (the EVIDENCED keep1-v8 cause, 2026-07-18).** harbor sets Daytona `auto_stop_interval_mins=5` + delete-on-stop (`environment/daytona/environment.py:946,984`): a sandbox with no **exec** for 5 min is stopped→deleted. **opencode reaches vLLM over HTTP (`HARBOR_MODEL_ENDPOINT`), NOT sandbox exec** — so only its bash-tool calls reset the idle timer, its model turns do NOT (contrast terminus-2, which drives the model via exec → timer stays warm). When `n_concurrent_trials` ≫ the vLLM decode slots (`max_num_seqs × num_inference_engines`), trials queue >5 min waiting for a slot → sandboxes idle-reaped mid-trial → "Sandbox not found" at finalization. keep1-v8: **288 trials vs 48 slots (6:1)** → reaped ~14 min in at queue saturation; fullgate (n=8 ≤ 48) never hit it. `auto_stop_interval_mins` is NOT exposed in the harbor YAML. **Fixes:** match `n_concurrent_trials` to the decode slots (≈ slots + small buffer), OR raise `max_num_seqs` (KV-bound), OR patch harbor to expose/raise the interval or reset the idle timer on model-endpoint activity. ⚠ Note: concurrency ≫ decode slots gives **NO throughput gain** (the engine decode-caps at the slot count) — the surplus trials just queue-and-reap. **⚠ TRADEOFF of `auto_stop_interval_mins=0`:** idle sandboxes no longer self-reap, so a **runaway/looping trial in a LIVE job can't be idle-killed** — it piles up (with the broken opencode kill-path, this is how loopers accumulate: 200 alive at keep1-v11). **BUT killed-job sandboxes DO self-clear (verified keep1-v10 2026-07-18):** when the job dies its vLLM endpoint dies → opencode's LLM calls fail → opencode exits → the sandbox tears down, so orphans do NOT persist indefinitely (v10's ~100 self-cleared to 0). So the standing cost is *within a live job* (loopers not idle-reapable until the real harbor kill-path fix lands), not lingering post-kill orphans. A manual `scripts/daytona/cleanup_stale_sandboxes.py --threshold <min> --delete` is still available if a batch ever lingers, but usually unnecessary.
- **Cause 2 — cross-agent snapshot reap-race (a real but SEPARATE phenomenon; NOT what hit keep1-v8).** A just-launched agentic-RL job needs its env snapshot but hasn't spun up a sandbox yet; in that window a CONCURRENT cleanup agent's `--delete-stale` can reap the not-yet-in-use snapshot. (Our own `daytona_snapshot_manager.py --stale-days 0.0833` spares <2h snapshots → the culprit would be ANOTHER agent's reaper.) Confirm via the snapshot CREATE→DELETE timeline (built-then-deleted around launch = reaped; never-existed = a real build miss; present-through-the-window = NOT this — it's Cause 1). Prevent: rebuild + relaunch promptly; the reaper must exclude fresh/in-use snapshots.

(keep1-v8 root-cause + refutation of the reap hypothesis: `agent_logs/2026-07-18_cron-catch-keep1v8-sandbox-marinbase-vllm.md`.)
2. **Per-launch cap** — a single dataset legitimately needing `> 10` UNIQUE envs (e.g. 5000 unique Dockerfiles) is a mis-designed/oversized dataset. Cleaning stale won't help (it wants 5000 NEW). **STOP + ask** the user: regenerate to share Dockerfiles / prune unique envs / explicitly approve a one-run cap change (named numeric value, documented in the commit message).

Org-cap-full ≠ dataset-needs-too-many-new — only the latter blocks. Either way: make room by deleting stale, never by lifting the gate.

### How to clean stale snapshots (case 1 procedure)

Tool: **`scripts/daytona/daytona_snapshot_manager.py`** (the *safe* reclaim tool — it ONLY audits and deletes snapshots; do NOT confuse it with `cleanup_stale_sandboxes.py`, which targets running sandboxes). Run from the otagent env; `source secrets.env` first (it reads the key from `--api-key-env` — env var only, never inline).

> **⚠️ MUST pass `--api-key-env DAYTONA_API_KEY` for datagen/eval.** The `SnapshotCapExceeded` on org `'cli'`
> fires against the org keyed by **`DAYTONA_API_KEY`** (that's the org the launcher's snapshot pre-build uses:
> `OrgConfig(name="cli", api_key=DAYTONA_API_KEY)`). But the tool **defaults `--api-key-env` to `DAYTONA_DATA_API_KEY`**
> (`daytona_snapshot_manager.py` argparse) — a **DIFFERENT org** (verified 2026-07-16: distinct key values, `cli`=60/60
> while the default org read 105). Omitting the flag audits/reclaims the wrong org, so the `cli` org silently saturates
> and the next launch still `SnapshotCapExceeded`s (root-caused a keep-3 refill block 2026-07-16 — the `cli` org had 19
> unreclaimed stale while the default-org reclaim reported "success"). **Always `--api-key-env DAYTONA_API_KEY` here.**

```bash
# 1. AUDIT first (read-only default — no deletes). Shows used/headroom + which snapshots are STALE.
#    --stale-days takes a FLOAT → 2 HOURS = 0.0833 (2/24).
python scripts/daytona/daytona_snapshot_manager.py --api-key-env DAYTONA_API_KEY --stale-days 0.0833
# 2. RECLAIM (dry-run unless --yes). Deletes only STALE harbor__* envs:
python scripts/daytona/daytona_snapshot_manager.py --api-key-env DAYTONA_API_KEY --delete-stale --yes --stale-days 0.0833
```

- **`--stale-days 0.0833` (= 2 HOURS) is the standard threshold, NOT 2 days.** In a fast-churning campaign (eval legs cycle in hours) a 2-day window reclaims ~nothing (everything is idle <2d). 2 hours is safe: staleness = idle (`last_used_at` older than `--stale-days`) **AND not protected/active** — so this NEVER deletes an env an ACTIVELY-running leg is still using (it has a fresh `last_used_at` <2h). A reclaimed shared `harbor__<hash>` env that a later run needs **rebuilds instantly as a registry hit (0 err)**, so reclaiming an env merely idle 2h+ costs a cheap rebuild, not lost work.
- **Exit codes:** `3` = `--delete-stale` requested but the confirm prompt was declined (use `--yes` to skip the prompt in autonomous runs).
- **Caveats:**
  - The manager's post-delete "N/60" re-read can lag (e.g. still shows `40/60` right after a reclaim) — that's a **Daytona list-API eventual-consistency artifact**, NOT a failed delete. Confirm real headroom by the next launch's prebuild line (`0 built` / registry-HIT = headroom freed).
  - "Failures" on `daytonaio/sandbox:*` base images + `daytona-gpu` are **non-org-snapshot images** (already gone) — harmless, ignore.
  - Some reclaimed `harbor__<hash>` envs are shared/re-buildable; a later run that needs one rebuilds it instantly as a registry hit (0 err) — reclaiming a stale-but-rebuildable env is safe.
- This is autonomous at the cap (case 1): never raise/bypass the cap, never block on the user; just reclaim stale and launch. Re-audit periodically as the sweep builds new-env snapshots. Tool added OT-Agent commit `a34e45db`.

### Org quotas

- **Daytona RL org snapshot quota = 40** (HARD, server-side). Snapshot-optimized dataset variants (converted to need FEW snapshots) launch fine — don't pre-flag them as cap-blocked.
