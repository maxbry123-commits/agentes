#!/bin/bash
# MarinSkyRL NON-AGENTIC RL canary for Leonardo (CINECA) — 1 node x 4 A100-64GB.
# GSM8K GRPO, Qwen2.5-1.5B-Instruct, small batches sized to reach a training step
# inside the boost_qos_dbg 30-min window. Runs via skyrl_train.entrypoints.main_base.
#
# This is invoked INSIDE the marinskyrl.sif via `apptainer exec --nv` from the
# accompanying sbatch (sbatch_gsm8k_canary.sh). It does NOT go through the OTA
# hpc.py launcher and has NO Harbor/Daytona/terminal_bench/agentic dependency.
#
# Required env (exported by the sbatch):
#   DATA_DIR   -> dir holding train.parquet + validation.parquet (local, pre-staged)
#   MODEL_PATH -> local HF model dir/cache id (offline)
#   NUM_GPUS   -> 4
#   CKPT_DIR   -> writable ckpt dir on scratch
# WANDB_MODE=offline and HF_HUB_OFFLINE=1 are set by the sbatch.
set -x

: "${DATA_DIR:?set DATA_DIR}"
: "${MODEL_PATH:?set MODEL_PATH}"
: "${NUM_GPUS:=4}"
: "${CKPT_DIR:?set CKPT_DIR}"
: "${LOGGER:=console}"        # offline canary -> console, not wandb
: "${INFERENCE_BACKEND:=vllm}"

# We run from the MarinSkyRL skyrl-train dir so the uv project / installed env resolves.
# $VENV_PY is the external uv-resolved venv python (set by the sbatch); fall back to `python`.
: "${VENV_PY:=python}"
"$VENV_PY" -m skyrl_train.entrypoints.main_base \
  data.train_data="['$DATA_DIR/train.parquet']" \
  data.val_data="['$DATA_DIR/validation.parquet']" \
  trainer.algorithm.advantage_estimator="grpo" \
  trainer.policy.model.path="$MODEL_PATH" \
  trainer.placement.colocate_all=true \
  trainer.strategy=fsdp2 \
  trainer.placement.policy_num_gpus_per_node=$NUM_GPUS \
  trainer.placement.critic_num_gpus_per_node=$NUM_GPUS \
  trainer.placement.ref_num_gpus_per_node=$NUM_GPUS \
  generator.num_inference_engines=$NUM_GPUS \
  generator.inference_engine_tensor_parallel_size=1 \
  trainer.epochs=1 \
  trainer.eval_batch_size=32 \
  trainer.eval_before_train=false \
  trainer.eval_interval=0 \
  trainer.update_epochs_per_batch=1 \
  trainer.train_batch_size=32 \
  trainer.policy_mini_batch_size=32 \
  trainer.micro_forward_batch_size_per_gpu=8 \
  trainer.micro_train_batch_size_per_gpu=8 \
  trainer.ckpt_interval=999999 \
  trainer.max_prompt_length=512 \
  generator.sampling_params.max_generate_length=512 \
  trainer.policy.optimizer_config.lr=1.0e-6 \
  trainer.algorithm.use_kl_loss=false \
  generator.backend=$INFERENCE_BACKEND \
  generator.run_engines_locally=true \
  generator.weight_sync_backend=nccl \
  generator.async_engine=true \
  generator.batched=true \
  environment.env_class=gsm8k \
  generator.n_samples_per_prompt=4 \
  generator.gpu_memory_utilization=0.7 \
  trainer.logger="$LOGGER" \
  trainer.project_name="gsm8k_canary" \
  trainer.run_name="leonardo_gsm8k_canary" \
  trainer.resume_mode=null \
  trainer.ckpt_path="$CKPT_DIR" \
  trainer.export_path="$CKPT_DIR/exports" \
  "$@"
