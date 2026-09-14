"""Coverage-Tests fuer vault.py -- fehlende Pfade abdecken.

Schwerpunkt: vault_search (Volltextsuche, Tag-Filter, Ordner-Filter),
vault_list (Sortierung, Filter), vault_read (Pfad, Slug, nicht gefunden),
vault_update (Fehler-Pfade), vault_link (bidirektional, bestehende Links),
_find_note, _resolve_folder, _parse_tags, _now_iso, _build_frontmatter,
_read_index Fehler, register_vault_tools.
"""

from __future__ import annotations

from pathlib import Path
from unittest.mock import MagicMock

import pytest

from cognithor.mcp.vault import (
    VaultTools,
    register_vault_tools,
)
from cognithor.mcp.vault_backend import now_iso as _now_iso
from cognithor.mcp.vault_backend import parse_tags as _parse_tags

# ============================================================================
# Fixtures
# ============================================================================


@pytest.fixture
def vault(tmp_path: Path) -> VaultTools:
    config = MagicMock()
    config.vault = MagicMock()
    config.vault.path = str(tmp_path / "vault")
    config.vault.default_folders = {
        "research": "recherchen",
        "meetings": "meetings",
        "knowledge": "wissen",
        "projects": "projekte",
        "daily": "daily",
    }
    return VaultTools(config=config)


# ============================================================================
# _parse_tags
# ============================================================================


class TestParseTags:
    def test_string_tags(self) -> None:
        assert _parse_tags("a, b, c") == ["a", "b", "c"]

    def test_list_tags(self) -> None:
        assert _parse_tags(["A", " B ", "C"]) == ["a", "b", "c"]

    def test_empty_string(self) -> None:
        assert _parse_tags("") == []

    def test_empty_list(self) -> None:
        assert _parse_tags([]) == []

    def test_whitespace_only(self) -> None:
        assert _parse_tags("  ,  , ") == []


# ============================================================================
# _now_iso
# ============================================================================


class TestNowIso:
    def test_format(self) -> None:
        result = _now_iso()
        assert "T" in result
        assert len(result) == 19  # YYYY-MM-DDTHH:MM:SS


# ============================================================================
# _resolve_folder
# ============================================================================


class TestResolveFolder:
    def test_logical_name(self, vault: VaultTools) -> None:
        assert vault._resolve_folder("research") == "recherchen"
        assert vault._resolve_folder("knowledge") == "wissen"

    def test_direct_directory_name(self, vault: VaultTools) -> None:
        assert vault._resolve_folder("recherchen") == "recherchen"

    def test_unknown_fallback(self, vault: VaultTools) -> None:
        assert vault._resolve_folder("nonexistent") == "wissen"


# ============================================================================
# _read_index / _write_index
# ============================================================================


class TestIndexOperations:
    def test_read_index_corrupt_json(self, vault: VaultTools) -> None:
        vault._index_path.write_text("not valid json", encoding="utf-8")
        result = vault._read_index()
        assert result == {}

    def test_update_index_preserves_created(self, vault: VaultTools) -> None:
        # First write
        vault._update_index("Test", "wissen/test.md", ["a"], "wissen")
        idx = vault._read_index()
        created = idx["Test"]["created"]

        # Second write should preserve created
        vault._update_index("Test", "wissen/test.md", ["a", "b"], "wissen")
        idx2 = vault._read_index()
        assert idx2["Test"]["created"] == created
        assert "b" in idx2["Test"]["tags"]


# ============================================================================
# _build_frontmatter
# ============================================================================


class TestBuildFrontmatter:
    def test_basic(self, vault: VaultTools) -> None:
        fm = vault._build_frontmatter("Test Title", ["tag1", "tag2"])
        assert "---" in fm
        assert 'title: "Test Title"' in fm
        assert "tags: [tag1, tag2]" in fm
        assert "author: jarvis" in fm

    def test_with_sources(self, vault: VaultTools) -> None:
        fm = vault._build_frontmatter(
            "T", ["t"], sources=["https://example.test/page1", "https://example.test/page2"]
        )
        assert "sources:" in fm
        assert "example.test/page1" in fm

    def test_with_linked_notes(self, vault: VaultTools) -> None:
        fm = vault._build_frontmatter("T", ["t"], linked_notes=["Note A", "Note B"])
        assert "linked_notes:" in fm
        assert '"Note A"' in fm


# ============================================================================
# vault_save edge cases
# ============================================================================


