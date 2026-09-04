---
name: rl-standard-launch-leonardo
description: >-
  Launch, relaunch, or sweep STANDARD (non-agentic) SkyRL RL on CINECA Leonardo —
  GRPO on math/reasoning datasets (gsm8k, MATH/aime) and on-policy distillation
  (OPD, teacher→student) — via raw `sbatch` of the `hpc/skyrl_standard/leonardo/*` run
  scripts inside the writable apptainer SANDBOX + uv `marin_venv` (NOT `python -m
  hpc.launch`, NOT a `.sif`, NOT `--rl_use_conda`). Use when asked to run/relaunch
  a gsm8k or OPD GRPO canary, throughput/accuracy grid, or multi-node RL on
  Leonardo A100-64GB. Covers the GRPO/OPD knobs, the grid cell structure, the
  1-node-vs-multi-node layout, the A100-64GB ceilings, and the no-internet/offline
  + gcc/HOME/Ray-temp-dir gotchas. For agentic Harbor+Daytona RL, this is the WRONG
  skill (Daytona needs internet — infeasible on Leonardo).
---

> ⚠ **Do not add comments to YAMLs. Report your recommendations directly to the supervisor.**

# rl-standard-launch-leonardo

> **⚠ VERIFY checkpoint/export paths resolve to `$WORK` (`$CHECKPOINTS_DIR`), NOT
> `$SF`/`$SCRATCH_FAST`** — scratch is 1 TB/over-quota; a ckpt write fails
> `OSError [Errno 122] Disk quota exceeded` mid-run (NOT an OOM). See
> `.agents/ops/leonardo/ops.md` "WRITE-PATH MANDATE".

Standard **non-agentic** SkyRL RL on Leonardo: GRPO on local math/reasoning parquet and on-policy distillation
(OPD). Compute nodes are offline: no Harbor, Daytona, terminal_bench, or proxyserver.

Authoritative source docs (this skill distills them — read for full numbers):
- `notes/RL/gsm8k_grid_leonardo/` — `grid.md` (throughput), `accuracy_grid.md`
  (pass@8 to convergence), `grid_experiment_log.md` (methodology), `scripts/`.
- `notes/RL/opd_grid_leonardo/` — `leonardo_opd_qwen3_plan.md`, `grid.md`,
  `throughput_grid.md`.
- Leonardo access boilerplate (ssh/2FA, preamble, code/data paths, step-ca cert,
  login-node killer) → `.agents/ops/leonardo/ops.md` + `CLAUDE.md`.

> Launch with an `sbatch` wrapper in `hpc/skyrl_standard/leonardo/`, not `hpc.launch`. It uses a writable sandbox
> directory and external uv venv, then calls the SkyRL entrypoint directly.

## 1. Cluster + env facts

A100-**64GB**, 4 GPUs/node, x86_64, SLURM. Account `AIFAC_5C0_290`, partition
`boost_usr_prod`. QOS: **`boost_qos_dbg`** (≤30 min, ≤2 nodes) or **`normal`**
(more nodes; **24h max**).

- **MarinSkyRL** = `marin-community/MarinSkyRL` `main @ 9bb6d5e` at
  `$WORK/code/MarinSkyRL` (`$WORK = /leonardo_work/AIFAC_5C0_290/bfeuer00`).
  Container `--pwd` = `MarinSkyRL/skyrl-train` → SkyRL fixes go to **MarinSkyRL
  `main`**.
- **Image = writable sandbox dir** `$SF/marinskyrl_sandbox`
  (`$SF = /leonardo_scratch/fast/AIFAC_5C0_290/bfeuer00`), from
  `docker://anyscale/ray:2.51.1-slim-py312-cu128`. Binary `/usr/bin/singularity`
  (SingularityPRO 4.3.1; no `apptainer` on PATH).
- **uv, not conda**: venv `$SF/marin_venv` (`uv sync --extra vllm` → torch
  2.8.0+cu128, vLLM 0.11.0, flash-attn 2.8.3). `$VENV_PY=$VENV/bin/python`.

### Standing gotchas
1. **No compute-node internet:** `HF_HUB_OFFLINE=1`,
   `TRANSFORMERS_OFFLINE=1`, `WANDB_MODE=offline`,
   `HF_HOME`/`HF_HUB_CACHE`=`$WORK/data/hub`. **Pre-stage model + parquet on the
   LOGIN node first.**
