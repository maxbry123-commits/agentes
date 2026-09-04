#!/bin/bash
#SBATCH --job-name=data
#SBATCH --partition=beta
#SBATCH --account=ny_chinmayh_datacomp
#SBATCH --qos=standard
#SBATCH --gres=gpu:b200:1
#SBATCH --cpus-per-task=32
#SBATCH --mem=240G
#SBATCH --time=08:00:00
#SBATCH --output=/mnt/home/bf996/logs/%x_%j.out

# ==============================================================================
# EmpireAI Beta — Unified Eval Harbor (B200 NVL72, sm_100, aarch64).
#
# The Beta analog of eval/tacc/eval_harbor.sbatch, but CONTAINERIZED: Beta compute
# nodes are a minimal install (Pyxis/Enroot MANDATORY), so instead of activating a
# conda env this srun-launches the `mega_v2_rl.sqsh` container and runs the whole
# harbor+vLLM+pinggy+upload body (eval/empireai/eval_incontainer.sh) inside it, on
# the RL venv (/opt/envs/rl). Container template = ~/scripts/dm_run1_dense.sbatch.
#
# KEY DIFFERENCES vs TACC Vista:
#   - Pyxis/Enroot container (mega_v2_rl.sqsh) instead of a conda env; the eval body
#     runs in-container as /opt/envs/rl/bin/python (the sm_100 vLLM fork + harbor).
#   - GPUs ARE a SLURM gres on Beta -> --gres=gpu:b200:N (Vista strips --gres). Both
#     the header default and the listener's untyped `--gres gpu:N` are accepted here.
#   - DIRECT egress like Vista -> DIRECT pinggy tunnel, NO proxychains.
#   - Node-local /tmp caches (set in the in-container script) dodge the VAST-NFS
#     ESTALE race the multi-node SFT hit (job 31689).
#
# Positional args (from the unified eval listener, identical contract to TACC):
#   $1 = MODEL (HF name) | $2 = REPO_ID (HF dataset, or a local /abs task path)
#   $3 = BENCHMARK_ID (optional) | $4 = RUN_TAG (optional; job name)
#
# Env from the listener: EVAL_CONFIG_YAML, EVAL_PINGGY_URL, EVAL_PINGGY_TOKEN,
#   EVAL_N_CONCURRENT, EVAL_N_ATTEMPTS, EVAL_GPU_MEMORY_UTIL, EVAL_TIMEOUT_MULTIPLIER,
#   EVAL_DB_JOB_ID, EVAL_VLLM_*, EVAL_AGENT_KWARGS, EVAL_AGENT_PARSER.
# Smoke knobs: EVAL_SKIP_DB=1 (no DB row), EVAL_SKIP_UPLOAD=1 (no HF/DB upload).
# ==============================================================================
set -euxo pipefail

# --- Host-side config (paths on Beta) ---
export IMG="${EVAL_IMG:-/mnt/home/bf996/images/mega_v2_rl.sqsh}"
export DCFT="${EVAL_PROJECT_ROOT:-/mnt/home/bf996/OpenThoughts-Agent}"
export SECRETS_ENV="${DC_AGENT_SECRET_ENV:-/mnt/home/bf996/secrets.env}"
export EVAL_JOBS_DIR="${EVAL_JOBS_DIR:-/mnt/home/bf996/eval_jobs}"
export HF_HOME="${HF_HOME:-/mnt/home/bf996/hf_cache}"
mkdir -p "$EVAL_JOBS_DIR" "$HF_HOME" /mnt/home/bf996/logs

# --- Positional args -> exported for --container-env forwarding ---
export MODEL="${1:?Usage: eval_harbor.sbatch <MODEL> <REPO_ID> [BENCHMARK_ID] [RUN_TAG]}"
export REPO_ID="${2:?Missing REPO_ID}"
export BENCHMARK_ID="${3:-}"
_SHORT_MODEL=$(echo "$MODEL" | awk -F'/' '{print $NF}')
if [ -n "${4:-}" ]; then export RUN_TAG="$4"; else export RUN_TAG="eval-$(echo "$MODEL" | tr '/:' '_')_$(basename "$REPO_ID" | tr '/:' '_')"; fi
scontrol update JobId=$SLURM_JOB_ID Name="eval_${_SHORT_MODEL}" 2>/dev/null || true

# --- Head node (for the in-container vLLM health check) ---
SCONTROL=$(command -v scontrol || echo /cm/local/apps/slurm/current/bin/scontrol)
export MASTER_ADDR="$($SCONTROL show hostnames "$SLURM_JOB_NODELIST" | head -n1)"

echo "=== EmpireAI Beta eval: model=$MODEL repo=$REPO_ID run_tag=$RUN_TAG node=$MASTER_ADDR img=$IMG ==="

# --- Vars forwarded into the container (names; values from this env) ---
CE="MODEL,REPO_ID,BENCHMARK_ID,RUN_TAG,MASTER_ADDR,SLURM_JOB_ID"
CE="$CE,DCFT,EVAL_JOBS_DIR,HF_HOME,SECRETS_ENV"
CE="$CE,EVAL_CONFIG_YAML,EVAL_N_CONCURRENT,EVAL_N_ATTEMPTS,EVAL_GPU_MEMORY_UTIL,EVAL_TIMEOUT_MULTIPLIER"
CE="$CE,EVAL_PINGGY_URL,EVAL_PINGGY_TOKEN,EVAL_DB_JOB_ID,EVAL_AGENT_KWARGS,EVAL_AGENT_PARSER"
CE="$CE,EVAL_SKIP_DB,EVAL_SKIP_UPLOAD,EVAL_N_TASKS,EVAL_OVERRIDE_MEMORY_MB,EVAL_AUTO_SNAPSHOT,EVAL_MAX_OUTPUT_TOKENS,VLLM_PORT"
CE="$CE,EVAL_VLLM_TENSOR_PARALLEL_SIZE,EVAL_VLLM_DATA_PARALLEL_SIZE,EVAL_VLLM_MAX_MODEL_LEN,EVAL_VLLM_MAX_NUM_SEQS"
CE="$CE,EVAL_VLLM_SWAP_SPACE,EVAL_VLLM_TRUST_REMOTE_CODE,EVAL_VLLM_TOOL_CALL_PARSER,EVAL_VLLM_REASONING_PARSER"
CE="$CE,EVAL_VLLM_EXTRA_ARGS,EVAL_VLLM_HF_OVERRIDES,EVAL_VLLM_TOKENIZER,EVAL_VLLM_LIMIT_MM_PER_PROMPT"

# --- One container task on this node; the in-container script does everything ---
srun --nodes=1 --ntasks-per-node=1 \
     --container-image="$IMG" --container-mount-home \
     --container-env="$CE" \
     bash -lc 'bash "$DCFT/eval/empireai/eval_incontainer.sh"'

echo "EVAL_HARBOR_BETA_DONE [$(date)]"
