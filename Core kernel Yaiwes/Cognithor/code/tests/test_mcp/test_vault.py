"""Tests für jarvis.mcp.vault — YAML-Frontmatter-Parsing und Vault-Operationen.

Validiert die PyYAML-basierte Frontmatter-Verarbeitung:
- _parse_frontmatter(): YAML-Parsing, Edge-Cases, Fehlerfälle
- _serialize_frontmatter(): Dict → YAML-Frontmatter mit Obsidian-Kompatibilität
- _extract_frontmatter_tags(): Tag-Extraktion (Liste, String, leer)
- _extract_frontmatter_field(): Einzelfeld-Extraktion
- _replace_frontmatter_field(): Feldersetzung und -hinzufügung
- _add_linked_note(): Linked-Notes-Management
- _extract_snippet(): Snippet-Extraktion mit Frontmatter-Skip
- vault_save / vault_update / vault_link: Integrationstests
"""

from __future__ import annotations

from typing import TYPE_CHECKING
from unittest.mock import MagicMock

import pytest

from cognithor.mcp.vault import VaultTools, _slugify

if TYPE_CHECKING:
    from pathlib import Path

# ── Fixtures ─────────────────────────────────────────────────────────────


@pytest.fixture
def vault(tmp_path: Path) -> VaultTools:
    """VaultTools mit temporärem Vault-Verzeichnis."""
    config = MagicMock()
    config.vault = MagicMock()
    config.vault.enabled = True
    config.vault.path = str(tmp_path / "vault")
    config.vault.auto_save_research = False
    config.vault.default_folders = {"allgemein": "allgemein"}
    config.cognithor_home = tmp_path
    vt = VaultTools(config=config)
    vt._vault_path = tmp_path / "vault"
    vt._vault_path.mkdir(parents=True, exist_ok=True)
    return vt


# ── _slugify ──────────────────────────────────────────────────────────────


class TestSlugify:
    def test_basic(self) -> None:
        assert _slugify("Hello World") == "hello-world"

    def test_umlauts(self) -> None:
        assert _slugify("Über Größe") == "ueber-groesse"

    def test_special_chars(self) -> None:
        assert _slugify("Test!@#$%") == "test"

    def test_empty(self) -> None:
        assert _slugify("") == "notiz"

    def test_max_length(self) -> None:
        result = _slugify("a" * 100)
        assert len(result) <= 80


# ── _parse_frontmatter ───────────────────────────────────────────────────


class TestParseFrontmatter:
    def test_valid_frontmatter(self, vault: VaultTools) -> None:
        content = "---\ntitle: Test\ntags: [a, b]\n---\nBody text"
        data, start, end = vault._parse_frontmatter(content)
        assert data == {"title": "Test", "tags": ["a", "b"]}
        assert start == 0
        assert end > 0

    def test_no_frontmatter(self, vault: VaultTools) -> None:
        content = "Just plain text"
        data, start, end = vault._parse_frontmatter(content)
        assert data == {}
        assert start == -1
        assert end == -1

    def test_incomplete_frontmatter(self, vault: VaultTools) -> None:
        content = "---\ntitle: Test\nNo closing delimiter"
        data, start, end = vault._parse_frontmatter(content)
        assert data == {}
        assert start == -1

    def test_empty_frontmatter(self, vault: VaultTools) -> None:
        content = "---\n---\nBody"
        data, start, end = vault._parse_frontmatter(content)
        # yaml.safe_load("") returns None → not a dict → ({}, -1, -1)
        assert data == {}

    def test_complex_yaml(self, vault: VaultTools) -> None:
        content = (
            '---\ntitle: "Test: Complex"\ntags: [python, yaml]\n'
            "date: 2026-03-01\ncount: 42\n---\nBody"
        )
        data, start, end = vault._parse_frontmatter(content)
        assert data["title"] == "Test: Complex"
        assert data["tags"] == ["python", "yaml"]
        assert data["count"] == 42

    def test_multiline_values(self, vault: VaultTools) -> None:
        content = "---\ntitle: Test\ndescription: |\n  Line 1\n  Line 2\n---\nBody"
        data, start, end = vault._parse_frontmatter(content)
        assert "Line 1" in data.get("description", "")

    def test_invalid_yaml(self, vault: VaultTools) -> None:
        content = "---\n: invalid: yaml: [unclosed\n---\nBody"
        data, start, end = vault._parse_frontmatter(content)
        assert data == {}
        assert start == -1

    def test_frontmatter_scalar_not_dict(self, vault: VaultTools) -> None:
        """YAML, das keinen Dict ergibt (z.B. nur ein String)."""
        content = "---\njust a string\n---\nBody"
        data, start, end = vault._parse_frontmatter(content)
        assert data == {}
        assert start == -1

    def test_body_after_frontmatter(self, vault: VaultTools) -> None:
        content = "---\ntitle: Test\n---\n\n# Heading\n\nParagraph"
        data, start, end = vault._parse_frontmatter(content)
        body = content[end:]
        assert body.strip().startswith("# Heading")


