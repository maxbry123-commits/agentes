#!/bin/bash
#SBATCH --job-name=dm_preprocess
#SBATCH --partition=beta
#SBATCH --account=ny_chinmayh_datacomp
#SBATCH --qos=test
#SBATCH --nodes=1
#SBATCH --ntasks-per-node=1
#SBATCH --gres=gpu:b200:1
#SBATCH --cpus-per-task=32
#SBATCH --mem=200G
#SBATCH --time=00:40:00
#SBATCH --output=/mnt/home/bf996/logs/dm_preprocess_%j.out

# Preprocess/dry-run for densemixer Run 1: tokenize the full opencode dataset + WRITE the
# shared dataset_prepared_path sentinel (multi-node fast-path; without it the 2-node job
# deadlocks at dataset load). --debug dumps the loss-mask for the first examples so we can
# confirm assistant+<think> trained / user masked. Also dumps the RESOLVED axolotl config.
set -euxo pipefail
export IMG=/mnt/home/bf996/images/mega_final_dm.sqsh
export CFG=/mnt/home/bf996/scripts/densemixer_run1_opencode.yaml
export HF_HOME=/mnt/home/bf996/hf_cache

srun --nodes=1 --ntasks-per-node=1 --gres=gpu:b200:1 \
     --container-image="$IMG" --container-mount-home \
     bash -lc '
       set -euxo pipefail
       export PATH=/usr/local/bin:/usr/local/cuda/bin:/usr/bin:/bin; hash -r
       unset PYENV_ROOT PYENV_VERSION PYENV_SHELL || true
       unset PIP_CONSTRAINT || true
       export HF_HOME=/mnt/home/bf996/hf_cache
       export HF_HUB_OFFLINE=1 TRANSFORMERS_OFFLINE=1   # θ₀ + data are local; no hub calls
       export TOKENIZERS_PARALLELISM=false
       PY=/usr/bin/python
       $PY -c "import densemixer, axolotl; print(\"densemixer\", densemixer.__version__, \"| axolotl\", axolotl.__version__)"
       $PY -m axolotl.cli.preprocess "'"$CFG"'" --debug 2>&1 | tail -400
     '
echo "DM_PREPROCESS_DONE [$(date)]"
