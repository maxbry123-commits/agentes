"""Tests fuer den Skill Lifecycle Manager."""

from __future__ import annotations

from typing import TYPE_CHECKING

import pytest

from cognithor.skills.lifecycle import SkillHealthStatus, SkillLifecycleManager  # noqa: F401
from cognithor.skills.registry import Skill, SkillRegistry

if TYPE_CHECKING:
    from pathlib import Path


@pytest.fixture
def registry_with_skills(tmp_path: Path):
    """Registry with a mix of healthy and broken skills."""
    reg = SkillRegistry()

    # Healthy skill
    healthy = tmp_path / "healthy.md"
    healthy.write_text(
        "---\nname: Healthy Skill\ntrigger_keywords: [test, healthy]\n"
        "category: general\n---\n\nThis skill works fine.",
        encoding="utf-8",
    )
    skill = reg._parse_skill_file(healthy)
    reg.register_skill(skill)

    # Skill with missing file
    broken = Skill(
        name="Broken Skill",
        slug="broken",
        file_path=tmp_path / "nonexistent.md",
        trigger_keywords=["broken"],
        body="some body",
    )
    reg.register_skill(broken)

    # Skill with empty body
    empty = tmp_path / "empty.md"
    empty.write_text(
        "---\nname: Empty Skill\ntrigger_keywords: [empty]\n---\n\n",
        encoding="utf-8",
    )
    skill_empty = reg._parse_skill_file(empty)
    reg.register_skill(skill_empty)

    return reg, tmp_path


class TestAudit:
    def test_audit_all_finds_issues(self, registry_with_skills):
        reg, tmp = registry_with_skills
        mgr = SkillLifecycleManager(reg, tmp)
        results = mgr.audit_all()
        assert len(results) == 3
        statuses = {r.slug: r.status for r in results}
        assert statuses["healthy"] == "healthy"
        assert statuses["broken"] == "broken"

    def test_audit_single(self, registry_with_skills):
        reg, tmp = registry_with_skills
        mgr = SkillLifecycleManager(reg, tmp)
        result = mgr.audit_single("healthy")
        assert result is not None
        assert result.status == "healthy"

    def test_audit_nonexistent(self, registry_with_skills):
        reg, tmp = registry_with_skills
        mgr = SkillLifecycleManager(reg, tmp)
        assert mgr.audit_single("does_not_exist") is None

    def test_get_broken(self, registry_with_skills):
        reg, tmp = registry_with_skills
        mgr = SkillLifecycleManager(reg, tmp)
        broken = mgr.get_broken_skills()
        assert len(broken) >= 1
        assert all(b.status == "broken" for b in broken)


class TestRepair:
    def test_repair_missing_file(self, registry_with_skills):
        reg, tmp = registry_with_skills
        mgr = SkillLifecycleManager(reg, tmp)
        result = mgr.repair_skill("broken")
        assert result is False  # Can't repair missing file

    def test_repair_empty_body(self, registry_with_skills):
        reg, tmp = registry_with_skills
        mgr = SkillLifecycleManager(reg, tmp)
        result = mgr.repair_skill("empty")
        assert result is True
        # Verify skill now has body
        skill = reg._skills.get("empty")
        assert skill is not None
        assert len(skill.body.strip()) > 0


class TestSuggest:
    def test_suggestions_returned(self, registry_with_skills):
        reg, tmp = registry_with_skills
        mgr = SkillLifecycleManager(reg, tmp)
        suggestions = mgr.suggest_skills()
        assert isinstance(suggestions, list)
        for s in suggestions:
            assert "name" in s
            assert "reason" in s

    def test_max_3_suggestions(self, registry_with_skills):
        reg, tmp = registry_with_skills
        mgr = SkillLifecycleManager(reg, tmp)
        assert len(mgr.suggest_skills()) <= 3


class TestPrune:
    def test_prune_does_not_touch_used_skills(self, registry_with_skills):
        reg, tmp = registry_with_skills
        # Mark healthy skill as recently used
        reg._skills["healthy"].total_uses = 10
        mgr = SkillLifecycleManager(reg, tmp)
        pruned = mgr.prune_unused(days=0)
        assert "healthy" not in pruned


class TestReport:
    def test_report_is_string(self, registry_with_skills):
        reg, tmp = registry_with_skills
        mgr = SkillLifecycleManager(reg, tmp)
        report = mgr.get_report()
        assert isinstance(report, str)
        assert "healthy" in report.lower() or "gesund" in report.lower()
        assert len(report) > 20