# ── _serialize_frontmatter ───────────────────────────────────────────────


class TestSerializeFrontmatter:
    def test_simple(self, vault: VaultTools) -> None:
        data = {"title": "Test", "tags": ["a", "b"]}
        result = vault._serialize_frontmatter(data)
        assert result.startswith("---")
        assert result.endswith("---")
        assert "title: Test" in result
        assert "tags: [a, b]" in result

    def test_empty_dict(self, vault: VaultTools) -> None:
        result = vault._serialize_frontmatter({})
        assert result == "---\n---"

    def test_string_with_special_chars(self, vault: VaultTools) -> None:
        data = {"title": 'Test: "Special"'}
        result = vault._serialize_frontmatter(data)
        assert 'title: "Test: \\"Special\\""' in result or "title:" in result

    def test_list_with_special_chars(self, vault: VaultTools) -> None:
        data = {"tags": ["normal", "has,comma"]}
        result = vault._serialize_frontmatter(data)
        assert '"has,comma"' in result

    def test_roundtrip(self, vault: VaultTools) -> None:
        """Serialisiertes Frontmatter kann wieder geparst werden."""
        original = {"title": "Roundtrip", "tags": ["a", "b"], "count": 42}
        serialized = vault._serialize_frontmatter(original)
        parsed, _, _ = vault._parse_frontmatter(serialized)
        assert parsed["title"] == "Roundtrip"
        assert parsed["tags"] == ["a", "b"]
        assert parsed["count"] == 42


# ── _extract_frontmatter_tags ────────────────────────────────────────────


class TestExtractFrontmatterTags:
    def test_list_tags(self, vault: VaultTools) -> None:
        content = "---\ntags: [Python, YAML, test]\n---\nBody"
        tags = vault._extract_frontmatter_tags(content)
        assert tags == ["python", "yaml", "test"]

    def test_string_tags(self, vault: VaultTools) -> None:
        content = "---\ntags: python, yaml, test\n---\nBody"
        tags = vault._extract_frontmatter_tags(content)
        # YAML parses unquoted "python, yaml, test" as a string → comma-split
        assert "python" in tags

    def test_csv_string_tags(self, vault: VaultTools) -> None:
        """CSV-String als Tags (Fallback für ältere Formate)."""
        content = '---\ntags: "python, yaml"\n---\nBody'
        tags = vault._extract_frontmatter_tags(content)
        # Quoted CSV → parsed as single string → split by comma
        assert "python" in tags

    def test_no_tags(self, vault: VaultTools) -> None:
        content = "---\ntitle: Test\n---\nBody"
        tags = vault._extract_frontmatter_tags(content)
        assert tags == []

    def test_no_frontmatter(self, vault: VaultTools) -> None:
        tags = vault._extract_frontmatter_tags("Just text")
        assert tags == []


# ── _extract_frontmatter_field ───────────────────────────────────────────


