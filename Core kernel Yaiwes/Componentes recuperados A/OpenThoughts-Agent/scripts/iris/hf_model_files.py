#!/usr/bin/env python3
"""Which files of a HuggingFace model repo a mirror should copy.

Shared by every ``scripts/iris/mirror_*`` route that reads from the Hub, so the GCS
and S3 mirrors cannot drift apart. Both previously carried their own byte-identical
copy of the selection tuple, and both therefore carried the same gap.

WHY A DENYLIST, NOT AN ALLOWLIST
--------------------------------
This module used to be an allowlist of known-good suffixes
(``.safetensors``/``.json``/``.txt``/``.py``/``.model``). That shape has the wrong
failure mode. A model repo file nobody thought of is silently DROPPED, and the
mirror still reports success — so the break surfaces much later, as a model that
loads with a missing piece.

That is not hypothetical. ``chat_template.jinja`` is not matched by any of those
suffixes, so mirroring a repo that ships one produced a model with **no chat
template** and no warning. For an RL run the rendered prompt is load-bearing, so the
result is a silently-wrong training run rather than a loud failure.

Inverting the default makes the cheap outcome the automatic one: an unrecognized
file is copied (costing a few KB) rather than dropped (costing a broken model). The
denylist stays small and only names things that are either genuinely useless to a
loader or genuinely expensive to copy.

THE ONE EXPENSIVE CASE
----------------------
Duplicate-format weights. A repo shipping both ``model.safetensors`` and
``pytorch_model.bin`` holds the same tensors twice, and copying both doubles a
125 GiB mirror for nothing. Those formats are excluded **only when the repo also
ships safetensors** — a repo whose only weights are ``.bin`` still mirrors, because
dropping them would leave no weights at all.
"""

from __future__ import annotations

from collections.abc import Sequence

# Weight formats that duplicate safetensors. Excluded ONLY when the repo also ships
# safetensors; see the module docstring. `.onnx_data` is the external-tensor sidecar
# ONNX writes next to a `.onnx` graph and is the large half of that pair.
DUPLICATE_WEIGHT_SUFFIXES = (
    ".bin",
    ".pt",
    ".pth",
    ".h5",
    ".ckpt",
    ".msgpack",
    ".onnx",
    ".onnx_data",
    ".tflite",
    ".gguf",
)

# Never useful to a loader, at any size.
EXCLUDED_SUFFIXES = (
    ".png",
    ".jpg",
    ".jpeg",
    ".gif",
    ".svg",
    ".webp",
    ".bmp",
    ".ico",
    ".mp4",
    ".webm",
    ".wav",
    ".mp3",
    ".pdf",
    ".zip",
    ".tar",
    ".tgz",
    ".gz",
    ".7z",
)

# Repository plumbing rather than model content.
EXCLUDED_BASENAMES = (
    ".gitattributes",
    ".gitignore",
    ".gitmodules",
    ".DS_Store",
)

# Anything under these prefixes is VCS or CI metadata, never model content.
EXCLUDED_PATH_PREFIXES = (
    ".git/",
    ".github/",
    ".cache/",
)

SAFETENSORS_SUFFIX = ".safetensors"


def _basename(path: str) -> str:
    return path.rsplit("/", 1)[-1]


def is_metadata(path: str) -> bool:
    """True for the small config/tokenizer/template files, as opposed to weight shards.

    Used only for upload ORDER: metadata goes first so an interrupted mirror still
    leaves a readable, if weightless, repo at the destination.
    """
    return not path.endswith(SAFETENSORS_SUFFIX)


def select_model_files(filenames: Sequence[str]) -> list[str]:
    """Return the repo files worth mirroring, ordered metadata-first.

    Args:
        filenames: Every repo-relative path in the model repo, e.g. the result of
            ``HfApi().list_repo_files(repo_id, repo_type="model")``.

    Returns:
        The subset to copy, sorted so small metadata precedes safetensors shards.
        Ordering matters because a partial mirror should leave usable config behind.
    """
    has_safetensors = any(f.endswith(SAFETENSORS_SUFFIX) for f in filenames)

    keep: list[str] = []
    for path in filenames:
        if any(path.startswith(prefix) for prefix in EXCLUDED_PATH_PREFIXES):
            continue
        if _basename(path) in EXCLUDED_BASENAMES:
            continue
        if path.endswith(EXCLUDED_SUFFIXES):
            continue
        if has_safetensors and path.endswith(DUPLICATE_WEIGHT_SUFFIXES):
            continue
        keep.append(path)

    # (is-a-shard, name): metadata first, then shards, each group name-sorted.
    keep.sort(key=lambda f: (not is_metadata(f), f))
    return keep


def selection_policy() -> dict[str, list[str]]:
    """The exclusion rules, for recording in a mirror manifest.

    A manifest that records only the file list cannot answer "why is this file
    missing?" years later. Recording the policy makes an omission attributable to a
    rule rather than to an unknown bug.
    """
    return {
        "mode": ["denylist: copy everything not excluded below"],
        "excluded_path_prefixes": list(EXCLUDED_PATH_PREFIXES),
        "excluded_basenames": list(EXCLUDED_BASENAMES),
        "excluded_suffixes": list(EXCLUDED_SUFFIXES),
        "duplicate_weight_suffixes_excluded_when_safetensors_present": list(
            DUPLICATE_WEIGHT_SUFFIXES
        ),
    }
