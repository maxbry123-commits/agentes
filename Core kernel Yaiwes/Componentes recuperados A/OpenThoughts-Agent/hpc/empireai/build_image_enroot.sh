#!/usr/bin/env bash
# Materialize a custom image into an enroot .sqsh on beta WITHOUT a docker daemon
# (beta compute nodes have enroot but no dockerd). Pattern: import base -> create rw container ->
# run a setup script inside it -> export a new .sqsh. This is how you "build" the Axolotl / Marin
# images from their Dockerfile.* recipes here (translate the RUN lines into $SETUP).
#
# Usage (drive from the login node; runs on a compute node via srun):
#   ssh -o BatchMode=yes EmpireAI_Beta "bash -lc 'EMPIREAI_ACCT=<acct> \
#     bash ~/empireai/build_image_enroot.sh \
#       nvcr.io#nvidia/pytorch:26.06-py3 \
#       ~/empireai/setup_axolotl.sh \
#       /ddn/client_validation/bf996/img/axolotl-aarch64.sqsh'"
#
# $SETUP is a shell script executed INSIDE the container as root (the pip block from the Dockerfile).
set -euo pipefail
BASE_URI="${1:?base enroot URI, e.g. nvcr.io#nvidia/pytorch:26.06-py3}"
SETUP="${2:?path to setup script run inside the container (the Dockerfile RUN block)}"
OUT="${3:?output .sqsh path}"
ACCT="${EMPIREAI_ACCT:?set EMPIREAI_ACCT=<slurm account>}"
QOS="${EMPIREAI_QOS:-standard}"     # build can exceed the 6h test-qos window; use standard
NAME="build_$$"

mkdir -p "$(dirname "$OUT")"
SETUP_ABS="$(readlink -f "$SETUP")"

# GPU may help if the setup compiles CUDA ext (flash-attn); request 1 to be safe.
srun -p beta -A "$ACCT" --qos="$QOS" -N1 -t 90 --gpus-per-node=1 --cpus-per-task=32 \
  bash -lc "set -euxo pipefail; \
    enroot import -o /tmp/${NAME}.sqsh 'docker://${BASE_URI}'; \
    enroot create -n ${NAME} /tmp/${NAME}.sqsh; \
    enroot start --root --rw -m ${SETUP_ABS}:/tmp/setup.sh ${NAME} bash -lc 'bash /tmp/setup.sh'; \
    enroot export -o '${OUT}' ${NAME}; \
    enroot remove -f ${NAME}; rm -f /tmp/${NAME}.sqsh; \
    ls -lh '${OUT}'"

echo "=== built -> $OUT ; use --container-image=$OUT ==="