class TestExtractFrontmatterField:
    def test_existing_field(self, vault: VaultTools) -> None:
        content = "---\ntitle: Test\nauthor: Claude\n---\nBody"
        assert vault._extract_frontmatter_field(content, "title") == "Test"
        assert vault._extract_frontmatter_field(content, "author") == "Claude"

    def test_missing_field(self, vault: VaultTools) -> None:
        content = "---\ntitle: Test\n---\nBody"
        assert vault._extract_frontmatter_field(content, "missing") == ""

    def test_none_value(self, vault: VaultTools) -> None:
        content = "---\ntitle: null\n---\nBody"
        assert vault._extract_frontmatter_field(content, "title") == ""

    def test_numeric_value(self, vault: VaultTools) -> None:
        content = "---\ncount: 42\n---\nBody"
        assert vault._extract_frontmatter_field(content, "count") == "42"


# ── _replace_frontmatter_field ───────────────────────────────────────────


class TestReplaceFrontmatterField:
    def test_replace_existing(self, vault: VaultTools) -> None:
        content = "---\ntitle: Old\ntags: [a]\n---\nBody"
        result = vault._replace_frontmatter_field(content, "title", "New")
        data, _, _ = vault._parse_frontmatter(result)
        assert data["title"] == "New"
        assert "Body" in result

    def test_add_new_field(self, vault: VaultTools) -> None:
        content = "---\ntitle: Test\n---\nBody"
        result = vault._replace_frontmatter_field(content, "author", "Claude")
        data, _, _ = vault._parse_frontmatter(result)
        assert data["author"] == "Claude"

    def test_replace_with_list(self, vault: VaultTools) -> None:
        content = "---\ntags: [old]\n---\nBody"
        result = vault._replace_frontmatter_field(content, "tags", ["new", "tags"])
        data, _, _ = vault._parse_frontmatter(result)
        assert data["tags"] == ["new", "tags"]

    def test_no_frontmatter(self, vault: VaultTools) -> None:
        content = "Just text"
        result = vault._replace_frontmatter_field(content, "title", "Test")
        assert result == "Just text"  # Keine Änderung

    def test_yaml_string_parsed(self, vault: VaultTools) -> None:
        """YAML-Strings wie '[a, b]' werden als Listen geparst."""
        content = "---\ntags: [old]\n---\nBody"
        result = vault._replace_frontmatter_field(content, "tags", "[new, tags]")
        data, _, _ = vault._parse_frontmatter(result)
        assert data["tags"] == ["new", "tags"]

    def test_body_preserved(self, vault: VaultTools) -> None:
        content = "---\ntitle: Test\n---\n\n# Body\n\nParagraph here."
        result = vault._replace_frontmatter_field(content, "title", "Updated")
        assert "# Body" in result
        assert "Paragraph here." in result


# ── _add_linked_note ─────────────────────────────────────────────────────


class TestAddLinkedNote:
    def test_add_first_link(self, vault: VaultTools) -> None:
        content = "---\ntitle: Test\n---\nBody"
        result = vault._add_linked_note(content, "Other Note")
        data, _, _ = vault._parse_frontmatter(result)
        assert "Other Note" in str(data.get("linked_notes", []))

    def test_no_duplicate(self, vault: VaultTools) -> None:
        content = '---\ntitle: Test\nlinked_notes: ["Note A"]\n---\nBody'
        result = vault._add_linked_note(content, "Note A")
        data, _, _ = vault._parse_frontmatter(result)
        linked = data.get("linked_notes", [])
        count = sum(1 for n in linked if "Note A" in str(n))
        assert count == 1

    def test_add_second_link(self, vault: VaultTools) -> None:
        content = '---\ntitle: Test\nlinked_notes: ["Note A"]\n---\nBody'
        result = vault._add_linked_note(content, "Note B")
        data, _, _ = vault._parse_frontmatter(result)
        linked = [str(n).strip('"') for n in data.get("linked_notes", [])]
        assert "Note A" in linked
        assert "Note B" in linked


# ── _extract_snippet ─────────────────────────────────────────────────────


