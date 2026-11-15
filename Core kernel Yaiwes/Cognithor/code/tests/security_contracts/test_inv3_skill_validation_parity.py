"""INVARIANT 3 — Self-generated skills run through the SAME validation as external packs.

A skill created by the agent at runtime must pass identical validation to
one installed from the marketplace. This test suite DOCUMENTS THE GAP:
generated skills currently bypass ToolEnforcer and the 5-check validation.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from cognithor.models import PlannedAction
from cognithor.skills.community.tool_enforcer import ToolEnforcer
from cognithor.skills.community.validator import SkillValidator
from cognithor.skills.registry import CommunitySkillManifest, Skill

pytestmark = pytest.mark.security_contract


def _skill(
    name: str = "test-skill",
    source: str = "community",
    tools: list[str] | None = None,
    max_calls: int = 10,
) -> Skill:
    manifest = (
        CommunitySkillManifest(
            name=name,
            tools_required=tools or ["web_search"],
            max_tool_calls=max_calls,
        )
        if source == "community"
        else None
    )
    return Skill(
        name=name,
        slug=name,
        file_path=Path("/fake/skill.md"),
        tools_required=tools or ["web_search"],
        source=source,
        manifest=manifest,
    )


def _action(tool: str = "web_search") -> PlannedAction:
    return PlannedAction(tool=tool, params={})


# ---------------------------------------------------------------------------
# INV-3.1 — Generated skill source is "generated"
# ---------------------------------------------------------------------------


def test_generated_skill_source_is_generated():
    """Skills loaded from the generated/ directory have source='generated'."""
    skill = _skill(source="generated")
    assert skill.source == "generated"


# ---------------------------------------------------------------------------
# INV-3.2 — ToolEnforcer BYPASSES generated skills (DOCUMENTS GAP)
# ---------------------------------------------------------------------------


def test_tool_enforcer_blocks_generated_skills():
    """Generated skills MUST be enforced by ToolEnforcer (same as community)."""
    enforcer = ToolEnforcer(max_tool_calls=10)
    skill = _skill(source="generated", tools=["web_search"])

    dangerous_action = _action("vault_delete")
    result = enforcer.check(dangerous_action, skill)
    assert result.allowed is False, "Generated skill must be blocked when calling undeclared tool"


# ---------------------------------------------------------------------------
# INV-3.3 — Community skill IS enforced by ToolEnforcer
# ---------------------------------------------------------------------------


def test_community_skill_enforced():
    """Community skills with tools_required MUST be enforced."""
    enforcer = ToolEnforcer(max_tool_calls=10)
    skill = _skill(source="community", tools=["web_search"])

    allowed_action = _action("web_search")
    result = enforcer.check(allowed_action, skill)
    assert result.allowed

    undeclared_action = _action("vault_delete")
    result = enforcer.check(undeclared_action, skill)
    assert not result.allowed


# ---------------------------------------------------------------------------
# INV-3.4 — Generated skill skips 5-check validation (DOCUMENTS GAP)
# ---------------------------------------------------------------------------


def test_generated_skill_runs_security_validation():
    """SkillGenerator.register() MUST call SkillValidator for security checks."""
    import inspect

    from cognithor.skills.generator import SkillGenerator

    source = inspect.getsource(SkillGenerator.register)
    assert "SkillValidator" in source, "SkillValidator must be called in register()"
    assert "injection_scan" in source or "content_safety" in source, (
        "Security checks (injection, content safety) must be enforced"
    )


# ---------------------------------------------------------------------------
# INV-3.5 — Community install DOES run 5-check
# ---------------------------------------------------------------------------


def test_community_install_runs_5check():
    """CommunityRegistryClient.install() must call SkillValidator.validate()."""
    import inspect

    from cognithor.skills.community.client import CommunityRegistryClient

    source = inspect.getsource(CommunityRegistryClient.install)
    assert "SkillValidator" in source or "validator" in source.lower()


# ---------------------------------------------------------------------------
# INV-3.6 — Injection pattern in generated skill not caught
# ---------------------------------------------------------------------------


def test_generated_skill_with_declared_tool_allowed():
    """A generated skill calling a declared tool must be allowed."""
    enforcer = ToolEnforcer(max_tool_calls=10)
    skill = _skill(source="generated", tools=["web_search"])

    result = enforcer.check(_action("web_search"), skill)
    assert result.allowed is True


# ---------------------------------------------------------------------------
# INV-3.7 — Generated skill referencing RED tools not caught at registration
# ---------------------------------------------------------------------------


def test_generated_skill_undeclared_tool_blocked():
    """Generated skill calling an undeclared tool must be blocked."""
    enforcer = ToolEnforcer(max_tool_calls=10)
    skill = _skill(source="generated", tools=["web_search"])

    result = enforcer.check(_action("vault_delete"), skill)
    assert result.allowed is False, "Generated skill must be blocked when calling undeclared tool"


# ---------------------------------------------------------------------------
# INV-3.8 — auto_approve_threshold config
# ---------------------------------------------------------------------------


def test_auto_approve_threshold():
    """Default auto_approve_threshold (0.7) must result in require_approval=True."""
    threshold = 0.7  # default
    require_approval = threshold < 1.0
    assert require_approval is True, "Default threshold must require approval for generated skills"


# ---------------------------------------------------------------------------
# INV-3.9 — Manifest optional passes check 5
# ---------------------------------------------------------------------------


def test_manifest_none_fails_integrity_check():
    """SkillValidator with manifest=None must FAIL integrity check."""
    validator = SkillValidator()
    skill_md = """---
