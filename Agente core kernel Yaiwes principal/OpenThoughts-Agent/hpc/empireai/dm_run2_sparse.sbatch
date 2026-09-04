#!/bin/bash
#SBATCH --job-name=dm_run2_sparse
#SBATCH --partition=beta
#SBATCH --account=ny_chinmayh_datacomp
#SBATCH --qos=standard
#SBATCH --nodes=2
#SBATCH --ntasks-per-node=1
#SBATCH --gres=gpu:b200:4
#SBATCH --segment=2
#SBATCH --cpus-per-task=64
#SBATCH --mem=1000G
#SBATCH --time=12:00:00
#SBATCH --output=/mnt/home/bf996/logs/dm_run2_sparse_%j.out

# =============================================================================
# Run 2 (DenseMixer OFF = native sparse) — the CONTROL arm. Byte-identical to Run 1
# except dense_mixer:false + output_dir. Same θ₀/seed/dataset+order/seq_len/batch/packing.
# 2 nodes × 4 B200, ZeRO-3, bf16 + flash-attn, fp8:false. Image = mega_final_dm.sqsh.
# Inherits ALL of Run 1's fixes via dm_incontainer.sh: bond0 NCCL + node-local triton/inductor
# caches (ESTALE fix) + the sequential θ₀/arrow page-cache PRE-WARM (cold-node mmap fix).
# =============================================================================
set -euxo pipefail

export IMG=/mnt/home/bf996/images/mega_final_dm.sqsh
export CFG=/mnt/home/bf996/scripts/densemixer_run2_sparse_opencode.yaml
export HF_HOME=/mnt/home/bf996/hf_cache
export HF_HUB_OFFLINE=1 TRANSFORMERS_OFFLINE=1

SCONTROL=$(command -v scontrol || echo /cm/local/apps/slurm/current/bin/scontrol)
nodes=($($SCONTROL show hostnames "$SLURM_JOB_NODELIST"))
export MASTER_ADDR="${nodes[0]}"
export MASTER_PORT=29500
echo "MASTER_ADDR=$MASTER_ADDR nodes=${nodes[*]}"

srun --nodes=2 --ntasks-per-node=1 --gres=gpu:b200:4 \
     --container-image="$IMG" --container-mount-home \
     --container-env=HF_HOME,HF_HUB_OFFLINE,TRANSFORMERS_OFFLINE,CFG,MASTER_ADDR,MASTER_PORT \
     bash -lc 'CFG="'"$CFG"'" MASTER_ADDR="'"$MASTER_ADDR"'" MASTER_PORT="'"$MASTER_PORT"'" bash /mnt/home/bf996/scripts/dm_incontainer.sh'

echo "DM_RUN2_DONE [$(date)]"
