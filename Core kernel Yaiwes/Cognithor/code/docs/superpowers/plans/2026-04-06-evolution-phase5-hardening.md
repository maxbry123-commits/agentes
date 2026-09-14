# Evolution Phase 5 Hardening Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Harden the Evolution Engine with autonomous exam-based learning cycles, complete ATL action dispatch, risk ceiling enforcement, REST API, and Flutter Goals UI.

**Architecture:** New `CycleController` manages the Expand→Examine→Decide loop. ATL loop.py gains 2 action types + risk check. New REST API exposes goals/plans/journal. Flutter EvolutionPage in Admin Hub.

**Tech Stack:** Python 3.12+, SQLite, FastAPI, Flutter/Dart, pytest

---

### Task 1: CycleController — Data Models + State Machine

**Files:**
- Create: `src/jarvis/evolution/cycle_controller.py`
- Test: `tests/test_cycle_controller.py`

- [ ] **Step 1: Write tests**

```python
"""Tests for LearningCycleController."""

from __future__ import annotations

import pytest

from jarvis.evolution.cycle_controller import (
    CycleController,
    CycleHistory,
    CycleState,
    ExamResult,
)


def _make_exam(score: float, gaps: list[str] | None = None, expansion_count: int = 10) -> ExamResult:
    return ExamResult(
        score=score,
        questions_total=10,
        questions_passed=int(score * 10),
        gaps=gaps or [],
        expansion_count=expansion_count,
    )


class TestCycleState:
    def test_all_states(self):
        assert len(CycleState) == 4


class TestCycleController:
    def test_initial_state(self):
        ctrl = CycleController()
        assert ctrl.state == CycleState.LEARNING
        assert ctrl.frequency_multiplier == 1.0

    def test_no_exam_before_10(self):
        ctrl = CycleController()
        result = ctrl.after_expansion("plan1", 5)
        assert result is None  # No exam triggered

    def test_exam_at_10(self):
        ctrl = CycleController()
        exam = _make_exam(0.6, gaps=["topic A"])
        result = ctrl.record_exam("plan1", exam)
        assert ctrl.state == CycleState.LEARNING

    def test_mastered_at_08(self):
        ctrl = CycleController()
        exam = _make_exam(0.85)
        ctrl.record_exam("plan1", exam)
        assert ctrl.state == CycleState.MASTERED

    def test_stagnation_after_2_low_deltas(self):
        ctrl = CycleController()
        ctrl.record_exam("plan1", _make_exam(0.5))
        ctrl.record_exam("plan1", _make_exam(0.52))  # delta 0.02 < 0.05
        ctrl.record_exam("plan1", _make_exam(0.53))  # delta 0.01 < 0.05, 2nd time
        assert ctrl.state == CycleState.STAGNATING
        assert ctrl.frequency_multiplier == 0.25

    def test_recovery_from_stagnation(self):
        ctrl = CycleController()
        ctrl.record_exam("plan1", _make_exam(0.5))
        ctrl.record_exam("plan1", _make_exam(0.52))
        ctrl.record_exam("plan1", _make_exam(0.53))
        assert ctrl.state == CycleState.STAGNATING
        # Big jump
        ctrl.record_exam("plan1", _make_exam(0.65))  # delta 0.12 > 0.05
        assert ctrl.state == CycleState.LEARNING
        assert ctrl.frequency_multiplier == 1.0

    def test_history_persists(self):
        ctrl = CycleController()
        ctrl.record_exam("plan1", _make_exam(0.4))
        ctrl.record_exam("plan1", _make_exam(0.5))
        history = ctrl.get_history("plan1")
        assert len(history.exam_results) == 2
        assert history.total_expansions == 20

    def test_gaps_returned(self):
        ctrl = CycleController()
        exam = _make_exam(0.6, gaps=["VVG Basics", "Haftpflicht"])
        ctrl.record_exam("plan1", exam)
        gaps = ctrl.get_gaps("plan1")
        assert "VVG Basics" in gaps
        assert "Haftpflicht" in gaps

    def test_should_skip_cycle_stagnating(self):
        ctrl = CycleController()
        ctrl.record_exam("plan1", _make_exam(0.5))
        ctrl.record_exam("plan1", _make_exam(0.52))
        ctrl.record_exam("plan1", _make_exam(0.53))
        # At 25% frequency, 3 out of 4 cycles should be skipped
        skips = sum(1 for i in range(100) if ctrl.should_skip_cycle("plan1"))
        assert skips > 60  # roughly 75%

    def test_mastered_always_skips(self):
        ctrl = CycleController()
        ctrl.record_exam("plan1", _make_exam(0.9))
        assert ctrl.should_skip_cycle("plan1") is True
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `pytest tests/test_cycle_controller.py -v`

- [ ] **Step 3: Implement cycle_controller.py**

```python
"""LearningCycleController — self-directed learning with autonomous exams.

Manages the Expand → Examine → Decide loop:
- After every 10 horizon expansions, triggers a quality exam
- Score ≥ 0.8 → MASTERED (stop)
- Score < 0.8 + progress → continue at full frequency
- Score < 0.8 + stagnating (Δ < 0.05 over 2 exams) → reduce frequency to 25%
- Stagnating + score rises → recover to full frequency
"""

