#!/usr/bin/env bash
# build_tpu_kaniko.sh — in-cluster kaniko build of the :tpu image.
#
# Adapted from build_gpu_rl_kaniko.sh for the TPU image, which is MUCH simpler:
# Dockerfile.tpu is single-stage (python:3.12-slim + apt + `uv sync` of the
# [datagen-tpu] resolve) with NO CUDA wheels / nvcc / WHEEL_SOURCE, so all of the
# gpu-rl wheelhouse machinery is stripped.
#
# Runs INSIDE an iris job whose task-image is docker.io/library/ubuntu:22.04
# (kaniko's executor is distroless / no bash, so it cannot be the task image
# directly). We crane-export the kaniko executor rootfs over / and run
# /kaniko/executor. See .agents/skills/build-gpu-rl-image-iris/SKILL.md.
#
# Required env (passed by the iris launch as -e):
#   DOCKER_USER_ID  ghcr user (penfever)
#   DOCKER_TOKEN    a GitHub PAT with write:packages (from `gh auth token`;
#                   NOT the Docker Hub dckr_pat_ in secrets.env)
#   GITSHA          OT-Agent commit sha for the immutable :tpu-<gitsha> tag
#
# PINNED-FIRST: this pushes ONLY the immutable :tpu-<gitsha> tag. The floating
# :tpu is promoted separately (crane tag) after smoke #22 verifies literals
# populate end-to-end, so a botched build cannot break other users' tpu jobs.
set -euxo pipefail

: "${DOCKER_USER_ID:?}"
: "${DOCKER_TOKEN:?}"
: "${GITSHA:?}"

# SINGLE_SNAPSHOT=0 (per-instruction layers) is the DEFAULT here: it dodges the
# un-pullable ~16 GB single-blob layer problem (containerd restarts the single-blob
# GET from 0 over the ghcr egress and dies), giving small independently-retriable
# layers. --compressed-caching=false writes layers to disk so multi-layer
# snapshotting does not blow up memory. Set SINGLE_SNAPSHOT=1 to collapse to one
# final layer (smaller image, but the un-pullable-layer risk).
SINGLE_SNAPSHOT="${SINGLE_SNAPSHOT:-0}"
if [ "$SINGLE_SNAPSHOT" = "1" ]; then SNAPSHOT_FLAG="--single-snapshot"; else SNAPSHOT_FLAG=""; fi

DOCKERFILE="${DOCKERFILE:-docker/Dockerfile.tpu}"
CACHE_REPO=ghcr.io/open-thoughts/openthoughts-agent/cache-tpu
DEST_PINNED=ghcr.io/open-thoughts/openthoughts-agent:tpu-${GITSHA}

# --- 1. fetch crane (static binary) ---
apt-get update -y && apt-get install -y --no-install-recommends ca-certificates curl tar
cd /tmp
CRANE_VER=v0.20.2
curl -fsSL "https://github.com/google/go-containerregistry/releases/download/${CRANE_VER}/go-containerregistry_Linux_x86_64.tar.gz" -o crane.tgz
tar -xzf crane.tgz crane
install -m 0755 crane /usr/local/bin/crane

# --- 2. crane-export the kaniko executor rootfs over / ---
crane export gcr.io/kaniko-project/executor:latest - | tar -xf - -C / || true

# --- 3. write the ghcr auth config AFTER the overlay (kaniko clobbers /kaniko otherwise) ---
export DOCKER_CONFIG=/kaniko/.docker
mkdir -p "$DOCKER_CONFIG"
# Disable `set -x` around the secret: under the script-wide `set -x` both the
# printf and the ${AUTH} heredoc expansion would echo the base64 ghcr PAT into
# the iris job logs. Re-enable tracing after.
{ set +x; } 2>/dev/null
AUTH=$(printf '%s:%s' "$DOCKER_USER_ID" "$DOCKER_TOKEN" | base64 | tr -d '\n')
cat > "$DOCKER_CONFIG/config.json" <<EOF
{"auths":{"ghcr.io":{"auth":"${AUTH}"}}}
EOF
unset AUTH
set -x

# --- 4. run kaniko (pinned tag ONLY; floating :tpu promoted after #22 verify) ---
exec /kaniko/executor \
  --context dir:///app \
  --dockerfile "${DOCKERFILE}" \
  --skip-unused-stages \
  $SNAPSHOT_FLAG \
  --compressed-caching=false \
  --cache=true \
  --cache-repo="${CACHE_REPO}" \
  --destination "${DEST_PINNED}"
