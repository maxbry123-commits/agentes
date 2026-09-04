#!/usr/bin/env bash
# Import a docker/NGC image into a persistent enroot .sqsh, ONCE, then reuse via
# --container-image=/path/to/img.sqsh (avoids re-pulling on every job).
#
# enroot must run on a COMPUTE node (bare enroot on the login node fails:
# "mkdir /var/lib/enroot: Permission denied"). So we drive it through srun.
#
# Usage:
#   ssh -o BatchMode=yes EmpireAI_Beta "bash -lc 'EMPIREAI_ACCT=<acct> \
#     bash ~/empireai/enroot_import.sh nvcr.io#nvidia/pytorch:26.06-py3 \
#     /ddn/client_validation/bf996/img/pytorch-26.06.sqsh'"
#
# NOTE the enroot URI form uses '#' between host and repo: docker://nvcr.io#nvidia/pytorch:26.06-py3
# (Pyxis --container-image accepts the '/' form; the enroot CLI wants the '#' form.)
set -euo pipefail

URI="${1:?docker://<host>#<repo>:<tag>  e.g. nvcr.io#nvidia/pytorch:26.06-py3}"
OUT="${2:?output .sqsh path (HOME <=100GB, or a self-made dir under /ddn/client_validation)}"
ACCT="${EMPIREAI_ACCT:?set EMPIREAI_ACCT=<slurm account>}"
QOS="${EMPIREAI_QOS:-test}"

mkdir -p "$(dirname "$OUT")"

# Import runs single-node, no GPU needed for the import itself; give it time (multi-GB pull).
srun -p beta -A "$ACCT" --qos="$QOS" -N1 -t 40 --gpus-per-node=0 \
  bash -lc "set -x; enroot import -o '$OUT' 'docker://${URI}'; ls -lh '$OUT'"

echo "=== imported -> $OUT ; reuse with --container-image=$OUT ==="