from __future__ import annotations

import json
import random
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from pathlib import Path
from typing import Any

from jarvis.utils.logging import get_logger

log = get_logger(__name__)

_MASTERY_THRESHOLD = 0.8
_STAGNATION_DELTA = 0.05
_STAGNATION_COUNT = 2
_EXAM_INTERVAL = 10
_STAGNATION_FREQUENCY = 0.25


class CycleState(str, Enum):
    LEARNING = "learning"
    EXAMINING = "examining"
    MASTERED = "mastered"
    STAGNATING = "stagnating"


@dataclass
class ExamResult:
    score: float
    questions_total: int
    questions_passed: int
    gaps: list[str] = field(default_factory=list)
    expansion_count: int = 0
    timestamp: str = field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )


@dataclass
class CycleHistory:
    plan_id: str = ""
    exam_results: list[ExamResult] = field(default_factory=list)
    total_expansions: int = 0
    state: CycleState = CycleState.LEARNING
    stagnation_count: int = 0
    frequency_multiplier: float = 1.0


class CycleController:
    """Controls the self-directed learning cycle with autonomous exams."""

    def __init__(self, plans_dir: Path | None = None) -> None:
        self._histories: dict[str, CycleHistory] = {}
        self._plans_dir = plans_dir

    @property
    def state(self) -> CycleState:
        """State of the most recently active plan."""
        if not self._histories:
            return CycleState.LEARNING
        last = list(self._histories.values())[-1]
        return last.state

    @property
    def frequency_multiplier(self) -> float:
        if not self._histories:
            return 1.0
        last = list(self._histories.values())[-1]
        return last.frequency_multiplier

    def after_expansion(self, plan_id: str, expansion_count: int) -> ExamResult | None:
        """Called after each horizon expansion. Returns ExamResult if exam was triggered."""
        history = self._get_or_create(plan_id)
        history.total_expansions = expansion_count
        if expansion_count % _EXAM_INTERVAL != 0:
            return None
        # Exam should be triggered — caller runs QualityAssessor and calls record_exam()
        history.state = CycleState.EXAMINING
        return None  # Caller must run exam externally and call record_exam()

    def record_exam(self, plan_id: str, exam: ExamResult) -> CycleState:
        """Record an exam result and update cycle state."""
        history = self._get_or_create(plan_id)
        history.exam_results.append(exam)
        history.total_expansions = max(
            history.total_expansions,
            len(history.exam_results) * _EXAM_INTERVAL,
        )

        # Mastered?
        if exam.score >= _MASTERY_THRESHOLD:
            history.state = CycleState.MASTERED
            history.frequency_multiplier = 0.0
            log.info("cycle_mastered", plan_id=plan_id, score=exam.score)
            self._persist(plan_id)
            return history.state

        # Check progress delta
        if len(history.exam_results) >= 2:
            delta = exam.score - history.exam_results[-2].score
            if delta < _STAGNATION_DELTA:
                history.stagnation_count += 1
            else:
                history.stagnation_count = 0
                if history.state == CycleState.STAGNATING:
                    history.state = CycleState.LEARNING
                    history.frequency_multiplier = 1.0
                    log.info("cycle_recovered", plan_id=plan_id, delta=round(delta, 3))

        if (
            history.stagnation_count >= _STAGNATION_COUNT
            and history.state != CycleState.STAGNATING
        ):
            history.state = CycleState.STAGNATING
            history.frequency_multiplier = _STAGNATION_FREQUENCY
            log.info(
                "cycle_stagnating",
                plan_id=plan_id,
                score=exam.score,
                stagnation_count=history.stagnation_count,
            )
        elif history.state not in (CycleState.STAGNATING, CycleState.MASTERED):
            history.state = CycleState.LEARNING

        self._persist(plan_id)
        return history.state

    def get_history(self, plan_id: str) -> CycleHistory:
        return self._get_or_create(plan_id)

    def get_gaps(self, plan_id: str) -> list[str]:
        history = self._histories.get(plan_id)
        if not history or not history.exam_results:
            return []
        return history.exam_results[-1].gaps

    def should_skip_cycle(self, plan_id: str) -> bool:
        """Returns True if this cycle should be skipped (stagnating or mastered)."""
        history = self._histories.get(plan_id)
        if not history:
            return False
        if history.state == CycleState.MASTERED:
            return True
        if history.state == CycleState.STAGNATING:
            return random.random() > history.frequency_multiplier
        return False

    def stats(self) -> dict[str, Any]:
        return {
            "plans": len(self._histories),
            "mastered": sum(
                1 for h in self._histories.values() if h.state == CycleState.MASTERED
            ),
            "stagnating": sum(
                1 for h in self._histories.values() if h.state == CycleState.STAGNATING
            ),
            "learning": sum(
                1 for h in self._histories.values() if h.state == CycleState.LEARNING
            ),
        }

    def _get_or_create(self, plan_id: str) -> CycleHistory:
        if plan_id not in self._histories:
            self._histories[plan_id] = CycleHistory(plan_id=plan_id)
            self._load(plan_id)
        return self._histories[plan_id]

    def _persist(self, plan_id: str) -> None:
        if not self._plans_dir:
            return
        plan_dir = self._plans_dir / plan_id
        plan_dir.mkdir(parents=True, exist_ok=True)
        path = plan_dir / "cycle_history.json"
        history = self._histories[plan_id]
        data = {
            "plan_id": history.plan_id,
            "state": history.state.value,
            "total_expansions": history.total_expansions,
            "stagnation_count": history.stagnation_count,
            "frequency_multiplier": history.frequency_multiplier,
            "exam_results": [
                {
                    "score": e.score,
                    "questions_total": e.questions_total,
                    "questions_passed": e.questions_passed,
                    "gaps": e.gaps,
                    "expansion_count": e.expansion_count,
                    "timestamp": e.timestamp,
                }
                for e in history.exam_results
            ],
        }
        path.write_text(json.dumps(data, indent=2), encoding="utf-8")

    def _load(self, plan_id: str) -> None:
        if not self._plans_dir:
            return
        path = self._plans_dir / plan_id / "cycle_history.json"
        if not path.exists():
            return
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
            history = self._histories[plan_id]
            history.state = CycleState(data.get("state", "learning"))
            history.total_expansions = data.get("total_expansions", 0)
            history.stagnation_count = data.get("stagnation_count", 0)
            history.frequency_multiplier = data.get("frequency_multiplier", 1.0)
            history.exam_results = [
                ExamResult(**e) for e in data.get("exam_results", [])
            ]
        except Exception:
            log.debug("cycle_history_load_failed", plan_id=plan_id, exc_info=True)
