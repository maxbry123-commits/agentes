"""Handlers de fase — ejecutar → AgentAdapter + MHYTOS strategy · 0% LLM
SOURCE: mejoras A + D
"""
from __future__ import annotations
from datetime import datetime, timezone
from typing import Any
from uuid import uuid4

from loops.agent_adapter import AgentAdapter, AgentExecResult
from loops.contracts.capability import CapabilityRequest
from loops.mhytos import MHYTOSExecutor, MHYTOS_PHASES, PhaseOut
from loops.phases import PhaseResult


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def make_ejecutar_handler(
    adapter: AgentAdapter,
    *,
    default_capability: str = "code_generation",
) -> Any:
    def ejecutar(ctx: dict[str, Any]) -> PhaseResult:
        strategy = str(ctx.get("strategy") or "sequential")
        if strategy in ("parallel", "adversarial", "consensus"):
            return _ejecutar_mhytos(adapter, ctx, strategy, default_capability)
        return _ejecutar_single(adapter, ctx, default_capability)

    return ejecutar


def _ejecutar_single(adapter: AgentAdapter, ctx: dict[str, Any], default_capability: str) -> PhaseResult:
    cap = str(ctx.get("capability") or ctx.get("plan_capability") or default_capability)
    run_id = str(ctx.get("run_id") or "unknown")
    payload = {
        "run_id": run_id,
        "iteration": ctx.get("iteration", 0),
        "plan": ctx.get("plan") or ctx.get("plan_output") or {},
        "inputs": ctx.get("inputs") or {},
        "anchors": ctx.get("anchors") or ctx.get("leer_anclas") or {},
        "strategy": "sequential",
    }
    req = CapabilityRequest(
        request_id=f"req-{uuid4().hex[:12]}",
        run_id=run_id,
        capability=cap,  # type: ignore[arg-type]
        issued_at=_now(),
        constraints=dict(ctx.get("constraints") or {}),
        priority=str(ctx.get("priority") or "normal"),
    )
    result: AgentExecResult = adapter.dispatch(req, payload)
    if not result.ok:
        return PhaseResult(
            phase="ejecutar", ok=False,
            error=result.error or "agent dispatch failed",
            output={"capability": cap, "resolved_by": req.resolved_by, "strategy": "sequential"},
        )
    return PhaseResult(
        phase="ejecutar", ok=True,
        output={
            "ejecutar": result.output,
            "capability": cap,
            "resolved_by": req.resolved_by,
            "tokens_used": result.tokens_used,
            "agent_output": result.output,
            "strategy": "sequential",
        },
    )


def _ejecutar_mhytos(
    adapter: AgentAdapter,
    ctx: dict[str, Any],
    strategy: str,
    default_capability: str,
) -> PhaseResult:
    """6 fases MHYTOS; cada una puede despachar capability."""
    cap = str(ctx.get("capability") or ctx.get("plan_capability") or default_capability)
    run_id = str(ctx.get("run_id") or "unknown")
    parallel = strategy == "parallel"

    def make_handler(phase_name: str):
        def _h(phase: str, c: dict[str, Any]) -> PhaseOut:
            payload = {
                "run_id": run_id,
                "mhytos_phase": phase_name,
                "strategy": strategy,
                "plan": c.get("plan") or {},
                "inputs": c.get("inputs") or {},
            }
            req = CapabilityRequest(
                request_id=f"mh-{phase_name}-{uuid4().hex[:8]}",
                run_id=run_id,
                capability=cap,  # type: ignore[arg-type]
                issued_at=_now(),
            )
            # adversarial/consensus: still dispatch; merge later
            res = adapter.dispatch(req, payload)
            if not res.ok:
                return PhaseOut(phase=phase_name, ok=False, error=res.error)
            return PhaseOut(phase=phase_name, ok=True, output={phase_name: res.output, "resolved_by": req.resolved_by})
        return _h

    handlers = {p: make_handler(p) for p in MHYTOS_PHASES}
    exe = MHYTOSExecutor(handlers=handlers)
    results = exe.run(dict(ctx), parallel=parallel)
    all_ok = exe.all_ok(results)
    merged = {r.phase: (r.output if r.ok else {"error": r.error}) for r in results}
    # consensus: majority ok; adversarial: require all ok
    if strategy == "consensus":
        ok_count = sum(1 for r in results if r.ok)
        all_ok = ok_count >= (len(results) + 1) // 2
    elif strategy == "adversarial":
        all_ok = all(r.ok for r in results)

    if not all_ok:
        return PhaseResult(
            phase="ejecutar", ok=False,
            error=f"mhytos {strategy} failed",
            output={"strategy": strategy, "mhytos": merged},
        )
    return PhaseResult(
        phase="ejecutar", ok=True,
        output={
            "strategy": strategy,
            "mhytos": merged,
            "agent_output": merged,
            "ejecutar": merged,
            "capability": cap,
        },
    )


def make_plan_handler() -> Any:
    def plan(ctx: dict[str, Any]) -> PhaseResult:
        cap = ctx.get("capability") or ctx.get("plan_capability") or "code_generation"
        plan_out = {
            "capability": cap,
            "steps": ctx.get("plan_steps") or ["dispatch_agent"],
            "constraints": ctx.get("constraints") or {},
            "strategy": ctx.get("strategy") or "sequential",
        }
        return PhaseResult(
            phase="plan", ok=True,
            output={"plan": plan_out, "plan_capability": cap, "capability": cap},
        )
    return plan


def make_validar_handler() -> Any:
    def validar(ctx: dict[str, Any]) -> PhaseResult:
        agent_out = ctx.get("agent_output") or ctx.get("ejecutar")
        if agent_out is None:
            return PhaseResult(phase="validar", ok=False, error="no agent_output from ejecutar")
        return PhaseResult(phase="validar", ok=True, output={"validation": {"has_output": True}})
    return validar


def make_default_handlers(adapter: AgentAdapter | None = None) -> dict[str, Any]:
    ad = adapter or AgentAdapter()
    return {
        "plan": make_plan_handler(),
        "ejecutar": make_ejecutar_handler(ad),
        "validar": make_validar_handler(),
        "leer_anclas": lambda ctx: PhaseResult(
            phase="leer_anclas", ok=True, output={"anchors": ctx.get("anchors") or {}}
        ),
        "evidencia": lambda ctx: PhaseResult(
            phase="evidencia", ok=True,
            output={"evidence": {
                "agent_output": ctx.get("agent_output"),
                "validation": ctx.get("validation"),
                "strategy": ctx.get("strategy"),
            }},
        ),
        "decidir": lambda ctx: PhaseResult(phase="decidir", ok=True, output={}),
    }
