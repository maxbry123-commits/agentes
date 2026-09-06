"""Pause/resume run-control adapter over the YAIWES state-store interface.

Provenance:
- source behavior: maxbry123-commits/Agentes-motores-Wordflow-YAIWES
  Loop Engineer/Loop-Engineer/loop/runcontrol.py
- source blob: 2c6aff845c97b600d4b3851b5ee9a6e0ee23defb

The external event-store is intentionally not copied.  This adapter keeps the
run-control invariants while using the existing YAIWES store contract:
``get``, ``set`` and ``checkpoint``.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Protocol


class RunControlStore(Protocol):
    def get(self, key: str, default: Any = None) -> Any: ...
    def set(self, key: str, value: Any) -> None: ...
    def checkpoint(self, block_id: str, payload: dict[str, Any]) -> str: ...


class RunControlError(RuntimeError):
    """Invalid or conflicting run-control transition."""


@dataclass(frozen=True)
class RunControlResult:
    run_id: str
    paused: bool
    checkpoint_id: str
    iteration_id: int


def _state_key(run_id: str) -> str:
    if not run_id:
        raise RunControlError("run_id must be non-empty")
    return f"run-control:{run_id}"


def _read(store: RunControlStore, run_id: str) -> dict[str, Any]:
    value = store.get(_state_key(run_id), {})
    if not isinstance(value, dict):
        raise RunControlError("run-control state must be a mapping")
    return dict(value)


def pause_run(
    store: RunControlStore,
    run_id: str,
    *,
    iteration_id: int,
    reason: str,
) -> RunControlResult:
    """Persist a pause exactly once at the current durable iteration."""
    if not reason.strip():
        raise RunControlError("pause reason must be non-empty")
    current = _read(store, run_id)
    if current.get("paused") is True:
        raise RunControlError("run is already paused")
    payload = {
        "run_id": run_id,
        "paused": True,
        "iteration_id": int(iteration_id),
        "reason": reason,
    }
    checkpoint_id = store.checkpoint(f"run-control:{run_id}:{iteration_id}", payload)
    payload["checkpoint_id"] = checkpoint_id
    store.set(_state_key(run_id), payload)
    return RunControlResult(run_id, True, checkpoint_id, int(iteration_id))


def resume_run(
    store: RunControlStore,
    run_id: str,
    *,
    expected_checkpoint_id: str,
    note: str | None = None,
) -> RunControlResult:
    """Resume only the exact paused checkpoint; fail closed on identity drift."""
    current = _read(store, run_id)
    if current.get("paused") is not True:
        raise RunControlError("run is not paused")
    recorded = str(current.get("checkpoint_id", ""))
    if not recorded or recorded != expected_checkpoint_id:
        raise RunControlError("resume checkpoint mismatch")
    resumed = dict(current)
    resumed["paused"] = False
    if note is not None:
        resumed["resume_note"] = note
    store.set(_state_key(run_id), resumed)
    return RunControlResult(
        run_id,
        False,
        recorded,
        int(resumed.get("iteration_id", 0)),
    )
