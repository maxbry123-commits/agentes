#!/bin/bash
# In-container multi-node launcher for densemixer Run 1 (one task per node; srun ntasks-per-node=1).
# torchrun spawns the 4 local ranks; static rendezvous on $MASTER_ADDR. axolotl SFT lives in the
# container's SYSTEM python (/usr/bin/python). Reads $CFG / $MASTER_ADDR / $MASTER_PORT from the env.
# Based on the validated ~/scripts/stage3_incontainer.sh (bond0 NCCL) + node-local WRITE caches.
set -euxo pipefail

# --container-mount-home leaks host ~/.pyenv onto PATH -> sanitize so /usr/bin/python wins.
export PATH=/usr/local/bin:/usr/local/cuda/bin:/usr/bin:/bin
hash -r
unset PYENV_ROOT PYENV_VERSION PYENV_SHELL || true
unset PIP_CONSTRAINT || true
export NCCL_DEBUG=INFO

# ⚠ MULTI-NODE NCCL BOOTSTRAP FIX (VALIDATED job 31604): pin bond0 (the routable 10.10.10.0/25
# inter-node iface); the 100.126.x IPoIB net is an unroutable-bootstrap trap. IB/MNNVL carry data.
export NCCL_SOCKET_IFNAME=bond0
export GLOO_SOCKET_IFNAME=bond0
export NCCL_SOCKET_FAMILY=AF_INET
export TOKENIZERS_PARALLELISM=false
export HF_HUB_ENABLE_HF_TRANSFER=0

# ⚠ NODE-LOCAL per-rank WRITE caches (fix for job 31689). A Triton/Inductor kernel JIT-compiles at
# the first training step; with the cache on the shared HOME/VAST-NFS (`~/.triton`), all 8 ranks
# race on `__triton_launcher.so` -> NFS "Stale file handle" (ESTALE) -> InductorError -> rank crash.
# Route triton/inductor/xdg/tmp to node-local /tmp so ranks don't contend on NFS (same remedy as the
# axolotl multi-node ENOLCK/ESTALE dataset-cache gotcha).
CACHE=/tmp/${USER:-bf996}/dmcache_${SLURM_JOB_ID:-nojob}
mkdir -p "$CACHE/triton" "$CACHE/inductor" "$CACHE/xdg" "$CACHE/tmp"
export TRITON_CACHE_DIR="$CACHE/triton"
export TRITON_HOME="$CACHE/triton"
export TORCHINDUCTOR_CACHE_DIR="$CACHE/inductor"
export XDG_CACHE_HOME="$CACHE/xdg"
export TMPDIR="$CACHE/tmp"

# ⚠ PAGE-CACHE PRE-WARM (fix for job 31693). On a COLD-cache node the 8 ranks concurrently
# mmap-PAGE-FAULT the 60 GB θ₀ from VAST-NFS at ~7 MB/s (random 4 KB faults, no readahead),
# vs 1 GB/s sequential — model load crawls for hours, GPUs 0%. (Earlier runs were fast ONLY
# because they reused nodes b2-16/18 whose page cache was already warm.) A one-shot SEQUENTIAL
# pre-read per node warms the node RAM so the ranks' mmap faults hit cache. Runs once per node
# (ntasks-per-node=1), before torchrun spawns the 4 local ranks. Nodes have ~1.5 TB RAM.
echo "=== [$(date)] page-cache pre-warm: theta0 + prepared arrow ==="
time cat /mnt/home/bf996/experiments/densemixer/theta0/*.safetensors > /dev/null 2>&1 || true
time cat /mnt/home/bf996/experiments/densemixer/prepared/run1/*/*.arrow > /dev/null 2>&1 || true
echo "=== [$(date)] pre-warm done ==="

PY=/usr/bin/python
echo "NODE_RANK=${SLURM_PROCID} HOST=$(hostname) MASTER=${MASTER_ADDR}:${MASTER_PORT} CFG=${CFG} TRITON_CACHE_DIR=${TRITON_CACHE_DIR}"
$PY -c "import torch; print('torch', torch.__version__, 'cuda', torch.version.cuda, 'gpus', torch.cuda.device_count(), 'cap', torch.cuda.get_device_capability(0))"
$PY -c "import axolotl, densemixer; print('axolotl', getattr(axolotl,'__version__','?'), '| densemixer', densemixer.__version__)"

$PY -m torch.distributed.run \
    --nnodes=2 --nproc_per_node=4 --node_rank="${SLURM_PROCID}" \
    --master_addr="${MASTER_ADDR}" --master_port="${MASTER_PORT}" \
    -m axolotl.cli.train "${CFG}"