class TestVaultSaveEdgeCases:
    @pytest.mark.asyncio
    async def test_empty_title(self, vault: VaultTools) -> None:
        result = await vault.vault_save(title="", content="text")
        assert "Fehler" in result or "error" in result.lower()

    @pytest.mark.asyncio
    async def test_empty_content(self, vault: VaultTools) -> None:
        result = await vault.vault_save(title="Title", content="")
        assert "Fehler" in result or "error" in result.lower()

    @pytest.mark.asyncio
    async def test_duplicate_filename_increments(self, vault: VaultTools) -> None:
        await vault.vault_save(title="Dup Test", content="First")
        await vault.vault_save(title="Dup Test", content="Second")
        files = list(vault._vault_root.rglob("*dup-test*.md"))
        assert len(files) == 2

    @pytest.mark.asyncio
    async def test_save_with_sources_and_links(self, vault: VaultTools) -> None:
        result = await vault.vault_save(
            title="Full Note",
            content="Body text.",
            tags="test",
            sources="https://a.com, https://b.com",
            linked_notes="Note A, Note B",
        )
        assert "gespeichert" in result.lower()
        files = list(vault._vault_root.rglob("*full-note*.md"))
        text = files[0].read_text(encoding="utf-8")
        assert "## Quellen" in text
        assert "## Verknüpfte Notizen" in text
        assert "[[Note A]]" in text

    @pytest.mark.asyncio
    async def test_save_in_custom_folder(self, vault: VaultTools) -> None:
        result = await vault.vault_save(
            title="Meeting Note",
            content="Meeting content.",
            folder="meetings",
        )
        assert "gespeichert" in result.lower()


# ============================================================================
# vault_search
# ============================================================================


class TestVaultSearch:
    @pytest.mark.asyncio
    async def test_empty_query(self, vault: VaultTools) -> None:
        result = await vault.vault_search(query="")
        assert "Fehler" in result or "error" in result.lower()

    @pytest.mark.asyncio
    async def test_search_finds_content(self, vault: VaultTools) -> None:
        await vault.vault_save(
            title="Searchable", content="This contains a unique keyword here.", tags="test"
        )
        result = await vault.vault_search(query="unique keyword")
        assert "Searchable" in result
        assert "1 Treffer" in result

    @pytest.mark.asyncio
    async def test_search_no_results(self, vault: VaultTools) -> None:
        await vault.vault_save(title="Other", content="Not what you search for.")
        result = await vault.vault_search(query="zzz_nonexistent")
        assert "Keine Notizen" in result

    @pytest.mark.asyncio
    async def test_search_with_tag_filter(self, vault: VaultTools) -> None:
        await vault.vault_save(title="Tagged Note", content="Body with searchterm.", tags="finance")
        await vault.vault_save(title="Untagged Note", content="Also has searchterm.", tags="other")
        result = await vault.vault_search(query="searchterm", tags="finance")
        assert "Tagged Note" in result
        # The untagged one should not appear when filtered by finance
        assert "Untagged Note" not in result

    @pytest.mark.asyncio
    async def test_search_with_folder_filter(self, vault: VaultTools) -> None:
        await vault.vault_save(title="Research Note", content="Body findme.", folder="research")
        await vault.vault_save(title="Knowledge Note", content="Also findme.", folder="knowledge")
        result = await vault.vault_search(query="findme", folder="research")
        assert "Research Note" in result

    @pytest.mark.asyncio
    async def test_search_limit(self, vault: VaultTools) -> None:
        for i in range(5):
            await vault.vault_save(title=f"Note {i}", content=f"Common content {i}.")
        result = await vault.vault_search(query="Common content", limit=2)
        # Should have at most 2 results
        assert result.count("[") <= 3  # [1] and [2] + maybe partial

    @pytest.mark.asyncio
    async def test_search_skips_underscore_files(self, vault: VaultTools) -> None:
        # The _index.json should be skipped by search
        await vault.vault_save(title="Normal", content="Normal content.")
        result = await vault.vault_search(query="_index")
        # Should either not find or not include _index.json
        assert "Keine Notizen" in result or "_index" not in result.lower()


# ============================================================================
# vault_list
# ============================================================================


