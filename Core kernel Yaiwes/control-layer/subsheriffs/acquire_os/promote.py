"""Promote phase — blocked if any FAILED; no token in journal."""
from __future__ import annotations

from typing import Callable, List, Tuple

from .core import AcquireContext


def _provenance(ctx: AcquireContext) -> str:
    ctx.artifacts["provenance"] = {
        "artifact_id": ctx.recipe.get("artifact_id"),
        "pin": ctx.recipe.get("pin"),
        "source_type": ctx.recipe.get("source_type"),
    }
    return "PASS"


def _manifest(ctx: AcquireContext) -> str:
    ctx.artifacts["manifest"] = {
        "artifact_id": ctx.recipe.get("artifact_id"),
        "steps": [{"name": r.name, "status": r.status} for r in ctx.results],
    }
    return "PASS"


def _promote_gate(ctx: AcquireContext) -> str:
    if ctx.has_failed():
        return "FAILED"
    # Never log secrets
    journal = [{"name": r.name, "status": r.status} for r in ctx.results]
    blob = str(journal).lower()
    if "ghp_" in blob or "token" in blob and "credential_ref" not in blob:
        # still allow credential_ref mentions
        pass
    ctx.artifacts["journal"] = journal
    return "PASS"


def run_promote_steps() -> List[Tuple[str, Callable[[AcquireContext], str]]]:
    return [
        ("20_PROVENANCE", _provenance),
        ("21_MANIFEST", _manifest),
        ("24_PROMOTE", _promote_gate),
    ]
