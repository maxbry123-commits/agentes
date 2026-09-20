"""Deterministic replay desde event log · 0% LLM
SOURCE: P2 · reconstruye estados desde LoopEvent chain
"""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import Any

from loops.contracts.types import LoopEvent, TRANSITIONS, can_transition
from loops.event_chain import verify_chain

# event type → implied state
EVENT_TO_STATE = {
    "LOOP_CREATED": "CREATED",
    "LOOP_LOCKED": "LOCKED",
    "PHASE_STARTED": "RUNNING",
    "PHASE_COMPLETED": "VALIDATING",
    "POLICY_DECIDED": "DECIDING",
    "LOOP_CONTINUED": "RUNNING",
    "REPAIR_STARTED": "REPAIRING",
    "REPAIR_COMPLETED": "RUNNING",
    "CHECKPOINT_CREATED": "CHECKPOINT",
    "LOOP_COMPLETED": "CLOSED",
    "LOOP_FAILED": "FAILED",
    "LOOP_ESCALATED": "ESCALATED",
    "LOOP_CANCELLED": "CANCELLED",
    "LOOP_PAUSED": "PAUSED",
    "LOOP_RESUMED": "RUNNING",
}


@dataclass
class ReplayResult:
    ok: bool
    final_state: str
    states: list[str] = field(default_factory=list)
    chain_ok: bool = True
    chain_reason: str = ""
    illegal_transitions: list[str] = field(default_factory=list)
    events_applied: int = 0


class EventReplayer:
    def replay(self, events: list[LoopEvent]) -> ReplayResult:
        chain_ok, chain_reason = verify_chain(events)
        state = "CREATED"
        states = [state]
        illegal: list[str] = []
        applied = 0
        for ev in events:
            if ev.type == "HEARTBEAT":
                continue
            target = EVENT_TO_STATE.get(ev.type)
            if not target:
                applied += 1
                continue
            if state != target and not can_transition(state, target):
                # allow if already at target (idempotent)
                if state != target:
                    illegal.append(f"{state}→{target} via {ev.type}")
            state = target
            states.append(state)
            applied += 1
        return ReplayResult(
            ok=chain_ok and len(illegal) == 0,
            final_state=state,
            states=states,
            chain_ok=chain_ok,
            chain_reason=chain_reason,
            illegal_transitions=illegal,
            events_applied=applied,
        )
