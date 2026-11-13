"""Tests fuer das Search-Tools MCP-Modul.

Testet Registrierung, Glob-Matching, Inhaltssuche, Binaer-Erkennung und Encoding-Fallback.
"""

from __future__ import annotations

from pathlib import Path
from unittest.mock import MagicMock

import pytest

from cognithor.config import CognithorConfig, ensure_directory_structure
from cognithor.mcp.search_tools import SearchTools, SearchToolsError, register_search_tools

# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def search_config(tmp_path: Path) -> CognithorConfig:
    """CognithorConfig mit temporaerem Workspace."""
    home = tmp_path / ".cognithor"
    config = CognithorConfig(cognithor_home=home)
    ensure_directory_structure(config)
    return config


@pytest.fixture
def search_tools(search_config: CognithorConfig) -> SearchTools:
    return SearchTools(search_config)


@pytest.fixture
def mock_mcp_client() -> MagicMock:
    client = MagicMock()
    client.register_builtin_handler = MagicMock()
    return client


@pytest.fixture
def populated_workspace(search_config: CognithorConfig) -> Path:
    """Workspace mit Test-Dateien befuellt."""
    ws = search_config.workspace_dir
    ws.mkdir(parents=True, exist_ok=True)

    # Python files
    (ws / "main.py").write_text("def hello():\n    print('Hello World')\n", encoding="utf-8")
    (ws / "utils.py").write_text("import os\nTODO_MARKER = 'fix me'\n", encoding="utf-8")

    # Subdirectory
    sub = ws / "lib"
    sub.mkdir()
    (sub / "helper.py").write_text("class Helper:\n    pass\n", encoding="utf-8")
    (sub / "data.json").write_text('{"key": "value"}\n', encoding="utf-8")

    # Excluded directory
    git_dir = ws / ".git"
    git_dir.mkdir()
    (git_dir / "config").write_text("[core]\n", encoding="utf-8")

    # Node modules
    nm = ws / "node_modules"
    nm.mkdir()
    (nm / "pkg.js").write_text("module.exports = {};\n", encoding="utf-8")

    # Binary file
    (ws / "image.bin").write_bytes(b"\x89PNG\r\n\x00\x1a\n" + b"\x00" * 100)

    # Latin-1 encoded file
    (ws / "legacy.txt").write_bytes("Umlaute: \xe4\xf6\xfc\n".encode("latin-1"))

    return ws


# ---------------------------------------------------------------------------
# Registration
# ---------------------------------------------------------------------------


class TestRegistration:
    def test_register_search_tools_registers_three_tools(
        self, mock_mcp_client: MagicMock, search_config: CognithorConfig
    ) -> None:
        register_search_tools(mock_mcp_client, search_config)
        assert mock_mcp_client.register_builtin_handler.call_count == 3

    def test_register_search_tools_tool_names(
        self, mock_mcp_client: MagicMock, search_config: CognithorConfig
    ) -> None:
        register_search_tools(mock_mcp_client, search_config)
        registered_names = [
            call.args[0] for call in mock_mcp_client.register_builtin_handler.call_args_list
        ]
        assert "search_files" in registered_names
        assert "find_in_files" in registered_names
        assert "find_and_replace" in registered_names


# ---------------------------------------------------------------------------
# Path Validation
# ---------------------------------------------------------------------------


class TestPathValidation:
    def test_validate_path_within_workspace(self, search_tools: SearchTools) -> None:
        workspace = search_tools._workspace.expanduser().resolve()
        workspace.mkdir(parents=True, exist_ok=True)
        result = search_tools._validate_path(str(workspace))
        assert result == workspace

    def test_validate_path_outside_workspace_raises(self, search_tools: SearchTools) -> None:
        with pytest.raises(SearchToolsError, match="Zugriff verweigert"):
            search_tools._validate_path("/etc/passwd")


# ---------------------------------------------------------------------------
# Binary Detection
# ---------------------------------------------------------------------------


class TestBinaryDetection:
    def test_text_file_not_binary(self, populated_workspace: Path) -> None:
        assert not SearchTools._is_binary(populated_workspace / "main.py")

    def test_binary_file_detected(self, populated_workspace: Path) -> None:
        assert SearchTools._is_binary(populated_workspace / "image.bin")

    def test_nonexistent_file_treated_as_binary(self, tmp_path: Path) -> None:
        assert SearchTools._is_binary(tmp_path / "nope.xyz")


