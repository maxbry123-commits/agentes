"""Per-dataset Nemotron-Gym → Harbor converters.

Each converter takes a HuggingFace dataset row (dict) and produces a HarborTask.
Converters are registered via the @register decorator on the class definition
and discovered by their HF repo path (e.g. "nvidia/Nemotron-RL-coding-...").
"""

from __future__ import annotations

from typing import Callable

from ..adapter import HarborTask


Converter = Callable[[dict, int], HarborTask | None]
"""Signature: (row, row_index) -> HarborTask | None (None = skip row)."""


_REGISTRY: dict[str, Converter] = {}


def register(hf_path: str) -> Callable[[Converter], Converter]:
    def decorator(fn: Converter) -> Converter:
        if hf_path in _REGISTRY:
            raise ValueError(f"converter already registered for {hf_path!r}")
        _REGISTRY[hf_path] = fn
        return fn

    return decorator


def get(hf_path: str) -> Converter:
    if hf_path not in _REGISTRY:
        raise KeyError(
            f"no converter registered for {hf_path!r}; available: {sorted(_REGISTRY)}"
        )
    return _REGISTRY[hf_path]


def all_registered() -> list[str]:
    return sorted(_REGISTRY)