```

- [ ] **Step 4: Run tests**

Run: `pytest tests/test_cycle_controller.py -v`
Expected: ALL PASS (11 tests)

- [ ] **Step 5: Commit**

```bash
git add src/jarvis/evolution/cycle_controller.py tests/test_cycle_controller.py
git commit -m "feat(evolution): CycleController — autonomous exam-based learning cycle"
```

---

### Task 2: ATL Actions + Risk Ceiling

**Files:**
- Modify: `src/jarvis/evolution/loop.py` (lines 586-623)
- Test: `tests/test_atl_actions.py`

- [ ] **Step 1: Write tests**

```python
"""Tests for ATL action dispatch extensions."""

from __future__ import annotations

import pytest


class TestRiskCeiling:
    def test_green_allows_green(self):
        from jarvis.evolution.loop import _check_risk_ceiling
        assert _check_risk_ceiling("research", "GREEN") is True

    def test_green_blocks_yellow(self):
        from jarvis.evolution.loop import _check_risk_ceiling
        assert _check_risk_ceiling("file_management", "GREEN") is False

    def test_yellow_allows_all(self):
        from jarvis.evolution.loop import _check_risk_ceiling
        assert _check_risk_ceiling("file_management", "YELLOW") is True
        assert _check_risk_ceiling("research", "YELLOW") is True

    def test_unknown_action_is_yellow(self):
        from jarvis.evolution.loop import _check_risk_ceiling
        assert _check_risk_ceiling("unknown_thing", "GREEN") is False
        assert _check_risk_ceiling("unknown_thing", "YELLOW") is True
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `pytest tests/test_atl_actions.py -v`

