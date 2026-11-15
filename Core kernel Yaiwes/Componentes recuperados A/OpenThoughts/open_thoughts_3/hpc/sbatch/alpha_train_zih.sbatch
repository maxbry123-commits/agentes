#!/bin/bash
#SBATCH --nodes={num_nodes}          
#SBATCH --cpus-per-task={cpus_per_node}      
#SBATCH --gres=gpu:{gpus_per_node}
#SBATCH --time={time_limit}
#SBATCH --mem={mem_per_node}
#SBATCH --exclusive
#SBATCH --account={account}
#SBATCH --output={experiments_dir}/logs/%x_%j.out
#SBATCH --job-name={job_name}
#SBATCH --mail-type=END,TIME_LIMIT,FAIL
#SBATCH --mail-user=dcft-slurm-notifs-aaaap7wt363mcsgryaejj2o6dm@dogs-and-ml.slack.com

module load release/24.04  GCCcore/12.3.0
module load CUDA/12.1.1
module load NCCL/2.18.3-CUDA-12.1.1

export PATH=/usr/local/cuda-12/bin:$PATH
export LD_LIBRARY_PATH=/usr/local/cuda-12/lib64:$LD_LIBRARY_PATH

export FI_EFA_FORK_SAFE=1
export FI_LOG_LEVEL=1
export FI_EFA_USE_DEVICE_RDMA=1
export NCCL_NET_GDR_LEVEL="SYS"
export NCCL_NET_GDR_READ=1
export TORCH_NCCL_ASYNC_ERROR_HANDLING=1

export PYTHONFAULTHANDLER=1

export CUDA_LAUNCH_BLOCKING=0
export OMPI_MCA_mtl_base_verbose=1
export FI_EFA_ENABLE_SHM_TRANSFER=0
export FI_PROVIDER=efa
export FI_EFA_TX_MIN_CREDITS=64
export NCCL_TREE_THRESHOLD=0
export NCCL_DEBUG=INFO

export OUTLINES_CACHE_DIR="/tmp/.outlines"
export MASTER_ADDR=$(scontrol show hostnames "$SLURM_JOB_NODELIST" | head -n 1)
export MASTER_PORT=12802
export FORCE_TORCHRUN=1

export DCFT=/data/horse/ws/ryma833h-DCFT_Shared
source $DCFT/dcft_private/hpc/dotenv/alpha.env
source $DCFT/dcft_private/database/access.env
echo "Loading conda: $DCFT_PRIVATE_ACTIVATE_ENV"
$DCFT_PRIVATE_ACTIVATE_ENV
cd $DCFT_PRIVATE
export TRITON_CACHE_DIR=$DCFT/triton_cache
export PYTHONPATH=$DCFT_PRIVATE:$PYTHONPATH

# export TORCHELASTIC_MAX_REGISTRATION_RETRY_INTERVAL=60
# export TORCHELASTIC_RENDEZVOUS_TIMEOUT=600
# export TORCH_DISTRIBUTED_DEBUG=DETAIL

# PATHS
CONFIG={train_config_path_out}
OUTPUT_DIR={experiments_dir}
echo -e "CONFIG: $CONFIG\nOUTPUT_DIR: $OUTPUT_DIR"
TMP_DIR=$OUTPUT_DIR/tmp
mkdir -p $OUTPUT_DIR
mkdir -p $TMP_DIR

srun --ntasks={num_nodes} --nodes={num_nodes} --ntasks-per-node=1 bash -c '
  host=$(hostname)
  hostlist=($(scontrol show hostnames "$SLURM_JOB_NODELIST"))
  for i in "${!hostlist[@]}"; do
    if [[ "${hostlist[$i]}" == "$host" ]]; then
      node_rank=$i
      break
    fi
  done

  echo "Starting torchrun on $host with node_rank=$node_rank"
  torchrun \
    --nproc-per-node={gpus_per_node} \
    --nnodes={num_nodes} \
    --node_rank=$node_rank \
    --rdzv_backend=static \
    --rdzv_endpoint='$MASTER_ADDR:$MASTER_PORT' \
    dcft/train/llamafactory/src/train.py '$CONFIG'
'
