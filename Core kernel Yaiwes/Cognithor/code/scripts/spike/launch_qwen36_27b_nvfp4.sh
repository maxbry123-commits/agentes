#!/usr/bin/env bash
# Launch Qwen3.6-27B-NVFP4 on cu130-nightly for RTX 5090 SM120.
#
# Critical flags:
#  --enforce-eager       reduce CUDA-graph VRAM during init
#  --gpu-memory-utilization 0.88   leave 3-4 GB headroom on 32 GB RTX 5090
#  --max-model-len 32768 enough for 32 video frames at 1000 tokens each
#  --reasoning-parser qwen3       required for Qwen3.6 thinking parse
#  --trust-remote-code   required for Qwen3NextGatedDeltaNet custom arch
#  --media-io-kwargs video.num_frames=-1  let video processor decide
#
# NVFP4 backend is auto-detected by vLLM on SM120 (falls back to flashinfer-cutlass).

set -euo pipefail

NAME=vllm-spike
IMAGE=vllm/vllm-openai:cu130-nightly
MODEL="mmangkad/Qwen3.6-27B-NVFP4"
PORT=8765

docker rm -f "$NAME" 2>/dev/null || true

docker run -d --name "$NAME" --gpus all \
  --add-host host.docker.internal:host-gateway \
  -v cognithor-spike-hf-cache:/root/.cache/huggingface \
  -p "$PORT":8000 \
  "$IMAGE" \
  --model "$MODEL" \
  --max-model-len 16384 \
  --max-num-seqs 2 \
  --max-num-batched-tokens 2048 \
  --gpu-memory-utilization 0.94 \
  --cpu-offload-gb 4 \
  --enforce-eager \
  --reasoning-parser qwen3 \
  --trust-remote-code \
  --media-io-kwargs '{"video": {"num_frames": -1}}'

echo "launched $NAME on port $PORT with image $IMAGE"
