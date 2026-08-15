"""Build/install phase — commands only from recipe, never hardcoded toolchains."""
from __future__ import annotations

from typing import Callable, List, Tuple

from .core import AcquireContext


def _plan_build(ctx: AcquireContext) -> str:
    build = ctx.recipe.get("build") or {}
    if not build and ctx.recipe.get("source_type") in ("release_binary", "local"):
        return "SKIPPED_EXPECTED"
    ctx.artifacts["build_plan"] = build
    return "PASS"


def _plan_install(ctx: AcquireContext) -> str:
    install = ctx.recipe.get("install") or {}
    ctx.artifacts["install_plan"] = install
    # Do not execute shell here in V1 skeleton — PLAN only unless flag
    return "PASS"


def _runtime_verify_plan(ctx: AcquireContext) -> str:
    verify = ctx.recipe.get("verify") or {}
    ctx.artifacts["verify_plan"] = verify
    return "PASS" if verify or True else "SKIPPED_EXPECTED"


def run_build_steps() -> List[Tuple[str, Callable[[AcquireContext], str]]]:
    return [
        ("12_PLAN_BUILD", _plan_build),
        ("13_PLAN_INSTALL", _plan_install),
        ("14_RUNTIME_VERIFY_PLAN", _runtime_verify_plan),
    ]
