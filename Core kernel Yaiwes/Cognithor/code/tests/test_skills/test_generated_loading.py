"""Tests for loading generated skills into the SkillRegistry."""

from __future__ import annotations

from pathlib import Path

from cognithor.skills.registry import Skill, SkillRegistry

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

_VALID_SKILL_MD = """\
---
name: test-gen-skill
trigger_keywords: [demo, generated]
tools_required: [web_search]
category: testing
priority: 2
---
# Test Generated Skill

Body content here.
"""

_MINIMAL_SKILL_MD = """\
---
name: minimal
---
Minimal body.
"""

_INVALID_YAML_MD = """\
---
name: [broken
trigger_keywords: ???
---
Body.
"""


def _write_skill(directory: Path, filename: str, content: str) -> Path:
    directory.mkdir(parents=True, exist_ok=True)
    path = directory / filename
    path.write_text(content, encoding="utf-8")
    return path


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------


class TestLoadGeneratedSkills:
    """Suite for SkillRegistry.load_generated_skills."""

    def test_loads_valid_generated_skill(self, tmp_path: Path) -> None:
        """A valid .md file in generated/ is loaded with source='generated'."""
        gen_dir = tmp_path / "generated"
        _write_skill(gen_dir, "demo.md", _VALID_SKILL_MD)

        registry = SkillRegistry()
        count = registry.load_generated_skills([tmp_path])

        assert count == 1
        # slug is derived from filename stem ("demo"), not the name field
        skill = registry.get("demo")
        assert skill is not None
        assert skill.source == "generated"
        assert skill.name == "test-gen-skill"
        assert "demo" in skill.trigger_keywords
        assert "Body content here." in skill.body

    def test_multiple_files_loaded(self, tmp_path: Path) -> None:
        """All .md files in generated/ are loaded."""
        gen_dir = tmp_path / "generated"
        _write_skill(gen_dir, "a.md", _VALID_SKILL_MD)
        _write_skill(gen_dir, "b.md", _MINIMAL_SKILL_MD)

        registry = SkillRegistry()
        count = registry.load_generated_skills([tmp_path])

        assert count == 2
        assert len(registry.get_generated_skills()) == 2

    def test_skips_invalid_files_continues(self, tmp_path: Path) -> None:
        """Invalid YAML doesn't crash — the file is skipped, valid ones load."""
        gen_dir = tmp_path / "generated"
        _write_skill(gen_dir, "bad.md", _INVALID_YAML_MD)
        _write_skill(gen_dir, "good.md", _MINIMAL_SKILL_MD)

        registry = SkillRegistry()
        count = registry.load_generated_skills([tmp_path])

        # bad.md falls back to simple frontmatter parser, may still parse
        # At minimum, the good one loads.
        assert count >= 1
        assert registry.get("good") is not None

    def test_does_not_overwrite_builtin(self, tmp_path: Path) -> None:
        """A generated skill with the same slug as a builtin is skipped."""
        gen_dir = tmp_path / "generated"
        # filename "existing.md" → slug "existing"
        _write_skill(gen_dir, "existing.md", _VALID_SKILL_MD)

        registry = SkillRegistry()
        # Pre-register a builtin with the same slug as the filename
        builtin = Skill(
            name="existing",
            slug="existing",
            file_path=Path("/fake/builtin.md"),
            source="builtin",
            body="original builtin body",
        )
        registry.register_skill(builtin)

        count = registry.load_generated_skills([tmp_path])

        assert count == 0
        skill = registry.get("existing")
        assert skill is not None
        assert skill.source == "builtin"
        assert skill.body == "original builtin body"

    def test_does_not_overwrite_community(self, tmp_path: Path) -> None:
        """A generated skill with the same slug as a community skill is skipped."""
        gen_dir = tmp_path / "generated"
        _write_skill(gen_dir, "existing.md", _VALID_SKILL_MD)

        registry = SkillRegistry()
        community = Skill(
            name="existing",
            slug="existing",
            file_path=Path("/fake/community.md"),
            source="community",
            body="community body",
        )
        registry.register_skill(community)

        count = registry.load_generated_skills([tmp_path])

        assert count == 0
        assert registry.get("existing").source == "community"

    def test_overwrites_existing_generated(self, tmp_path: Path) -> None:
        """A generated skill CAN overwrite another generated skill (reload)."""
        gen_dir = tmp_path / "generated"
        _write_skill(gen_dir, "test-gen-skill.md", _VALID_SKILL_MD)

        registry = SkillRegistry()
        old_gen = Skill(
            name="test-gen-skill",
            slug="test-gen-skill",
            file_path=Path("/fake/old.md"),
            source="generated",
            body="old generated body",
        )
        registry.register_skill(old_gen)

        count = registry.load_generated_skills([tmp_path])

        assert count == 1
        skill = registry.get("test-gen-skill")
        assert skill.source == "generated"
        assert "Body content here." in skill.body

    def test_empty_generated_directory(self, tmp_path: Path) -> None:
        """An empty generated/ directory loads zero skills without error."""
        gen_dir = tmp_path / "generated"
        gen_dir.mkdir(parents=True)

        registry = SkillRegistry()
        count = registry.load_generated_skills([tmp_path])

        assert count == 0
        assert registry.get_generated_skills() == []

    def test_missing_generated_directory(self, tmp_path: Path) -> None:
        """If generated/ doesn't exist, nothing happens (no error)."""
        registry = SkillRegistry()
        count = registry.load_generated_skills([tmp_path])

        assert count == 0

    def test_missing_parent_directory(self) -> None:
        """If the parent directory itself doesn't exist, no error."""
        registry = SkillRegistry()
        count = registry.load_generated_skills([Path("/nonexistent/path")])

        assert count == 0

    def test_get_generated_skills_filters_correctly(self, tmp_path: Path) -> None:
        """get_generated_skills() returns only source='generated' skills."""
        gen_dir = tmp_path / "generated"
        _write_skill(gen_dir, "gen.md", _MINIMAL_SKILL_MD)

        registry = SkillRegistry()
        # Add a builtin
        registry.register_skill(
            Skill(name="builtin-one", slug="builtin-one", file_path=Path("/x.md"), source="builtin")
        )
        registry.load_generated_skills([tmp_path])

        generated = registry.get_generated_skills()
        assert len(generated) == 1
        assert generated[0].source == "generated"
        assert generated[0].slug == "gen"

    def test_load_from_directories_includes_generated(self, tmp_path: Path) -> None:
        """load_from_directories automatically loads generated/ subdirs."""
        gen_dir = tmp_path / "generated"
        _write_skill(gen_dir, "auto.md", _MINIMAL_SKILL_MD)
        # Also put a normal skill in the parent
        _write_skill(tmp_path, "normal.md", _VALID_SKILL_MD)

        registry = SkillRegistry()
        count = registry.load_from_directories([tmp_path])

        # Both should be loaded
        assert count >= 2
        normal = registry.get("normal")
        assert normal is not None
        assert normal.source == "builtin"

        gen = registry.get("auto")
        assert gen is not None
        assert gen.source == "generated"

    def test_non_md_files_ignored(self, tmp_path: Path) -> None:
        """Non-.md files in generated/ are ignored."""
        gen_dir = tmp_path / "generated"
        gen_dir.mkdir(parents=True)
        (gen_dir / "readme.txt").write_text("not a skill", encoding="utf-8")
        (gen_dir / "data.json").write_text("{}", encoding="utf-8")

        registry = SkillRegistry()
        count = registry.load_generated_skills([tmp_path])

        assert count == 0
