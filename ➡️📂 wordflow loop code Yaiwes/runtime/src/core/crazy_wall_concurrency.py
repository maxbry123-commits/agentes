"""Optimistic concurrency and ownership protocol for Crazy Wall state."""
from __future__ import annotations

import copy
from dataclasses import dataclass
from typing import Any, Dict, Tuple


class ConcurrencyError(ValueError):
    pass


@dataclass(frozen=True)
class Mutation:
    owner: str
    expected_version: int
    idempotency_key: str
    patch: Dict[str, Any]


@dataclass(frozen=True)
class MutationResult:
    document: Dict[str, Any]
    status: str
    changed_keys: Tuple[str, ...]


def apply_mutation(document: Dict[str, Any], mutation: Mutation) -> MutationResult:
    if not mutation.owner.strip() or not mutation.idempotency_key.strip():
        raise ConcurrencyError("owner and idempotency_key required")

    current_version = int(document.get("version", 0))
    seen = set(document.get("applied_idempotency_keys", []))
    if mutation.idempotency_key in seen:
        return MutationResult(copy.deepcopy(document), "IDEMPOTENT_REPLAY", ())

    lock = document.get("lock")
    if (
        lock
        and lock.get("status") == "CLAIMED"
        and lock.get("owner") != mutation.owner
    ):
        raise ConcurrencyError("OWNER_CONFLICT")
    if mutation.expected_version != current_version:
        raise ConcurrencyError("VERSION_CONFLICT")

    output = copy.deepcopy(document)
    for key, value in mutation.patch.items():
        if key in {"version", "applied_idempotency_keys"}:
            raise ConcurrencyError("RESERVED_KEY")
        output[key] = value
    output["version"] = current_version + 1
    output["lock"] = {"status": "CLAIMED", "owner": mutation.owner}
    output["applied_idempotency_keys"] = sorted(
        seen | {mutation.idempotency_key}
    )
    return MutationResult(output, "APPLIED", tuple(sorted(mutation.patch)))
