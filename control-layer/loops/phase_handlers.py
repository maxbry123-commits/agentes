"""Handlers de fase reales — ejecutar → AgentAdapter · 0% LLM control
SOURCE: mejora A · loop produce trabajo
"""
from __future__ import annotations
from datetime import datetime, timezone
from typing import Any
from uuid import uuid4

from loops.agent_adapter import AgentAdapter, AgentExecResult
from loops.contracts.capability import CapabilityRequest
from loops.phases import PhaseResult


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def make_ejecutar_handler(
    adapter: AgentAdapter,
    *,
    default_capability: str = "code_generation",
) -> Any:
    """Factory: phase ejecutar despacha capability al agente resuelto."""

    def ejecutar(ctx: dict[str, Any]) -> PhaseResult:
        cap = str(ctx.get("capability") or ctx.get("plan_capability") or default_capability)
        run_id = str(ctx.get("run_id") or "unknown")
        payload = {
            "run_id": run_id,
            "iteration": ctx.get("iteration", 0),
            "plan": ctx.get("plan") or ctx.get("plan_output") or {},
            "inputs": ctx.get("inputs") or {},
            "anchors": ctx.get("anchors") or ctx.get("leer_anclas") or {},
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
                phase="ejecutar",
                ok=False,
                error=result.error or "agent dispatch failed",
                output={"capability": cap, "resolved_by": req.resolved_by},
            )
        return PhaseResult(
            phase="ejecutar",
            ok=True,
            output={
                "ejecutar": result.output,
                "capability": cap,
                "resolved_by": req.resolved_by,
                "tokens_used": result.tokens_used,
                "agent_output": result.output,
            },
        )

    return ejecutar


def make_plan_handler() -> Any:
    """Plan mínimo determinista: fija capability si falta."""

    def plan(ctx: dict[str, Any]) -> PhaseResult:
        cap = ctx.get("capability") or ctx.get("plan_capability") or "code_generation"
        plan_out = {
            "capability": cap,
            "steps": ctx.get("plan_steps") or ["dispatch_agent"],
            "constraints": ctx.get("constraints") or {},
        }
        return PhaseResult(phase="plan", ok=True, output={"plan": plan_out, "plan_capability": cap, "capability": cap})

    return plan


def make_validar_handler() -> Any:
    """Valida que ejecutar produjo output."""

    def validar(ctx: dict[str, Any]) -> PhaseResult:
        agent_out = ctx.get("agent_output") or ctx.get("ejecutar")
        if agent_out is None:
            return PhaseResult(phase="validar", ok=False, error="no agent_output from ejecutar")
        return PhaseResult(phase="validar", ok=True, output={"validation": {"has_output": True}})

    return validar


def make_default_handlers(adapter: AgentAdapter | None = None) -> dict[str, Any]:
    """Set listo para PhaseRunner / LoopEngine."""
    ad = adapter or AgentAdapter()
    return {
        "plan": make_plan_handler(),
        "ejecutar": make_ejecutar_handler(ad),
        "validar": make_validar_handler(),
        "leer_anclas": lambda ctx: PhaseResult(phase="leer_anclas", ok=True, output={"anchors": ctx.get("anchors") or {}}),
        "evidencia": lambda ctx: PhaseResult(
            phase="evidencia", ok=True,
            output={"evidence": {"agent_output": ctx.get("agent_output"), "validation": ctx.get("validation")}},
        ),
        "decidir": lambda ctx: PhaseResult(phase="decidir", ok=True, output={}),
    }
