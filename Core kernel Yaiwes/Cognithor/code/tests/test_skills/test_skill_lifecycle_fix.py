"""Tests for Skill Lifecycle Fix — context pipeline, registry injection, lifecycle cron."""

from __future__ import annotations

from unittest.mock import MagicMock


class TestContextPipelineSkillLookup:
    def test_get_skill_context_returns_matches(self):
        from cognithor.core.context_pipeline import ContextPipeline

        cp = ContextPipeline.__new__(ContextPipeline)
        cp._skill_registry = MagicMock()

        mock_skill = MagicMock()
        mock_skill.name = "ARC-AGI-3 Benchmark"
        mock_skill.description = "Spielt ARC-AGI-3 Games"
        mock_skill.trigger_keywords = ["arc", "benchmark", "puzzle"]

        mock_match = MagicMock()
        mock_match.skill = mock_skill

        cp._skill_registry.match.return_value = [mock_match]

        result = cp._get_skill_context("spiele arc benchmark")

        assert "ARC-AGI-3 Benchmark" in result
        assert "Spielt ARC-AGI-3" in result
        assert "arc" in result
        cp._skill_registry.match.assert_called_once()

    def test_get_skill_context_no_registry_returns_empty(self):
        from cognithor.core.context_pipeline import ContextPipeline

        cp = ContextPipeline.__new__(ContextPipeline)
        cp._skill_registry = None

        result = cp._get_skill_context("anything")
        assert result == ""

    def test_get_skill_context_no_matches_returns_empty(self):
        from cognithor.core.context_pipeline import ContextPipeline

        cp = ContextPipeline.__new__(ContextPipeline)
        cp._skill_registry = MagicMock()
        cp._skill_registry.match.return_value = []

        result = cp._get_skill_context("something unrelated")
        assert result == ""

    def test_get_skill_context_exception_returns_empty(self):
        from cognithor.core.context_pipeline import ContextPipeline

        cp = ContextPipeline.__new__(ContextPipeline)
        cp._skill_registry = MagicMock()
        cp._skill_registry.match.side_effect = RuntimeError("DB error")

        result = cp._get_skill_context("test")
        assert result == ""


class TestRegistryInjection:
    def test_set_skill_registry_stores_reference(self):
        from cognithor.core.context_pipeline import ContextPipeline

        cp = ContextPipeline.__new__(ContextPipeline)
        cp._skill_registry = None

        mock_registry = MagicMock()
        cp.set_skill_registry(mock_registry)

        assert cp._skill_registry is mock_registry


class TestToolAvailabilityLogging:
    def test_skill_skipped_when_tools_missing(self):
        from cognithor.skills.registry import Skill, SkillRegistry

        registry = SkillRegistry()

        skill = Skill(
            name="ARC Test",
            slug="arc_test",
            file_path=None,
            trigger_keywords=["arc", "test"],
            tools_required=["arc_play", "arc_status"],
            description="Test skill needing ARC tools",
            category="test",
            body="# Test\nDo ARC stuff.",
        )
        registry._register(skill)

        matches = registry.match(
            "play arc game",
            available_tools=["read_file", "write_file"],
        )

        assert len(matches) == 0

    def test_skill_matches_when_tools_available(self):
        from cognithor.skills.registry import Skill, SkillRegistry

        registry = SkillRegistry()

        skill = Skill(
            name="ARC Test",
            slug="arc_test",
            file_path=None,
            trigger_keywords=["arc", "test"],
            tools_required=["arc_play"],
            description="Test skill needing ARC tools",
            category="test",
            body="# Test\nDo ARC stuff.",
        )
        registry._register(skill)

        matches = registry.match(
            "play arc game",
            available_tools=["arc_play", "read_file"],
        )

        assert len(matches) >= 1
        assert matches[0].skill.slug == "arc_test"


class TestLifecycleCronIntegration:
    def test_lifecycle_manager_can_be_created(self):
        from pathlib import Path

        from cognithor.skills.lifecycle import SkillLifecycleManager
        from cognithor.skills.registry import SkillRegistry

        registry = SkillRegistry()
        lifecycle = SkillLifecycleManager(
            registry=registry,
            generated_dir=Path("/tmp/test_skills"),
        )
        assert lifecycle is not None

    def test_audit_all_returns_list(self):
        import tempfile
        from pathlib import Path

        from cognithor.skills.lifecycle import SkillLifecycleManager
        from cognithor.skills.registry import SkillRegistry

        registry = SkillRegistry()
        with tempfile.TemporaryDirectory() as tmp:
            lifecycle = SkillLifecycleManager(
                registry=registry,
                generated_dir=Path(tmp),
            )
            result = lifecycle.audit_all()
            assert isinstance(result, list)
