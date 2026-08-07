"""W14 · Ask/Preview gate · plan mínimo tokens antes de execute."""
from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any


@dataclass
class PreviewPlan:
    goal: str
    steps: list[str]
    estimated_tokens: int
    estimated_cost_usd: float
    risks: list[str] = field(default_factory=list)
    requires_confirm: bool = False
    ready: bool = False
    blockers: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def build_preview(
    *,
    goal: str,
    steps: list[str] | None = None,
    estimated_tokens: int = 0,
    estimated_cost_usd: float = 0.0,
    risks: list[str] | None = None,
    max_tokens_without_confirm: int = 50_000,
    max_cost_without_confirm: float = 1.0,
) -> PreviewPlan:
    st = list(steps or [])
    blockers: list[str] = []
    if not (goal or "").strip():
        blockers.append("empty_goal")
    if not st:
        blockers.append("empty_steps")
    needs_confirm = (
        estimated_tokens > max_tokens_without_confirm
        or estimated_cost_usd > max_cost_without_confirm
    )
    ready = len(blockers) == 0 and not needs_confirm
    return PreviewPlan(
        goal=goal or "",
        steps=st,
        estimated_tokens=estimated_tokens,
        estimated_cost_usd=estimated_cost_usd,
        risks=list(risks or []),
        requires_confirm=needs_confirm,
        ready=ready,
        blockers=blockers,
    )


def gate_execute(plan: PreviewPlan, *, user_confirmed: bool = False) -> tuple[bool, list[str]]:
    if plan.blockers:
        return False, list(plan.blockers)
    if plan.requires_confirm and not user_confirmed:
        return False, ["needs_user_confirm"]
    return True, []
