#!/usr/bin/env bash
#
# Build and push OpenThoughts Docker images to GitHub Container Registry (ghcr.io)
#
# Usage:
#   ./docker/build_and_push.sh              # Build and push all images (multi-platform)
#   ./docker/build_and_push.sh --build-only # Build without pushing (local platform only)
#   ./docker/build_and_push.sh gpu-1x       # Build/push specific image
#
# Prerequisites:
#   1. Docker installed and running with buildx support
#   2. Authenticated to ghcr.io:
#      echo $GITHUB_TOKEN | docker login ghcr.io -u YOUR_USERNAME --password-stdin
#
# Platforms:
#   Builds for both linux/amd64 (x86) and linux/arm64 (ARM, e.g., GH200)
#
# Architecture Note:
#   These images contain ONLY dependencies, not the actual source code.
#   Source code is synced at runtime via SkyPilot to /sky/workdir.
#   The cloud eval launcher sets PYTHONPATH=/sky/workdir to ensure synced
#   code takes precedence over any stubs in the image.
#
#   This design ensures:
#   - Code changes don't require rebuilding Docker images
#   - No stale code in the image causes import conflicts
#   - Smaller image sizes
#

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(dirname "$SCRIPT_DIR")"

# GitHub Container Registry settings
REGISTRY="ghcr.io"
ORG="open-thoughts"
IMAGE_NAME="openthoughts-agent"
IMAGE_BASE="${REGISTRY}/${ORG}/${IMAGE_NAME}"

# Default target platforms (amd64 for x86, arm64 for GH200/ARM).
# Overridden per-variant by platforms_for_variant() below.
PLATFORMS="linux/amd64,linux/arm64"

# Available image variants
# gpu-Nx: Standard images with N GPUs configured
# tpu:    Cloud TPU image (vLLM-TPU 0.20.0 + Harbor[daytona]); slice size is a
#         submit-time argument so we don't fan out to {1x,4x,8x}.
# (The gpu-rl RL image is built/pushed from MarinSkyRL — docker/Dockerfile.gpu-rl
#  + docker/build_gpu_rl_kaniko.sh there — NOT this script.)
VARIANTS=("gpu-1x" "gpu-4x" "gpu-8x" "tpu")

# Per-variant platform override. Cloud TPU host VMs are all linux/amd64,
# so the tpu image is built single-arch (avoids a wasted arm64 QEMU pass).
platforms_for_variant() {
    case "$1" in
        tpu)    echo "linux/amd64" ;;
        *)      echo "$PLATFORMS" ;;
    esac
}

# Parse arguments
BUILD=true
PUSH=true
SELECTED_VARIANTS=()

while [[ $# -gt 0 ]]; do
    case $1 in
        --build-only)
            PUSH=false
            shift
            ;;
        --push-only)
            echo "ERROR: --push-only not supported with multi-platform builds."
            echo "Multi-platform images must be built and pushed together."
            exit 1
            ;;
        --help|-h)
            echo "Usage: $0 [--build-only] [variant...]"
            echo ""
            echo "Options:"
            echo "  --build-only    Build images without pushing (local platform only)"
            echo ""
            echo "Variants: ${VARIANTS[*]}"
            echo ""
            echo "Examples:"
            echo "  $0                    # Build and push all (multi-platform)"
            echo "  $0 gpu-1x             # Build and push gpu-1x only"
            echo "  $0 --build-only       # Build all without pushing (local only)"
            echo ""
            echo "Platforms: ${PLATFORMS}"
            exit 0
            ;;
        gpu-*|tpu)
            SELECTED_VARIANTS+=("$1")
            shift
            ;;
        *)
            echo "Unknown option: $1"
            exit 1
            ;;
    esac
done

# Default to all variants if none selected
if [[ ${#SELECTED_VARIANTS[@]} -eq 0 ]]; then
    SELECTED_VARIANTS=("${VARIANTS[@]}")
fi

# Get git commit for tagging
GIT_SHA=$(git -C "$REPO_ROOT" rev-parse --short HEAD 2>/dev/null || echo "unknown")

echo "============================================"
echo "OpenThoughts Docker Build"
echo "============================================"
echo "Registry:  ${REGISTRY}"
echo "Image:     ${ORG}/${IMAGE_NAME}"
echo "Variants:  ${SELECTED_VARIANTS[*]}"
echo "Platforms: ${PLATFORMS}"
echo "Git SHA:   ${GIT_SHA}"
echo "Push:      ${PUSH}"
echo "============================================"

cd "$REPO_ROOT"

# Ensure buildx builder exists for multi-platform builds
BUILDER_NAME="openthoughts-builder"
if ! docker buildx inspect "$BUILDER_NAME" &>/dev/null; then
    echo ""
    echo ">>> Creating buildx builder for multi-platform support..."
    docker buildx create --name "$BUILDER_NAME" --use --bootstrap
else
    docker buildx use "$BUILDER_NAME"
fi

for variant in "${SELECTED_VARIANTS[@]}"; do
    dockerfile="docker/Dockerfile.${variant}"

    if [[ ! -f "$dockerfile" ]]; then
        echo "ERROR: Dockerfile not found: $dockerfile"
        exit 1
    fi

    image_tag="${IMAGE_BASE}:${variant}"
    image_tag_sha="${IMAGE_BASE}:${variant}-${GIT_SHA}"
    variant_platforms=$(platforms_for_variant "$variant")

    echo ""
    echo ">>> Building ${variant} (platforms: ${variant_platforms})..."

    if [[ "$PUSH" == "true" ]]; then
        # Multi-platform build and push (buildx requires --push for multi-platform)
        docker buildx build \
            --platform "$variant_platforms" \
            -f "$dockerfile" \
            -t "$image_tag" \
            -t "$image_tag_sha" \
            --push \
            .
        echo ">>> Built and pushed: ${image_tag} (platforms: ${variant_platforms})"
    else
        # Local build only (single platform - current machine's architecture)
        echo ">>> Building for local platform only (multi-platform requires --push)"
        docker buildx build \
            -f "$dockerfile" \
            -t "$image_tag" \
            -t "$image_tag_sha" \
            --load \
            .
        echo ">>> Built locally: ${image_tag}"
    fi
done

echo ""
echo "============================================"
echo "Done!"
echo ""
echo "Images available:"
for variant in "${SELECTED_VARIANTS[@]}"; do
    echo "  ${IMAGE_BASE}:${variant}  ($(platforms_for_variant "$variant"))"
done
echo "============================================"
