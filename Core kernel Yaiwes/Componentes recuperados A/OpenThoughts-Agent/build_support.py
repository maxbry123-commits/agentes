"""Helpers for setuptools dynamic metadata (extras, etc.)."""

from __future__ import annotations

import os
import shutil
import subprocess
import warnings
from pathlib import Path


DATA_EXTRAS = [
    "click",
    "bs4",
    "rapidfuzz",
]

LLAMAFACTORY_SUBMODULE = Path("sft/llamafactory")
LLAMAFACTORY_EXTRAS = ["hf-kernels", "liger-kernel", "deepspeed", "bitsandbytes"]


def _maybe_sync_llamafactory(repo_root: Path) -> None:
    """Best-effort ensure the LLaMA-Factory submodule exists before referencing it.

    This runs at metadata-computation time for EVERY ``uv sync`` / ``pip install``
    of this package — including ``uv sync --all-packages`` (no ``--extra sft``),
    where the ``sft`` extra is only resolved for metadata and never installed.

    On a worker that received only the uploaded workspace bundle (e.g. iris's
    ``uv sync`` on /app), the ``sft/llamafactory`` submodule is absent and there
    is no usable git checkout / network to fetch it. Previously this raised a
    RuntimeError and aborted the whole sync (exit 128) even though the caller
    didn't ask for the sft extra. We now WARN-AND-SKIP instead: the
    ``resolve_llamafactory_requirement`` path URI still points at the (possibly
    missing) submodule dir, which is harmless unless ``--extra sft`` is actually
    selected. Local dev + real SFT installs are unaffected: when the submodule
    is present we early-return; when it can be fetched we still fetch it.
    """

    llama_dir = (repo_root / LLAMAFACTORY_SUBMODULE).resolve()
    if llama_dir.exists():
        return

    if shutil.which("git") is None:
        warnings.warn(
            "git is not available to sync the sft/llamafactory submodule; "
            "skipping. The 'sft' extra will be unusable until the submodule is "
            "present, but other extras can still install.",
            stacklevel=2,
        )
        return

    cmd = [
        "git",
        "-C",
        str(repo_root),
        "submodule",
        "update",
        "--init",
        "--remote",
        LLAMAFACTORY_SUBMODULE.as_posix(),
    ]

    try:
        subprocess.run(cmd, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    except subprocess.CalledProcessError as exc:  # pragma: no cover - setup-time guard
        warnings.warn(
            "Failed to sync sft/llamafactory submodule "
            f"({exc.stderr.decode(errors='replace').strip() if exc.stderr else exc}); "
            "skipping. The 'sft' extra will be unusable until you run the submodule "
            "update manually, but other extras can still install.",
            stacklevel=2,
        )


def resolve_llamafactory_requirement() -> str:
    """Build the direct-reference requirement pointing at the submodule path."""

    repo_root = Path(__file__).resolve().parent
    if os.environ.get("OT_AGENT_SKIP_SFT_SYNC", "0") != "1":
        _maybe_sync_llamafactory(repo_root)

    llama_dir = (repo_root / LLAMAFACTORY_SUBMODULE).resolve()
    extras = ",".join(LLAMAFACTORY_EXTRAS)
    return f"llamafactory[{extras}] @ {llama_dir.as_uri()}"
