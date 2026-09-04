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

module load release/24.04  GCCcore/12.3.0
module load CUDA/12.1.1
module load NCCL/2.18.3-CUDA-12.1.1

export PATH=/usr/local/cuda-12/bin:$PATH
export LD_LIBRARY_PATH=/usr/local/cuda-12/lib64:$LD_LIBRARY_PATH

# Network configuration
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

# Set master node for distributed training
export MASTER_ADDR=$(scontrol show hostnames "$SLURM_JOB_NODELIST" | head -n 1)
export MASTER_PORT=12802
export FORCE_TORCHRUN=1

# Add additional networking settings for multi-node
export NCCL_SOCKET_IFNAME=efa0
export NCCL_IB_DISABLE=0
export NCCL_IB_GID_INDEX=3
export NCCL_IB_HCA=mlx5_0:1,mlx5_2:1,mlx5_4:1,mlx5_6:1
export NCCL_ALGO=Ring
export NCCL_DEBUG_SUBSYS=ALL
export NCCL_PROTO=Simple
export UCX_TLS=tcp
export UCX_NET_DEVICES=mlx5_0:1

# Load environment variables
source /data/horse/ws/ryma833h-DCFT_Shared/dcft_private/hpc/dotenv/alpha.env
source /data/horse/ws/ryma833h-DCFT_Shared/dcft_private/database/access.env

echo "Loading conda: $DCFT_PRIVATE_ACTIVATE_ENV"
$DCFT_PRIVATE_ACTIVATE_ENV

cd $DCFT_PRIVATE
export TRITON_CACHE_DIR=$DCFT/triton_cache
export PYTHONPATH=$DCFT_PRIVATE:$PYTHONPATH

# Uncomment if needed
# export TORCHELASTIC_MAX_REGISTRATION_RETRY_INTERVAL=60
# export TORCHELASTIC_RENDEZVOUS_TIMEOUT=600
# export TORCH_DISTRIBUTED_DEBUG=DETAIL

# PATHS
CONFIG={train_config_path_out}
OUTPUT_DIR={experiments_dir}
echo -e "CONFIG: $CONFIG\nOUTPUT_DIR: $OUTPUT_DIR"

# Required for multi-node training - ensure environment is completely propagated
export PYTHONUNBUFFERED=1
export SLURM_PROPAGATE_PRIO=1

# Create a unique directory for the current job's store for distributed coordination
DIST_STORE_DIR=$TMP_DIR/dist_store_$SLURM_JOB_ID
mkdir -p $DIST_STORE_DIR
export TORCH_DISTRIBUTED_STORE_DIR=$DIST_STORE_DIR

# Launch distributed training with more robust node rank detection
srun --ntasks={num_nodes} --nodes={num_nodes} --ntasks-per-node=1 bash -c "
  # More robust way to determine node_rank for multi-node setup
  hostnames=(\$(scontrol show hostnames \$SLURM_JOB_NODELIST))
  host=\$(hostname -s)
  
  # Find position of this host in the array
  node_rank=0
  for (( i=0; i<\${#hostnames[@]}; i++ )); do
    if [[ \"\$host\" == \"\${hostnames[\$i]}\" ]]; then
      node_rank=\$i
      break
    fi
  done
  
  # Print debug information
  echo \"Master address: $MASTER_ADDR\"
  echo \"Master port: $MASTER_PORT\"
  echo \"Starting torchrun on \$host (node_rank=\$node_rank) out of {num_nodes} nodes\"
  echo \"Full hostlist: \${hostnames[@]}\"
  
  # Run torchrun with explicit parameters
  torchrun \\
    --nnodes={num_nodes} \\
    --nproc_per_node={gpus_per_node} \\
    --node_rank=\$node_rank \\
    --master_addr=\"$MASTER_ADDR\" \\
    --master_port=$MASTER_PORT \\
    --rdzv_backend=c10d \\
    --rdzv_endpoint=\"$MASTER_ADDR:$MASTER_PORT\" \\
    --rdzv_id=\$SLURM_JOB_ID \\
    --max_restarts=0 \\
    dcft/train/llamafactory/src/train.py $CONFIG
"