"""Tests fuer das Git-Tools MCP-Modul.

Testet Registrierung, Pfad-Validierung und Git-Operationen mit gemocktem subprocess.
"""

from __future__ import annotations

from typing import TYPE_CHECKING
from unittest.mock import MagicMock, patch

import pytest

from cognithor.config import CognithorConfig, ensure_directory_structure
from cognithor.mcp.git_tools import GitTools, GitToolsError, register_git_tools

if TYPE_CHECKING:
    from pathlib import Path

# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def git_config(tmp_path: Path) -> CognithorConfig:
    """CognithorConfig mit temporaerem Workspace."""
    home = tmp_path / ".cognithor"
    config = CognithorConfig(cognithor_home=home)
    ensure_directory_structure(config)
    return config


@pytest.fixture
def git_tools(git_config: CognithorConfig) -> GitTools:
    return GitTools(git_config)


@pytest.fixture
def mock_mcp_client() -> MagicMock:
    """Mock MCP-Client der register_builtin_handler trackt."""
    client = MagicMock()
    client.register_builtin_handler = MagicMock()
    return client


# ---------------------------------------------------------------------------
# Registration
# ---------------------------------------------------------------------------


class TestRegistration:
    def test_register_git_tools_registers_five_tools(
        self, mock_mcp_client: MagicMock, git_config: CognithorConfig
    ) -> None:
        register_git_tools(mock_mcp_client, git_config)
        assert mock_mcp_client.register_builtin_handler.call_count == 5

    def test_register_git_tools_tool_names(
        self, mock_mcp_client: MagicMock, git_config: CognithorConfig
    ) -> None:
        register_git_tools(mock_mcp_client, git_config)
        registered_names = [
            call.args[0] for call in mock_mcp_client.register_builtin_handler.call_args_list
        ]
        assert "git_status" in registered_names
        assert "git_diff" in registered_names
        assert "git_log" in registered_names
        assert "git_commit" in registered_names
        assert "git_branch" in registered_names


# ---------------------------------------------------------------------------
# Path Validation
# ---------------------------------------------------------------------------


class TestPathValidation:
    def test_validate_path_within_workspace(self, git_tools: GitTools) -> None:
        workspace = git_tools._workspace.expanduser().resolve()
        test_dir = workspace / "myrepo"
        test_dir.mkdir(parents=True, exist_ok=True)
        result = git_tools._validate_path(str(test_dir))
        assert result == test_dir

    def test_validate_path_outside_workspace_raises(self, git_tools: GitTools) -> None:
        with pytest.raises(GitToolsError, match="Zugriff verweigert"):
            git_tools._validate_path("/etc/passwd")

    def test_get_repo_path_default_workspace(self, git_tools: GitTools) -> None:
        result = git_tools._get_repo_path(None)
        assert result == git_tools._workspace.expanduser().resolve()


# ---------------------------------------------------------------------------
# Git Status
# ---------------------------------------------------------------------------


class TestGitStatus:
    async def test_status_not_a_repo(self, git_tools: GitTools) -> None:
        result = await git_tools.git_status()
        assert "kein Git-Repository" in result or "git_not_a_repo" in result

    async def test_status_clean_repo(self, git_tools: GitTools) -> None:
        with (
            patch.object(git_tools, "_check_is_git_repo", return_value=None),
            patch.object(
                git_tools,
                "_run_git",
                side_effect=[
                    (0, "", ""),  # porcelain
                    (0, "On branch main\nnothing to commit", ""),  # human
                ],
            ),
        ):
            result = await git_tools.git_status()
            assert "clean" in result.lower() or "nichts" in result.lower()

    async def test_status_with_changes(self, git_tools: GitTools) -> None:
        porcelain = "M  src/main.py\n?? new_file.txt\n"
        human = (
            "On branch main\nChanges to be committed:\n"
            "  modified: src/main.py\nUntracked files:\n  new_file.txt"
        )
        with (
            patch.object(git_tools, "_check_is_git_repo", return_value=None),
            patch.object(
                git_tools,
                "_run_git",
                side_effect=[
                    (0, porcelain, ""),
                    (0, human, ""),
                ],
            ),
        ):
            result = await git_tools.git_status()
            assert "Staged" in result or "staged_header" in result
            assert "Untracked" in result or "untracked_header" in result


# ---------------------------------------------------------------------------
# Git Diff
# ---------------------------------------------------------------------------


