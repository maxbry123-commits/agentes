"""Blocking bridge for interactive tool-ui components: AskUI parks here until the user
answers in the transcript (or the wait times out). Keyed by (session_id, component props.id),
so the frontend can respond without ever learning a server-side request id."""

import asyncio
import time
from typing import Any, Dict, Literal, Optional, Tuple

from pydantic import BaseModel, ConfigDict, InstanceOf
from typeguard import typechecked

MAX_PENDING = 50
MAX_WAIT_SECONDS = 600.0
# The card is clickable the moment its tool_call broadcasts, but the wait only parks after the CLI hook round-trip, stdio dispatch and an HTTP hop; an instant click landing in that gap must not be dropped (ENG-232 D4).
EARLY_ANSWER_TTL_SECONDS = 45.0
MAX_EARLY = 50

RespondOutcome = Literal["delivered", "buffered", "gone"]


class PendingUiRequest(BaseModel):
    model_config = ConfigDict(validate_assignment=True)
    event: InstanceOf[asyncio.Event]
    response: Optional[Dict[str, Any]] = None


class EarlyAnswer(BaseModel):
    model_config = ConfigDict(validate_assignment=True)
    stamp: float
    response: Dict[str, Any]


p_pending: Dict[Tuple[str, str], PendingUiRequest] = {}
p_early: Dict[Tuple[str, str], EarlyAnswer] = {}


@typechecked
def p_prune_early(now: float) -> None:
    for key in [k for k, v in p_early.items() if now - v.stamp > EARLY_ANSWER_TTL_SECONDS]:
        p_early.pop(key, None)


@typechecked
async def wait_for_ui_response(session_id: str, component_id: str, timeout_s: float) -> Optional[Dict[str, Any]]:
    """Registers the request and blocks until respond_to_ui_request fires it; None on timeout."""
    key = (session_id, component_id)
    p_prune_early(time.monotonic())
    early = p_early.pop(key, None)
    if early is not None:
        return early.response
    if len(p_pending) >= MAX_PENDING:
        raise ValueError("too many pending UI requests")
    # A retried tool call for the same component replaces the stale wait; the old waiter times out.
    pending = PendingUiRequest(event=asyncio.Event())
    p_pending[key] = pending
    try:
        await asyncio.wait_for(pending.event.wait(), timeout=min(timeout_s, MAX_WAIT_SECONDS))
        return pending.response
    except asyncio.TimeoutError:
        return None
    finally:
        if p_pending.get(key) is pending:
            p_pending.pop(key, None)


@typechecked
def respond_to_ui_request(session_id: str, component_id: str, response: Dict[str, Any]) -> RespondOutcome:
    """Delivers the user's answer to the parked wait, or holds it briefly for a wait still en route."""
    pending = p_pending.get((session_id, component_id))
    if pending is not None:
        pending.response = response
        pending.event.set()
        return "delivered"
    now = time.monotonic()
    p_prune_early(now)
    if len(p_early) >= MAX_EARLY:
        return "gone"
    p_early[(session_id, component_id)] = EarlyAnswer(stamp=now, response=response)
    return "buffered"


@typechecked
def reset_ui_bridge() -> None:
    p_pending.clear()
    p_early.clear()


@typechecked
def cancel_session_waits(session_id: str) -> int:
    """Releases every parked wait for a stopped session so its cards can't eat later clicks (ENG-232 D5)."""
    released = 0
    for key, pending in list(p_pending.items()):
        if key[0] == session_id:
            pending.event.set()
            released += 1
    for key in [k for k in p_early if k[0] == session_id]:
        p_early.pop(key, None)
    return released
