#!/usr/bin/env bash
#SBATCH --job-name=eai-axolotl-smoke
#SBATCH --partition=beta
#SBATCH --gpus-per-node=1
#SBATCH --gres=gpu:b200:1
#SBATCH --nodes=1
#SBATCH --cpus-per-task=32
#SBATCH --time=00:40:00
#SBATCH --output=%x-%j.out
# Account + QoS are passed at submit time (do NOT hardcode):
#   sbatch -A "$EMPIREAI_ACCT" --qos=test hpc/empireai/sft_axolotl_smoke.sbatch
#
# Phase 1 — tiny Axolotl SFT smoke on one B200. Proves: Axolotl trains a step + writes a checkpoint.
# Container = the axolotl-aarch64 .sqsh built via build_image_enroot.sh (or NGC base + runtime pip).
set -euo pipefail

IMG="${EMPIREAI_AXOLOTL_SQSH:-/ddn/client_validation/bf996/img/axolotl-aarch64.sqsh}"
WORK="/ddn/client_validation/bf996/axolotl_smoke"        # or /tmp/$USER for node-local scratch
mkdir -p "$WORK"

# Minimal axolotl config: small model, tiny built-in dataset (alpaca sample), 2 optimizer steps, save.
cat > "$WORK/smoke.yaml" <<'YAML'
base_model: Qwen/Qwen2.5-0.5B
model_type: AutoModelForCausalLM
tokenizer_type: AutoTokenizer
load_in_8bit: false
load_in_4bit: false
datasets:
  - path: tatsu-lab/alpaca
    type: alpaca
    split: train[:256]
val_set_size: 0.0
sequence_len: 1024
sample_packing: false
pad_to_sequence_len: true
micro_batch_size: 2
gradient_accumulation_steps: 1
max_steps: 2
num_epochs: 1
optimizer: adamw_torch
learning_rate: 1.0e-5
lr_scheduler: constant
bf16: true
flash_attention: false          # start with sdpa; flip true only after flash-attn is proven on sm_100
gradient_checkpointing: true
logging_steps: 1
save_steps: 2
save_strategy: steps
output_dir: /workspace/out
dataset_prepared_path: /workspace/prep
special_tokens: {}
YAML

# HF token forwarded from the submit env (never hardcode). source /Users/.../secrets.env before sbatch.
srun --container-image="$IMG" \
     --container-mounts="$WORK:/workspace" \
     --container-env=HF_TOKEN,HF_HOME \
     --container-remap-root \
     bash -lc '
       set -euo pipefail
       nvidia-smi -L
       python -c "import torch;print(\"cap\", torch.cuda.get_device_capability(0))"
       cd /workspace
       accelerate launch -m axolotl.cli.train smoke.yaml
       echo "=== checkpoint contents ==="; ls -R /workspace/out | head -50
     '

echo "=== PASS CRITERIA: training logged step 1->2, loss printed, /workspace/out has a checkpoint ==="