2. **gcc for Triton JIT** — the ray base image ships no compiler. Wrapper binds
   host miniforge `$WORK/miniforge3/envs/otagent/bin` onto PATH + exports
   `CC`/`CXX` (gcc 14.3.0). `RAY_USAGE_STATS_ENABLED=0`.
3. **HOME is read-only in-container:** set `HOME=$SF/canary_home`,
   `ckpt_path`/`export_path` at writable `$SF`. The `/leonardo/home` RO
   `FileNotFoundError`/`Read-only file system`/`Traceback` lines (tvm_ffi dlpack,
   vLLM telemetry) are **benign engine-init noise** — ignore them.

## 2. Pre-launch (login node, tmux)

Run the standard Leonardo preamble (ops.md), then pre-stage offline data:
```bash
ssh Leonardo                              # step-ca cert; 2FA once (ops.md)
cd /leonardo_work/AIFAC_5C0_290/bfeuer00/code/MarinSkyRL && GIT_TERMINAL_PROMPT=0 git pull
# Pre-stage on the LOGIN node (compute has no internet):
hf download Qwen/Qwen2.5-1.5B-Instruct    # → $WORK/data/hub
# gsm8k parquet → $WORK/data/gsm8k/{train,validation}.parquet  (MarinSkyRL examples/gsm8k/gsm8k_dataset.py)
# MATH:  hpc/skyrl_standard/leonardo/math_dataset.py → $WORK/data/math/
```
Edit code locally, commit/push, and `git pull` on Leonardo; never patch remote files.

## 3. Launch — single node

```bash
cd /leonardo_work/AIFAC_5C0_290/bfeuer00/code/OpenThoughts-Agent/hpc/skyrl_standard/leonardo
sbatch sbatch_gsm8k_canary.sh             # bare canary: 1 node × 4 A100, ≤30 min
```
The sbatch sets `DATA_DIR`/`MODEL_PATH`/`NUM_GPUS=4`/`CKPT_DIR` + offline env,
then `singularity exec --nv --no-home --bind /leonardo_work,/leonardo_scratch
--pwd $MARIN $SANDBOX bash run_gsm8k_canary.sh`, which calls
`$VENV_PY -m skyrl_train.entrypoints.main_base` with the GRPO knobs.

**Canary GRPO config** (`run_gsm8k_canary.sh`, Qwen2.5-1.5B-Instruct):
`advantage_estimator=grpo`, `strategy=fsdp2`, `colocate_all=true`,
`backend=vllm`, `run_engines_locally=true`, `weight_sync_backend=nccl`,
`async_engine=true`, 4 engines × TP1, `use_kl_loss=false`, `lr=1e-6`,
`n_samples_per_prompt=4`, `train_batch_size=32`, `max_prompt_length=512`,
`max_generate_length=512`, `gpu_memory_utilization=0.70`, `env_class=gsm8k`,
`epochs=1`, `logger=console` (offline). Reference: job **44478923** COMPLETED,
233-step epoch, 9.58 s/step, reward 0.14→0.64, pass@4 0.78.

### Grid-cell overrides
`run_gsm8k_canary.sh` ends in `"$@"` (trailing hydra overrides, last-wins), **but
`sbatch_gsm8k_canary.sh` does NOT forward `"$@"`** — for grid cells use
**`sbatch_gsm8k_grid.sh`** (passthrough + **fresh per-cell `CKPT_DIR`**, `rm -rf`'d
before launch):
```bash
sbatch --job-name=grid_cudagraph sbatch_gsm8k_grid.sh generator.enforce_eager=false
sbatch --job-name=grid_tbs128    sbatch_gsm8k_grid.sh trainer.train_batch_size=128 trainer.policy_mini_batch_size=128
```
`--job-name=grid_<cell>` is load-bearing: the script derives
`CKPT_DIR=$SF/grid_ckpts/${SLURM_JOB_NAME#grid_}` from it. Per-cell scripts in
`notes/RL/gsm8k_grid_leonardo/scripts/run_<cell>.sh`; launchers
`launch_throughput_grid.sh`/`launch_accuracy_grid.sh` + catalogs `*_grid_cells.txt`
in `hpc/skyrl_standard/leonardo/`.

