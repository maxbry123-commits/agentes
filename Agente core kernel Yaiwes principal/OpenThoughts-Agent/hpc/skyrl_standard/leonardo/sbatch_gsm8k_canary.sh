#!/bin/bash
#SBATCH --job-name=marinskyrl_gsm8k_canary
#SBATCH --account=AIFAC_5C0_290
#SBATCH --partition=boost_usr_prod
#SBATCH --qos=boost_qos_dbg
#SBATCH --time=00:30:00
#SBATCH --nodes=1
#SBATCH --ntasks-per-node=1
#SBATCH --cpus-per-task=32
#SBATCH --gres=gpu:4
#SBATCH --mem=480G
#SBATCH --output=%x_%j.out
#SBATCH --error=%x_%j.out
#
# MarinSkyRL NON-AGENTIC GSM8K GRPO canary on Leonardo (1 node x 4 A100-64GB).
# apptainer exec --nv the marinskyrl apptainer image (writable sandbox built on
# the login node) + an external uv-resolved venv, running run_gsm8k_canary.sh
# with LOCAL pre-staged model + dataset, fully offline.
#
# Env approach (DOCUMENTED): SkyRL is uv-native. We use SkyRL's native uv flow
# (`uv sync --extra vllm`) rather than a conda env, because conda cannot reliably
# satisfy SkyRL's pinned cu128 wheels + flashinfer-jit-cache custom index + the
# torch/vllm/flash-attn conflict graph that uv resolves deterministically from
# the committed uv.lock. The resolved venv lives OUTSIDE the image at
# $SF/marin_venv (Lustre, bind-mounted at runtime). The container itself is a
# WRITABLE SANDBOX dir (not a .sif): the squashfs/mksquashfs step OOM-killed on
# the login node (and hit lustre.lov xattr fatals on Lustre tmp), so we run
# apptainer directly against the sandbox dir, which is a fully valid image.
set -euxo pipefail

WORK=/leonardo_work/AIFAC_5C0_290/bfeuer00
SF=/leonardo_scratch/fast/AIFAC_5C0_290/bfeuer00
SANDBOX=$SF/marinskyrl_sandbox
VENV=$SF/marin_venv
MARIN=$WORK/code/MarinSkyRL/skyrl-train
CFG=$WORK/code/OpenThoughts-Agent/hpc/skyrl_standard/leonardo

export DATA_DIR=$WORK/data/gsm8k
export MODEL_PATH=Qwen/Qwen2.5-1.5B-Instruct      # resolved from offline HF cache
export NUM_GPUS=4
export CKPT_DIR=$SF/ckpts/gsm8k_canary

# Offline / cache env (compute nodes have no internet)
export HF_HUB_OFFLINE=1
export TRANSFORMERS_OFFLINE=1
export HF_HOME=$WORK/data/hub
export HF_HUB_CACHE=$WORK/data/hub
export WANDB_MODE=offline
export VLLM_CACHE_ROOT=$SF/vllm_cache
export TRITON_CACHE_DIR=$SF/vllm_cache/triton
export FLASHINFER_WORKSPACE_BASE=$SF/vllm_cache/flashinfer
# Writable HOME on scratch — SkyRL defaults several paths to ${HOME}/... and the
# container's own /home is read-only (image root -> /leonardo RO fs).
export CONTAINER_HOME=$SF/canary_home
mkdir -p "$CKPT_DIR" "$VLLM_CACHE_ROOT" "$TRITON_CACHE_DIR" "$FLASHINFER_WORKSPACE_BASE" "$CONTAINER_HOME"

# C compiler for Triton JIT (the ray base image ships no gcc; we couldn't apt it
# in without a fakeroot mapping). Reuse the host miniforge gcc 14.3.0 (on $WORK,
# bind-mounted); verified to compile+run inside the container. CONDA_BIN is added
# to PATH and CC/CXX are exported into the container below.
export CONDA_BIN=$WORK/miniforge3/envs/otagent/bin
# Silence ray usage telemetry (it writes to ~/.ray and spams /leonardo/home RO errors).
export RAY_USAGE_STATS_ENABLED=0

# Point the run script at the external uv venv python.
export VENV_PY=$VENV/bin/python

# Bind the full Lustre roots (so $WORK, $SF, model, data, venv all resolve in-container).
# --no-home + clean PATH to avoid the host ~/.bashrc conda-leak seen during the build.
nvidia-smi || true

singularity exec --nv \
  --no-home \
  --bind /leonardo_work:/leonardo_work,/leonardo_scratch:/leonardo_scratch \
  --pwd "$MARIN" \
  --env HOME=$CONTAINER_HOME,PATH=$CONDA_BIN:/usr/local/bin:/usr/bin:/bin,CC=$CONDA_BIN/gcc,CXX=$CONDA_BIN/g++ \
  --env HF_HUB_OFFLINE=1,TRANSFORMERS_OFFLINE=1,HF_HOME=$HF_HOME,HF_HUB_CACHE=$HF_HUB_CACHE,WANDB_MODE=offline,VLLM_CACHE_ROOT=$VLLM_CACHE_ROOT,TRITON_CACHE_DIR=$TRITON_CACHE_DIR,FLASHINFER_WORKSPACE_BASE=$FLASHINFER_WORKSPACE_BASE,RAY_USAGE_STATS_ENABLED=0,DATA_DIR=$DATA_DIR,MODEL_PATH=$MODEL_PATH,NUM_GPUS=$NUM_GPUS,CKPT_DIR=$CKPT_DIR,LOGGER=console,VENV_PY=$VENV_PY \
  "$SANDBOX" bash "$CFG/run_gsm8k_canary.sh"

echo "CANARY_EXIT=$?"
