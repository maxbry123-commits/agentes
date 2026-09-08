"""Transactional CLI run-control operations over the event store."""
from __future__ import annotations

from pathlib import Path
from typing import Any

from . import emit, fsm, runner
from .events import (
    EventStoreOperationalError,
    EventValidationError,
    SequenceConflictError,
    SQLiteEventStore,
)
from .paths import resolve_loop_paths
from .runtime import RuntimeStoreError


class RunControlError(RuntimeError):
    pass


class IllegalRunControlStateError(RunControlError):
    pass


class RunControlUsageError(RunControlError):
    pass


class RunControlConflictError(RunControlError):
    pass


def _append_event(target: str | Path, run_id: str, projection: dict[str, Any], event_type: str,
                  payload: dict[str, Any], *, causation_id: str | None = None) -> dict[str, Any]:
    try:
        return SQLiteEventStore(resolve_loop_paths(target).loop_dir / "events.db").append(
            run_id, event_type, payload, actor="loop.runcontrol", causation_id=causation_id,
            expected_sequence=projection["last_sequence"] + 1,
        )
    except SequenceConflictError as exc:
        raise RunControlConflictError("retry: another writer advanced the run") from exc
    except EventValidationError as exc:
        raise RunControlUsageError(str(exc)) from exc
    except EventStoreOperationalError as exc:
        raise RuntimeStoreError("event_store_unusable", str(exc)) from exc


def approve_run(target: str | Path, *, decision: str, resume_target: str | None = None,
                mode: str | None = None) -> dict[str, Any]:
    if decision not in {"approved", "denied"}:
        raise RunControlUsageError("decision must be 'approved' or 'denied'")
    if decision == "approved" and resume_target is None:
        raise RunControlUsageError("--resume-target is required when --decision approved")
    if decision == "denied" and resume_target is not None:
        raise RunControlUsageError("--resume-target is forbidden when --decision denied")
    run_id, projection = runner._projection(target, mode)
    if projection["terminal"] is not None:
        raise IllegalRunControlStateError("run is already terminal")
    if projection["state"] != "approval-wait":
        raise IllegalRunControlStateError("run is not in approval-wait")
    pending = projection["pending_approval"]
    if pending is None:
        raise IllegalRunControlStateError("no pending approval is recorded")
    payload: dict[str, Any] = {"iteration_id": projection["iteration_id"], "decision": decision}
    if decision == "approved":
        if resume_target == fsm.TERMINAL_MARKER or resume_target not in fsm.legal_targets("approval-wait"):
            raise IllegalRunControlStateError(
                f"approval_resolved.resume_target {resume_target!r} is not a legal non-terminal resume target from approval-wait"
            )
        payload["resume_target"] = resume_target
    event = _append_event(target, run_id, projection, "approval_resolved", payload,
                          causation_id=pending["event_id"])
    _, post = runner._projection(target, mode)
    emit.sync_state_to_projection(target, post)
    return {"ok": True, "event": event, "state": post["state"]}


def pause_run(target: str | Path, *, reason: str, mode: str | None = None) -> dict[str, Any]:
    if not isinstance(reason, str) or not reason.strip():
        raise RunControlUsageError("--reason must be a non-empty string")
    run_id, projection = runner._projection(target, mode)
    if projection["terminal"] is not None:
        raise IllegalRunControlStateError("run is already terminal")
    if projection["paused"]:
        raise IllegalRunControlStateError("run is already paused (state.json/projection agree)")
    event = _append_event(target, run_id, projection, "run_paused",
                          {"iteration_id": projection["iteration_id"], "reason": reason})
    _, post = runner._projection(target, mode)
    emit.sync_state_to_projection(target, post)
    return {"ok": True, "event": event, "state": post["state"]}


def resume_run(target: str | Path, *, note: str | None = None, mode: str | None = None) -> dict[str, Any]:
    run_id, projection = runner._projection(target, mode)
    if projection["terminal"] is not None:
        raise IllegalRunControlStateError("run is already terminal")
    if not projection["paused"]:
        raise IllegalRunControlStateError("run is not paused")
    payload: dict[str, Any] = {"iteration_id": projection["iteration_id"]}
    if note is not None:
        payload["note"] = note
    event = _append_event(target, run_id, projection, "run_resumed", payload)
    _, post = runner._projection(target, mode)
    emit.sync_state_to_projection(target, post)
    return {"ok": True, "event": event, "state": post["state"]}


def cancel_run(target: str | Path, *, reason: str | None = None, mode: str | None = None) -> dict[str, Any]:
    run_id, projection = runner._projection(target, mode)
    if projection["terminal"] is not None:
        raise IllegalRunControlStateError("run is already terminal")
    event = _append_event(target, run_id, projection, "terminal_written", {
        "state": "AbortedByHuman", "criteria_met": {}, "evidence": [], "false_completion": False,
        "completion_policy": emit.normalize_completion_policy(None),
    })
    emit.terminate(target, state="AbortedByHuman", criteria_met={}, evidence=[],
                   reason="" if reason is None else reason, iteration_id=projection["iteration_id"],
                   false_completion=False)
    return {"ok": True, "event": event, "state": fsm.TERMINAL_MARKER}
