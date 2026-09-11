"""Deterministic multi-agent claim gate for the YAIWES Crazy Wall.

Contract: yaiwes.crazywall.claim/v1
No I/O, network, LLM, scheduler, or implicit retries live here.
"""

from __future__ import annotations

from copy import deepcopy
from dataclasses import dataclass
from typing import Any, Mapping

CONTRACT = "yaiwes.crazywall.claim/v1"


class ClaimGateError(ValueError):
    """Base fail-closed coordination error."""


class VersionConflict(ClaimGateError):
    """The caller acted on a stale node version."""


class OwnershipConflict(ClaimGateError):
    """The node is owned by another executor."""


class InvalidTransition(ClaimGateError):
    """The requested state transition is not permitted."""


@dataclass(frozen=True)
class ClaimResult:
    node: dict[str, Any]
    changed: bool
    operation: str
    contract: str = CONTRACT


def _require_node(node: Mapping[str, Any]) -> None:
    required = {"id", "status", "claimed_by", "version", "steps"}
    missing = required.difference(node)
    if missing:
        raise ClaimGateError(f"missing fields: {sorted(missing)}")
    if not isinstance(node["version"], int) or node["version"] < 1:
        raise ClaimGateError("version must be a positive integer")
    if not isinstance(node["steps"], list):
        raise ClaimGateError("steps must be a list")


def _require_expected_version(node: Mapping[str, Any], expected_version: int) -> None:
    if node["version"] != expected_version:
        raise VersionConflict(
            f"stale version for {node['id']}: expected {expected_version}, current {node['version']}"
        )


def _same_operation(node: Mapping[str, Any], operation: str, actor: str, key: str) -> bool:
    op = node.get("last_operation")
    return bool(
        isinstance(op, Mapping)
        and op.get("operation") == operation
        and op.get("actor") == actor
        and op.get("idempotency_key") == key
    )


def _stamp(node: dict[str, Any], operation: str, actor: str, key: str) -> None:
    node["last_operation"] = {
        "operation": operation,
        "actor": actor,
        "idempotency_key": key,
        "resulting_version": node["version"],
    }


def claim_node(
    node: Mapping[str, Any], *, actor: str, expected_version: int, idempotency_key: str
) -> ClaimResult:
    """Claim one PENDING node using optimistic concurrency and idempotency."""
    _require_node(node)
    if not actor or not idempotency_key:
        raise ClaimGateError("actor and idempotency_key are required")

    if _same_operation(node, "CLAIM", actor, idempotency_key):
        return ClaimResult(deepcopy(dict(node)), False, "CLAIM_IDEMPOTENT_REPLAY")

    _require_expected_version(node, expected_version)
    owner = node.get("claimed_by")
    status = node.get("status")
    if owner not in (None, actor):
        raise OwnershipConflict(f"{node['id']} is owned by {owner}")
    if status == "CLAIMED" and owner == actor:
        raise InvalidTransition("already claimed by actor with a different idempotency key")
    if status != "PENDING" or owner is not None:
        raise InvalidTransition(f"cannot claim status={status} owner={owner}")

    updated = deepcopy(dict(node))
    updated["status"] = "CLAIMED"
    updated["claimed_by"] = actor
    updated["version"] += 1
    if updated["steps"]:
        first = updated["steps"][0]
        if first.get("id") == "1_RESEARCH" and first.get("status") == "PENDING":
            first["status"] = "RUNNING"
    _stamp(updated, "CLAIM", actor, idempotency_key)
    return ClaimResult(updated, True, "CLAIMED")


def release_node(
    node: Mapping[str, Any], *, actor: str, expected_version: int, idempotency_key: str
) -> ClaimResult:
    """Release only a node currently owned by actor."""
    _require_node(node)
    if not actor or not idempotency_key:
        raise ClaimGateError("actor and idempotency_key are required")

    if _same_operation(node, "RELEASE", actor, idempotency_key):
        return ClaimResult(deepcopy(dict(node)), False, "RELEASE_IDEMPOTENT_REPLAY")

    _require_expected_version(node, expected_version)
    if node.get("claimed_by") != actor:
        raise OwnershipConflict(f"{node['id']} is not owned by {actor}")
    if node.get("status") != "CLAIMED":
        raise InvalidTransition(f"cannot release status={node.get('status')}")

    updated = deepcopy(dict(node))
    updated["status"] = "PENDING"
    updated["claimed_by"] = None
    updated["version"] += 1
    if updated["steps"]:
        first = updated["steps"][0]
        if first.get("id") == "1_RESEARCH" and first.get("status") == "RUNNING":
            first["status"] = "PENDING"
    _stamp(updated, "RELEASE", actor, idempotency_key)
    return ClaimResult(updated, True, "RELEASED")


def detect_claim_drift(task_node: Mapping[str, Any], checkpoint: Mapping[str, Any]) -> dict[str, Any]:
    """Compare canonical task ownership with checkpoint ownership without mutating either."""
    _require_node(task_node)
    task_owner = task_node.get("claimed_by")
    checkpoint_owner = checkpoint.get("claimed_by")
    checkpoint_node = checkpoint.get("verified_this_cycle", {}).get("gap") or checkpoint.get("current_node")
    same_node = checkpoint_node in (task_node.get("id"), f"CG18_FABLES_CANONICAL_BINDING_{task_node.get('id','').replace('-', '')}")
    owner_match = task_owner == checkpoint_owner
    return {
        "contract": CONTRACT,
        "task_node": task_node.get("id"),
        "task_owner": task_owner,
        "checkpoint_owner": checkpoint_owner,
        "same_node": same_node,
        "owner_match": owner_match,
        "drift": bool(same_node and not owner_match),
        "decision": "FAIL_CLOSED_RECONCILE" if same_node and not owner_match else "CONSISTENT",
    }
