---
name: rl-agentic-launch-jupiter
description: >-
  Launch / relaunch agentic RL (SkyRL terminal_bench + Harbor + Daytona) on JSC Jupiter (GH200).
  Covers the dense 8B/32B FSDP2 arms (seqnorm, TIS, shaped, symclip, lrboost, loopshape) and the
  MoE/80B Megatron arms (Qwen3-Coder-30B-A3B, Qwen3-Next-80B-A3B) — the exact `python -m hpc.launch
  --job_type rl` flag set, which flags vary per arm (config / model_path / train_data / num_nodes),
  runtime+SIF selection, the Daytona RL-org + chain-restart conventions, and the standing constraints
  (≤6 RL/cluster, a3 CONCLUDED, TIMEOUT restarts are normal). Use when asked to launch / relaunch /
  refill an agentic SkyRL RL run on Jupiter. Reference: notes/ot-agent/rl_experiments.md,
  .agents/ops/jupiter/{ops.md,ENVIRONMENT_MAP.md}.
---

> ⚠ **Do not add comments to YAMLs. Report your recommendations directly to the supervisor.**

# rl-agentic-launch-jupiter

> **⚠ Local clone = ground truth (CLAUDE.md §Always).** ALL code/config/sbatch edits
> (OpenThoughts-Agent + MarinSkyRL) go in the local Mac checkouts → commit → push →
> `git pull` on the cluster. **NEVER** hand-edit, `git commit`, or leave divergent/
> untracked changes on a cluster; no patch-by-rsync (vLLM is the only exception —
> built from source per-cluster). Bake this into every subagent you dispatch.

Agentic SkyRL/GRPO RL runs through **`python -m hpc.launch --job_type rl`** with FSDP2 or Megatron. Each
rollout is a Harbor agent episode in a Daytona `terminal_bench` sandbox with a colocated vLLM engine.
Jupiter nodes have four 96GB GH200 GPUs. Read `.agents/ops/jupiter/ops.md` first; runtime/SIF details are in
`.agents/ops/jupiter/ENVIRONMENT_MAP.md`.

## 1. The canonical launch

> **🚧 SUBMIT FROM THE REPO DIR WITH `DCFT` SET.** Before launching/resuming:
> `cd /e/scratch/jureap59/feuer1/OpenThoughts-Agent && export DCFT=$PWD` (the ops.md
> preamble does this). The generated `universal_rl.sbatch` resolves `WORKDIR` from
> `DCFT_PRIVATE → DCFT → $PWD`; submitted from `$HOME`/a scratch subdir with `DCFT`
> unset, the guard detects the wrong dir (missing `hpc/shell_utils/triton_cache.sh`
> marker) and **`exit 1`s** with `FATAL: WORKDIR=... is not the OpenThoughts-Agent
> repo root`. Fix: `cd` to the repo, `export DCFT=$PWD`, resubmit.

```bash
python -m hpc.launch --job_type rl \
  --rl_config ./hpc/skyrl_yaml/jupiter/<cfg>.yaml \
  --model_path <hf-or-local-model> \
  --train_data '["<HF-repo-or-/abs/task/dir>"]' \
  --num_nodes N \
  --time_limit 11:59:00 \
  --max_restarts K \
  --reservation reformo \
  --experiments_dir /e/data1/datasets/playground/ot-baf \
  --job_name <name>
```
**Varies per arm:** `--rl_config`, `--model_path`, `--train_data`, and `--num_nodes` (§2). **Fixed on Jupiter:**
- `--time_limit 11:59:00` — booster QOS caps walltime at 12h; chain with `--max_restarts` (§5).
- `--reservation reformo` — `jureap59` booster QOS is suspended (`InvalidQOS`);
  `reformo` is the runnable account/reservation.
- `--experiments_dir /e/data1/datasets/playground/ot-baf` — the `ot-baf` personal
  data root (`/ot` is read-only-for-you).
- `--train_data` is a **JSON-list string** `'["..."]'` — an HF repo (`DCAgent/…`,
  `laion/…`, `SankalpKJ/…`) **or** a pre-extracted local task dir
  (`/e/scratch/jureap59/feuer1/tasks/<name>`).
