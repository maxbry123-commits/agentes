"""Tests for ATL proactive goal creation from curiosity gaps."""

from __future__ import annotations

from unittest.mock import MagicMock

from cognithor.evolution.atl_config import ATLConfig
from cognithor.evolution.goal_manager import Goal, GoalManager


def test_auto_goal_from_curiosity(tmp_path):
    from cognithor.evolution.loop import EvolutionLoop

    idle = MagicMock()
    idle.is_idle = True
    idle.idle_seconds = 300.0

    loop = EvolutionLoop(idle_detector=idle)
    loop._atl_config = ATLConfig(enabled=True)

    gm = GoalManager(goals_path=tmp_path / "goals.yaml")
    loop._goal_manager = gm

    curiosity = MagicMock()
    gap = MagicMock()
    gap.entity_name = "Kubernetes"
    gap.gap_type = "low_confidence"
    gap.importance = 0.8
    gap.description = "Low confidence entity needs verification"
    curiosity.propose_exploration.return_value = [gap]
    loop._curiosity = curiosity

    created = loop._create_goals_from_curiosity()
    assert created >= 1
    goals = gm.active_goals()
    assert any("Kubernetes" in g.title for g in goals)
    assert any(g.source == "curiosity" for g in goals)


def test_no_duplicate_goals(tmp_path):
    from cognithor.evolution.loop import EvolutionLoop

    idle = MagicMock()
    idle.is_idle = True
    loop = EvolutionLoop(idle_detector=idle)
    loop._atl_config = ATLConfig(enabled=True)

    gm = GoalManager(goals_path=tmp_path / "goals.yaml")
    gm.add_goal(
        Goal(
            title="Lerne Kubernetes",
            description="Already exists",
            priority=3,
            source="user",
        )
    )
    loop._goal_manager = gm

    curiosity = MagicMock()
    gap = MagicMock()
    gap.entity_name = "Kubernetes"
    gap.gap_type = "low_confidence"
    gap.importance = 0.8
    gap.description = "duplicate"
    curiosity.propose_exploration.return_value = [gap]
    loop._curiosity = curiosity

    created = loop._create_goals_from_curiosity()
    assert created == 0
    assert len(gm.active_goals()) == 1


def test_low_importance_skipped(tmp_path):
    from cognithor.evolution.loop import EvolutionLoop

    idle = MagicMock()
    idle.is_idle = True
    loop = EvolutionLoop(idle_detector=idle)
    loop._atl_config = ATLConfig(enabled=True)
    loop._goal_manager = GoalManager(goals_path=tmp_path / "goals.yaml")

    curiosity = MagicMock()
    gap = MagicMock()
    gap.entity_name = "TrivialThing"
    gap.importance = 0.3  # Below 0.6 threshold
    gap.description = "Not important"
    curiosity.propose_exploration.return_value = [gap]
    loop._curiosity = curiosity

    created = loop._create_goals_from_curiosity()
    assert created == 0