class TestGitDiff:
    async def test_diff_no_changes(self, git_tools: GitTools) -> None:
        with (
            patch.object(git_tools, "_check_is_git_repo", return_value=None),
            patch.object(git_tools, "_run_git", return_value=(0, "", "")),
        ):
            result = await git_tools.git_diff()
            assert "Keine unstaged" in result or "git_diff_no_unstaged" in result

    async def test_diff_staged(self, git_tools: GitTools) -> None:
        with (
            patch.object(git_tools, "_check_is_git_repo", return_value=None),
            patch.object(git_tools, "_run_git", return_value=(0, "", "")) as mock_run,
        ):
            await git_tools.git_diff(staged=True)
            args = mock_run.call_args[0][0]
            assert "--cached" in args

    async def test_diff_with_commit(self, git_tools: GitTools) -> None:
        with (
            patch.object(git_tools, "_check_is_git_repo", return_value=None),
            patch.object(git_tools, "_run_git", return_value=(0, "diff output", "")) as mock_run,
        ):
            result = await git_tools.git_diff(commit="abc123")
            args = mock_run.call_args[0][0]
            assert "abc123" in args
            assert "diff output" in result

    async def test_diff_invalid_commit(self, git_tools: GitTools) -> None:
        with patch.object(git_tools, "_check_is_git_repo", return_value=None):
            result = await git_tools.git_diff(commit="abc;rm -rf /")
            assert (
                "Ungueltig" in result or "invalid" in result.lower() or "git_diff_invalid" in result
            )


# ---------------------------------------------------------------------------
# Git Log
# ---------------------------------------------------------------------------


class TestGitLog:
    async def test_log_default(self, git_tools: GitTools) -> None:
        log_output = "abc1234 | Author | 2024-01-01 | Initial commit"
        with (
            patch.object(git_tools, "_check_is_git_repo", return_value=None),
            patch.object(git_tools, "_run_git", return_value=(0, log_output, "")),
        ):
            result = await git_tools.git_log()
            assert "Initial commit" in result

    async def test_log_oneline(self, git_tools: GitTools) -> None:
        with (
            patch.object(git_tools, "_check_is_git_repo", return_value=None),
            patch.object(git_tools, "_run_git", return_value=(0, "abc Short", "")) as mock_run,
        ):
            await git_tools.git_log(oneline=True)
            args = mock_run.call_args[0][0]
            assert "--oneline" in args

    async def test_log_count_clamped(self, git_tools: GitTools) -> None:
        with (
            patch.object(git_tools, "_check_is_git_repo", return_value=None),
            patch.object(git_tools, "_run_git", return_value=(0, "commit", "")) as mock_run,
        ):
            await git_tools.git_log(count=999)
            args = mock_run.call_args[0][0]
            assert "-100" in args

    async def test_log_with_author_filter(self, git_tools: GitTools) -> None:
        with (
            patch.object(git_tools, "_check_is_git_repo", return_value=None),
            patch.object(git_tools, "_run_git", return_value=(0, "log", "")) as mock_run,
        ):
            await git_tools.git_log(author="Alice")
            args = mock_run.call_args[0][0]
            assert "--author" in args
            assert "Alice" in args

    async def test_log_no_commits(self, git_tools: GitTools) -> None:
        with (
            patch.object(git_tools, "_check_is_git_repo", return_value=None),
            patch.object(git_tools, "_run_git", return_value=(0, "", "")),
        ):
            result = await git_tools.git_log()
            assert "Keine Commits" in result or "git_log_no_commits" in result


# ---------------------------------------------------------------------------
# Git Commit
# ---------------------------------------------------------------------------


class TestGitCommit:
    async def test_commit_no_message(self, git_tools: GitTools) -> None:
        result = await git_tools.git_commit(message="", files=["a.py"])
        assert "erforderlich" in result or "git_commit_message_required" in result

    async def test_commit_no_files(self, git_tools: GitTools) -> None:
        result = await git_tools.git_commit(message="fix", files=[])
        assert "Mindestens eine Datei" in result or "git_commit_files_required" in result

    async def test_commit_success(self, git_tools: GitTools) -> None:
        workspace = git_tools._workspace.expanduser().resolve()
        test_file = workspace / "test.py"
        test_file.write_text("# test", encoding="utf-8")

        with (
            patch.object(git_tools, "_check_is_git_repo", return_value=None),
            patch.object(
                git_tools,
                "_run_git",
                side_effect=[
                    (0, "", ""),  # git add
                    (0, "[main abc123] fix bug\n 1 file changed", ""),  # git commit
                ],
            ),
        ):
            result = await git_tools.git_commit(message="fix bug", files=["test.py"])
            assert (
                "fix bug" in result
                or "Commit erfolgreich" in result
                or "git_commit_success" in result
            )

    async def test_commit_file_outside_workspace(self, git_tools: GitTools) -> None:
        with patch.object(git_tools, "_check_is_git_repo", return_value=None):
            result = await git_tools.git_commit(
                message="hack",
                files=["../../../etc/passwd"],
            )
            assert "ausserhalb" in result or "outside" in result.lower() or "file_outside" in result

    async def test_commit_amend(self, git_tools: GitTools) -> None:
        workspace = git_tools._workspace.expanduser().resolve()
        test_file = workspace / "a.txt"
        test_file.write_text("data", encoding="utf-8")

        with (
            patch.object(git_tools, "_check_is_git_repo", return_value=None),
            patch.object(
                git_tools,
                "_run_git",
                side_effect=[
                    (0, "", ""),
                    (0, "amended", ""),
                ],
            ) as mock_run,
        ):
            await git_tools.git_commit(message="fix", files=["a.txt"], amend=True)
            commit_args = mock_run.call_args_list[1][0][0]
            assert "--amend" in commit_args