- [ ] **Step 3: Add risk ceiling function and extend action map in loop.py**

In `src/jarvis/evolution/loop.py`, add this module-level function (before the class):

```python
_ACTION_RISK: dict[str, str] = {
    "research": "GREEN",
    "memory_update": "GREEN",
    "notification": "GREEN",
    "goal_management": "GREEN",
    "file_management": "YELLOW",
}


def _check_risk_ceiling(action_type: str, ceiling: str) -> bool:
    """Check if an action is allowed under the current risk ceiling."""
    risk = _ACTION_RISK.get(action_type, "YELLOW")
    if ceiling == "GREEN" and risk != "GREEN":
        return False
    return True
```

Then in the `thinking_cycle()` method, find the action dispatch loop (line ~591 `while not queue.empty():`) and add the risk check + new action types:

Replace the `_action_map` and dispatch block with:

```python
            _action_map = {
                "research": "search_and_read",
                "memory_update": "save_to_memory",
                "notification": "send_notification",
            }
            _risk_ceiling = self._atl_config.risk_ceiling if self._atl_config else "YELLOW"

            while not queue.empty():
                action = queue.dequeue()
                if not action:
                    break

                # Risk ceiling enforcement
                if not _check_risk_ceiling(action.type, _risk_ceiling):
                    executed_actions.append(f"[BLOCKED] {action.type}: risk ceiling {_risk_ceiling}")
                    log.info("atl_action_risk_blocked", type=action.type, ceiling=_risk_ceiling)
                    continue

                # Goal management (direct, no MCP tool needed)
                if action.type == "goal_management":
                    try:
                        sub = action.params.get("sub_action", "")
                        if sub == "add" and self._goal_manager:
                            from jarvis.evolution.goal_manager import Goal
                            self._goal_manager.add_goal(Goal(
                                title=action.params.get("title", action.rationale[:60]),
                                description=action.params.get("description", ""),
                                priority=action.params.get("priority", 3),
                            ))
                        elif sub == "pause" and self._goal_manager:
                            self._goal_manager.pause_goal(action.params["goal_id"])
                        elif sub == "resume" and self._goal_manager:
                            self._goal_manager.resume_goal(action.params["goal_id"])
                        elif sub == "complete" and self._goal_manager:
                            self._goal_manager.complete_goal(action.params["goal_id"])
                        executed_actions.append(f"[OK] goal_management:{sub}")
                    except Exception as exc:
                        executed_actions.append(f"[FAIL] goal_management: {exc!s:.60}")
                    continue

                # File management (via MCP vault/memory tools)
                if action.type == "file_management":
                    try:
                        sub = action.params.get("sub_action", "")
                        if sub == "create_report":
                            await self._mcp_client.call_tool("vault_save", {
                                "title": action.params.get("title", "ATL Report"),
                                "content": action.params.get("content", action.rationale),
                                "tags": "atl,report,evolution",
                            })
                        elif sub == "save_note":
                            await self._mcp_client.call_tool("save_to_memory", {
                                "content": action.params.get("content", action.rationale[:500]),
                                "tier": "semantic",
                            })
                        executed_actions.append(f"[OK] file_management:{sub}")
                    except Exception as exc:
                        executed_actions.append(f"[FAIL] file_management: {exc!s:.60}")
                    continue

                # Standard MCP tool dispatch
                tool_name = _action_map.get(action.type, action.type)
```

