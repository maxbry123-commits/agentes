"""Immutable node/input/checkpoint identity for fail-closed reinjection.

Provenance patterns:
- dta-au/elspeth/src/elspeth/contracts/identity.py
  blob 98b791e350e3a2829fb2c2977cc0fbc25beb4321
- dta-au/elspeth/src/elspeth/contracts/audit.py
  blob c89a5d9d2354ae549845aeab9a90cc3ab14f853e
- pinned source commit 720d441336434d227c2a00caaac100db48a07d5c

YAIWES-specific invariant: a resume may advance the attempt, but it may not
change the literal input hash, node id or checkpoint provenance supplied by the
caller.
"""
from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass, replace
from typing import Any


class ResumeIdentityError(RuntimeError):
    """Resume/reinjection identity drifted from its persisted contract."""


def stable_hash(value: Any) -> str:
    """SHA-256 over deterministic JSON bytes."""
    payload = json.dumps(
        value,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


@dataclass(frozen=True)
class ResumeIdentity:
    run_id: str
    node_id: str
    input_hash: str
    checkpoint_id: str
    attempt: int = 0

    @classmethod
    def from_literal_input(
        cls,
        *,
        run_id: str,
        node_id: str,
        input_block: Any,
        checkpoint_id: str,
        attempt: int = 0,
    ) -> "ResumeIdentity":
        if not run_id or not node_id or not checkpoint_id:
            raise ResumeIdentityError("run_id, node_id and checkpoint_id are required")
        if attempt < 0:
            raise ResumeIdentityError("attempt must be >= 0")
        return cls(run_id, node_id, stable_hash(input_block), checkpoint_id, attempt)

    def resume(
        self,
        *,
        node_id: str,
        input_block: Any,
        checkpoint_id: str,
    ) -> "ResumeIdentity":
        """Advance one attempt only when persisted identity is exactly preserved."""
        candidate_hash = stable_hash(input_block)
        if node_id != self.node_id:
            raise ResumeIdentityError("resume node_id mismatch")
        if checkpoint_id != self.checkpoint_id:
            raise ResumeIdentityError("resume checkpoint_id mismatch")
        if candidate_hash != self.input_hash:
            raise ResumeIdentityError("resume INPUT_BLOCK hash mismatch")
        return replace(self, attempt=self.attempt + 1)

    def as_record(self) -> dict[str, Any]:
        return {
            "run_id": self.run_id,
            "node_id": self.node_id,
            "input_hash": self.input_hash,
            "checkpoint_id": self.checkpoint_id,
            "attempt": self.attempt,
        }
