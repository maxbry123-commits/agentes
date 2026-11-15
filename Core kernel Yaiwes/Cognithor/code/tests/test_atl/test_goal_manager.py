"""Tests for ATL GoalManager."""

from __future__ import annotations

import pytest

from cognithor.evolution.goal_manager import Goal, GoalManager


@pytest.fixture
def gm(tmp_path):
    return GoalManager(goals_path=tmp_path / "goals.yaml")


def test_add_and_list_goals(gm):
    gm.add_goal(
        Goal(
            id="g_001",
            title="Learn Solvency II",
            description="Full knowledge of insurance regulation",
            priority=2,
            source="user",
        )
    )
    goals = gm.active_goals()
    assert len(goals) == 1
    assert goals[0].id == "g_001"
    assert goals[0].status == "active"


def test_get_goal(gm):
    gm.add_goal(Goal(id="g_001", title="Test", description="d", priority=3, source="user"))
    goal = gm.get_goal("g_001")
    assert goal is not None
    assert goal.title == "Test"
    assert gm.get_goal("nonexistent") is None


def test_update_progress(gm):
    gm.add_goal(Goal(id="g_001", title="Test", description="d", priority=3, source="user"))
    gm.update_progress("g_001", delta=0.25, note="First chunk done")
    goal = gm.get_goal("g_001")
    assert goal.progress == pytest.approx(0.25)


def test_progress_clamped(gm):
    gm.add_goal(Goal(id="g_001", title="Test", description="d", priority=3, source="user"))
    gm.update_progress("g_001", delta=1.5, note="Overflow")
    assert gm.get_goal("g_001").progress == pytest.approx(1.0)


def test_complete_goal(gm):
    gm.add_goal(Goal(id="g_001", title="Test", description="d", priority=3, source="user"))
    gm.complete_goal("g_001")
    assert gm.get_goal("g_001").status == "completed"
    assert len(gm.active_goals()) == 0


def test_pause_and_resume(gm):
    gm.add_goal(Goal(id="g_001", title="Test", description="d", priority=3, source="user"))
    gm.pause_goal("g_001")
    assert gm.get_goal("g_001").status == "paused"
    assert len(gm.active_goals()) == 0
    gm.resume_goal("g_001")
    assert gm.get_goal("g_001").status == "active"


def test_persistence(tmp_path):
    path = tmp_path / "goals.yaml"
    gm1 = GoalManager(goals_path=path)
    gm1.add_goal(Goal(id="g_001", title="Persist", description="d", priority=3, source="user"))
    # New instance reads from disk
    gm2 = GoalManager(goals_path=path)
    assert len(gm2.active_goals()) == 1
    assert gm2.get_goal("g_001").title == "Persist"


def test_migrate_learning_goals(gm):
    old = ["Learn ARC-AGI", "Master cybersecurity"]
    gm.migrate_learning_goals(old)
    goals = gm.active_goals()
    assert len(goals) == 2
    assert goals[0].source == "user"
    assert any("ARC-AGI" in g.title for g in goals)


def test_priority_sorting(gm):
    gm.add_goal(Goal(id="g_low", title="Low", description="d", priority=5, source="self"))
    gm.add_goal(Goal(id="g_high", title="High", description="d", priority=1, source="user"))
    goals = gm.active_goals()
    assert goals[0].id == "g_high"  # priority 1 first


def test_auto_id(gm):
    goal = Goal(title="No ID", description="d", priority=3, source="user")
    gm.add_goal(goal)
    goals = gm.active_goals()
    assert len(goals) == 1
    assert goals[0].id  # auto-generated, non-empty


def test_duplicate_id_rejected(gm):
    gm.add_goal(Goal(id="g_001", title="First", description="d", priority=3, source="user"))
    with pytest.raises(ValueError, match="already exists"):
        gm.add_goal(Goal(id="g_001", title="Dupe", description="d", priority=3, source="user"))
