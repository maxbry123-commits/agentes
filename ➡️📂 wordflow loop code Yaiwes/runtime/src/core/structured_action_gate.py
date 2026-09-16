"""Structured action gate inspired by the vendored Muse Glimmer trace.

The model may propose an action, but raw/free-form model text is never executable.
A proposal is normalized into a deterministic command identity and then checked by
YAIWES' existing LLM boundary. Side effects additionally require deterministic
runtime authority plus an explicit Sheriff approval.
"""
from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from typing import Any, Mapping

try:  # package import
    from .llm_boundary import enforce_boundary
except ImportError:  # direct-file/offline test import
    from llm_boundary import enforce_boundary  # type: ignore


class StructuredActionError(ValueError):
    """Fail-closed malformed structured action."""


@dataclass(frozen=True)
class StructuredAction:
    command_id: str
    action: str
    actor: str
    arguments: Mapping[str, Any]
    target: str | None
    side_effect: bool
    parent_id: str | None = None


@dataclass(frozen=True)
class StructuredActionDecision:
    command_id: str
    boundary_allowed: bool
    sheriff_required: bool
    sheriff_approved: bool
    execution_authorized: bool
    reason: str


def _stable_command_id(
    action: str,
    actor: str,
    arguments: Mapping[str, Any],
    target: str | None,
    parent_id: str | None,
) -> str:
    payload = {
        "action": action,
        "actor": actor.strip().upper(),
        "arguments": arguments,
        "target": target,
        "parent_id": parent_id,
    }
    raw = json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
    return "cmd-" + hashlib.sha256(raw.encode("utf-8")).hexdigest()[:24]


def normalize_action(payload: Mapping[str, Any]) -> StructuredAction:
    """Accept only a mapping; never parse arbitrary assistant prose as an action."""
    if not isinstance(payload, Mapping):
        raise StructuredActionError("STRUCTURED_ACTION_MAPPING_REQUIRED")

    action = str(payload.get("action", "")).strip()
    actor = str(payload.get("actor", "")).strip().upper()
    arguments = payload.get("arguments", {})
    target_value = payload.get("target")
    parent_value = payload.get("parent_id")
    side_effect = payload.get("side_effect", False)

    if not action:
        raise StructuredActionError("ACTION_REQUIRED")
    if not actor:
        raise StructuredActionError("ACTOR_REQUIRED")
    if not isinstance(arguments, Mapping):
        raise StructuredActionError("ARGUMENTS_MAPPING_REQUIRED")
    if not isinstance(side_effect, bool):
        raise StructuredActionError("SIDE_EFFECT_BOOL_REQUIRED")

    target = None if target_value is None else str(target_value).strip() or None
    parent_id = None if parent_value is None else str(parent_value).strip() or None
    supplied_id = str(payload.get("command_id", "")).strip()
    command_id = supplied_id or _stable_command_id(
        action, actor, arguments, target, parent_id
    )

    return StructuredAction(
        command_id=command_id,
        action=action,
        actor=actor,
        arguments=dict(arguments),
        target=target,
        side_effect=side_effect,
        parent_id=parent_id,
    )


def evaluate_action(
    action: StructuredAction, *, sheriff_approved: bool = False
) -> StructuredActionDecision:
    boundary = enforce_boundary(action.action, action.actor)
    sheriff_required = action.side_effect

    if not boundary.allowed:
        return StructuredActionDecision(
            command_id=action.command_id,
            boundary_allowed=False,
            sheriff_required=sheriff_required,
            sheriff_approved=sheriff_approved,
            execution_authorized=False,
            reason=boundary.reason,
        )

    if action.side_effect:
        if action.actor not in {"DETERMINISTIC", "DETERMINISTIC_RUNTIME"}:
            return StructuredActionDecision(
                command_id=action.command_id,
                boundary_allowed=True,
                sheriff_required=True,
                sheriff_approved=sheriff_approved,
                execution_authorized=False,
                reason="LLM_SIDE_EFFECT_FORBIDDEN",
            )
        if not sheriff_approved:
            return StructuredActionDecision(
                command_id=action.command_id,
                boundary_allowed=True,
                sheriff_required=True,
                sheriff_approved=False,
                execution_authorized=False,
                reason="SHERIFF_APPROVAL_REQUIRED",
            )

    return StructuredActionDecision(
        command_id=action.command_id,
        boundary_allowed=True,
        sheriff_required=sheriff_required,
        sheriff_approved=sheriff_approved,
        execution_authorized=True,
        reason="STRUCTURED_ACTION_AUTHORIZED",
    )
