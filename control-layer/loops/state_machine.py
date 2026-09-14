"""State machine determinista + invariantes · 0% LLM
SOURCE: loop_state.schema · LoopContext contracts
"""
from __future__ import annotations
from datetime import datetime, timezone
from typing import Any

from loops.contracts.types import (
    LoopContext,
    LoopEvent,
    TRANSITIONS,
    TERMINAL,
    assert_transition,
    can_transition,
)


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _hash_event(event_id: str, run_id: str, etype: str, payload: dict, prev: str) -> str:
    import hashlib
    raw = f"{event_id}|{run_id}|{etype}|{payload}|{prev}"
    return hashlib.sha256(raw.encode()).hexdigest()


class InvariantError(ValueError):
    pass


def check_invariants(ctx: LoopContext, *, previous: LoopContext | None = None) -> None:
    """Invariantes duras. Lanza InvariantError si se violan."""
    if not ctx.run_id:
        raise InvariantError("run_id required")
    if not ctx.project_id or not ctx.agent_id or not ctx.goal_id:
        raise InvariantError("project_id, agent_id, goal_id required")
    if ctx.iteration < 0:
        raise InvariantError("iteration must be >= 0")
    if previous is not None:
        if ctx.run_id != previous.run_id:
            raise InvariantError("run_id immutable")
        if ctx.project_id != previous.project_id:
            raise InvariantError("project_id immutable")
        if ctx.agent_id != previous.agent_id:
            raise InvariantError("agent_id immutable")
        if previous.state not in ("CREATED",) and ctx.goal_id != previous.goal_id:
            # goal locked from LOCKED onward
            if previous.state != "CREATED":
                raise InvariantError("goal_id immutable after CREATED")
        if ctx.iteration < previous.iteration:
            raise InvariantError("iteration must not decrease")
        if previous.state in TERMINAL and ctx.state != previous.state:
            if not (previous.state in ("FAILED", "ESCALATED") and ctx.state == "LOCKED"):
                # REOPEN path only FAILED/ESCALATED → LOCKED via command
                if previous.state == "CLOSED":
                    raise InvariantError("CLOSED is terminal")
    if ctx.state in TERMINAL and ctx.closed_at is None and ctx.state != "PAUSED":
        pass  # closed_at set by transition helper


class StateMachine:
    """Aplica transiciones + emite eventos (lista, no side-effects externos)."""

    def __init__(self) -> None:
        self._prev_hash: dict[str, str] = {}

    def transition(
        self,
        ctx: LoopContext,
        to_state: str,
        *,
        event_type: str,
        payload: dict[str, Any] | None = None,
        actor: str = "system",
    ) -> tuple[LoopContext, LoopEvent]:
        previous = LoopContext(**{**ctx.__dict__}) if hasattr(ctx, "__dict__") else ctx
        # shallow copy for invariant compare
        from copy import deepcopy
        prev_snap = deepcopy(ctx)

        assert_transition(ctx.state, to_state)
        ctx.state = to_state  # type: ignore[assignment]
        ctx.updated_at = _now()
        if to_state == "RUNNING" and ctx.started_at is None:
            ctx.started_at = ctx.updated_at
        if to_state in TERMINAL:
            ctx.closed_at = ctx.updated_at

        check_invariants(ctx, previous=prev_snap)

        event_id = f"evt-{ctx.run_id}-{ctx.updated_at}"
        prev_h = self._prev_hash.get(ctx.run_id, "")
        pl = payload or {}
        h = _hash_event(event_id, ctx.run_id, event_type, pl, prev_h)
        ev = LoopEvent(
            event_id=event_id,
            run_id=ctx.run_id,
            type=event_type,
            timestamp=ctx.updated_at,
            prev_hash=prev_h,
            hash=h,
            phase=ctx.phase or None,
            iteration=ctx.iteration,
            payload=pl,
            actor=actor,
        )
        self._prev_hash[ctx.run_id] = h
        return ctx, ev

    def apply_command_state(self, ctx: LoopContext, command: str) -> str | None:
        """Mapa comando → estado destino propuesto (None si inválido)."""
        mapping = {
            "START": "LOCKED" if ctx.state == "CREATED" else None,
            "CANCEL": "CANCELLED",
            "PAUSE": "PAUSED" if ctx.state in ("RUNNING", "CHECKPOINT") else None,
            "RESUME": "RUNNING" if ctx.state == "PAUSED" else None,
            "ABORT": "FAILED",
            "FORCE_CHECKPOINT": "CHECKPOINT" if ctx.state == "RUNNING" else None,
            "REOPEN": "LOCKED" if ctx.state in ("FAILED", "ESCALATED") else None,
            "RETRY": "RUNNING" if ctx.state == "FAILED" else None,
        }
        target = mapping.get(command)
        if target is None:
            return None
        if not can_transition(ctx.state, target):
            return None
        return target
