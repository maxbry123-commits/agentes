"""Tests for marketplace monitor skill."""

from __future__ import annotations

from pathlib import Path


def test_marketplace_skill_loadable():
    """The marketplace-monitor skill should be loadable from data/procedures/."""
    from cognithor.skills.registry import SkillRegistry

    registry = SkillRegistry()

    # Load from the repo's data/procedures directory
    procedures_dir = Path(__file__).parent.parent.parent / "data" / "procedures"
    assert procedures_dir.exists(), f"procedures dir not found: {procedures_dir}"

    count = registry.load_from_directories([procedures_dir])
    assert count > 0

    # Verify the marketplace-monitor skill was loaded
    skill = registry.get("marketplace-monitor")
    assert skill is not None
    assert skill.name == "marketplace-monitor"
    assert skill.category == "productivity"
    assert "web_search" in skill.tools_required
    assert "search_and_read" in skill.tools_required
    assert len(skill.trigger_keywords) >= 5


def test_marketplace_skill_matching():
    """Skill should match marketplace-related queries."""
    from cognithor.skills.registry import SkillRegistry

    registry = SkillRegistry()
    procedures_dir = Path(__file__).parent.parent.parent / "data" / "procedures"
    registry.load_from_directories([procedures_dir])

    # Should match German marketplace query
    matches = registry.match("Finde guenstige Angebote auf dem Marktplatz")
    slugs = [m.skill.slug for m in matches]
    assert "marketplace-monitor" in slugs

    # Should match English marketplace query
    matches = registry.match("Find cheap deals on the marketplace")
    slugs = [m.skill.slug for m in matches]
    assert "marketplace-monitor" in slugs


def test_autonomous_detects_marketplace_monitoring():
    """Autonomous orchestrator should detect marketplace monitoring as orchestration-worthy."""
    from cognithor.core.autonomous_orchestrator import AutonomousOrchestrator

    orch = AutonomousOrchestrator()

    # "monitor" triggers both complexity (moderate) and recurring (hourly)
    msg = "Monitor Facebook Marketplace for cheap 5090s daily"
    assert orch.should_orchestrate(msg) is True
    assert orch.detect_recurring(msg) == "daily"

    # "monitor" alone triggers complexity and recurring
    msg2 = "Monitor eBay for cheap RTX 5090"
    assert orch.should_orchestrate(msg2) is True
