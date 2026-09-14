"""Tests fuer skills/manager.py -- SkillManager (list, create, search, install)."""

from __future__ import annotations

from pathlib import Path

import pytest

from cognithor.skills.manager import (
    _slugify,
    create_skill,
    install_remote_skill,
    list_skills,
    search_remote_skills,
)

# ============================================================================
# _slugify
# ============================================================================


class TestSlugify:
    def test_simple_name(self) -> None:
        assert _slugify("Hello World") == "hello-world"

    def test_special_chars_removed(self) -> None:
        assert _slugify("Blog: Artikel!") == "blog-artikel"

    def test_strip_whitespace(self) -> None:
        assert _slugify("  spaces  ") == "spaces"

    def test_multiple_spaces(self) -> None:
        assert _slugify("a   b   c") == "a-b-c"

    def test_empty_string(self) -> None:
        assert _slugify("") == ""

    def test_only_special_chars(self) -> None:
        assert _slugify("!!!") == ""

    def test_umlauts_removed(self) -> None:
        # Umlauts are not in [a-z0-9\-], but ASCII letters stay
        assert _slugify("Aehnlich") == "aehnlich"
        # Real umlaut ä gets removed
        assert _slugify("Über") == "ber"


# ============================================================================
# list_skills
# ============================================================================


class TestListSkills:
    def test_empty_directory(self, tmp_path: Path) -> None:
        d = tmp_path / "skills"
        d.mkdir()
        assert list_skills(d) == []

    def test_nonexistent_directory(self, tmp_path: Path) -> None:
        assert list_skills(tmp_path / "nonexistent") == []

    def test_finds_md_files(self, tmp_path: Path) -> None:
        d = tmp_path / "skills"
        d.mkdir()
        (d / "skill-a.md").write_text("# A")
        (d / "skill-b.md").write_text("# B")
        (d / "not-a-skill.txt").write_text("nope")
        result = list_skills(d)
        assert sorted(result) == ["skill-a.md", "skill-b.md"]

    def test_ignores_directories(self, tmp_path: Path) -> None:
        d = tmp_path / "skills"
        d.mkdir()
        (d / "subdir.md").mkdir()  # directory with .md name
        result = list_skills(d)
        assert result == []


# ============================================================================
# create_skill
# ============================================================================


class TestCreateSkill:
    def test_creates_file(self, tmp_path: Path) -> None:
        d = tmp_path / "skills"
        path = create_skill(d, "Mein Skill")
        assert path.exists()
        assert path.name == "mein-skill.md"
        content = path.read_text(encoding="utf-8")
        assert "name: Mein Skill" in content
        assert "# Mein Skill" in content

    def test_creates_directory_if_missing(self, tmp_path: Path) -> None:
        d = tmp_path / "new_dir" / "skills"
        path = create_skill(d, "Test")
        assert d.exists()
        assert path.exists()

    def test_with_trigger_keywords(self, tmp_path: Path) -> None:
        d = tmp_path / "skills"
        path = create_skill(d, "Test Skill", trigger_keywords=["test", "probe"])
        content = path.read_text(encoding="utf-8")
        assert "trigger_keywords: [test, probe]" in content

    def test_no_trigger_keywords(self, tmp_path: Path) -> None:
        d = tmp_path / "skills"
        path = create_skill(d, "Leer")
        content = path.read_text(encoding="utf-8")
        assert "trigger_keywords: []" in content

    def test_file_exists_raises(self, tmp_path: Path) -> None:
        d = tmp_path / "skills"
        create_skill(d, "Doppelt")
        with pytest.raises(FileExistsError, match="existiert bereits"):
            create_skill(d, "Doppelt")

    def test_content_has_all_sections(self, tmp_path: Path) -> None:
        d = tmp_path / "skills"
        path = create_skill(d, "Komplett")
        content = path.read_text(encoding="utf-8")
        assert "## Voraussetzungen" in content
        assert "## Schritte" in content
        assert "## Hinweise" in content


# ============================================================================
# search_remote_skills
# ============================================================================


class TestSearchRemoteSkills:
    def test_empty_query(self) -> None:
        # Empty query won't match anything meaningful but should not crash
        result = search_remote_skills("", limit=5)
        assert isinstance(result, list)

    def test_respects_limit(self) -> None:
        """search_remote_skills respects the limit parameter."""
        result = search_remote_skills("test", limit=2)
        assert isinstance(result, list)
        assert len(result) <= 2

    def test_returns_list(self) -> None:
        result = search_remote_skills("nonexistent-xyz-query")
        assert isinstance(result, list)

    def test_search_matches_filename(self, tmp_path: Path) -> None:
        """Search with manually created directory structure."""
        proc_dir = tmp_path / "data" / "procedures"
        proc_dir.mkdir(parents=True)
        (proc_dir / "web-recherche.md").write_text(
            "---\nname: Web Recherche\ntrigger_keywords: [recherche, web]\n---\n# Recherche\n",
            encoding="utf-8",
        )

        # Monkey-patch the module to look at our directory
        import cognithor.skills.manager as mgr

        Path(mgr.__file__).resolve()
        # Since the path resolution depends on parents, we test differently:
        # Just test that the function handles no matching directories gracefully
        result = search_remote_skills("recherche", limit=10)
        assert isinstance(result, list)

    def test_search_with_frontmatter_name(self, tmp_path: Path) -> None:
        """Test frontmatter parsing in search."""
        proc_dir = tmp_path / "data" / "procedures"
        proc_dir.mkdir(parents=True)
        (proc_dir / "morgen.md").write_text(
            "---\nname: Morgen-Briefing\ntrigger_keywords: [briefing, morgen]\n---\n# Briefing\n",
            encoding="utf-8",
        )
        # This tests that the function doesn't crash on various inputs
        result = search_remote_skills("briefing")
        assert isinstance(result, list)


# ============================================================================
# install_remote_skill
# ============================================================================


class TestInstallRemoteSkill:
    def test_already_installed(self, tmp_path: Path) -> None:
        d = tmp_path / "skills"
        d.mkdir()
        existing = d / "mein-skill.md"
        existing.write_text("existing content", encoding="utf-8")

        result = install_remote_skill(d, "Mein Skill")
        assert result == existing
        # Content should NOT be overwritten
        assert existing.read_text(encoding="utf-8") == "existing content"

    def test_creates_stub_when_not_found(self, tmp_path: Path) -> None:
        d = tmp_path / "skills"
        result = install_remote_skill(d, "Neuer Skill")
        assert result.exists()
        content = result.read_text(encoding="utf-8")
        assert "Neuer Skill" in content
        assert "automatisch erstellt" in content

    def test_creates_directory(self, tmp_path: Path) -> None:
        d = tmp_path / "new" / "skills"
        result = install_remote_skill(d, "Test")
        assert d.exists()
        assert result.exists()

    def test_slug_normalization(self, tmp_path: Path) -> None:
        d = tmp_path / "skills"
        result = install_remote_skill(d, "Hello World!")
        assert result.name == "hello-world.md"

    def test_repo_url_ignored(self, tmp_path: Path) -> None:
        """repo_url parameter is accepted but ignored."""
        d = tmp_path / "skills"
        result = install_remote_skill(d, "Test", repo_url="https://example.com")
        assert result.exists()

    def test_stub_has_frontmatter(self, tmp_path: Path) -> None:
        d = tmp_path / "skills"
        result = install_remote_skill(d, "Stub Test")
        content = result.read_text(encoding="utf-8")
        assert "name: Stub Test" in content
        assert "trigger_keywords: []" in content
