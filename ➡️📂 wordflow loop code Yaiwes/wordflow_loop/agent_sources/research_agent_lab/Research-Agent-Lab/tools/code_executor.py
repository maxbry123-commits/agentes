from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import subprocess


@dataclass(slots=True)
class CommandResult:
    returncode: int
    stdout: str
    stderr: str


class ScopedCodeExecutor:
    def __init__(self, root: Path | str):
        self.root = Path(root).resolve()

    def run(self, command: list[str], cwd: Path | str | None = None, timeout: int = 120) -> CommandResult:
        working_dir = (Path(cwd).resolve() if cwd else self.root)
        if self.root not in [working_dir, *working_dir.parents]:
            raise ValueError(f"cwd is outside scoped root: {working_dir}")
        completed = subprocess.run(
            command,
            cwd=working_dir,
            timeout=timeout,
            text=True,
            capture_output=True,
            check=False,
        )
        return CommandResult(
            returncode=completed.returncode,
            stdout=completed.stdout,
            stderr=completed.stderr,
        )
