#!/usr/bin/env bash
#SBATCH --job-name=eai-marin-moe-smoke
#SBATCH --partition=beta
#SBATCH --gpus-per-node=4
#SBATCH --gres=gpu:b200:4
#SBATCH --nodes=1
#SBATCH --cpus-per-task=64
#SBATCH --time=00:40:00
#SBATCH --output=%x-%j.out
# Submit:  sbatch -A "$EMPIREAI_ACCT" --qos=test hpc/empireai/marin_moe_smoke.sbatch
#
# Phase 2 — tiny initialized-MoE (Levanter "grug" MoE) pretrain smoke on B200.
# Proves: jax[cuda13] sees the B200, Levanter initializes an MoE, a few pretrain steps run.
# Container = the marin-aarch64 .sqsh (Dockerfile.marin-aarch64 -> build_image_enroot.sh).
#
# Framework/reference (marin GitHub, via mumwelt): MoE = Levanter "grug" backend (#929, PR #958;
# expert-parallel + DeepEP #5982). B200 requires jax[cuda13]/JAX 0.9.2 (#5427/#5428), staged CUDA
# toolchain (ptxas/nvlink, #6637), FA4 deps (#6237). Small MoE recipe = experiments/grug/nano_moe
# (hidden~512, 16 experts top-2, Muon). Smoke sharp edges: PR #5431.
set -euo pipefail

IMG="${EMPIREAI_MARIN_SQSH:-/ddn/client_validation/bf996/img/marin-aarch64.sqsh}"
WORK="/ddn/client_validation/bf996/marin_moe_smoke"
mkdir -p "$WORK"

# A tiny MoE + tiny synthetic/tokenized data config for levanter.main.train_lm.
# NOTE: the exact keys must match the pinned Levanter's grug-MoE model config — confirm against
# lib/levanter/config/*moe* (or experiments/grug/nano_moe/launch.py) in the pinned MARIN_REF.
# This is a STARTING TEMPLATE (few layers / few experts / few steps), not yet cluster-validated.
cat > "$WORK/moe_smoke.yaml" <<'YAML'
data:
  # Tiny built-in / cached tokenized set; swap for a small marin data mixture or a local tokenized dir.
  id: dclm_tiny            # placeholder: point at a small tokenized cache or a HF tokenized dataset
  tokenizer: gpt2
model:
  type: gpt_moe           # grug MoE model type in the pinned Levanter (confirm exact name)
  hidden_dim: 256
  intermediate_dim: 512
  num_layers: 2
  num_heads: 4
  num_experts: 8
  top_k: 2
  seq_len: 512
trainer:
  num_train_steps: 20
  train_batch_size: 16
  steps_per_eval: 100000       # skip eval in the smoke
  tensor_parallel_axes: ["mlp", "heads"]
  mp: p=f32,c=bf16
  checkpointer:
    base_path: /workspace/ckpt
    save_interval: 10m
optimizer:
  type: adam
  learning_rate: 3.0e-4
  weight_decay: 0.1
YAML

srun --container-image="$IMG" \
     --container-mounts="$WORK:/workspace" \
     --container-env=HF_TOKEN,HF_HOME \
     --container-remap-root \
     bash -lc '
       set -euo pipefail
       nvidia-smi -L
       python -c "import jax; print(\"jax\", jax.__version__); print(\"devices\", jax.devices())"
       cd /opt/marin
       # Direct Levanter entrypoint (single-node, no Ray needed for a smoke):
       python -m levanter.main.train_lm --config /workspace/moe_smoke.yaml
       echo "=== ckpt ==="; ls -R /workspace/ckpt | head -40
     '

echo "=== PASS CRITERIA: jax.devices() lists cuda B200, MoE model built, loss printed over ~20 steps ==="
