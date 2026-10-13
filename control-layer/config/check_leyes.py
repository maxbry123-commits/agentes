"""Checks de las 15 leyes (subset automático).
SOURCE: config/leyes_l01_l15.yaml
"""
from __future__ import annotations
from dataclasses import dataclass, field
from pathlib import Path


@dataclass
class LeyResult:
    ok: bool
    violations: list[str] = field(default_factory=list)


def check_l02_loc(path: Path, max_loc: int = 200) -> list[str]:
    if not path.suffix == ".py":
        return []
    lines = path.read_text(encoding="utf-8", errors="ignore").splitlines()
    code = [l for l in lines if l.strip() and not l.strip().startswith("#")]
    if len(code) > max_loc:
        return [f"L02:{path.name}:{len(code)}>{max_loc}"]
    return []


def check_tree(root: str | Path) -> LeyResult:
    r = Path(root)
    violations: list[str] = []
    for p in r.rglob("*.py"):
        violations.extend(check_l02_loc(p))
    return LeyResult(ok=len(violations) == 0, violations=violations)
