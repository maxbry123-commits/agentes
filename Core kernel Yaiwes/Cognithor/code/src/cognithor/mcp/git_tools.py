"""Git-Tools fuer Cognithor -- Versionskontrolle als MCP-Tools.

Fuenf Tools:
  - git_status: Working-Tree-Status anzeigen
  - git_diff: Diffs anzeigen (staged/unstaged/commit)
  - git_log: Commit-History anzeigen
  - git_commit: Dateien stagen und committen
  - git_branch: Branch-Operationen (list/create/switch/delete)

Factory: register_git_tools(mcp_client, config) -> None

Bibel-Referenz: §5.3 (MCP-Tools)
"""

from __future__ import annotations

import asyncio
import contextlib
from pathlib import Path
from typing import TYPE_CHECKING, Any

from cognithor.i18n import t
from cognithor.utils.logging import get_logger

if TYPE_CHECKING:
    from cognithor.config import CognithorConfig

log = get_logger(__name__)

# Maximale Ausgabe-Laenge (50 KB)
_MAX_OUTPUT_CHARS = 50_000

# Timeout fuer Git-Befehle (30s)
_GIT_TIMEOUT = 30

__all__ = [
    "GitTools",
    "GitToolsError",
    "register_git_tools",
]


class GitToolsError(Exception):
    """Fehler bei Git-Operationen."""


