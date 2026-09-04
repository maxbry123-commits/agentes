from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass, field
from enum import Enum
from typing import Any


class Status(str, Enum):
    PENDING = "PENDING"
    RUNNING = "RUNNING"
    PASS = "PASS"
    FAIL = "FAIL"
    BLOCKED = "BLOCKED"
    INCONCLUSIVE = "INCONCLUSIVE"


def canonical(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def sha256(value: Any) -> str:
    raw = value if isinstance(value, str) else canonical(value)
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()


@dataclass(frozen=True)
class Evidence:
    kind: str
    ref: str
    sha256: str = ""
    detail: str = ""

    def valid(self) -> bool:
        return bool(self.kind and self.ref)


@dataclass(frozen=True)
class NodeContract:
    node_id: str
    layer: str
    literal: str
    literal_sha256: str
    depends_on: tuple[str, ...] = ()
    allowed_actions: tuple[str, ...] = ()
    allowed_paths: tuple[str, ...] = ()
    forbidden_actions: tuple[str, ...] = ()
    mutation: bool = False
    authorization: tuple[str, ...] = ()
    timeout_ms: int = 30_000

    @classmethod
    def build(
        cls,
        *,
        node_id: str,
        layer: str,
        literal: str,
        depends_on: tuple[str, ...] = (),
        allowed_actions: tuple[str, ...] = (),
        allowed_paths: tuple[str, ...] = (),
        forbidden_actions: tuple[str, ...] = (),
        mutation: bool = False,
        authorization: tuple[str, ...] = (),
        timeout_ms: int = 30_000,
    ) -> "NodeContract":
        return cls(
            node_id=node_id,
            layer=layer,
            literal=literal,
            literal_sha256=sha256(literal),
            depends_on=depends_on,
            allowed_actions=allowed_actions,
            allowed_paths=allowed_paths,
            forbidden_actions=forbidden_actions,
            mutation=mutation,
            authorization=authorization,
            timeout_ms=timeout_ms,
        )


@dataclass
class LayerResult:
    node_id: str
    layer: str
    status: Status
    output: dict[str, Any] = field(default_factory=dict)
    evidence: list[Evidence] = field(default_factory=list)
    gaps: list[str] = field(default_factory=list)
    touched_paths: list[str] = field(default_factory=list)
    actions: list[str] = field(default_factory=list)

    def has_real_evidence(self) -> bool:
        return bool(self.evidence) and all(e.valid() for e in self.evidence)