- [ ] **Step 4: Run tests**

Run: `pytest tests/test_atl_actions.py -v`
Expected: ALL PASS (4 tests)

- [ ] **Step 5: Commit**

```bash
git add src/jarvis/evolution/loop.py tests/test_atl_actions.py
git commit -m "feat(evolution): ATL goal_management + file_management actions + risk ceiling"
```

---

### Task 3: Wire CycleController into DeepLearner

**Files:**
- Modify: `src/jarvis/evolution/deep_learner.py` (line ~513-532)
- Modify: `src/jarvis/gateway/gateway.py` (evolution init section)

- [ ] **Step 1: Add CycleController to DeepLearner**

In `deep_learner.py`, add an attribute in `__init__`:

```python
        self._cycle_controller: Any = None  # set by gateway
```

Then in the section where horizon expansion happens (line ~513-532), wrap it with CycleController:

```python
        # Check if ALL SubGoals done → horizon scan + schedules
        all_done = all(sg.status in ("passed", "failed") for sg in plan.sub_goals)
        if all_done:
            if getattr(self._config, "auto_expand", True):
                # CycleController: check if we should skip (stagnating/mastered)
                if self._cycle_controller and self._cycle_controller.should_skip_cycle(plan.goal_slug):
                    log.info("deep_learner_cycle_skipped", plan=plan.goal_slug,
                             state=self._cycle_controller.state.value)
                else:
                    expansions = await self._horizon_scanner.scan(plan)
                    if expansions:
                        new_context = "\n".join(
                            f"- {e['title']}: {e.get('reason', '')}" for e in expansions
                        )
                        plan = await self._strategy_planner.replan(plan, new_context)
                        plan.expansions.extend(e["title"] for e in expansions)
                        log.info("deep_learner_horizon_expanded", count=len(expansions))

                        # CycleController: track expansion count, trigger exam if needed
                        if self._cycle_controller:
                            exp_count = len(plan.expansions)
                            self._cycle_controller.after_expansion(plan.goal_slug, exp_count)
                            if exp_count % 10 == 0 and exp_count > 0:
                                # Run quality exam
                                try:
                                    exam_result = await self._quality_assessor.run_quality_test(plan)
                                    from jarvis.evolution.cycle_controller import ExamResult
                                    exam = ExamResult(
                                        score=exam_result.get("score", 0.0) if isinstance(exam_result, dict) else 0.0,
                                        questions_total=exam_result.get("total", 10) if isinstance(exam_result, dict) else 10,
                                        questions_passed=exam_result.get("passed", 0) if isinstance(exam_result, dict) else 0,
                                        gaps=exam_result.get("gaps", []) if isinstance(exam_result, dict) else [],
                                        expansion_count=exp_count,
                                    )
                                    state = self._cycle_controller.record_exam(plan.goal_slug, exam)
                                    if state.value == "mastered":
                                        plan.status = "mastered"
                                    elif state.value == "stagnating":
                                        # Create Kanban task
                                        try:
                                            _kanban = getattr(self, "_kanban_engine", None)
                                            if _kanban:
                                                from jarvis.kanban.sources import SystemTaskAdapter
                                                _task_data = SystemTaskAdapter.from_recovery_failure(
                                                    f"goal:{plan.goal[:30]}", exp_count,
                                                    f"Stagnating at {exam.score:.0%} after {exp_count} expansions"
                                                )
                                                _kanban.create_task(**{k: v for k, v in _task_data.items() if k != "status"})
                                        except Exception:
                                            pass
                                except Exception:
                                    log.debug("cycle_exam_failed", exc_info=True)
```