## 4. Grid structure (one-factor-at-a-time off the base)

- **Throughput grid** (`grid.md`, 18 cells, maximize sec/step / eff tok/s):
  varies `train_batch_size` (32→512), `n_samples_per_prompt` (4→16),
  `gpu_memory_utilization` (0.70→0.85), `enforce_eager` (CUDA graphs), engine
  layout (4×TP1 vs 2×TP2 vs 1×TP4), `micro_*_batch_size_per_gpu`,
  `reshard_after_forward`, `colocate_all`. **Winners:** `enforce_eager=false`
  = −29% sec/step (always on); **4×TP1 > 2×TP2 > 1×TP4**; **colocated >
  disaggregated** at 4 GPU. Base width is gen-bound (cudagraph fixes it); past
  ~tbs128 it's `policy_train` compute-bound; **never memory-bound** (KV <11%).
- **Accuracy grid** (`accuracy_grid.md`, 20 cells, maximize **pass@8 to
  convergence** off the throughput winner `combo_C`): varies **lr** (dominant
  lever; GRPO knee **1e-5**, 3e-7 undertrains, 3e-5 unstable), `n_samples` (n8
  winner), `max_generate_length` (gen1024 winner), `use_kl_loss`/`kl_loss_coef`,
  rollout temp, `eps_clip_high` (DAPO), entropy bonus (`use_entropy_loss=true,
  entropy_loss_coef=0.01` = anti-collapse winner), reward shaping. **Best:**
  `combo_acc` (lr1e-5 + n8 + gen1024) → pass@8 ~0.97 but entropy collapses;
  `combo_acc_stab` (+ entbonus) holds ~0.95–0.98 WITHOUT collapse.

**gsm8k:** short CoT (~245–268 tokens), exact-match ±1 reward, and lr knee 1e-5. MATH/`aime` needs
`max_generate_length=4096`; 32B OOMs on a single 4×A100-64GB node, so use multi-node.

## 5. OPD — on-policy distillation (teacher→student)

Student (Qwen3-1.7B) generates; per-token reward = −KL(student‖teacher) over the
student's tokens. Entrypoint
**`examples.on_policy_distillation_logits.main_on_policy_distill_logits`** (NOT
`main_base`, NOT the agentic `main_tbench_opd_logits` which needs Daytona). Knobs:
`advantage_estimator=no_op`, `policy_loss_type=importance_sampling`,
`use_kl_in_reward=true`, `use_kl_loss=false`; the FSDP **ref worker is loaded with
the teacher** + a separate **vLLM-served teacher** supplies top-K logprobs
(`teacher.top_k_logprobs`).
```bash
sbatch sbatch_opd_qwen3.sh                         # smoke defaults (2 nodes, ≤90 min)
sbatch --job-name=opd_q3_full --time=08:00:00 sbatch_opd_qwen3.sh \
  MAX_STEPS=60 EPOCHS=2 TRAIN_BATCH_SIZE=64 MINI_BATCH_SIZE=64 N_SAMPLES=8 MAX_GEN_LEN=1024 TOPK=128
```
**Layout (2 nodes × 4 A100-64GB):** student colocated (FSDP2 ↔ 4× vLLM TP1) on
node-0; teacher **Qwen3-32B TP2** (32B bf16 ≈ 64 GB > one 64 GB card) on its own
Ray PACK PG on node-1; 2 GPUs spare. Shared tokenizer → retokenization is a no-op
(Qwen3-1.7B is the nearest size to a nonexistent 1.5B).

OPD is **teacher-score-bound** (90–97% of each step). The speed lever is `top_k`; the lr knee is 3e-5.
**Recommended OPD:** `lr=3e-5, top_k=64, n_samples=8, gen=1024, teacher TP2, cudagraph off`.

## 6. Multi-node

Use `sbatch_gsm8k_grid_multinode.sh`, `sbatch_math_grid_multinode.sh`, or `sbatch_opd_qwen3.sh`. These start a
Ray head on node 0, attach workers, and launch the trainer with `RAY_ADDRESS`. Keep these gotchas:
- **InfiniBand `ib0`** pinned: `NCCL_SOCKET_IFNAME=ib0`, `GLOO_SOCKET_IFNAME=ib0`;
  head IP resolved from `ib0` (not the `eno*` mgmt addr).
