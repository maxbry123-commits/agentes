from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class MemoryCandidate:
    content: str
    score: float = 0.0
    source: str = ""
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class MemoryRequest:
    task_id: str
    trace_id: str
    op: str  # search | store | context | audit
    query: str = ""
    item: dict[str, Any] | None = None
    scope: str | None = None
    policy: dict[str, Any] = field(default_factory=dict)


@dataclass
class MemoryResponse:
    status: str
    candidates: list[MemoryCandidate] = field(default_factory=list)
    detail: dict[str, Any] = field(default_factory=dict)