- [ ] **Step 2: Wire CycleController in gateway.py**

In `gateway/gateway.py`, find the DeepLearner init section (around line 721-751). After `self._deep_learner` is created, add:

```python
                # CycleController for autonomous exam-based learning
                try:
                    from jarvis.evolution.cycle_controller import CycleController
                    _cycle_ctrl = CycleController(plans_dir=plans_dir)
                    self._deep_learner._cycle_controller = _cycle_ctrl
                    log.info("cycle_controller_initialized")
                except Exception:
                    log.debug("cycle_controller_init_failed", exc_info=True)
```

- [ ] **Step 3: Commit**

```bash
git add src/jarvis/evolution/deep_learner.py src/jarvis/gateway/gateway.py
git commit -m "feat(evolution): wire CycleController into DeepLearner + gateway"
```

---

### Task 4: Evolution REST API

**Files:**
- Create: `src/jarvis/evolution/api.py`
- Test: `tests/test_evolution_api.py`

- [ ] **Step 1: Write tests**

```python
"""Tests for Evolution REST API."""

from __future__ import annotations

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from jarvis.evolution.api import create_evolution_router


class MockGoalManager:
    def __init__(self):
        self._goals = []

    def active_goals(self):
        return self._goals

    def all_goals(self):
        return self._goals

    def add_goal(self, goal):
        self._goals.append(goal)

    def get_goal(self, goal_id):
        return next((g for g in self._goals if g.id == goal_id), None)

    def pause_goal(self, goal_id):
        g = self.get_goal(goal_id)
        if g:
            g.status = "paused"

    def save(self):
        pass


class MockGoal:
    def __init__(self, id, title, status="active", progress=0.0, priority=3):
        self.id = id
        self.title = title
        self.status = status
        self.progress = progress
        self.priority = priority
        self.description = ""
        self.sub_goals = []
        self.success_criteria = []
        self.tags = []


class MockJournal:
    def recent(self, days=7):
        return "Day 1: Learned about insurance."


class MockDeepLearner:
    def list_plans(self):
        return []


@pytest.fixture
def client():
    gm = MockGoalManager()
    gm.add_goal(MockGoal("g1", "Insurance Expert", progress=0.4))
    gm.add_goal(MockGoal("g2", "Cybersecurity", status="paused"))

    router = create_evolution_router(
        goal_manager=gm,
        journal=MockJournal(),
        deep_learner=MockDeepLearner(),
    )
    app = FastAPI()
    app.include_router(router)
    return TestClient(app)


class TestEvolutionAPI:
    def test_list_goals(self, client):
        resp = client.get("/api/v1/evolution/goals")
        assert resp.status_code == 200
        goals = resp.json()
        assert len(goals) == 2
        assert goals[0]["title"] == "Insurance Expert"

    def test_create_goal(self, client):
        resp = client.post("/api/v1/evolution/goals", json={
            "title": "Learn Rust",
            "description": "Master Rust programming",
            "priority": 2,
        })
        assert resp.status_code == 201

    def test_journal(self, client):
        resp = client.get("/api/v1/evolution/journal", params={"days": 7})
        assert resp.status_code == 200
        assert "insurance" in resp.json()["content"].lower()

    def test_plans(self, client):
        resp = client.get("/api/v1/evolution/plans")
        assert resp.status_code == 200
        assert isinstance(resp.json(), list)

    def test_stats(self, client):
        resp = client.get("/api/v1/evolution/stats")
        assert resp.status_code == 200
        assert "total_goals" in resp.json()
```

- [ ] **Step 2: Implement api.py**

