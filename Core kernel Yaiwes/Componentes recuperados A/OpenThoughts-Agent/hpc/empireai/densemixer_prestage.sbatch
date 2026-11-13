#!/bin/bash
#SBATCH --job-name=dm_prestage
#SBATCH --partition=beta
#SBATCH --account=ny_chinmayh_datacomp
#SBATCH --qos=test
#SBATCH --gres=gpu:b200:1
#SBATCH --cpus-per-task=16
#SBATCH --mem=128G
#SBATCH --time=02:00:00
#SBATCH --output=/mnt/home/bf996/logs/dm_prestage_%j.out

# =============================================================================
# Pre-stage the SHARED θ₀ + the opencode SFT dataset for the densemixer ablation.
# BOTH runs (dense/sparse) load the IDENTICAL pinned revisions (control discipline).
#   θ₀    = Qwen/Qwen3-30B-A3B-Thinking-2507 @ 144afc2f... (model_type qwen3_moe)
#   data  = penfever/nemotron-code-oracle-filtered-...-opencode-traces @ <PIN>
# θ₀ is downloaded to a STABLE dir (~/experiments/densemixer/theta0) so cache
# eviction can't touch the shared init the Δθ analysis measures against.
# =============================================================================
set -euxo pipefail

export IMG=/mnt/home/bf996/images/mega_final.sqsh
export HF_HOME=/mnt/home/bf996/hf_cache
THETA0_DIR=/mnt/home/bf996/experiments/densemixer/theta0
DATA_DIR=/mnt/home/bf996/experiments/densemixer/data_nemotron_code_oracle
MODEL_REV=144afc2f379b542fdd4e85a1fcd5e1f79112d95d
DATA_REPO=penfever/nemotron-code-oracle-filtered-qwen3.5-122b-131k-opencode-traces
DATA_REV=6cc0c0b5ccec0792a61a98c384a1612bb38c2309

srun --container-image="$IMG" --container-mount-home \
     --container-env=HF_TOKEN \
     bash -lc '
       set -euxo pipefail
       export PATH=/usr/local/bin:/usr/local/cuda/bin:/usr/bin:/bin; hash -r
       unset PYENV_ROOT PYENV_VERSION PYENV_SHELL || true
       unset PIP_CONSTRAINT || true
       export HF_HOME=/mnt/home/bf996/hf_cache
       export HF_HUB_ENABLE_HF_TRANSFER=1
       PY=/usr/bin/python
       mkdir -p "'"$THETA0_DIR"'" "'"$DATA_DIR"'"
       # θ₀ — pinned revision to a stable local dir (this IS the archived shared init).
       # dataset — pinned revision (repo_type dataset). Use the snapshot_download API
       # (the container has huggingface_hub as a transformers dep; `python -m huggingface_hub`
       # has no __main__, and the `hf`/`huggingface-cli` console script may be absent).
       $PY - <<PYDL
from huggingface_hub import snapshot_download
snapshot_download("Qwen/Qwen3-30B-A3B-Thinking-2507", revision="'"$MODEL_REV"'",
                  local_dir="'"$THETA0_DIR"'", max_workers=16)
snapshot_download("'"$DATA_REPO"'", repo_type="dataset", revision="'"$DATA_REV"'",
                  local_dir="'"$DATA_DIR"'", max_workers=16)
print("DOWNLOADS_OK")
PYDL
       echo "=== theta0 contents ==="; ls -la "'"$THETA0_DIR"'" | head
       $PY -c "import json,glob,os; d=\"'"$THETA0_DIR"'\"; c=json.load(open(os.path.join(d,\"config.json\"))); print(\"THETA0 model_type\", c.get(\"model_type\"), \"num_experts\", c.get(\"num_experts\"), \"num_experts_per_tok\", c.get(\"num_experts_per_tok\"))"
     '
echo "DM_PRESTAGE_COMPLETE [$(date)]"
