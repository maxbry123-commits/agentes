"""Tests for research quality self-assessment in prompts."""

from __future__ import annotations


def test_replan_prompt_has_quality_check():
    """REPLAN_PROMPT must include quality self-assessment instructions."""
    from cognithor.core.planner import REPLAN_PROMPT

    lower = REPLAN_PROMPT.lower()
    assert "qualitaet" in lower or "quellen" in lower
    assert "deep_research" in lower or "search_and_read" in lower


def test_system_prompt_has_thoroughness():
    """SYSTEM_PROMPT must instruct thoroughness for factual questions."""
    from cognithor.core.planner import SYSTEM_PROMPT

    lower = SYSTEM_PROMPT.lower()
    assert "gruendlichkeit" in lower or "quellen" in lower