class TestExtractSnippet:
    def test_basic_snippet(self, vault: VaultTools) -> None:
        content = "---\ntitle: Test\n---\nThis is the body with a keyword inside."
        snippet = vault._extract_snippet(content, "keyword")
        assert "keyword" in snippet
        assert "---" not in snippet

    def test_no_match(self, vault: VaultTools) -> None:
        content = "---\ntitle: Test\n---\nBody text here."
        snippet = vault._extract_snippet(content, "notfound")
        assert snippet == ""

    def test_no_frontmatter(self, vault: VaultTools) -> None:
        content = "Plain text with keyword in it."
        snippet = vault._extract_snippet(content, "keyword")
        assert "keyword" in snippet

    def test_frontmatter_not_in_snippet(self, vault: VaultTools) -> None:
        content = "---\ntitle: search_target\n---\nBody text only."
        # Der Query "search_target" ist im Frontmatter, nicht im Body
        snippet = vault._extract_snippet(content, "search_target")
        assert snippet == ""


# ── Integration: vault_save ──────────────────────────────────────────────


class TestVaultSave:
    @pytest.mark.asyncio
    async def test_save_basic(self, vault: VaultTools) -> None:
        result = await vault.vault_save(
            title="Test Note",
            content="This is test content.",
            tags="test, integration",
        )
        assert "gespeichert" in result.lower() or "test-note" in result.lower()

        # Datei existiert
        files = list(vault._vault_path.rglob("*.md"))
        assert len(files) >= 1
        text = files[0].read_text(encoding="utf-8")
        assert "Test Note" in text
        assert "test content" in text

    @pytest.mark.asyncio
    async def test_save_with_folder(self, vault: VaultTools) -> None:
        # "projects" ist ein Standard-Folder → wird zu "projekte" aufgelöst
        await vault.vault_save(
            title="Projekt Note",
            content="Projekt content.",
            tags="projekt",
            folder="projects",
        )
        # Datei wurde in einem Unterordner gespeichert
        files = list(vault._vault_path.rglob("*projekt-note*.md"))
        assert len(files) >= 1

    @pytest.mark.asyncio
    async def test_save_frontmatter_roundtrip(self, vault: VaultTools) -> None:
        await vault.vault_save(
            title="Roundtrip",
            content="Roundtrip body.",
            tags="tag1, tag2",
        )
        files = list(vault._vault_path.rglob("*roundtrip*.md"))
        assert len(files) >= 1
        text = files[0].read_text(encoding="utf-8")
        data, _, _ = vault._parse_frontmatter(text)
        assert data.get("title") == "Roundtrip"
        assert "tag1" in data.get("tags", [])


# ── Integration: vault_update ────────────────────────────────────────────


class TestVaultUpdate:
    @pytest.mark.asyncio
    async def test_update_append(self, vault: VaultTools) -> None:
        await vault.vault_save(title="Update Me", content="Original.")
        await vault.vault_update(
            identifier="Update Me",
            append_content="Appended content.",
        )
        files = list(vault._vault_path.rglob("*update-me*.md"))
        assert len(files) >= 1
        text = files[0].read_text(encoding="utf-8")
        assert "Original." in text
        assert "Appended content." in text

    @pytest.mark.asyncio
    async def test_update_tags(self, vault: VaultTools) -> None:
        await vault.vault_save(title="Tag Test", content="Content.", tags="old")
        await vault.vault_update(identifier="Tag Test", add_tags="new")
        files = list(vault._vault_path.rglob("*tag-test*.md"))
        text = files[0].read_text(encoding="utf-8")
        data, _, _ = vault._parse_frontmatter(text)
        tags = data.get("tags", [])
        assert "old" in tags
        assert "new" in tags


# ── Integration: vault_link ──────────────────────────────────────────────


class TestVaultLink:
    @pytest.mark.asyncio
    async def test_link_notes(self, vault: VaultTools) -> None:
        await vault.vault_save(title="Note A", content="Content A.")
        await vault.vault_save(title="Note B", content="Content B.")
        await vault.vault_link(source_note="Note A", target_note="Note B")
        # Verify backlink in Note A
        files = list(vault._vault_path.rglob("*note-a*.md"))
        assert len(files) >= 1
        text = files[0].read_text(encoding="utf-8")
        assert "Note B" in text
