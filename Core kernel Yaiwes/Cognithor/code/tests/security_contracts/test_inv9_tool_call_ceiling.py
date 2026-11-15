"""INVARIANT 9 — ToolEnforcer max_tool_calls is a hard ceiling per skill.

A community skill must never execute more tool calls than declared
in its manifest's max_tool_calls field.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from cognithor.models import PlannedAction
from cognithor.skills.community.tool_enforcer import ToolEnforcer
from cognithor.skills.registry import CommunitySkillManifest, Skill

pytestmark = pytest.mark.security_contract


def _community_skill(
    name: str = "test-skill",
    tools: list[str] | None = None,
    max_calls: int = 5,
) -> Skill:
    manifest = CommunitySkillManifest(
        name=name,
        tools_required=tools or ["web_search"],
        max_tool_calls=max_calls,
    )
    return Skill(
        name=name,
        slug=name,
        file_path=Path("/fake/skill.md"),
        tools_required=tools or ["web_search"],
        source="community",
        manifest=manifest,
    )


def _action(tool: str = "web_search") -> PlannedAction:
    return PlannedAction(tool=tool, params={})


# ---------------------------------------------------------------------------
# INV-9.1 — Blocks at limit
# ---------------------------------------------------------------------------


def test_max_calls_blocks_at_limit():
    """After max_tool_calls successful checks, the next must be blocked."""
    enforcer = ToolEnforcer(max_tool_calls=10)
    skill = _community_skill(max_calls=3)

    for i in range(3):
        result = enforcer.check(_action(), skill)
        assert result.allowed, f"Call {i} should be allowed"

    result = enforcer.check(_action(), skill)
    assert not result.allowed
    assert "max_tool_calls" in result.reason


# ---------------------------------------------------------------------------
# INV-9.2 — Per-skill isolation
# ---------------------------------------------------------------------------


def test_max_calls_per_skill_isolation():
    """Skill A's counter must not affect Skill B."""
    enforcer = ToolEnforcer(max_tool_calls=10)
    skill_a = _community_skill(name="skill-a", max_calls=2)
    skill_b = _community_skill(name="skill-b", max_calls=2)

    enforcer.check(_action(), skill_a)
    enforcer.check(_action(), skill_a)
    result_a = enforcer.check(_action(), skill_a)
    assert not result_a.allowed

    result_b = enforcer.check(_action(), skill_b)
    assert result_b.allowed


# ---------------------------------------------------------------------------
# INV-9.3 — Reset works
# ---------------------------------------------------------------------------


def test_reset_call_count_works():
    """After reset, counter is zero — calls allowed again."""
    enforcer = ToolEnforcer(max_tool_calls=10)
    skill = _community_skill(max_calls=2)

    enforcer.check(_action(), skill)
    enforcer.check(_action(), skill)
    assert not enforcer.check(_action(), skill).allowed

    enforcer.reset_call_count(skill.slug)
    assert enforcer.check(_action(), skill).allowed


# ---------------------------------------------------------------------------
# INV-9.4 — Zero means unlimited
# ---------------------------------------------------------------------------


def test_zero_max_means_unlimited():
    """max_tool_calls=0 means no limit enforced."""
    enforcer = ToolEnforcer(max_tool_calls=0)
    skill = _community_skill(max_calls=0)

    for _ in range(100):
        result = enforcer.check(_action(), skill)
        assert result.allowed
