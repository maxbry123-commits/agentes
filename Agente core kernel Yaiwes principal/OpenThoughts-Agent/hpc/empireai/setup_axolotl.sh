#!/usr/bin/env bash
# Runs INSIDE the NGC pytorch arm64 base (via build_image_enroot.sh) to add Axolotl.
# Mirrors Dockerfile.axolotl-aarch64. Keeps the base's Blackwell-built torch (constraint pin).
set -euxo pipefail
python -m pip install --upgrade pip packaging ninja
TORCH_V="$(python -c 'import torch;print(torch.__version__.split("+")[0])')"
printf 'torch==%s\n' "$TORCH_V" > /tmp/torch-constraint.txt
pip install --no-build-isolation -c /tmp/torch-constraint.txt \
    "axolotl[deepspeed]" \
    "transformers>=4.46" "datasets" "accelerate" "peft" "trl" "sentencepiece" "bitsandbytes"
python -c "import axolotl, transformers, torch; print('axolotl OK; torch', torch.__version__, 'cuda', torch.version.cuda)"