- **Ray `--temp-dir=/tmp`** (not Lustre scratch): the AF_UNIX plasma-store socket
  path **cannot exceed 107 bytes**; the Lustre scratch root is already ~55 chars
  → a temp-dir there overflows. (verify `RAY_TMP` in the script before relaunch.)
- gsm8k/1.5B multi-node generator scaling does NOT help (train-bound, not
  gen-bound). Multi-node pays off only for big models (≥32B, single-node-OOM) or
  genuinely gen-bound small-model long-CoT.

## 7. Monitoring + completion

- **Monitor** detached: poll `%x_%j.out` for the per-step
  `WANDB_MIRROR kind=train step=N metrics={...}` JSON lines (offline → stdout).
  Watch `timing/{step,generate,policy_train,sync_weights}`, GRPO reward +
  `policy/policy_entropy` (collapse guard, mandatory), grad_norm. OPD:
  `distill/token_kl_mean` (should DECREASE), `teacher/chosen_logprob_mean`, entropy.
  Sweep cadence → **`monitor-cron-sweep`**.
- **Resume:** run scripts set `resume_mode=null` (fresh) per cell to avoid
  cross-cell stale-`global_step` resume. Genuine resume: `resume_mode=latest` +
  keep `ckpt_path` stable; clean re-run: `rm -rf` the ckpt dir first.
  - **⚠ DESTRUCTIVE — pass `RESUME_MODE`/`DATA_DIR` via `--export`, NOT positionally.**
    `sbatch_delphi_math_rl_multinode.sh` reads them from the **environment**; its
    positional parser only strips
    `MODEL_PATH/RUN_NAME/STAGE/DATASET/THINK/THINK_MODE/DELPHI_TEMPLATE`. Positional
    `KEY=val` tokens leak to hydra → `Could not override 'RESUME_MODE'` → head FAILS.
    An unset/invalid `RESUME_MODE` is a HARD `exit 1` (you MUST pass it explicitly):
    `sbatch --export=ALL,DATA_DIR=<path>,RESUME_MODE=latest sbatch_delphi_math_rl_multinode.sh <positional… only>`
    (fresh cell: `…,RESUME_MODE=null …`).
- **24h wall:** `boost_usr_prod` caps at `23:59:00`; OPD full (~24 min/step) fits
  only ~18–20 steps/slot → ckpt every few steps and chain `--dependency=afterany:`.
- **Completion → `rl-standard-job-cleanup`** for upload, optional registration, metrics, and cleanup.
  Measurement runs with throwaway checkpoints only clean disk.

## 8. Guardrails

- **Launch via `sbatch hpc/skyrl_standard/leonardo/sbatch_*.sh`**, NOT
  `python -m hpc.launch`, NOT a `.sif`, NOT `--rl_use_conda`.
- **Fully offline** — pre-stage model + parquet on the login node; the
  `/leonardo/home` RO `FileNotFoundError`/`Traceback` lines are benign (§1.3).
- **Grid cells need `sbatch_gsm8k_grid.sh` (the `"$@"`-forwarding wrapper) + a
  unique `--job-name=grid_<cell>`** → fresh per-cell ckpt dir; the bare canary
  sbatch does NOT forward overrides. Never share a ckpt dir across cells.
- **A100-64GB ceilings:** `gpu_memory_utilization` ≤ **0.85** (≥0.90 OOMs eval);
  dense ≥32B and MoE 30B-A3B OOM single-node → multi-node/disaggregated.
- **Never alter hparams mid-series** (controlled grid) — flag + propose a separate
  cell. **Entropy/log-ratio/grad-norm are mandatory monitoring columns.**
- **Multi-node:** `ib0` NICs + Ray `--temp-dir` short path (107-byte AF_UNIX limit).
- **SkyRL fixes → MarinSkyRL `main`**, pushed + pulled on Leonardo; never patch
  remote files.
- **Agentic RL (Harbor/Daytona/TBench) is INFEASIBLE on Leonardo** (no
  compute-node internet) — different skill.
