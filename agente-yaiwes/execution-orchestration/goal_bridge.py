"""Bridge: GoalLock / goals_in → continuous loop State + 12-stage Plan.

Does not invent goals. Reads structured goal lists and produces executable
loop state. Markers (objective/task ids) are stable strings — no UI emoji dependency.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Sequence

from wordflow_kernel.models import stable_hash
from wordflow_kernel.stages.models import Goal as StageGoal, Plan as StagePlan


@dataclass(frozen=True)
class GoalLockView:
    mission_id: str
    workspace_id: str
    goals_in: tuple[str, ...]
    goals_out: tuple[str, ...] = ()
    context: dict[str, Any] = field(default_factory=dict)

    @property
    def context_hash(self) -> str:
        return stable_hash(
            {
                "mission_id": self.mission_id,
                "goals_in": list(self.goals_in),
                "goals_out": list(self.goals_out),
                "context": self.context,
            }
        )


def goals_to_loop_state(view: GoalLockView):
    """Build maxbry_loop State from GoalLockView."""
    from maxbry_loop.models import Goal, State, Task, uid

    goal = Goal(
        text="\n".join(f"- {g}" for g in view.goals_in) or view.mission_id,
        source="goal_lock",
        requirements=list(view.goals_in),
    )
    tasks = {}
    for i, g in enumerate(view.goals_in):
        tid = uid("GL")
        tasks[tid] = Task(
            id=tid,
            title=f"G{i+1}: {g[:60]}",
            description=g,
            priority=100 - i,
            acceptance=["Evidence recorded", f"goal_marker:{g[:40]}"],
            provenance={
                "source": "goal_lock",
                "mission_id": view.mission_id,
                "workspace_id": view.workspace_id,
                "context_hash": view.context_hash,
            },
        )
    return State(schema_version="2.0", goal=goal, tasks=tasks)


def goals_to_stage_plan(
    view: GoalLockView,
    planned_steps: Sequence[str] | None = None,
) -> StagePlan:
    """Build 12-stage Plan from GoalLockView."""
    goals = [
        StageGoal(id=f"g{i+1}", description=g, required=True)
        for i, g in enumerate(view.goals_in)
    ]
    steps = list(planned_steps) if planned_steps else [f"execute:{g[:40]}" for g in view.goals_in]
    if not steps:
        steps = ["execute:mission"]
    return StagePlan(
        mission_id=view.mission_id,
        goals=goals,
        steps=steps,
        metadata={
            "workspace_id": view.workspace_id,
            "context_hash": view.context_hash,
            "goals_out": list(view.goals_out),
        },
    )
