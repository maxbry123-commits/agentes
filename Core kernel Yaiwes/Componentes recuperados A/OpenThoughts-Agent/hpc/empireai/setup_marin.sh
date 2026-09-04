#!/usr/bin/env bash
# Runs INSIDE a CUDA-13 arm64 base (via build_image_enroot.sh) to add Marin/Levanter + jax[cuda13].
# Mirrors Dockerfile.marin-aarch64. jax[cuda13]==0.9.2 is the Blackwell/B200 runtime (#5427/#5428).
set -euxo pipefail
export DEBIAN_FRONTEND=noninteractive
apt-get update && apt-get install -y --no-install-recommends git curl ca-certificates \
    python3 python3-pip python3-venv build-essential
curl -LsSf https://astral.sh/uv/install.sh | sh
export PATH="/root/.local/bin:$PATH"
MARIN_REF="${MARIN_REF:-main}"   # pin a commit >= PR #5428 (CUDA-13 gpu extra) once validated
cd /opt
git clone https://github.com/marin-community/marin.git
cd marin && git checkout "$MARIN_REF"
uv venv /opt/venv && . /opt/venv/bin/activate
uv pip install "jax[cuda13]==0.9.2"
uv pip install -e lib/levanter -e lib/marin
python -c "import jax; print('jax', jax.__version__, jax.devices())"
