"""Tests for ATL system prompt and response parsing."""

from __future__ import annotations

from cognithor.evolution.atl_prompt import AutonomousThought, build_atl_prompt, parse_atl_response


def test_build_prompt_contains_key_sections():
    prompt = build_atl_prompt(
        identity="I am Jarvis",
        goals_formatted="- g_001: Learn BU (35%)",
        recent_events="User asked about WWK",
        goal_knowledge="BU Protect: premium product",
        now="2026-03-30 08:15",
        max_actions=3,
    )
    assert "autonomen Denkmodus" in prompt
    assert "Learn BU" in prompt
    assert "I am Jarvis" in prompt
    assert "WWK" in prompt
    assert "3" in prompt


def test_parse_valid_response():
    raw = (
        '{"summary": "All good", "goal_evaluations": '
        '[{"goal_id": "g_001", "progress_delta": 0.05, "note": "ok"}], '
        '"proposed_actions": [], "wants_to_notify": false, '
        '"notification": null, "priority": "low"}'
    )
    thought = parse_atl_response(raw)
    assert isinstance(thought, AutonomousThought)
    assert thought.summary == "All good"
    assert len(thought.goal_evaluations) == 1
    assert thought.goal_evaluations[0]["goal_id"] == "g_001"
    assert thought.priority == "low"
    assert thought.wants_to_notify is False


def test_parse_with_think_tags():
    raw = (
        "<think>internal reasoning here</think>"
        '{"summary": "test", "goal_evaluations": [], '
        '"proposed_actions": [{"type": "research", '
        '"params": {"q": "x"}, "rationale": "need info"}], '
        '"wants_to_notify": false, "notification": null, '
        '"priority": "medium"}'
    )
    thought = parse_atl_response(raw)
    assert thought.summary == "test"
    assert len(thought.proposed_actions) == 1
    assert thought.proposed_actions[0]["type"] == "research"


def test_parse_with_markdown_code_block():
    raw = (
        '```json\n{"summary": "wrapped", "goal_evaluations": [], '
        '"proposed_actions": [], "wants_to_notify": false, '
        '"notification": null, "priority": "low"}\n```'
    )
    thought = parse_atl_response(raw)
    assert thought.summary == "wrapped"


def test_parse_invalid_returns_empty():
    thought = parse_atl_response("not json at all")
    assert thought.summary == ""
    assert thought.proposed_actions == []
    assert thought.wants_to_notify is False


def test_parse_partial_json():
    raw = '{"summary": "partial", "goal_evaluations": []}'
    thought = parse_atl_response(raw)
    assert thought.summary == "partial"
    assert thought.proposed_actions == []
    assert thought.priority == "low"  # default
