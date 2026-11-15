"""Tests for ATL thinking cycle integration in EvolutionLoop."""

from __future__ import annotations

from unittest.mock import MagicMock

import pytest

from cognithor.evolution.atl_config import ATLConfig


@pytest.fixture
def make_loop(tmp_path):
    """Create an EvolutionLoop with ATL components wired."""
    from cognithor.evolution.atl_journal import ATLJournal
    from cognithor.evolution.goal_manager import Goal, GoalManager
    from cognithor.evolution.loop import EvolutionLoop

    def _factory(idle=True, llm_response=None, quiet_hours=False):
        idle_det = MagicMock()
        idle_det.is_idle = idle
        idle_det.idle_seconds = 300.0

        loop = EvolutionLoop(idle_detector=idle_det)

        if quiet_hours:
            loop._atl_config = ATLConfig(
                enabled=True,
                quiet_hours_start="00:00",
                quiet_hours_end="23:59",
            )
        else:
            loop._atl_config = ATLConfig(
                enabled=True,
                quiet_hours_start="03:00",
                quiet_hours_end="04:00",
            )

        gm = GoalManager(goals_path=tmp_path / "goals.yaml")
        gm.add_goal(
            Goal(
                id="g_test",
                title="Test goal",
                description="A test",
                priority=2,
                source="user",
            )
        )
        loop._goal_manager = gm
        loop._atl_journal = ATLJournal(journal_dir=tmp_path / "journal")

        if llm_response is not None:

            async def mock_llm(prompt):
                return llm_response

            loop._llm_fn = mock_llm

        return loop

    return _factory


@pytest.mark.asyncio
async def test_thinking_cycle_skips_when_not_idle(make_loop):
    loop = make_loop(idle=False)
    result = await loop.thinking_cycle()
    assert result.skipped
    assert result.reason == "not_idle"


@pytest.mark.asyncio
async def test_thinking_cycle_skips_quiet_hours(make_loop):
    loop = make_loop(idle=True, quiet_hours=True)
    result = await loop.thinking_cycle()
    assert result.skipped
    assert "quiet" in result.reason


@pytest.mark.asyncio
async def test_thinking_cycle_skips_no_llm(make_loop):
    loop = make_loop(idle=True, llm_response=None)
    loop._llm_fn = None
    result = await loop.thinking_cycle()
    assert result.skipped
    assert "no_llm" in result.reason


@pytest.mark.asyncio
async def test_thinking_cycle_runs_with_valid_response(make_loop):
    import json

    response = json.dumps(
        {
            "summary": "Evaluated test goal, looking good",
            "goal_evaluations": [{"goal_id": "g_test", "progress_delta": 0.1, "note": "progress"}],
            "proposed_actions": [],
            "wants_to_notify": False,
            "notification": None,
            "priority": "low",
        }
    )
    loop = make_loop(idle=True, llm_response=response)
    result = await loop.thinking_cycle()
    assert not result.skipped
    assert "Evaluated" in result.thought
    # Check goal progress was updated
    goal = loop._goal_manager.get_goal("g_test")
    assert goal.progress == pytest.approx(0.1)


@pytest.mark.asyncio
async def test_thinking_cycle_handles_invalid_llm_response(make_loop):
    loop = make_loop(idle=True, llm_response="not valid json at all")
    result = await loop.thinking_cycle()
    # Should not crash, just produce an empty cycle
    assert not result.skipped
    assert result.thought == ""


@pytest.mark.asyncio
async def test_thinking_cycle_writes_journal(make_loop):
    import json

    response = json.dumps(
        {
            "summary": "Journal test cycle",
            "goal_evaluations": [],
            "proposed_actions": [],
            "wants_to_notify": False,
            "notification": None,
            "priority": "low",
        }
    )
    loop = make_loop(idle=True, llm_response=response)
    await loop.thinking_cycle()
    journal_content = loop._atl_journal.today()
    assert journal_content is not None
    assert "Journal test cycle" in journal_content
