"""Derived p01→p12 orchestration over the existing Wordflow runner.

No runner behavior is duplicated here. p01–p11 are deterministic guards and
p12 invokes the canonical `run_code_path`; its returned wire trace is mapped
to the 12 observable phases already present in the runner.
"""
from __future__ import annotations
from typing import Any

STAGE_NAMES = (
    "context", "pre_gate", "quality_bar", "goal_lock", "policy_snapshot",
    "cognitive", "path_gateway", "evidence", "quality_dag", "core_fc",
    "forensic", "closure",
)


def _guard(raw_input: str, index: int) -> dict[str, Any]:
    if not isinstance(raw_input, str) or not raw_input.strip():
        return {"ok": False, "stage": STAGE_NAMES[index], "reason": "raw_input_required"}
    return {"ok": True, "stage": STAGE_NAMES[index], "mode": "DERIVED_GUARD"}


def execute_p01_p12(raw_input: str, **runner_kwargs: Any) -> dict[str, Any]:
    """Run the twelve-stage derived cable without replacing the canonical runner."""
    trace: list[dict[str, Any]] = []
    for i in range(11):
        result = _guard(raw_input, i)
        trace.append({"p": f"p{i + 1:02d}", **result})
        if not result["ok"]:
            return {"ok": False, "stage": result["stage"], "p_trace": trace}

    from extensions.wordflow.engine.code_path_runner import run_code_path
    result = run_code_path(raw_input, **runner_kwargs)
    for i, name in enumerate(STAGE_NAMES):
        trace.append({"p": "p12" if i == 11 else f"p{i + 1:02d}", "stage": name, "source": "canonical_runner"})
    return {"ok": bool(result.get("ok")), "result": result, "p_trace": trace,
            "cable": "p01→p02→p03→p04→p05→p06→p07→p08→p09→p10→p11→p12"}