- `--job_name <name>` — set explicitly for predictable chain-restart and cleanup paths.
- `--skyrl_override '++a.b.c=val'` — appends a Hydra override (last-wins over the
  base yaml). For per-arm tweaks without forking a config: sampling
  (`generator.sampling_params.temperature=1.0`, `…top_p`, `…top_k`, `…min_p`),
  Harbor sandbox sizing
  (`++terminal_bench_config.harbor.override_{cpus,memory_mb,storage_mb}`), context
  bumps (`++generator.engine_init_kwargs.max_model_len=…`). Pass **`++`-prefixed,
  struct-safe** keys — a bare top-level key risks a Hydra `ConfigKeyError`.
- **Launch from the `otagent` conda env**
  (`/e/scratch/jureap59/feuer1/miniforge3/envs/otagent/bin/python`), NOT the RL
  venv — task extraction imports `google.cloud.storage`, which the RL venv lacks.
  (The launcher then selects the RL venv/SIF for the *training* — §3.)

## 2. Config map + node count (`num_nodes` MUST match the config)
`num_nodes = GPUs / 4`. Pick the config, then set `--num_nodes` to its budget:

| Config (`hpc/skyrl_yaml/jupiter/…`) | Model | GPUs → `--num_nodes` |
|---|---|---|
| `56GPU_seqnorm_tis.yaml` (+ `extra/56GPU_seqnorm.yaml`, `extra/56GPU_seqnorm_tis_shaped.yaml`) | dense 8B | 56 → **14** |
| `extra/56GPU_seqnorm_tis_untrunc_symclip.yaml` | dense 8B (symclip) | 56 → **14** |
| `extra/56GPU_seqnorm_tis_untrunc_symclip_loopshape.yaml` | dense 8B (symclip+loopshape) | 56 → **14** |
| `extra/56GPU_seqnorm_tis_untrunc_lrboost.yaml` | dense 8B (lr-boost) | 56 → **14** |
| `56GPU_shaped.yaml` (`extra/24GPU_shaped.yaml`) | dense 8B (shaped reward) | 56→14 / 24→**6** |
| `24GPU_base_131k.yaml` / `extra/24GPU_base_old.yaml` | dense 8B | 24 → **6** |
| `64GPU_base_32b.yaml`, `extra/64GPU_base_32b_fp8.yaml`, `extra/48GPU_*_32b.yaml`, `extra/128GPU_base_32b.yaml` | dense 32B | 64→16 / 48→12 / 128→32 |
| **`24GPU_qwen3_coder_30b_a3b.yaml`** | **Qwen3-Coder-30B-A3B (MoE)** | 24 → **6** |
| **`extra/128GPU_qwen3_next_80b_a3b.yaml`** | **Qwen3-Next-80B-A3B (MoE, prod)** | 64 → **16** (name is historical; header = 64 GPU/16 node) |
| `extra/16GPU_mixtral_8x7b.yaml` | Mixtral-8x7B (MoE bring-up) | 16 → **4** |

General rule: 24GPU→6, 48GPU→12, 56GPU→14, 64GPU→16, 96GPU→24, 128GPU→32. The CLI controls
`-N` despite generated `#SBATCH --nodes=1`. For an unexplained <15-minute failure, check node count first.

## 3. Runtime / SIF selection
The launcher selects the training runtime (`hpc/sbatch_rl/universal_rl.sbatch`). Confirm it from the rendered
sbatch, rather than assuming.
- **Dense 8B/32B FSDP2** (seqnorm / TIS / shaped / symclip / lrboost / loopshape) →
  **RL venv** `$WORKDIR/envs/rl` (**torch 2.9**). Default RL runtime.
- **MoE — Qwen3-Coder-30B-A3B** and **prod 80B Qwen3-Next-80B-A3B (R3+TIS)** → **SIF
  `skyrl_megatron_vllm_r3baked.sif`** (**torch 2.9**, overlays baked in).
- **torch≥2.10 / DCP / torch-native CP / Mixtral-multinode** → **SIF
  `skyrl_megatron_vllm0202rc0_r3.sif`** (**torch 2.11**); stack the
  **`skyrl_titan_overlay.img`** when torchtitan-0.2.2 / `_StridedShard` (CP+EP) is
  needed.

> Use `torch`, not `vllm.__version__`, to identify the runtime. See ENVIRONMENT_MAP §4 for probes and SIF gotchas.

## 4. Agentic infra conventions
- **Daytona uses the RL-org key** for RL rollouts (distinct from the eval-org key);
  set by the launch preamble / `hpc/dotenv/jupiter.env`, not the CLI.
- **Pinggy is EVAL-only, not RL** — `--pinggy_persistent_url` / `--pinggy_token` are
  eval-path flags.