```python
"""Evolution Engine REST API."""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from jarvis.utils.logging import get_logger

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
        goals = goal_manager.all_goals() if hasattr(goal_manager, "all_goals") else goal_manager.active_goals()
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
            from jarvis.evolution.goal_manager import Goal
            goal = Goal(title=req.title, description=req.description, priority=req.priority)
            goal_manager.add_goal(goal)
            return {"status": "created", "id": goal.id, "title": goal.title}
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))

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
        elif req.status == "completed":
            if hasattr(goal_manager, "complete_goal"):
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
        goals = goal_manager.all_goals() if hasattr(goal_manager, "all_goals") else goal_manager.active_goals()
        return {
            "total_goals": len(goals),
            "active": sum(1 for g in goals if g.status == "active"),
            "paused": sum(1 for g in goals if g.status == "paused"),
            "mastered": sum(1 for g in goals if g.status in ("completed", "mastered")),
            "cycle": cycle_controller.stats() if cycle_controller else {},
        }

    return router
```

- [ ] **Step 3: Run tests**

Run: `pytest tests/test_evolution_api.py -v`
Expected: ALL PASS (5 tests)

- [ ] **Step 4: Register API in __main__.py**

In `src/jarvis/__main__.py`, after the kanban API registration, add:

```python
                # Evolution Engine API
                try:
                    if hasattr(gateway, "_goal_manager") and gateway._goal_manager is not None:
                        from jarvis.evolution.api import create_evolution_router
                        api_app.include_router(create_evolution_router(
                            goal_manager=gateway._goal_manager,
                            journal=getattr(gateway, "_atl_journal", None),
                            deep_learner=getattr(gateway, "_deep_learner", None),
                            cycle_controller=getattr(gateway._deep_learner, "_cycle_controller", None) if hasattr(gateway, "_deep_learner") and gateway._deep_learner else None,
                        ))
                        log.info("evolution_api_registered")
                except Exception:
                    log.debug("evolution_api_registration_failed", exc_info=True)
```

- [ ] **Step 5: Commit**

```bash
git add src/jarvis/evolution/api.py tests/test_evolution_api.py src/jarvis/__main__.py
git commit -m "feat(evolution): REST API — goals, plans, journal, stats"
```

---

### Task 5: HorizonScanner targeted expansion

**Files:**
- Modify: `src/jarvis/evolution/horizon_scanner.py`

- [ ] **Step 1: Add targeted expansion method**

Add to `HorizonScanner` class:

```python
    def add_targeted_expansion(self, gap_topic: str) -> None:
        """Queue a specific topic for the next scan cycle.

        Called by CycleController when exam reveals knowledge gaps.
        """
        if not hasattr(self, "_targeted_gaps"):
            self._targeted_gaps = []
        if gap_topic not in self._targeted_gaps:
            self._targeted_gaps.append(gap_topic)
            logger.info("horizon_targeted_gap_added", topic=gap_topic)
```

Also modify the `scan()` method to include targeted gaps in the results:

```python
    async def scan(self, plan: LearningPlan) -> list[dict]:
        """Run both discovery mechanisms and return deduplicated results."""
        llm_results = await self.explore_via_llm(plan)
        graph_results = await self.discover_graph_gaps(plan.goal_slug)

        # Add targeted gaps from CycleController
        targeted = []
        if hasattr(self, "_targeted_gaps") and self._targeted_gaps:
            for gap in self._targeted_gaps:
                targeted.append({
                    "title": gap,
                    "reason": "Knowledge gap detected in quality exam",
                    "source": "cycle_controller",
                })
            self._targeted_gaps.clear()

        return self._deduplicate(llm_results + graph_results + targeted, plan)
```

- [ ] **Step 2: Commit**

```bash
git add src/jarvis/evolution/horizon_scanner.py
git commit -m "feat(evolution): HorizonScanner targeted expansion from exam gaps"
```

---

### Task 6: Run all tests + push

- [ ] **Step 1: Run the complete test suite**

```bash
pytest tests/test_cycle_controller.py tests/test_atl_actions.py tests/test_evolution_api.py -v
```

Expected: ALL PASS (~20 tests)

- [ ] **Step 2: Ruff check**

```bash
ruff check src/jarvis/evolution/cycle_controller.py src/jarvis/evolution/api.py tests/test_cycle_controller.py tests/test_atl_actions.py tests/test_evolution_api.py --select=F821,F811 --no-fix
```

Expected: All checks passed

- [ ] **Step 3: Push**

```bash
git push origin main
```
