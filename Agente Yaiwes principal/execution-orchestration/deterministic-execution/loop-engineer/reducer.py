"""Pure deterministic event@1 reducer; persistence is deliberately not involved."""

from __future__ import annotations

from typing import Any, Iterable, Mapping

from . import chain, fsm
from .completion import (CompletionPolicyError, criteria_satisfy_completion,
                         evidence_entry_is_record_shaped, normalize_completion_policy,
                         policy_requires_verified_evidence)
from .contract import TERMINAL_STATES
from .events import _structural_validate_event


class EventReplayError(ValueError):
    """An event stream is malformed or violates a replay domain invariant."""


class ChainBreakError(EventReplayError):
    """The event stream's hash link is broken or forged.

    Not a gap detector: a mid-stream deletion surfaces as a sequence error, and a
    truncated tail is caught only by an anchored head.
    """


def _empty_projection(run_id: str | None) -> dict[str, Any]:
    return {"run_id": run_id, "state": None, "iteration_id": None, "active_task": None,
            "terminal": None, "runlog_entries": [], "receipts": [], "superseded_history": [], "event_count": 0,
            "last_sequence": None, "paused": False, "pause_reason": None, "pending_approval": None,
            "chain_head": None, "unchained_prefix": 0}


def _validate_terminal_payload_semantics(payload: Mapping[str, Any]) -> None:
    state = payload.get("state")
    if state not in TERMINAL_STATES:
        raise EventReplayError(f"terminal payload has non-canonical state {state!r}")
    if state != "Succeeded":
        return
    if payload.get("false_completion") is True:
        raise EventReplayError("refusing Succeeded terminal with false_completion=True (G1)")
    try:
        policy = normalize_completion_policy(payload.get("completion_policy"))
    except CompletionPolicyError as exc:
        raise EventReplayError(f"invalid completion_policy: {exc}") from exc
    criteria = payload.get("criteria_met")
    if not isinstance(criteria, dict) or not criteria_satisfy_completion(criteria, policy):
        raise EventReplayError("Succeeded terminal does not satisfy the completion policy (G1)")
    evidence = payload.get("evidence")
    if not isinstance(evidence, list) or not evidence:
        raise EventReplayError("Succeeded terminal has empty evidence (G1)")
    # The STRUCTURAL half only: this fold is pure and holds no workspace, so it can
    # check the shape of a citation and nothing more (repo-os-contract §16).
    if (policy_requires_verified_evidence(policy)
            and not all(evidence_entry_is_record_shaped(item) for item in evidence)):
        raise EventReplayError(
            "Succeeded terminal declares verified evidence but an entry is not a "
            ".loop/evidence record (G1)")


def _validate_superseded_payload_semantics(payload: Mapping[str, Any]) -> None:
    _validate_terminal_payload_semantics(payload)
    if not isinstance(payload.get("justification"), str) or not payload["justification"].strip():
        raise EventReplayError("terminal_superseded payload missing non-empty justification")
    authority = payload.get("authority")
    if (not isinstance(authority, dict)
            or not isinstance(authority.get("by"), str) or not authority.get("by", "").strip()
            or not isinstance(authority.get("at"), str) or not authority.get("at", "").strip()):
        raise EventReplayError("terminal_superseded payload missing authority.by/authority.at")


def _check_approval_resume_target(target: object) -> None:
    if target == fsm.TERMINAL_MARKER or target not in fsm.legal_targets("approval-wait"):
        raise EventReplayError(
            f"approval_resolved.resume_target {target!r} is not a legal non-terminal resume target from approval-wait"
        )


