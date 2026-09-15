from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from schemas.base import new_id


@dataclass(slots=True)
class RunValidationCheck:
    name: str
    status: str
    severity: str
    message: str
    evidence: dict[str, Any] = field(default_factory=dict)


@dataclass(slots=True)
class RunValidationReport:
    run_id: str
    run_dir: str
    status: str
    score: int
    checks: list[RunValidationCheck] = field(default_factory=list)
    blocking_issues: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    summary: list[str] = field(default_factory=list)
    validation_id: str = field(default_factory=lambda: new_id("runval"))
