"""Fail-closed continuity supervisor for run-scoped YAIWES nodes.

It does not create an infinite retry loop. Exhausted/non-retryable work is marked
BLOCKED and the supervisor may continue another independent ready node. If no safe
independent work exists it returns WAIT_BLOCKED instead of inventing PASS.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Mapping, Sequence


class ContinuityError(ValueError):
    pass


@dataclass(frozen=True)
class ContinuityDecision:
    action: str
    current_node: str
    next_node: str | None
    command_id: str
    preserve_checkpoint: bool
    reason: str


_DONE={"PASS","DONE","VERIFIED_CLOSED","CLOSED"}


def ready_independent_nodes(nodes: Sequence[Mapping[str, Any]], *, exclude: set[str] | None=None) -> tuple[str,...]:
    excluded=set(exclude or ())
    by_id={}
    for row in nodes:
        node_id=str(row.get("id","")).strip()
        if not node_id or node_id in by_id:
            raise ContinuityError("NODE_ID_INVALID_OR_DUPLICATE")
        by_id[node_id]=row
    ready=[]
    for node_id,row in by_id.items():
        if node_id in excluded:
            continue
        state=str(row.get("state","PENDING")).upper()
        if state not in {"PENDING","READY","FREE"}:
            continue
        deps=row.get("depends_on",[])
        if not isinstance(deps,Sequence) or isinstance(deps,(str,bytes)):
            raise ContinuityError("DEPENDS_ON_LIST_REQUIRED")
        good=True
        for dep in deps:
            dep_id=str(dep)
            if dep_id not in by_id:
                raise ContinuityError("DEPENDENCY_NOT_FOUND:"+dep_id)
            dep_state=str(by_id[dep_id].get("state","PENDING")).upper()
            if dep_state not in _DONE:
                good=False
                break
        if good:
            ready.append(node_id)
    return tuple(sorted(ready))


def decide_after_failure(
    *,
    nodes: Sequence[Mapping[str, Any]],
    node_id: str,
    command_id: str,
    recovery_action: str,
) -> ContinuityDecision:
    node_id=node_id.strip(); command_id=command_id.strip()
    if not node_id or not command_id:
        raise ContinuityError("NODE_AND_COMMAND_ID_REQUIRED")
    ids={str(row.get("id","")).strip() for row in nodes}
    if node_id not in ids:
        raise ContinuityError("CURRENT_NODE_NOT_FOUND")
    action=recovery_action.strip().upper()
    if action=="RETRY":
        return ContinuityDecision(
            action="RETRY_SAME_COMMAND",
            current_node=node_id,
            next_node=node_id,
            command_id=command_id,
            preserve_checkpoint=True,
            reason="RECOVERY_ENGINE_RETRYABLE",
        )
    if action not in {"ESCALATE_TO_DIRECTOR","BLOCK","NON_RETRYABLE"}:
        raise ContinuityError("RECOVERY_ACTION_UNKNOWN")
    candidates=ready_independent_nodes(nodes,exclude={node_id})
    if candidates:
        return ContinuityDecision(
            action="BLOCK_CURRENT_CONTINUE_INDEPENDENT",
            current_node=node_id,
            next_node=candidates[0],
            command_id=command_id,
            preserve_checkpoint=True,
            reason="CURRENT_NODE_BLOCKED_SAFE_INDEPENDENT_NODE_READY",
        )
    return ContinuityDecision(
        action="WAIT_BLOCKED",
        current_node=node_id,
        next_node=None,
        command_id=command_id,
        preserve_checkpoint=True,
        reason="NO_SAFE_INDEPENDENT_NODE_READY",
    )