# ---------------------------------------------------------------------------
# Encoding Fallback
# ---------------------------------------------------------------------------


class TestEncodingFallback:
    def test_read_utf8(self, populated_workspace: Path) -> None:
        content = SearchTools._read_file_text(populated_workspace / "main.py")
        assert content is not None
        assert "hello" in content

    def test_read_latin1_fallback(self, populated_workspace: Path) -> None:
        content = SearchTools._read_file_text(populated_workspace / "legacy.txt")
        assert content is not None
        assert "Umlaute" in content


# ---------------------------------------------------------------------------
# Excluded Directories
# ---------------------------------------------------------------------------


class TestExcludedDirs:
    def test_git_excluded(self) -> None:
        assert SearchTools._is_excluded_dir(".git")

    def test_node_modules_excluded(self) -> None:
        assert SearchTools._is_excluded_dir("node_modules")

    def test_pycache_excluded(self) -> None:
        assert SearchTools._is_excluded_dir("__pycache__")

    def test_egg_info_excluded(self) -> None:
        assert SearchTools._is_excluded_dir("mypackage.egg-info")

    def test_normal_dir_not_excluded(self) -> None:
        assert not SearchTools._is_excluded_dir("src")


# ---------------------------------------------------------------------------
# search_files
# ---------------------------------------------------------------------------


class TestSearchFiles:
    async def test_search_py_files(
        self, search_tools: SearchTools, populated_workspace: Path
    ) -> None:
        result = await search_tools.search_files("**/*.py")
        assert "main.py" in result
        assert "utils.py" in result
        assert "helper.py" in result

    async def test_search_excludes_git(
        self, search_tools: SearchTools, populated_workspace: Path
    ) -> None:
        result = await search_tools.search_files("**/*")
        assert (
            ".git" not in result or "config" not in result.split(".git")[0]
            if ".git" in result
            else True
        )
        # Better check: the .git/config file should not appear
        assert ".git" not in result.replace("git_", "").replace("git.", "")

    async def test_search_excludes_node_modules(
        self, search_tools: SearchTools, populated_workspace: Path
    ) -> None:
        result = await search_tools.search_files("**/*.js")
        assert "pkg.js" not in result

    async def test_search_no_matches(
        self, search_tools: SearchTools, populated_workspace: Path
    ) -> None:
        result = await search_tools.search_files("*.xyz")
        assert "Keine Dateien" in result

    async def test_search_empty_pattern(self, search_tools: SearchTools) -> None:
        result = await search_tools.search_files("")
        assert "erforderlich" in result

    async def test_search_max_results(
        self, search_tools: SearchTools, populated_workspace: Path
    ) -> None:
        result = await search_tools.search_files("**/*", max_results=2)
        assert "begrenzt" in result

    async def test_search_json_files(
        self, search_tools: SearchTools, populated_workspace: Path
    ) -> None:
        result = await search_tools.search_files("**/*.json")
        assert "data.json" in result


# ---------------------------------------------------------------------------
# find_in_files
# ---------------------------------------------------------------------------


class TestFindInFiles:
    async def test_find_text(self, search_tools: SearchTools, populated_workspace: Path) -> None:
        result = await search_tools.find_in_files("Hello World")
        assert "main.py" in result
        assert "Hello World" in result

    async def test_find_regex(self, search_tools: SearchTools, populated_workspace: Path) -> None:
        result = await search_tools.find_in_files(r"def \w+\(", regex=True)
        assert "main.py" in result

    async def test_find_with_glob_filter(
        self, search_tools: SearchTools, populated_workspace: Path
    ) -> None:
        result = await search_tools.find_in_files("import", glob="*.py")
        assert "utils.py" in result

    async def test_find_skips_binary(
        self, search_tools: SearchTools, populated_workspace: Path
    ) -> None:
        result = await search_tools.find_in_files("PNG")
        # Should not find in binary file
        assert "image.bin" not in result

    async def test_find_no_matches(
        self, search_tools: SearchTools, populated_workspace: Path
    ) -> None:
        result = await search_tools.find_in_files("NONEXISTENT_STRING_xyz123")
        assert "Keine Treffer" in result

    async def test_find_empty_query(self, search_tools: SearchTools) -> None:
        result = await search_tools.find_in_files("")
        assert "erforderlich" in result

    async def test_find_invalid_regex(self, search_tools: SearchTools) -> None:
        result = await search_tools.find_in_files("[invalid", regex=True)
        assert "Ungueltig" in result

    async def test_find_context_lines(
        self, search_tools: SearchTools, populated_workspace: Path
    ) -> None:
        result = await search_tools.find_in_files("Hello World", context_lines=1)
        assert "main.py" in result
        # Should show the match line plus context
        assert ">" in result  # match marker

    async def test_find_in_latin1_file(
        self, search_tools: SearchTools, populated_workspace: Path
    ) -> None:
        result = await search_tools.find_in_files("Umlaute")
        assert "legacy.txt" in result


