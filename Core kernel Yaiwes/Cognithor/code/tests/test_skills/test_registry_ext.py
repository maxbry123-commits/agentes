"""Extended tests for skills/registry.py -- missing lines coverage.

Targets:
  - list_by_agent
  - _parse_simple_frontmatter
  - P2P skill loading from subdirectories
  - inject_into_working_memory
  - record_usage
  - match with available_tools filter
  - fuzzy matching path
  - overlap matching path
"""

from __future__ import annotations

from pathlib import Path
from unittest.mock import MagicMock

from cognithor.skills.registry import Skill, SkillRegistry


def _create_skill_file(path: Path, frontmatter: str, body: str) -> None:
    content = f"---\n{frontmatter}\n---\n{body}"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


class TestListByAgent:
    def test_list_by_agent(self) -> None:
        registry = SkillRegistry()
        registry._skills["s1"] = Skill(
            name="S1",
            slug="s1",
            file_path=Path("/fake"),
            agent="email_agent",
            enabled=True,
        )
        registry._skills["s2"] = Skill(
            name="S2",
            slug="s2",
            file_path=Path("/fake"),
            agent="code_agent",
            enabled=True,
        )
        registry._skills["s3"] = Skill(
            name="S3",
            slug="s3",
            file_path=Path("/fake"),
            agent="email_agent",
            enabled=False,  # Disabled
        )
        result = registry.list_by_agent("email_agent")
        assert len(result) == 1
        assert result[0].slug == "s1"

    def test_list_by_agent_empty(self) -> None:
        registry = SkillRegistry()
        assert registry.list_by_agent("nonexistent") == []


class TestParseSimpleFrontmatter:
    def test_basic_key_value(self) -> None:
        text = "name: My Skill\ncategory: general\npriority: 5"
        result = SkillRegistry._parse_simple_frontmatter(text)
        assert result["name"] == "My Skill"
        assert result["category"] == "general"
        assert result["priority"] == "5"

    def test_list_value(self) -> None:
        text = "trigger_keywords: [hello, world, test]"
        result = SkillRegistry._parse_simple_frontmatter(text)
        assert result["trigger_keywords"] == ["hello", "world", "test"]

    def test_empty_list(self) -> None:
        text = "tools_required: []"
        result = SkillRegistry._parse_simple_frontmatter(text)
        assert result["tools_required"] == []


class TestP2PSkillLoading:
    def test_load_p2p_subdirectory(self, tmp_path: Path) -> None:
        skills_dir = tmp_path / "skills"
        skills_dir.mkdir()

        # Create P2P skill in subdirectory
        sub_dir = skills_dir / "p2p_calculator"
        sub_dir.mkdir()
        _create_skill_file(
            sub_dir / "skill.md",
            "name: Calculator\ncategory: tools\ntrigger_keywords: [calc, rechner]",
            "# Calculator\nA simple calculator skill.",
        )

        registry = SkillRegistry()
        count = registry.load_from_directories([skills_dir])
        assert count >= 1
        # The slug should be the directory name or the name from frontmatter
        assert registry.count >= 1


class TestInjectIntoWorkingMemory:
    def test_inject_success(self, tmp_path: Path) -> None:
        skills_dir = tmp_path / "skills"
        skills_dir.mkdir()
        _create_skill_file(
            skills_dir / "briefing.md",
            "name: Briefing\ntrigger_keywords: [briefing, morgen]",
            "# Briefing\nErstelle ein Morgen-Briefing.",
        )

        registry = SkillRegistry()
        registry.load_from_directories([skills_dir])

        wm = MagicMock()
        wm.injected_procedures = []

        result = registry.inject_into_working_memory("Erstelle ein briefing", wm)
        assert result is not None
        assert len(wm.injected_procedures) == 1

    def test_inject_no_match(self) -> None:
        registry = SkillRegistry()
        wm = MagicMock()
        wm.injected_procedures = []

        result = registry.inject_into_working_memory("xyznonexistent", wm)
        assert result is None

    def test_inject_no_duplicate(self, tmp_path: Path) -> None:
        skills_dir = tmp_path / "skills"
        skills_dir.mkdir()
        _create_skill_file(
            skills_dir / "calc.md",
            "name: Calc\ntrigger_keywords: [calc]",
            "# Calc\nBody.",
        )

        registry = SkillRegistry()
        registry.load_from_directories([skills_dir])

        wm = MagicMock()
        wm.injected_procedures = []

        registry.inject_into_working_memory("calc", wm)
        registry.inject_into_working_memory("calc", wm)
        # Should not inject twice
        assert len(wm.injected_procedures) == 1


