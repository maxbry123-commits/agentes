"""YAIWES kernel entrypoint with native capability routing.

Control/Sheriff always runs first. External AI capabilities only run after the
control gate and their outputs are returned as evidence, never as direct
critical actions.
"""
from __future__ import annotations

from typing import Any, Mapping

from bootstrap import run_control_pipeline
from capabilities.timesfm_native import (
    TimesFMAdapter,
    execute_native_capability,
    route_native_capability,
)


def run_native_capability_pipeline(
    *,
    op_type: str,
    payload: Mapping[str, Any] | None = None,
    goal: str | None = None,
    execute_capability: bool = False,
    timesfm_adapter: TimesFMAdapter | None = None,
    **control_kwargs: Any,
) -> dict[str, Any]:
    data = dict(payload or {})
    control = run_control_pipeline(
        op_type=op_type,
        payload=data,
        goal=goal,
        **control_kwargs,
    )
    out: dict[str, Any] = {
        "control": control.to_dict(),
        "native_capability": route_native_capability(goal or "", data).to_dict(),
        "capability_result": None,
    }
    if control.blocked:
        out["capability_state"] = "blocked_by_kernel_policy"
        return out

    if not execute_capability:
        out["capability_state"] = "selected_not_executed"
        return out

    result = execute_native_capability(
        goal or "",
        data,
        adapter=timesfm_adapter,
    )
    out["capability_result"] = result
    out["capability_state"] = result.get("status")
    return out
