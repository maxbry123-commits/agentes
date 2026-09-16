from __future__ import annotations

from pathlib import Path

from tools.code_executor import CommandResult, ScopedCodeExecutor


class GitTool:
    def __init__(self, repo_root: Path | str):
        self.executor = ScopedCodeExecutor(repo_root)

    def status_short(self) -> CommandResult:
        return self.executor.run(["git", "status", "--short"])

    def diff(self) -> CommandResult:
        return self.executor.run(["git", "diff", "--"])