class TestRecordUsage:
    def test_record_success(self) -> None:
        registry = SkillRegistry()
        registry._skills["s1"] = Skill(
            name="S1",
            slug="s1",
            file_path=Path("/fake"),
        )
        registry.record_usage("s1", success=True, score=0.9)
        skill = registry.get("s1")
        assert skill.success_count == 1
        assert skill.total_uses == 1
        assert skill.last_used is not None

    def test_record_failure(self) -> None:
        registry = SkillRegistry()
        registry._skills["s1"] = Skill(
            name="S1",
            slug="s1",
            file_path=Path("/fake"),
        )
        registry.record_usage("s1", success=False, score=0.2)
        skill = registry.get("s1")
        assert skill.failure_count == 1

    def test_record_unknown_skill(self) -> None:
        registry = SkillRegistry()
        registry.record_usage("nonexistent", success=True)  # Should not crash


class TestMatchExtended:
    def test_match_with_available_tools_filter(self, tmp_path: Path) -> None:
        skills_dir = tmp_path / "skills"
        skills_dir.mkdir()
        _create_skill_file(
            skills_dir / "reader.md",
            "name: Reader\ntrigger_keywords: [read, lesen]\ntools_required: [read_file]",
            "# Reader",
        )
        _create_skill_file(
            skills_dir / "writer.md",
            "name: Writer\ntrigger_keywords: [write, schreiben]\ntools_required: [write_file]",
            "# Writer",
        )

        registry = SkillRegistry()
        registry.load_from_directories([skills_dir])

        # Only read_file available
        matches = registry.match("read something", available_tools=["read_file"])
        assert len(matches) >= 1
        assert all(m.skill.name == "Reader" for m in matches)

    def test_match_empty_query(self) -> None:
        registry = SkillRegistry()
        assert registry.match("") == []
        assert registry.match("   ") == []

    def test_match_best_returns_none(self) -> None:
        registry = SkillRegistry()
        assert registry.match_best("nonexistent") is None

    def test_match_overlap_scoring(self, tmp_path: Path) -> None:
        skills_dir = tmp_path / "skills"
        skills_dir.mkdir()
        _create_skill_file(
            skills_dir / "email_triage.md",
            "name: Email Triage\ndescription: Scan and prioritize"
            " emails\ntrigger_keywords: [email]",
            "# Email Triage",
        )

        registry = SkillRegistry()
        registry.load_from_directories([skills_dir])

        # Overlap with description words
        matches = registry.match("scan emails and prioritize")
        assert len(matches) >= 1


class TestSkillSuccessRate:
    def test_success_rate_untested(self) -> None:
        skill = Skill(name="S", slug="s", file_path=Path("/fake"))
        assert skill.success_rate == 0.5  # Neutral

    def test_success_rate_all_success(self) -> None:
        skill = Skill(name="S", slug="s", file_path=Path("/fake"), success_count=10)
        assert skill.success_rate == 1.0

    def test_success_rate_mixed(self) -> None:
        skill = Skill(
            name="S",
            slug="s",
            file_path=Path("/fake"),
            success_count=7,
            failure_count=3,
        )
        assert abs(skill.success_rate - 0.7) < 0.01
