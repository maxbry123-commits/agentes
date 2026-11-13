from __future__ import annotations

from pathlib import Path

from tools.code_executor import CommandResult, ScopedCodeExecutor


class TestRunner:
    def __init__(self, repo_root: Path | str):
        self.executor = ScopedCodeExecutor(repo_root)

    def run_unittest(self, test_dir: str = "tests") -> CommandResult:
        return self.executor.run(["python", "-m", "unittest", "discover", "-s", test_dir])