- **`enable_db_registration: false`** — the launcher **auto-injects**
  `++trainer.enable_db_registration=false` for RL. Do NOT also pass a bare
  `--skyrl_override enable_db_registration=false` (Hydra struct `ConfigKeyError`
  risk, redundant). DB registration is a **manual cleanup step**, not a launch flag.
- **Daytona snapshots:** a new task set builds snapshots on first launch; caps are **HARD** (10 new / 60 org).
  At the org cap, clean stale snapshots first; do not raise the cap:
  `python scripts/daytona/daytona_snapshot_manager.py --api-key-env DAYTONA_RL_API_KEY --delete-stale --yes`
  (deletes only idle/unprotected `harbor__*` envs — safe; threshold in
  `.agents/projects/daytona/daytona.md`). Only a single dataset legitimately needing
  >`max_new_snapshots` unique envs escalates → ask.
- **vLLM DP>1 (ray backend): never hardcode `--data-parallel-address 127.0.0.1`** —
  Ray registers the head only under its real IPv4 → `127.0.0.1` gives
  `AssertionError: DP master node missing or dead`. `hpc/vllm_utils.py`
  `VLLMServer.start()` auto-injects the head IP for DP>1; don't add the flag to new
  yamls. If overriding, use the real Ray head IPv4.
- **MoE / 80B placement:** the MoE configs carry their own FSDP/EP sizing in-yaml
  (Coder-30B: EP=4×FSDP=4=16 policy GPUs + 4 TP=2 vLLM engines = 24 GPU/6 nodes;
  80B: 8 TP=4 engines + 8-node FSDP shard = 64 GPU/16 nodes). The **80B yaml sets
  `policy_strict_spread_pg: true`** (opt-in anti-affinity reserving the policy PG up
  front to dodge the two-PACK-PG init-OOM race); leave as-configured. Honor the MoE
  FSDP/EP divisibility constraint (`fsdp_size` must divide `num_experts // ep_size`)
  — don't hand-edit node/EP counts. Details → `.agents/projects/marinskyrl/marinskyrl.md`.

## 5. Chain-restart (`--max_restarts K`)
`--max_restarts K` submits a head job + K `afterany`-dependent restart links. A link
that hits the **12h wall TIMEOUT auto-resumes from the latest checkpoint** in the
next link — **TIMEOUT is the NORMAL terminal state of a healthy chain, not a
failure.** Typical `K` = **5–6**.
- A fresh `python -m hpc.launch` with the SAME `--job_name` forks to `<dir>_2` at
  step 0 if the original exp dir's `configs/*.json` exists (the dedup resume-manager
  engages only for datagen/eval, not RL). To *resume* instead of forking: either
  resubmit the existing generated sbatch (`experiments/<dir>/sbatch/*_rl.sbatch`)
  via `--dependency=afterany`, or move the original `configs/*.json` aside so dedup
  lands on the un-suffixed dir. (`--dry_run` regenerates that config → re-move after
  a dry-run, or skip it.)
- Relaunching auto-resumes from `checkpoints/global_step_N/`. For a clean ablation, remove
  `<exp>/<job>/<job>/checkpoints/` before relaunching; retain it for a chain extension.
- Always **`scancel` the previous failed/superseded chain** before resubmitting.

## 6. Standing constraints (do NOT violate)
- **Daytona RL concurrency ≤ 6 RUNNING per cluster** (PENDING restart links don't
  count). Don't launch a 7th concurrent RL job on Jupiter.
- **The a3 series is CONCLUDED — do NOT launch, refill, or auto-advance a3 rows**
  (binary reward + RLOO-n + token_mean; uninformative). Successor arms = the
  seqnorm / TIS / shaped / symclip / loopshape ablations above. *(Exception:
  `DCAgent/r2egym-patched-full-oracle` is a separate snapshot-optimized variant —
  not the a3 row — and launches fine.)*
- **Never alter config/hparams mid-series.** A controlled ablation needing a change
  → propose a separate experiment; don't mutate the in-flight arm.
- **TIMEOUT restarts are expected** (§5) — don't treat a chain's TIMEOUT links as
  failures or salvage them.

## 7. After launch
- **Monitor:** `monitor-cron-sweep` (entropy / log_ratio / grad_norm are mandatory
  progress columns).
- **On completion → `rl-agentic-job-cleanup`** (best-ckpt selection, HF upload from
  the login node, the **manual** Supabase DB registration, trace export +
  `parse_skyrl_metrics`). `enable_db_registration` stays false at launch (§4).
- **Behavior analysis:** `analyze-rl-behavior` for a post-hoc arm comparison.