class GitTools:
    """Git-Operationen mit Workspace-Validierung. [B§5.3]

    Alle Pfade werden gegen config.workspace_dir validiert.
    Git-Befehle werden via asyncio.create_subprocess_exec ausgefuehrt.
    """

    def __init__(self, config: CognithorConfig) -> None:
        self._config = config
        self._workspace = config.workspace_dir

        log.info(
            "git_tools_init",
            workspace=str(self._workspace),
        )

    def _validate_path(self, path_str: str) -> Path:
        """Validiert und normalisiert einen Pfad gegen den Workspace.

        Raises:
            GitToolsError: Wenn Pfad ausserhalb des Workspace liegt.
        """
        try:
            path = Path(path_str).expanduser().resolve()
        except (ValueError, OSError) as exc:
            raise GitToolsError(f"Ungueltiger Pfad: {path_str}") from exc

        workspace_root = self._workspace.expanduser().resolve()
        try:
            path.relative_to(workspace_root)
        except ValueError:
            raise GitToolsError(
                f"Zugriff verweigert: '{path_str}' liegt ausserhalb "
                f"des Workspace ({workspace_root})"
            ) from None

        return path

    def _get_repo_path(self, path: str | None) -> Path:
        """Ermittelt den Repository-Pfad (Default: workspace_dir)."""
        if path:
            return self._validate_path(path)
        return self._workspace.expanduser().resolve()

    async def _run_git(
        self,
        args: list[str],
        cwd: Path,
        timeout: int = _GIT_TIMEOUT,
    ) -> tuple[int, str, str]:
        """Fuehrt einen Git-Befehl via asyncio.create_subprocess_exec aus.

        Returns:
            Tuple von (exit_code, stdout, stderr).
        """
        try:
            proc = await asyncio.create_subprocess_exec(
                "git",
                *args,
                cwd=str(cwd),
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )
            stdout_bytes, stderr_bytes = await asyncio.wait_for(
                proc.communicate(),
                timeout=timeout,
            )
        except FileNotFoundError:
            return 1, "", t("tools.git_not_installed")
        except TimeoutError:
            with contextlib.suppress(OSError, ProcessLookupError):
                proc.kill()
            return 1, "", t("tools.git_timeout", timeout=timeout)

        stdout = stdout_bytes.decode("utf-8", errors="replace")
        stderr = stderr_bytes.decode("utf-8", errors="replace")

        return proc.returncode or 0, stdout, stderr

    @staticmethod
    def _truncate(text: str) -> str:
        """Kuerzt Output auf maximale Laenge."""
        if len(text) > _MAX_OUTPUT_CHARS:
            return text[:_MAX_OUTPUT_CHARS] + t("tools.git_output_truncated")
        return text

    async def _check_is_git_repo(self, cwd: Path) -> str | None:
        """Prueft ob das Verzeichnis ein Git-Repository ist.

        Returns:
            Fehlermeldung wenn kein Repo, sonst None.
        """
        code, _stdout, _stderr = await self._run_git(
            ["rev-parse", "--is-inside-work-tree"],
            cwd=cwd,
            timeout=10,
        )
        if code != 0:
            return t("tools.git_not_a_repo", cwd=str(cwd))
        return None

    async def git_status(self, path: str = "") -> str:
        """Zeigt den Working-Tree-Status (staged, unstaged, untracked).

        Args:
            path: Repository-Pfad (Default: workspace_dir).

        Returns:
            Status-Uebersicht als Text.
        """
        cwd = self._get_repo_path(path or None)

        repo_check = await self._check_is_git_repo(cwd)
        if repo_check:
            return repo_check

        # Porcelain-Output fuer maschinenlesbare Ergebnisse
        code_p, stdout_p, stderr_p = await self._run_git(
            ["status", "--porcelain=v1"],
            cwd=cwd,
        )

        # Human-readable Output
        code_h, stdout_h, stderr_h = await self._run_git(
            ["status"],
            cwd=cwd,
        )

        if code_h != 0:
            return t("tools.git_status_error", stderr=stderr_h or stderr_p)

        parts: list[str] = []

        # Parse porcelain output for summary
        if stdout_p.strip():
            staged = []
            unstaged = []
            untracked = []
            for line in stdout_p.strip().split("\n"):
                if len(line) < 3:
                    continue
                index_status = line[0]
                worktree_status = line[1]
                filename = line[3:]

                if index_status == "?":
                    untracked.append(filename)
                else:
                    if index_status not in (" ", "?"):
                        staged.append(f"  {index_status} {filename}")
                    if worktree_status not in (" ", "?"):
                        unstaged.append(f"  {worktree_status} {filename}")

            if staged:
                parts.append(t("tools.git_status_staged_header", count=len(staged)))
                parts.extend(staged)
            if unstaged:
                parts.append(t("tools.git_status_unstaged_header", count=len(unstaged)))
                parts.extend(unstaged)
            if untracked:
                parts.append(t("tools.git_status_untracked_header", count=len(untracked)))
                for f in untracked:
                    parts.append(f"  ? {f}")
        else:
            parts.append(t("tools.git_status_clean"))

        parts.append(t("tools.git_status_detail_header"))
        parts.append(stdout_h.strip())

        return self._truncate("\n".join(parts))

    async def git_diff(
        self,
        path: str = "",
        staged: bool = False,
        commit: str = "",
    ) -> str:
        """Zeigt Diffs an.

        Args:
            path: Repository-Pfad (Default: workspace_dir).
            staged: Wenn True, zeige staged (--cached) Diff.
            commit: Wenn gesetzt, vergleiche mit diesem Commit.

        Returns:
            Diff-Output als Text.
        """
        cwd = self._get_repo_path(path or None)

        repo_check = await self._check_is_git_repo(cwd)
        if repo_check:
            return repo_check

        args = ["diff"]
        if staged:
            args.append("--cached")
        elif commit:
            # Validate commit hash/ref (basic sanitization)
            safe_commit = commit.strip()
            if not safe_commit or any(c in safe_commit for c in [";", "&", "|", "`", "$"]):
                return t("tools.git_diff_invalid_commit", commit=commit)
            args.append(safe_commit)

        code, stdout, stderr = await self._run_git(args, cwd=cwd)

        if code != 0:
            return t("tools.git_diff_error", stderr=stderr)

        if not stdout.strip():
            if staged:
                return t("tools.git_diff_no_staged")
            if commit:
                return t("tools.git_diff_no_commit_diff", commit=commit)
            return t("tools.git_diff_no_unstaged")

        return self._truncate(stdout)

    async def git_log(
        self,
        path: str = "",
        count: int = 10,
        oneline: bool = False,
        author: str = "",
    ) -> str:
        """Zeigt die Commit-History.

        Args:
            path: Repository-Pfad (Default: workspace_dir).
            count: Anzahl der Commits (Default: 10, Max: 100).
            oneline: Kompaktes Format.
            author: Filter nach Autor.

        Returns:
            Commit-History als Text.
        """
        cwd = self._get_repo_path(path or None)

        repo_check = await self._check_is_git_repo(cwd)
        if repo_check:
            return repo_check

        # Count begrenzen
        count = max(1, min(count, 100))

        args = ["log", f"-{count}"]

        if oneline:
            args.append("--oneline")
        else:
            args.extend(
                [
                    "--format=%h | %an | %ad | %s",
                    "--date=short",
                ]
            )

        if author:
            safe_author = author.strip()
            if any(c in safe_author for c in [";", "&", "|", "`", "$"]):
                return t("tools.git_log_invalid_author", author=author)
            args.extend(["--author", safe_author])

        code, stdout, stderr = await self._run_git(args, cwd=cwd)

        if code != 0:
            return t("tools.git_log_error", stderr=stderr)

        if not stdout.strip():
            return t("tools.git_log_no_commits")

        return self._truncate(stdout)

    async def git_commit(
        self,
        message: str,
        files: list[str],
        amend: bool = False,
        path: str = "",
    ) -> str:
        """Staged Dateien und erstellt einen Commit.

        Args:
            message: Commit-Nachricht (erforderlich).
            files: Liste von Dateipfaden zum Stagen (erforderlich, kein 'git add .').
            amend: Wenn True, letzten Commit aendern.
            path: Repository-Pfad (Default: workspace_dir).

        Returns:
            Commit-Bestaetigungsnachricht.
        """
        if not message or not message.strip():
            return t("tools.git_commit_message_required")

        if not files:
            return t("tools.git_commit_files_required")

        cwd = self._get_repo_path(path or None)

        repo_check = await self._check_is_git_repo(cwd)
        if repo_check:
            return repo_check

        # Alle Dateipfade validieren -- muessen innerhalb Workspace liegen
        validated_files: list[str] = []
        workspace_root = self._workspace.expanduser().resolve()
        for file_path in files:
            try:
                resolved = (cwd / file_path).resolve()
                resolved.relative_to(workspace_root)
                # Verwende den relativen Pfad zum Repo
                try:
                    rel = resolved.relative_to(cwd)
                    validated_files.append(str(rel))
                except ValueError:
                    validated_files.append(str(resolved))
            except (ValueError, OSError):
                return t(
                    "tools.git_commit_file_outside_workspace",
                    file_path=file_path,
                    workspace_root=str(workspace_root),
                )

        # Stage files
        code, stdout, stderr = await self._run_git(
            ["add", "--", *validated_files],
            cwd=cwd,
        )
        if code != 0:
            return t("tools.git_commit_stage_error", stderr=stderr)

        # Commit
        commit_args = ["commit", "-m", message.strip()]
        if amend:
            commit_args.append("--amend")

        code, stdout, stderr = await self._run_git(commit_args, cwd=cwd)

        if code != 0:
            return t("tools.git_commit_error", stderr=stderr)

        log.info(
            "git_commit_created",
            files_count=len(validated_files),
            amend=amend,
            cwd=str(cwd),
        )

        return self._truncate(stdout.strip() or t("tools.git_commit_success"))

    async def git_branch(
        self,
        action: str = "list",
        name: str = "",
        path: str = "",
    ) -> str:
        """Branch-Operationen.

        Args:
            action: Operation (list/create/switch/delete).
            name: Branch-Name (erforderlich fuer create/switch/delete).
            path: Repository-Pfad (Default: workspace_dir).

        Returns:
            Ergebnis der Branch-Operation.
        """
        cwd = self._get_repo_path(path or None)

        repo_check = await self._check_is_git_repo(cwd)
        if repo_check:
            return repo_check

        action = action.lower().strip()

        if action == "list":
            code, stdout, stderr = await self._run_git(
                ["branch", "-a"],
                cwd=cwd,
            )
            if code != 0:
                return t("tools.git_branch_list_error", stderr=stderr)
            if not stdout.strip():
                return t("tools.git_branch_no_branches")
            return self._truncate(stdout)

        # Alle anderen Aktionen brauchen einen Branch-Namen
        if not name or not name.strip():
            return t("tools.git_branch_name_required", action=action)

        safe_name = name.strip()
        # Basic sanitization
        if any(c in safe_name for c in [";", "&", "|", "`", "$", " ", "..", "~"]):
            return t("tools.git_branch_invalid_name", name=name)

        if action == "create":
            code, stdout, stderr = await self._run_git(
                ["checkout", "-b", safe_name],
                cwd=cwd,
            )
            if code != 0:
                return t("tools.git_branch_create_error", name=safe_name, stderr=stderr)
            log.info("git_branch_created", branch=safe_name, cwd=str(cwd))
            return t("tools.git_branch_created", name=safe_name)

        if action == "switch":
            code, stdout, stderr = await self._run_git(
                ["checkout", safe_name],
                cwd=cwd,
            )
            if code != 0:
                return t("tools.git_branch_switch_error", name=safe_name, stderr=stderr)
            log.info("git_branch_switched", branch=safe_name, cwd=str(cwd))
            return t("tools.git_branch_switched", name=safe_name)

        if action == "delete":
            # Nur sicheres Loeschen (-d, nicht -D)
            code, stdout, stderr = await self._run_git(
                ["branch", "-d", safe_name],
                cwd=cwd,
            )
            if code != 0:
                return t("tools.git_branch_delete_error", name=safe_name, stderr=stderr)
            log.info("git_branch_deleted", branch=safe_name, cwd=str(cwd))
            return t("tools.git_branch_deleted", name=safe_name)

        return t("tools.git_branch_unknown_action", action=action)


