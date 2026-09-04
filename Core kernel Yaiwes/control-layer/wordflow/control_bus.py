"""W16 · Wiring Control Bus · goals+budget+events+memory+preview+output."""
from __future__ import annotations

from pathlib import Path
from typing import Any

from contracts.budget import ChainBudget
from contracts.failure import Failure, FailureType, choose_recovery
from contracts.goals import validate_goals_in, validate_goals_out
from contracts.output_contract import compile_output, validate_output
from memory.api import build_memory_stack, default_context
from observability.events import EventStore
from planning.preview import build_preview, gate_execute


class ControlBus:
    """Fachada única del núcleo determinista (no orquestador LLM)."""

    def __init__(self, state_dir: str | Path) -> None:
        self.root = Path(state_dir)
        self.root.mkdir(parents=True, exist_ok=True)
        self.events = EventStore(self.root / "events.jsonl")
        self.budget = ChainBudget()
        self.memory = build_memory_stack(state_dir=self.root, enable_tencent=False)

    def start_mission(
        self,
        *,
        workflow_id: str,
        goals_in: dict[str, Any],
        preview_steps: list[str] | None = None,
        estimated_tokens: int = 0,
        user_confirmed: bool = False,
    ) -> dict[str, Any]:
        gin = validate_goals_in(goals_in)
        if not gin.ok:
            self.events.append(
                workflow_id=workflow_id,
                event_type="goals_in_fail",
                evidence={"missing": gin.missing},
            )
            return {"ok": False, "stage": "goals_in", "validation": gin.to_dict()}

        plan = build_preview(
            goal=str(goals_in.get("G01_objetivo") or ""),
            steps=preview_steps or ["research", "plan", "build", "verify"],
            estimated_tokens=estimated_tokens,
        )
        allowed, reasons = gate_execute(plan, user_confirmed=user_confirmed)
        if not allowed:
            self.events.append(
                workflow_id=workflow_id,
                event_type="preview_block",
                evidence={"reasons": reasons, "plan": plan.to_dict()},
            )
            return {"ok": False, "stage": "preview", "reasons": reasons, "plan": plan.to_dict()}

        if not self.budget.allow():
            return {"ok": False, "stage": "budget", "exhausted": self.budget.exhausted()}

        self.events.append(
            workflow_id=workflow_id,
            event_type="mission_start",
            state="RUNNING",
            evidence={"goals_score": gin.score},
        )
        return {"ok": True, "stage": "running", "goals": gin.to_dict(), "plan": plan.to_dict()}

    def remember(self, *,
                 project_id: str,
                 agent_id: str,
                 content: str,
                 type: str = "fact") -> Any:
        ctx = default_context(project_id=project_id, agent_id=agent_id)
        return self.memory.capture(ctx, content, type=type)

    def finish_mission(
        self,
        *,
        workflow_id: str,
        goals_out: dict[str, Any],
        result: str,
        evidence: dict | None = None,
        termination: str = "complete",
    ) -> dict[str, Any]:
        gout = validate_goals_out(goals_out)
        oc, ov = compile_output(
            goal=str(goals_out.get("O01_objetivo_cumplido") or ""),
            result=result,
            evidence=evidence,
            termination=termination,
            limitations=[],
            next_state={"workflow_id": workflow_id},
        )
        if not gout.ok or not ov.ok:
            self.events.append(
                workflow_id=workflow_id,
                event_type="finish_fail",
                evidence={"goals_out": gout.to_dict(), "output": ov.__dict__},
            )
            return {
                "ok": False,
                "stage": "finish",
                "goals_out": gout.to_dict(),
                "output_validation": ov.__dict__,
            }
        self.events.append(
            workflow_id=workflow_id,
            event_type="mission_complete",
            state="SUCCESS",
            evidence={"termination": termination},
        )
        return {"ok": True, "output": oc.to_dict(), "events_tip": self.events.tip_hash}

    def on_failure(self, *,
                   workflow_id: str,
                   failure: Failure,
                   retries_done: int = 0) -> dict[str, Any]:
        strategy = choose_recovery(failure, retries_done=retries_done)
        self.events.append(
            workflow_id=workflow_id,
            event_type="failure",
            state=strategy.value,
            evidence=failure.to_dict(),
        )
        return {"strategy": strategy.value, "failure": failure.to_dict()}
