#!/bin/bash
#SBATCH --job-name=dm_run1_dense
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
#SBATCH --output=/mnt/home/bf996/logs/dm_run1_dense_%j.out

# =============================================================================
# Run 1 (DenseMixer ON) — Qwen3-30B-A3B-Thinking-2507 SFT on opencode traces.
# 2 nodes × 4 B200 = 8 GPUs, DDP via torch.distributed.run static rendezvous,
# ZeRO-3, bf16 + flash-attn (job 31623 healthy), fp8:false, packing, densemixer.
# Image = mega_final_dm.sqsh (densemixer==1.0.1 baked into the SFT system python).
# Uses the repo-tracked in-container script hpc/empireai/dm_incontainer.sh (bond0 NCCL
# bootstrap + MNNVL, job 31604) + NODE-LOCAL triton/inductor caches (fix for the job-31689
# NFS "Stale file handle" ESTALE race on the shared ~/.triton cache), with CFG pointed at Run 1.
# Prereq: dm_preprocess wrote the shared dataset_prepared_path sentinel (else the
# multi-node dataset load deadlocks).
# =============================================================================
set -euxo pipefail

export IMG=/mnt/home/bf996/images/mega_final_dm.sqsh
export CFG=/mnt/home/bf996/scripts/densemixer_run1_opencode.yaml
export HF_HOME=/mnt/home/bf996/hf_cache
export HF_HUB_OFFLINE=1 TRANSFORMERS_OFFLINE=1   # θ₀ + data + prepared set all local

# head node for the static rendezvous (full path — Bright module env gotcha)
SCONTROL=$(command -v scontrol || echo /cm/local/apps/slurm/current/bin/scontrol)
nodes=($($SCONTROL show hostnames "$SLURM_JOB_NODELIST"))
export MASTER_ADDR="${nodes[0]}"
export MASTER_PORT=29500
echo "MASTER_ADDR=$MASTER_ADDR nodes=${nodes[*]}"

# one container task per node; dm_incontainer.sh spawns the 4 local ranks via torchrun.
srun --nodes=2 --ntasks-per-node=1 --gres=gpu:b200:4 \
     --container-image="$IMG" --container-mount-home \
     --container-env=HF_HOME,HF_HUB_OFFLINE,TRANSFORMERS_OFFLINE,CFG,MASTER_ADDR,MASTER_PORT \
     bash -lc 'CFG="'"$CFG"'" MASTER_ADDR="'"$MASTER_ADDR"'" MASTER_PORT="'"$MASTER_PORT"'" bash /mnt/home/bf996/scripts/dm_incontainer.sh'

echo "DM_RUN1_DONE [$(date)]"