# ---------------------------------------------------------------------------
# Git Branch
# ---------------------------------------------------------------------------


class TestGitBranch:
    async def test_branch_list(self, git_tools: GitTools) -> None:
        with (
            patch.object(git_tools, "_check_is_git_repo", return_value=None),
            patch.object(
                git_tools,
                "_run_git",
                return_value=(0, "* main\n  feature-x\n", ""),
            ),
        ):
            result = await git_tools.git_branch(action="list")
            assert "main" in result
            assert "feature-x" in result

    async def test_branch_create(self, git_tools: GitTools) -> None:
        with (
            patch.object(git_tools, "_check_is_git_repo", return_value=None),
            patch.object(git_tools, "_run_git", return_value=(0, "", "")),
        ):
            result = await git_tools.git_branch(action="create", name="feature-new")
            assert "erstellt" in result or "git_branch_created" in result

    async def test_branch_switch(self, git_tools: GitTools) -> None:
        with (
            patch.object(git_tools, "_check_is_git_repo", return_value=None),
            patch.object(git_tools, "_run_git", return_value=(0, "", "")),
        ):
            result = await git_tools.git_branch(action="switch", name="main")
            assert "gewechselt" in result or "git_branch_switched" in result

    async def test_branch_delete(self, git_tools: GitTools) -> None:
        with (
            patch.object(git_tools, "_check_is_git_repo", return_value=None),
            patch.object(git_tools, "_run_git", return_value=(0, "", "")),
        ):
            result = await git_tools.git_branch(action="delete", name="old")
            assert (
                "geloescht" in result
                or "deleted" in result.lower()
                or "git_branch_deleted" in result
            )

    async def test_branch_no_name(self, git_tools: GitTools) -> None:
        with patch.object(git_tools, "_check_is_git_repo", return_value=None):
            result = await git_tools.git_branch(action="create", name="")
            assert "erforderlich" in result or "git_branch_name_required" in result

    async def test_branch_invalid_name(self, git_tools: GitTools) -> None:
        with patch.object(git_tools, "_check_is_git_repo", return_value=None):
            result = await git_tools.git_branch(action="create", name="bad;name")
            assert (
                "Ungueltig" in result or "invalid" in result.lower() or "git_diff_invalid" in result
            )

    async def test_branch_unknown_action(self, git_tools: GitTools) -> None:
        with patch.object(git_tools, "_check_is_git_repo", return_value=None):
            result = await git_tools.git_branch(action="merge", name="x")
            assert "Unbekannte Aktion" in result or "git_branch_unknown_action" in result


# ---------------------------------------------------------------------------
# Output Truncation
# ---------------------------------------------------------------------------


class TestTruncation:
    def test_truncate_short_text(self) -> None:
        assert GitTools._truncate("hello") == "hello"

    def test_truncate_long_text(self) -> None:
        long_text = "x" * 60_000
        result = GitTools._truncate(long_text)
        assert len(result) < 60_000
        assert (
            "gekuerzt" in result or "truncat" in result.lower() or "git_output_truncated" in result
        )


# ---------------------------------------------------------------------------
# _run_git edge cases
# ---------------------------------------------------------------------------


class TestRunGit:
    async def test_run_git_not_installed(self, git_tools: GitTools) -> None:
        cwd = git_tools._workspace.expanduser().resolve()
        with patch("asyncio.create_subprocess_exec", side_effect=FileNotFoundError):
            code, stdout, stderr = await git_tools._run_git(["status"], cwd=cwd)
            assert code == 1
            assert "nicht installiert" in stderr or "git_not_installed" in stderr