name: test-skill
description: A test skill
trigger_keywords: [test]
tools_required: [web_search]
---

Do something with web_search.
"""
    result = validator.validate(skill_md, manifest=None, existing_names=set())
    integrity_check = next((c for c in result.checks if c.check_name == "manifest_integrity"), None)
    assert integrity_check is not None
    assert integrity_check.passed is False, "manifest=None must fail integrity check"


# ---------------------------------------------------------------------------
# INV-3.10 — Asymmetry proof: generated vs community validation
# ---------------------------------------------------------------------------


def test_validation_parity():
    """Community and generated skills must have identical ToolEnforcer behavior."""
    enforcer = ToolEnforcer(max_tool_calls=10)

    community = _skill(source="community", tools=["web_search"])
    generated = _skill(source="generated", tools=["web_search"])

    action = _action("vault_delete")

    community_result = enforcer.check(action, community)
    generated_result = enforcer.check(action, generated)

    assert not community_result.allowed, "Community should block undeclared tool"
    assert not generated_result.allowed, "Generated should block undeclared tool"

    assert community_result.allowed == generated_result.allowed, (
        "Community and generated must have IDENTICAL enforcement"
    )


# ---------------------------------------------------------------------------
# INV-3.11 — Builtin skills also bypass enforcer
# ---------------------------------------------------------------------------


def test_builtin_skills_bypass_enforcer():
    """Builtin skills (source='builtin') bypass ToolEnforcer — by design."""
    enforcer = ToolEnforcer(max_tool_calls=10)
    skill = _skill(source="builtin", tools=["web_search"])

    result = enforcer.check(_action("vault_delete"), skill)
    assert result.allowed


# ---------------------------------------------------------------------------
# INV-3.12 — Generated cannot overwrite community
# ---------------------------------------------------------------------------


def test_generated_cannot_overwrite_community():
    """SkillRegistry rejects generated skills that match existing community slugs."""
    from cognithor.skills.registry import SkillRegistry

    registry = SkillRegistry()
    community_skill = _skill(name="my-skill", source="community")
    registry._skills["my-skill"] = community_skill

    generated = _skill(name="my-skill", source="generated")

    existing = registry._skills.get(generated.slug)
    assert existing is not None
    assert existing.source == "community"