class TestVaultList:
    @pytest.mark.asyncio
    async def test_list_empty(self, vault: VaultTools) -> None:
        result = await vault.vault_list()
        assert "Keine Notizen" in result

    @pytest.mark.asyncio
    async def test_list_all(self, vault: VaultTools) -> None:
        await vault.vault_save(title="Note 1", content="Content 1.")
        await vault.vault_save(title="Note 2", content="Content 2.")
        result = await vault.vault_list()
        assert "Note 1" in result
        assert "Note 2" in result

    @pytest.mark.asyncio
    async def test_list_sort_by_title(self, vault: VaultTools) -> None:
        await vault.vault_save(title="Zebra", content="Z content.")
        await vault.vault_save(title="Alpha", content="A content.")
        result = await vault.vault_list(sort_by="title")
        alpha_pos = result.find("Alpha")
        zebra_pos = result.find("Zebra")
        assert alpha_pos < zebra_pos

    @pytest.mark.asyncio
    async def test_list_sort_by_created(self, vault: VaultTools) -> None:
        await vault.vault_save(title="First", content="First content.")
        await vault.vault_save(title="Second", content="Second content.")
        result = await vault.vault_list(sort_by="created")
        assert "First" in result
        assert "Second" in result

    @pytest.mark.asyncio
    async def test_list_filter_by_folder(self, vault: VaultTools) -> None:
        await vault.vault_save(title="Research Item", content="R content.", folder="research")
        await vault.vault_save(title="Knowledge Item", content="K content.", folder="knowledge")
        result = await vault.vault_list(folder="research")
        assert "Research Item" in result
        assert "Knowledge Item" not in result

    @pytest.mark.asyncio
    async def test_list_filter_by_tags(self, vault: VaultTools) -> None:
        await vault.vault_save(title="Finance Note", content="Money stuff.", tags="finance")
        await vault.vault_save(title="Tech Note", content="Code stuff.", tags="tech")
        result = await vault.vault_list(tags="finance")
        assert "Finance Note" in result
        assert "Tech Note" not in result

    @pytest.mark.asyncio
    async def test_list_with_limit(self, vault: VaultTools) -> None:
        for i in range(5):
            await vault.vault_save(title=f"Limit Note {i}", content=f"Content {i}.")
        result = await vault.vault_list(limit=2)
        assert "2 Notizen" in result


# ============================================================================
# vault_read
# ============================================================================


class TestVaultRead:
    @pytest.mark.asyncio
    async def test_read_empty_identifier(self, vault: VaultTools) -> None:
        result = await vault.vault_read("")
        assert "Fehler" in result or "error" in result.lower()

    @pytest.mark.asyncio
    async def test_read_by_title(self, vault: VaultTools) -> None:
        await vault.vault_save(title="Readable", content="Read this content.")
        result = await vault.vault_read("Readable")
        assert "Read this content." in result

    @pytest.mark.asyncio
    async def test_read_by_relative_path(self, vault: VaultTools) -> None:
        await vault.vault_save(title="Path Test", content="Path content.")
        # Find the file
        files = list(vault._vault_root.rglob("*path-test*.md"))
        assert len(files) >= 1
        rel_path = str(files[0].relative_to(vault._vault_root))
        result = await vault.vault_read(rel_path)
        assert "Path content." in result

    @pytest.mark.asyncio
    async def test_read_by_slug(self, vault: VaultTools) -> None:
        await vault.vault_save(title="Slug Read Test", content="Slug content.")
        result = await vault.vault_read("slug-read-test")
        assert "Slug content." in result

    @pytest.mark.asyncio
    async def test_read_not_found(self, vault: VaultTools) -> None:
        result = await vault.vault_read("nonexistent")
        assert "not_found" in result or "nicht gefunden" in result


# ============================================================================
# vault_update edge cases
# ============================================================================


class TestVaultUpdateEdgeCases:
    @pytest.mark.asyncio
    async def test_update_empty_identifier(self, vault: VaultTools) -> None:
        result = await vault.vault_update(identifier="", append_content="x")
        assert "Fehler" in result or "error" in result.lower()

    @pytest.mark.asyncio
    async def test_update_no_changes(self, vault: VaultTools) -> None:
        result = await vault.vault_update(identifier="Something", append_content="", add_tags="")
        assert "Fehler" in result or "error" in result.lower()

    @pytest.mark.asyncio
    async def test_update_not_found(self, vault: VaultTools) -> None:
        result = await vault.vault_update(identifier="nonexistent", append_content="text")
        assert "not_found" in result or "nicht gefunden" in result

    @pytest.mark.asyncio
    async def test_update_only_append(self, vault: VaultTools) -> None:
        await vault.vault_save(title="Appendable", content="Original.")
        result = await vault.vault_update(identifier="Appendable", append_content="Extra text.")
        assert "aktualisiert" in result.lower()
        content = await vault.vault_read("Appendable")
        assert "Extra text." in content

    @pytest.mark.asyncio
    async def test_update_only_tags(self, vault: VaultTools) -> None:
        await vault.vault_save(title="Taggable", content="Content.", tags="old")
        result = await vault.vault_update(identifier="Taggable", add_tags="newtag")
        assert "aktualisiert" in result.lower()
        content = await vault.vault_read("Taggable")
        data, _, _ = vault._parse_frontmatter(content)
        tags = data.get("tags", [])
        assert "old" in tags
        assert "newtag" in tags


# ============================================================================
# vault_link edge cases
# ============================================================================