def _reduce_one(state: dict[str, Any], event: Mapping[str, Any]) -> dict[str, Any]:
    if not isinstance(event, Mapping):
        raise EventReplayError("event must be a mapping")
    issues = _structural_validate_event(dict(event))
    payload = event.get("payload")
    if (
        issues == ["approval_resolved.resume_target must be a non-empty string when decision is 'approved'"]
        and event.get("type") == "approval_resolved"
        and isinstance(payload, Mapping)
        and payload.get("decision") == "approved"
        and payload.get("resume_target") == ""
    ):
        target = payload["resume_target"]
        _check_approval_resume_target(target)
    if issues:
        raise EventReplayError(f"malformed event: {issues}")
    run_id = event["run_id"]
    if state["run_id"] is not None and state["run_id"] != run_id:
        raise EventReplayError(f"mixed run_id in one replay: {state['run_id']!r} vs {run_id!r}")
    expected_sequence = 0 if state["last_sequence"] is None else state["last_sequence"] + 1
    if event["sequence"] != expected_sequence:
        raise EventReplayError(f"non-monotonic sequence: expected {expected_sequence}, got {event['sequence']!r}")
    issue = chain.link_issue(event, state["chain_head"])
    if issue is not None:
        raise ChainBreakError(f"event chain broken: {issue}")
    event_type = event["type"]
    if state["terminal"] is not None:
        if event_type != "terminal_superseded":
            raise EventReplayError("event appended after terminal — terminal is immutable")
    elif event_type == "terminal_superseded":
        raise EventReplayError("terminal_superseded has nothing to supersede (no terminal record yet)")
    if event_type == "contract_opened" and state["last_sequence"] is not None:
        raise EventReplayError("contract_opened must be the first event in a run")
    if event_type != "contract_opened" and state["state"] is None:
        raise EventReplayError(f"{event_type} event before contract_opened")
    new_state = {**state, "run_id": run_id, "last_sequence": event["sequence"], "event_count": state["event_count"] + 1}
    if event.get("event_hash") is None:
        new_state["unchained_prefix"] = state["unchained_prefix"] + 1
    else:
        new_state["chain_head"] = {"sequence": event["sequence"], "event_hash": event["event_hash"]}
    payload = event["payload"]
    if event_type == "contract_opened":
        new_state["state"] = "intake"
        new_state["iteration_id"] = 0
    elif event_type == "iteration_appended":
        target = payload.get("state")
        if target is not None:
            if target not in fsm.ALL_STATES:
                raise EventReplayError(f"illegal FSM transition {new_state['state']!r} -> {target!r}")
            if not fsm.is_legal_transition(new_state["state"], target):
                raise EventReplayError(f"illegal FSM transition {new_state['state']!r} -> {target!r}")
            new_state["state"] = target
        new_state["iteration_id"] = payload["iteration_id"]
        if payload.get("task_id"):
            new_state["active_task"] = payload["task_id"]
        entry = dict(payload, event_id=event["event_id"], causation_id=event.get("causation_id"), correlation_id=event.get("correlation_id"), ts=event["ts"])
        new_state["runlog_entries"] = new_state["runlog_entries"] + [entry]
    elif event_type == "receipt_appended":
        entry = dict(payload, event_id=event["event_id"], causation_id=event.get("causation_id"), correlation_id=event.get("correlation_id"), ts=event["ts"])
        new_state["receipts"] = new_state["receipts"] + [entry]
    elif event_type == "terminal_written":
        if not fsm.is_legal_transition(new_state["state"], fsm.TERMINAL_MARKER):
            raise EventReplayError(f"illegal FSM transition {new_state['state']!r} -> {fsm.TERMINAL_MARKER!r}")
        _validate_terminal_payload_semantics(payload)
        new_state["state"] = fsm.TERMINAL_MARKER
        new_state["terminal"] = dict(payload, event_id=event["event_id"], ts=event["ts"])
    elif event_type == "terminal_superseded":
        current_terminal = state["terminal"]
        if event.get("causation_id") != current_terminal.get("event_id"):
            raise EventReplayError(
                "terminal_superseded.causation_id must reference the event_id "
                "of the terminal record it corrects"
            )
        _validate_superseded_payload_semantics(payload)
        history_entry = {**current_terminal, "superseded_by": event["event_id"], "superseded_at": event["ts"]}
        new_state["superseded_history"] = state["superseded_history"] + [history_entry]
        new_state["terminal"] = dict(payload, event_id=event["event_id"], ts=event["ts"])
    elif event_type == "approval_requested":
        if not fsm.is_legal_transition(new_state["state"], "approval-wait"):
            raise EventReplayError(
                f"illegal FSM transition {new_state['state']!r} -> 'approval-wait'"
            )
        new_state["state"] = "approval-wait"
        new_state["iteration_id"] = payload["iteration_id"]
        new_state["pending_approval"] = {"event_id": event["event_id"], "request": payload["request"]}
    elif event_type == "approval_resolved":
        if new_state["state"] != "approval-wait":
            raise EventReplayError(
                f"approval_resolved is only legal from approval-wait, current state is {new_state['state']!r}"
            )
        pending = new_state["pending_approval"]
        if pending is None:
            raise EventReplayError("approval_resolved has no pending approval_requested event to resolve")
        if event.get("causation_id") != pending["event_id"]:
            raise EventReplayError(
                "approval_resolved.causation_id must reference the pending approval_requested event_id"
        )
        if payload["decision"] == "approved":
            target = payload["resume_target"]
            _check_approval_resume_target(target)
            new_state["state"] = target
        new_state["pending_approval"] = None
        new_state["iteration_id"] = payload["iteration_id"]
    elif event_type == "run_paused":
        if new_state["paused"]:
            raise EventReplayError("run_paused: run is already paused")
        new_state["paused"] = True
        new_state["pause_reason"] = payload["reason"]
        new_state["iteration_id"] = payload["iteration_id"]
    elif event_type == "run_resumed":
        if not new_state["paused"]:
            raise EventReplayError("run_resumed: run is not paused")
        new_state["paused"] = False
        new_state["pause_reason"] = None
        new_state["iteration_id"] = payload["iteration_id"]
    return new_state


def _check_prechain_seam(event: Mapping[str, Any]) -> None:
    """A snapshot predating v0.10.0 carries no head, so a chained non-genesis tail
    cannot link to it — an honest resume, not the forgery ChainBreakError names."""
    if (not isinstance(event, Mapping)
            or event.get("event_hash") is None or event.get("prev_event_hash") is None):
        return
    raise EventReplayError(
        "initial snapshot predates the chain: re-fold from sequence 0 "
        "or include chain_head in the snapshot"
    )


def reduce_events(events: Iterable[Mapping[str, Any]], *, initial: Mapping[str, Any] | None = None) -> dict[str, Any]:
    """Fold events without mutating the supplied stream or initial projection."""
    if initial is None:
        state = _empty_projection(None)
    else:
        merged = {**_empty_projection(None), **initial}
        state = {**merged, "runlog_entries": list(merged["runlog_entries"]),
                 "receipts": list(merged["receipts"]),
                 "superseded_history": list(merged["superseded_history"])}
    seam_unchecked = initial is not None and "chain_head" not in initial
    for event in events:
        if seam_unchecked:
            seam_unchecked = False
            _check_prechain_seam(event)
        state = _reduce_one(state, event)
    return state
