#!/usr/bin/env bash
# Phase 0 — validate the container chain on Empire AI Beta (B200 NVL72).
# Proves: Pyxis+Enroot pull/import works, GPU injection works, torch sees Blackwell sm_100.
#
# Run from the beta LOGIN node (module env loaded via login shell), NOT inside a container:
#   ssh -o BatchMode=yes EmpireAI_Beta "bash -lc 'EMPIREAI_ACCT=<acct> bash ~/empireai/phase0_smoke.sh'"
#
# REQUIRES a valid SLURM account association (EMPIREAI_ACCT). As of 2026-07-01 SU charging is live
# and bf996 has none yet -> this WILL fail with "Invalid account or account/partition combination"
# until an admin associates the user. See README.md.
set -uo pipefail

IMG="${EMPIREAI_IMG:-nvcr.io/nvidia/pytorch:26.06-py3}"   # multi-arch, has linux/arm64, CUDA>=12.8
ACCT="${EMPIREAI_ACCT:?set EMPIREAI_ACCT=<slurm account> (e.g. nyu_beta_test)}"
QOS="${EMPIREAI_QOS:-test}"
ACCT_FLAGS="-A ${ACCT} --qos=${QOS}"

echo "=== login host / arch ==="; hostname; uname -m
echo "=== image: $IMG   account: $ACCT   qos: $QOS ==="

echo "=== [1/2] nvidia-smi -L on 4x B200 (Pyxis pulls+imports the image on the compute node) ==="
srun -p beta $ACCT_FLAGS --gpus-per-node=4 -N1 -t 20 \
  --container-image="$IMG" \
  bash -lc 'echo "in-container arch: $(uname -m)"; nvidia-smi -L'

echo "=== [2/2] torch Blackwell check on 1x B200 ==="
srun -p beta $ACCT_FLAGS --gpus-per-node=1 -N1 -t 15 \
  --container-image="$IMG" \
  python -c 'import torch; \
print("torch", torch.__version__, "cuda", torch.version.cuda); \
print("device", torch.cuda.get_device_name(0), "capability", torch.cuda.get_device_capability(0)); \
x=torch.randn(4096,4096,device="cuda"); y=(x@x).sum(); torch.cuda.synchronize(); \
print("matmul_ok", bool(y.abs()>0), "sm100_expected=(10, 0)")'

echo "=== PASS CRITERIA: device name contains B200, capability == (10, 0), matmul_ok True ==="