# ---------------------------------------------------------------------------
# find_and_replace
# ---------------------------------------------------------------------------


class TestFindAndReplace:
    async def test_dry_run_default(
        self, search_tools: SearchTools, populated_workspace: Path
    ) -> None:
        result = await search_tools.find_and_replace(
            query="TODO_MARKER",
            replacement="DONE_MARKER",
        )
        assert "DRY RUN" in result
        assert "TODO_MARKER" in result or "utils.py" in result

        # Verify file NOT changed
        content = (populated_workspace / "utils.py").read_text(encoding="utf-8")
        assert "TODO_MARKER" in content

    async def test_actual_replace(
        self, search_tools: SearchTools, populated_workspace: Path
    ) -> None:
        result = await search_tools.find_and_replace(
            query="TODO_MARKER",
            replacement="DONE_MARKER",
            dry_run=False,
        )
        assert "abgeschlossen" in result

        # Verify file changed
        content = (populated_workspace / "utils.py").read_text(encoding="utf-8")
        assert "DONE_MARKER" in content
        assert "TODO_MARKER" not in content

        # Verify backup created
        bak = populated_workspace / "utils.py.bak"
        assert bak.exists()

    async def test_replace_with_glob_filter(
        self, search_tools: SearchTools, populated_workspace: Path
    ) -> None:
        result = await search_tools.find_and_replace(
            query="Hello",
            replacement="Hi",
            glob="*.py",
            dry_run=True,
        )
        assert "main.py" in result

    async def test_replace_regex(
        self, search_tools: SearchTools, populated_workspace: Path
    ) -> None:
        result = await search_tools.find_and_replace(
            query=r"def (\w+)",
            replacement=r"def new_\1",
            regex=True,
            dry_run=True,
        )
        assert "main.py" in result

    async def test_replace_no_matches(
        self, search_tools: SearchTools, populated_workspace: Path
    ) -> None:
        result = await search_tools.find_and_replace(
            query="NONEXISTENT_xyz",
            replacement="whatever",
        )
        assert "Keine Treffer" in result

    async def test_replace_empty_query(self, search_tools: SearchTools) -> None:
        result = await search_tools.find_and_replace(query="", replacement="x")
        assert "erforderlich" in result

    async def test_replace_skips_binary(
        self, search_tools: SearchTools, populated_workspace: Path
    ) -> None:
        result = await search_tools.find_and_replace(
            query="PNG",
            replacement="JPG",
            dry_run=True,
        )
        assert "image.bin" not in result


# ---------------------------------------------------------------------------
# _walk_files
# ---------------------------------------------------------------------------


class TestWalkFiles:
    def test_walk_excludes_git_dir(
        self, search_tools: SearchTools, populated_workspace: Path
    ) -> None:
        files = search_tools._walk_files(populated_workspace)
        file_strs = [str(f) for f in files]
        assert not any(".git" + str(Path("/")) in s or ".git\\" in s for s in file_strs)

    def test_walk_excludes_node_modules(
        self, search_tools: SearchTools, populated_workspace: Path
    ) -> None:
        files = search_tools._walk_files(populated_workspace)
        file_strs = [str(f) for f in files]
        assert not any("node_modules" in s for s in file_strs)

    def test_walk_with_glob_filter(
        self, search_tools: SearchTools, populated_workspace: Path
    ) -> None:
        files = search_tools._walk_files(populated_workspace, file_glob="*.py")
        assert all(f.suffix == ".py" for f in files)
        assert len(files) >= 3  # main.py, utils.py, helper.py
