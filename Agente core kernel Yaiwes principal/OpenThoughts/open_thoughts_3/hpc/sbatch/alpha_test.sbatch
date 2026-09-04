#!/bin/bash
#SBATCH --nodes=4            # Use same number of nodes as your training job
#SBATCH --ntasks-per-node=1  # One task per node for this test
#SBATCH --cpus-per-task=4    # Reduced CPU count for simple test
#SBATCH --gres=gpu:1         # One GPU per node is sufficient for testing
#SBATCH --time=00:15:00      # Short time limit (15 min) for quick tests
#SBATCH --mem=16G            # Reduced memory requirements
#SBATCH --account=p_finetuning  # Your account
#SBATCH --output=nccl_test_%j.out
#SBATCH --job-name=nccl_test

# Load necessary modules
module load release/24.04 GCCcore/12.3.0
module load CUDA/12.1.1
module load NCCL/2.18.3-CUDA-12.1.1

# Set path variables
export PATH=/usr/local/cuda-12/bin:$PATH
export LD_LIBRARY_PATH=/usr/local/cuda-12/lib64:$LD_LIBRARY_PATH

# Basic network configuration - keep minimal for testing
export NCCL_DEBUG=INFO
export NCCL_IB_DISABLE=0
export NCCL_SOCKET_IFNAME=ib0
export NCCL_IB_HCA=mlx5_0:1,mlx5_2:1,mlx5_4:1,mlx5_6:1

# Set master node for distributed test
export MASTER_ADDR=$(scontrol show hostnames "$SLURM_JOB_NODELIST" | head -n 1)
export MASTER_PORT=12802

# First run basic network connectivity tests
echo "===== NETWORK CONNECTIVITY TESTS ====="
HOSTLIST=$(scontrol show hostnames "$SLURM_JOB_NODELIST")
for host in $HOSTLIST; do
  echo "Pinging $host from $(hostname)..."
  ping -c 2 $host
  
  echo "Testing SSH to $host..."
  ssh -o BatchMode=yes -o ConnectTimeout=5 $host "echo SSH to $host successful" || echo "SSH to $host FAILED"
done

# Run network interface checks on each node
echo -e "\n===== NETWORK INTERFACE TESTS ====="
srun --nodes=$SLURM_JOB_NUM_NODES --ntasks=$SLURM_JOB_NUM_NODES bash -c '
  echo "=== Node: $(hostname) ==="
  echo "InfiniBand devices:"
  if command -v ibstat &> /dev/null; then
    ibstat -l || echo "ibstat command not found"
  else
    echo "ibstat not available"
  fi
  
  echo "Network interfaces:"
  ip a | grep -E "ib|eth" || echo "No ib/eth interfaces found"
  
  echo "Active RDMA devices:"
  ls -la /dev/infiniband/ 2>/dev/null || echo "No RDMA devices found"
'

# Create and run a simple NCCL test using PyTorch
echo -e "\n===== CREATING PYTORCH NCCL TEST ====="
cat > nccl_test.py << 'EOF'
import os
import torch
import torch.distributed as dist
import torch.multiprocessing as mp
import time

def run_test():
    # Get rank and world size from environment
    rank = int(os.environ['SLURM_PROCID'])
    world_size = int(os.environ['SLURM_NTASKS'])
    local_rank = int(os.environ['SLURM_LOCALID'])
    
    # Initialize process group
    print(f"[{rank}] Initializing process group with backend=nccl")
    start = time.time()
    dist.init_process_group(
        backend='nccl',
        init_method=f"env://",
        world_size=world_size,
        rank=rank
    )
    init_duration = time.time() - start
    print(f"[{rank}] Process group initialization took {init_duration:.2f} seconds")
    
    # Print device info
    device = torch.device(f"cuda:{local_rank}")
    print(f"[{rank}] Using device: {torch.cuda.get_device_name(device)}")
    
    # Create some data
    tensor_size = 10_000_000  # 10M elements (~40MB)
    data = torch.randn(tensor_size, device=device)
    print(f"[{rank}] Created tensor of size {tensor_size} on {device}")
    
    # Barrier to synchronize all processes
    dist.barrier()
    if rank == 0:
        print("\n===== All processes reached barrier, starting all-reduce test =====\n")
    dist.barrier()
    
    # Run all-reduce
    for i in range(5):  # Run 5 iterations
        start = time.time()
        dist.all_reduce(data)
        torch.cuda.synchronize()
        duration = time.time() - start
        bandwidth = (tensor_size * 4 * 2 * (world_size - 1) / world_size) / duration / (1024**3)  # GB/s
        print(f"[{rank}] All-reduce iteration {i}: {duration:.4f} seconds, {bandwidth:.2f} GB/s")
        dist.barrier()
        time.sleep(0.5)  # Small delay between iterations
    
    # Test point-to-point communication with the next rank
    next_rank = (rank + 1) % world_size
    prev_rank = (rank - 1 + world_size) % world_size
    
    small_tensor = torch.ones(1000000, device=device) * rank
    
    if rank % 2 == 0:
        # Even ranks send then receive
        print(f"[{rank}] Sending to rank {next_rank}")
        dist.send(small_tensor, dst=next_rank)
        print(f"[{rank}] Receiving from rank {prev_rank}")
        dist.recv(small_tensor, src=prev_rank)
    else:
        # Odd ranks receive then send
        print(f"[{rank}] Receiving from rank {prev_rank}")
        dist.recv(small_tensor, src=prev_rank)
        print(f"[{rank}] Sending to rank {next_rank}")
        dist.send(small_tensor, dst=next_rank)
    
    print(f"[{rank}] Point-to-point communication test passed")
    
    # Clean up
    dist.destroy_process_group()
    print(f"[{rank}] Process group destroyed, test complete")

if __name__ == "__main__":
    run_test()
EOF

echo -e "\n===== RUNNING PYTORCH NCCL TEST ====="
srun --nodes=$SLURM_JOB_NUM_NODES --ntasks=$SLURM_JOB_NUM_NODES --gres=gpu:1 python nccl_test.py

# Optional: If the nccl-tests package is available on your cluster, use it
echo -e "\n===== CHECKING FOR NCCL-TESTS ====="
NCCL_TESTS_PATH="/opt/nccl-tests/build"  # Adjust path as needed

if [ -d "$NCCL_TESTS_PATH" ]; then
    echo "Found NCCL tests at $NCCL_TESTS_PATH, running all_reduce_perf"
    srun --nodes=$SLURM_JOB_NUM_NODES --ntasks-per-node=1 --gres=gpu:1 \
        $NCCL_TESTS_PATH/all_reduce_perf -b 8 -e 128M -f 2 -g 1
else
    echo "NCCL tests not found at $NCCL_TESTS_PATH"
    echo "If available elsewhere, run: srun --nodes=$SLURM_JOB_NUM_NODES --ntasks-per-node=1 --gres=gpu:1 /path/to/all_reduce_perf -b 8 -e 128M -f 2 -g 1"
fi

echo -e "\n===== TEST COMPLETE ====="