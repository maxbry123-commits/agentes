"""Verify phase steps — pin, checksum, license gate placeholders."""
from __future__ import annotations

from typing import Callable, List, Tuple

from .core import AcquireContext


def _receive(ctx: AcquireContext) -> str:
    if not ctx.recipe.get("artifact_id"):
        return "FAILED"
    ctx.artifacts["artifact_id"] = ctx.recipe["artifact_id"]
    return "PASS"


def _verify_pin(ctx: AcquireContext) -> str:
    pin = (ctx.recipe.get("pin") or {})
    if not pin and ctx.recipe.get("source_type") != "local":
        return "FAILED"
    ctx.artifacts["pin"] = pin
    return "PASS"


def _source_type_gate(ctx: AcquireContext) -> str:
    st = ctx.recipe.get("source_type")
    if st not in ("git_native", "hf_hub", "release_binary", "package_manager", "local"):
        return "FAILED"
    return "PASS"


def _checksum_placeholder(ctx: AcquireContext) -> str:
    # Real checksum when LOCAL_ARTIFACT present; else SKIPPED_EXPECTED for plan-only
    if ctx.recipe.get("checksum"):
        ctx.artifacts["checksum_expected"] = ctx.recipe["checksum"]
        return "PASS"
    return "SKIPPED_EXPECTED"


def run_verify_steps() -> List[Tuple[str, Callable[[AcquireContext], str]]]:
    return [
        ("01_RECEIVE", _receive),
        ("02_VERIFY_PIN", _verify_pin),
        ("03_SOURCE_TYPE", _source_type_gate),
        ("04_CHECKSUM", _checksum_placeholder),
    ]
