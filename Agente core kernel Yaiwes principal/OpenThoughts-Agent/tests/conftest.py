"""Shared pytest configuration for the OT-Agent repo test suite.

Additive + import-safe: this file only *adds* auto-skip guards for infra-marked
tests (gpu/cluster/daytona/hf/supabase/net). It marks nothing and imports
nothing heavy at module scope, so the default CI-safe unit suite is unaffected.

The infra-need axis is carried by markers (registered in pyproject.toml
[tool.pytest.ini_options]), NOT by directory. A test that needs a resource that
is absent off-target is SKIPPED (not ERRORed) by the hook below, so
`pytest -m gpu` on a laptop skips cleanly and `pytest --collect-only` still
lists every test for awareness.
"""

from __future__ import annotations

import importlib.util
import os

import pytest


def _has(mod: str) -> bool:
    """True if an importable module spec exists (no import side effects)."""
    try:
        return importlib.util.find_spec(mod) is not None
    except Exception:
        return False


def _gpu() -> bool:
    if not _has("torch"):
        return False
    try:
        import torch  # noqa: PLC0415

        return bool(torch.cuda.is_available())
    except Exception:
        return False


# marker -> (predicate returning True when the resource is MISSING, reason)
_GUARD = {
    "gpu": (lambda: not _gpu(), "no CUDA device"),
    "cluster": (lambda: not os.getenv("OT_CLUSTER"), "no live cluster ($OT_CLUSTER)"),
    "daytona": (lambda: not os.getenv("DAYTONA_API_KEY"), "no DAYTONA_API_KEY"),
    "hf": (
        lambda: not (os.getenv("HF_TOKEN") or os.getenv("HUGGINGFACE_TOKEN")),
        "no HF token",
    ),
    "supabase": (lambda: not os.getenv("SUPABASE_URL"), "no SUPABASE_URL"),
    "net": (lambda: os.getenv("OT_NO_NET") == "1", "network disabled (OT_NO_NET=1)"),
}


def pytest_collection_modifyitems(config, items):
    """Auto-skip infra-marked items when their resource is unavailable."""
    for item in items:
        for name, (missing, why) in _GUARD.items():
            if item.get_closest_marker(name) and missing():
                item.add_marker(pytest.mark.skip(reason=f"{name}: {why}"))
