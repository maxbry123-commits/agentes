"""Central configuration for the tokenizer-visualization deliverable.

Model IDs are kept here as clearly-marked constants so they are trivial to swap
if the chosen repos ever disappear from the Hugging Face Hub.
"""

from __future__ import annotations

import os
from pathlib import Path

# --------------------------------------------------------------------------- #
# MODEL IDS
# --------------------------------------------------------------------------- #
INSTRUCT_MODEL_ID = os.environ.get("TOKVIZ_INSTRUCT_MODEL", "Qwen/Qwen3.5-2B")
BASE_MODEL_ID = os.environ.get("TOKVIZ_BASE_MODEL", "Qwen/Qwen3.5-2B-Base")

# --------------------------------------------------------------------------- #
# Generation / runtime settings
# --------------------------------------------------------------------------- #
# A 2B model on CPU/MPS is fine for short generations. Keep new tokens modest so
# the end-to-end chat half finishes quickly.
MAX_NEW_TOKENS = int(os.environ.get("TOKVIZ_MAX_NEW_TOKENS", "200"))
# Thinking-ON (enable_thinking=True) output is longer: the model emits a
# <think>...</think> reasoning block BEFORE the answer. Give the instruct chat
# path a bigger (but still bounded) budget so the think block + answer are both
# captured. The shim also honours a max in this range.
MAX_NEW_TOKENS_INSTRUCT = int(os.environ.get("TOKVIZ_MAX_NEW_TOKENS_INSTRUCT", "2048"))
DO_SAMPLE = False  # deterministic greedy decoding for reproducible HTML


# Torch device preference: MPS on Apple Silicon, else CPU.
def pick_device() -> str:
    try:
        import torch

        if torch.backends.mps.is_available():
            return "mps"
    except Exception:
        pass
    return "cpu"


# --------------------------------------------------------------------------- #
# Paths
# --------------------------------------------------------------------------- #
HERE = Path(__file__).resolve().parent
# Outputs land in the foundation_models tree (overridable via TOKVIZ_OUTPUT_DIR).
# Note: the *scripts* live under scripts/analysis/tokviz/, but the generated HTML
# is written to this foundation_models path.
OUTPUT_DIR = Path(
    os.environ.get(
        "TOKVIZ_OUTPUT_DIR",
        "/Users/benjaminfeuer/Documents/foundation_models/Qwen/qwen3_5_literals/output",
    )
)
REPOS_DIR = HERE / "repos"
SHIM_LOG = HERE / "shim_prompts.jsonl"  # OpenAI shim logs every templated prompt here

OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
REPOS_DIR.mkdir(parents=True, exist_ok=True)

# --------------------------------------------------------------------------- #
# OpenAI-compatible shim
# --------------------------------------------------------------------------- #
SHIM_HOST = "127.0.0.1"
SHIM_PORT = int(os.environ.get("TOKVIZ_SHIM_PORT", "8123"))


# --------------------------------------------------------------------------- #
# Chat-half prompts (5 arbitrary user queries, hardcoded)
# --------------------------------------------------------------------------- #
CHAT_PROMPTS = [
    "What is the capital of France, and why is it famous?",
    "Write a haiku about a tab\tcharacter and a newline.",
    "Explain in one sentence what a byte-level BPE tokenizer does.",
    "Translate 'good morning' into Japanese and German.",
    "List three prime numbers between 10 and 20.",
]
