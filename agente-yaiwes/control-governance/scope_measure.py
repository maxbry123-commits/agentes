"""G-W13 / G-W13b — medición de scope. G-W13b = git diff, no lista fija."""
from __future__ import annotations

import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import Any


@dataclass
class ScopeMeasure:
    expected_paths: list[str]
    actual_paths: list[str]

    def unexpected(self) -> list[str]:
        exp = set(self.expected_paths)
        return [p for p in self.actual_paths if p not in exp]

    def missing(self) -> list[str]:
        act = set(self.actual_paths)
        return [p for p in self.expected_paths if p not in act]

    def ok(self) -> bool:
        return len(self.unexpected()) == 0


def measure_requirements(declared: list[str], satisfied: list[str]) -> dict[str, Any]:
    ds, ss = set(declared), set(satisfied)
    return {
        "declared": list(ds),
        "satisfied": list(ss),
        "missing": list(ds - ss),
        "extra": list(ss - ds),
        "ok": ds <= ss,
    }


def scope_from_git_diff(
    repo: str | Path,
    base: str = "HEAD~1",
    expected_paths: list[str] | None = None,
) -> dict[str, Any]:
    """G-W13b: actual_paths from git diff --name-only, not a hardcoded list."""
    root = Path(repo)
    try:
        proc = subprocess.run(
            ["git", "diff", "--name-only", base],
            cwd=root,
            capture_output=True,
            text=True,
            check=False,
            timeout=15,
        )
    except (OSError, subprocess.TimeoutExpired) as exc:
        return {
            "ok": False,
            "error": str(exc),
            "actual_paths": [],
            "source": "git_diff",
            "base": base,
        }
    actual = [p.strip() for p in proc.stdout.splitlines() if p.strip()]
    expected = list(expected_paths or [])
    measure = ScopeMeasure(expected_paths=expected, actual_paths=actual)
    return {
        "ok": proc.returncode == 0,
        "actual_paths": actual,
        "expected_paths": expected,
        "unexpected": measure.unexpected() if expected else [],
        "missing": measure.missing() if expected else [],
        "source": "git_diff",
        "base": base,
        "returncode": proc.returncode,
        "stderr": (proc.stderr or "")[:400],
    }