class TestVaultLinkEdgeCases:
    @pytest.mark.asyncio
    async def test_link_source_not_found(self, vault: VaultTools) -> None:
        await vault.vault_save(title="Target", content="T content.")
        result = await vault.vault_link(source_note="nonexistent", target_note="Target")
        assert (
            "source_not_found" in result
            or "not_found" in result
            or "Quell-Notiz nicht gefunden" in result
        )

    @pytest.mark.asyncio
    async def test_link_target_not_found(self, vault: VaultTools) -> None:
        await vault.vault_save(title="Source", content="S content.")
        result = await vault.vault_link(source_note="Source", target_note="nonexistent")
        assert (
            "target_not_found" in result
            or "not_found" in result
            or "Ziel-Notiz nicht gefunden" in result
        )

    @pytest.mark.asyncio
    async def test_link_already_linked_no_duplicate(self, vault: VaultTools) -> None:
        await vault.vault_save(title="A", content="Content A.")
        await vault.vault_save(title="B", content="Content B.")
        # First link
        await vault.vault_link(source_note="A", target_note="B")
        # Second link (should not duplicate)
        result = await vault.vault_link(source_note="A", target_note="B")
        assert "Verknüpfung" in result

        # Check that B appears only once in linked_notes in A's frontmatter
        content_a = await vault.vault_read("A")
        data, _, _ = vault._parse_frontmatter(content_a)
        linked = data.get("linked_notes", [])
        b_count = sum(1 for n in linked if "B" in str(n))
        assert b_count == 1


# ============================================================================
# _find_note
# ============================================================================


class TestFindNote:
    @pytest.mark.asyncio
    async def test_find_by_direct_path(self, vault: VaultTools) -> None:
        await vault.vault_save(title="Direct Path", content="C.")
        files = list(vault._vault_root.rglob("*direct-path*.md"))
        rel = str(files[0].relative_to(vault._vault_root))
        result = vault._find_note(rel)
        assert result is not None

    @pytest.mark.asyncio
    async def test_find_by_title(self, vault: VaultTools) -> None:
        await vault.vault_save(title="Title Find", content="C.")
        result = vault._find_note("Title Find")
        assert result is not None

    @pytest.mark.asyncio
    async def test_find_by_slug(self, vault: VaultTools) -> None:
        await vault.vault_save(title="Slug Find Test", content="C.")
        result = vault._find_note("slug-find-test")
        assert result is not None

    def test_find_not_found(self, vault: VaultTools) -> None:
        result = vault._find_note("nonexistent_note_xyz")
        assert result is None


# ============================================================================
# register_vault_tools
# ============================================================================


class TestRegisterVaultTools:
    def test_registers_all_tools(self, tmp_path: Path) -> None:
        mock_client = MagicMock()
        config = MagicMock()
        config.vault = MagicMock()
        config.vault.path = str(tmp_path / "vault")
        config.vault.default_folders = {}
        vault = register_vault_tools(mock_client, config=config)
        assert isinstance(vault, VaultTools)
        assert mock_client.register_builtin_handler.call_count == 7

    def test_tool_names(self, tmp_path: Path) -> None:
        mock_client = MagicMock()
        config = MagicMock()
        config.vault = MagicMock()
        config.vault.path = str(tmp_path / "vault")
        config.vault.default_folders = {}
        register_vault_tools(mock_client, config=config)
        registered = [call.args[0] for call in mock_client.register_builtin_handler.call_args_list]
        assert "vault_save" in registered
        assert "vault_search" in registered
        assert "vault_list" in registered
        assert "vault_read" in registered
        assert "vault_update" in registered
        assert "vault_link" in registered

    def test_register_without_config(self) -> None:
        mock_client = MagicMock()
        vault = register_vault_tools(mock_client)
        assert isinstance(vault, VaultTools)


# ============================================================================
# _ensure_structure
# ============================================================================


class TestEnsureStructure:
    def test_creates_directories(self, tmp_path: Path) -> None:
        config = MagicMock()
        config.vault = MagicMock()
        config.vault.path = str(tmp_path / "new_vault")
        config.vault.default_folders = {"knowledge": "wissen", "projects": "projekte"}
        VaultTools(config=config)
        assert (tmp_path / "new_vault" / "wissen").exists()
        assert (tmp_path / "new_vault" / "projekte").exists()
        assert (tmp_path / "new_vault" / "_index.json").exists()


# ============================================================================
# Init without config
# ============================================================================


class TestVaultNoConfig:
    def test_defaults(self) -> None:
        vault = VaultTools(config=None)
        assert vault._vault_root == Path.home() / ".cognithor" / "vault"
        assert "research" in vault._default_folders