def register_git_tools(
    mcp_client: Any,
    config: CognithorConfig,
) -> None:
    """Registriert Git-Tools beim MCP-Client."""
    tools = GitTools(config)

    mcp_client.register_builtin_handler(
        "git_status",
        tools.git_status,
        description=(
            "Zeigt den Git Working-Tree-Status: staged, unstaged und untracked Dateien. "
            "Read-only, kein Risiko."
        ),
        input_schema={
            "type": "object",
            "properties": {
                "path": {
                    "type": "string",
                    "description": "Repository-Pfad (Default: Workspace)",
                    "default": "",
                },
            },
        },
    )

    mcp_client.register_builtin_handler(
        "git_diff",
        tools.git_diff,
        description=(
            "Zeigt Git-Diffs an. Optionen: unstaged (Default), staged (--cached), "
            "oder Vergleich mit einem bestimmten Commit."
        ),
        input_schema={
            "type": "object",
            "properties": {
                "path": {
                    "type": "string",
                    "description": "Repository-Pfad (Default: Workspace)",
                    "default": "",
                },
                "staged": {
                    "type": "boolean",
                    "description": "Zeige staged Aenderungen (--cached)",
                    "default": False,
                },
                "commit": {
                    "type": "string",
                    "description": "Vergleiche mit diesem Commit (Hash oder Ref)",
                    "default": "",
                },
            },
        },
    )

    mcp_client.register_builtin_handler(
        "git_log",
        tools.git_log,
        description=("Zeigt die Git-Commit-History. Optionaler Autor-Filter und kompaktes Format."),
        input_schema={
            "type": "object",
            "properties": {
                "path": {
                    "type": "string",
                    "description": "Repository-Pfad (Default: Workspace)",
                    "default": "",
                },
                "count": {
                    "type": "integer",
                    "description": "Anzahl der Commits (Default: 10, Max: 100)",
                    "default": 10,
                },
                "oneline": {
                    "type": "boolean",
                    "description": "Kompaktes Einzeilen-Format",
                    "default": False,
                },
                "author": {
                    "type": "string",
                    "description": "Filter nach Autor-Name",
                    "default": "",
                },
            },
        },
    )

    mcp_client.register_builtin_handler(
        "git_commit",
        tools.git_commit,
        description=(
            "Staged bestimmte Dateien und erstellt einen Git-Commit. "
            "KEIN 'git add .' -- nur explizit benannte Dateien werden gestaged. "
            "Optional: --amend zum Aendern des letzten Commits."
        ),
        input_schema={
            "type": "object",
            "properties": {
                "message": {
                    "type": "string",
                    "description": "Commit-Nachricht",
                },
                "files": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "Liste von Dateipfaden zum Stagen (relativ zum Repository)",
                },
                "amend": {
                    "type": "boolean",
                    "description": "Letzten Commit aendern (--amend)",
                    "default": False,
                },
                "path": {
                    "type": "string",
                    "description": "Repository-Pfad (Default: Workspace)",
                    "default": "",
                },
            },
            "required": ["message", "files"],
        },
    )

    mcp_client.register_builtin_handler(
        "git_branch",
        tools.git_branch,
        description=(
            "Git-Branch-Operationen: list (alle Branches anzeigen), "
            "create (neuen Branch erstellen), switch (Branch wechseln), "
            "delete (Branch sicher loeschen, nur -d)."
        ),
        input_schema={
            "type": "object",
            "properties": {
                "action": {
                    "type": "string",
                    "description": "Operation: list, create, switch, delete",
                    "enum": ["list", "create", "switch", "delete"],
                    "default": "list",
                },
                "name": {
                    "type": "string",
                    "description": "Branch-Name (erforderlich fuer create/switch/delete)",
                    "default": "",
                },
                "path": {
                    "type": "string",
                    "description": "Repository-Pfad (Default: Workspace)",
                    "default": "",
                },
            },
        },
    )

    log.info(
        "git_tools_registered",
        tools=["git_status", "git_diff", "git_log", "git_commit", "git_branch"],
    )
