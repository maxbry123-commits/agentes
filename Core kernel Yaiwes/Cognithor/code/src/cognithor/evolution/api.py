"""Evolution Engine REST API."""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from cognithor.utils.logging import get_logger

log = get_logger(__name__)


class CreateGoalRequest(BaseModel):
    title: str
    description: str = ""
    priority: int = 3


class UpdateGoalRequest(BaseModel):
    status: str | None = None
    priority: int | None = None


def create_evolution_router(
    goal_manager: Any,
    journal: Any,
    deep_learner: Any,
    cycle_controller: Any = None,
) -> APIRouter:
    router = APIRouter(prefix="/api/v1/evolution", tags=["evolution"])

    @router.get("/goals")
    def list_goals() -> list[dict[str, Any]]:
        goals = (
            goal_manager.all_goals()
            if hasattr(goal_manager, "all_goals")
            else goal_manager.active_goals()
        )
        return [
            {
                "id": g.id,
                "title": g.title,
                "description": getattr(g, "description", ""),
                "status": g.status,
                "progress": g.progress,
                "priority": g.priority,
                "tags": getattr(g, "tags", []),
            }
            for g in goals
        ]

    @router.post("/goals", status_code=201)
    def create_goal(req: CreateGoalRequest) -> dict[str, str]:
        try:
            from cognithor.evolution.goal_manager import Goal

            goal = Goal(title=req.title, description=req.description, priority=req.priority)
            goal_manager.add_goal(goal)
            return {"status": "created", "id": goal.id, "title": goal.title}
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e)) from e

    @router.patch("/goals/{goal_id}")
    def update_goal(goal_id: str, req: UpdateGoalRequest) -> dict[str, str]:
        goal = goal_manager.get_goal(goal_id)
        if not goal:
            raise HTTPException(status_code=404, detail="Goal not found")
        if req.status == "paused":
            goal_manager.pause_goal(goal_id)
        elif req.status == "active":
            if hasattr(goal_manager, "resume_goal"):
                goal_manager.resume_goal(goal_id)
        elif req.status == "completed" and hasattr(goal_manager, "complete_goal"):
            goal_manager.complete_goal(goal_id)
        if req.priority is not None:
            goal.priority = req.priority
            goal_manager.save()
        return {"status": "updated", "id": goal_id}

    @router.delete("/goals/{goal_id}", status_code=204)
    def delete_goal(goal_id: str) -> None:
        if hasattr(goal_manager, "remove_goal"):
            goal_manager.remove_goal(goal_id)

    @router.get("/plans")
    def list_plans() -> list[dict[str, Any]]:
        plans = deep_learner.list_plans() if deep_learner else []
        return [
            {
                "id": getattr(p, "goal_slug", ""),
                "goal": getattr(p, "goal", ""),
                "status": getattr(p, "status", ""),
                "sub_goals_total": len(getattr(p, "sub_goals", [])),
                "sub_goals_passed": sum(
                    1 for sg in getattr(p, "sub_goals", []) if sg.status == "passed"
                ),
                "coverage_score": getattr(p, "coverage_score", 0.0),
                "quality_score": getattr(p, "quality_score", 0.0),
                "cycle_state": (
                    cycle_controller.get_history(getattr(p, "goal_slug", "")).state.value
                    if cycle_controller and hasattr(p, "goal_slug")
                    else "unknown"
                ),
            }
            for p in plans
        ]

    @router.get("/plans/{plan_id}")
    def get_plan(plan_id: str) -> dict[str, Any]:
        if not deep_learner:
            raise HTTPException(status_code=404, detail="No deep learner")
        plan = deep_learner.get_plan(plan_id)
        if not plan:
            raise HTTPException(status_code=404, detail="Plan not found")
        result = {
            "id": plan.goal_slug,
            "goal": plan.goal,
            "status": plan.status,
            "coverage_score": plan.coverage_score,
            "quality_score": plan.quality_score,
            "sub_goals": [
                {
                    "title": sg.title,
                    "status": sg.status,
                    "coverage_score": sg.coverage_score,
                    "quality_score": sg.quality_score,
                    "chunks_created": sg.chunks_created,
                    "entities_created": sg.entities_created,
                }
                for sg in plan.sub_goals
            ],
        }
        if cycle_controller:
            history = cycle_controller.get_history(plan_id)
            result["cycle"] = {
                "state": history.state.value,
                "total_expansions": history.total_expansions,
                "frequency": history.frequency_multiplier,
                "exams": [
                    {"score": e.score, "gaps": e.gaps, "timestamp": e.timestamp}
                    for e in history.exam_results
                ],
            }
        return result

    @router.get("/journal")
    def get_journal(days: int = 7) -> dict[str, Any]:
        content = journal.recent(days=days) if journal else ""
        return {"days": days, "content": content}

    @router.get("/stats")
    def get_stats() -> dict[str, Any]:
        goals = (
            goal_manager.all_goals()
            if hasattr(goal_manager, "all_goals")
            else goal_manager.active_goals()
        )
        return {
            "total_goals": len(goals),
            "active": sum(1 for g in goals if g.status == "active"),
            "paused": sum(1 for g in goals if g.status == "paused"),
            "mastered": sum(1 for g in goals if g.status in ("completed", "mastered")),
            "cycle": cycle_controller.stats() if cycle_controller else {},
        }

    return router
