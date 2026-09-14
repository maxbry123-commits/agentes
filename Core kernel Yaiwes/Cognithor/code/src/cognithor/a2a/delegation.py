"""Direction-based delegation for A2A protocol.

Extends the A2A message envelope with a ``direction`` field.
Agents hand off tasks as directions, not rigid calls.

Directions:
  - ``"remember"`` — target writes to its memory tier, returns confirmation
  - ``"act"``      — target executes the payload as a task, returns result
  - ``"notes"``    — target appends to log/notes store, fire-and-forget
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from typing import Any, Literal

from cognithor.utils.logging import get_logger

log = get_logger(__name__)

Direction = Literal["remember", "act", "notes"]

# Which roles can send which directions
_ROLE_SEND_PERMISSIONS: dict[str, set[Direction]] = {
    "orchestrator": {"remember", "act", "notes"},
    "worker": {"notes"},
    "monitor": {"notes"},
}


@dataclass
class DirectedMessage:
    """An A2A message with a direction field."""

    direction: Direction = "act"
    source_agent: str = ""
    target_agent: str = ""
    payload: dict[str, Any] = field(default_factory=dict)
    context: dict[str, Any] = field(default_factory=dict)
    message_id: str = field(default_factory=lambda: uuid.uuid4().hex[:16])

    def to_dict(self) -> dict[str, Any]:
        return {
            "direction": self.direction,
            "source_agent": self.source_agent,
            "target_agent": self.target_agent,
            "payload": self.payload,
            "context": self.context,
            "message_id": self.message_id,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> DirectedMessage:
        return cls(
            direction=data.get("direction", "act"),
            source_agent=data.get("source_agent", ""),
            target_agent=data.get("target_agent", ""),
            payload=data.get("payload", {}),
            context=data.get("context", {}),
            message_id=data.get("message_id", ""),
        )


class DirectionPermissionError(Exception):
    """Raised when an agent doesn't have permission to send a direction."""


def can_send_direction(role: str, direction: Direction) -> bool:
    """Check if the given role is allowed to send the given direction."""
    allowed = _ROLE_SEND_PERMISSIONS.get(role, set())
    return direction in allowed


def validate_direction_target(direction: Direction, target_tools: set[str]) -> bool:
    """Validate that the target agent has the required tools for the direction.

    - ``"remember"`` requires memory-write tools
    - ``"act"`` can go to any worker
    - ``"notes"`` can go to anyone
    """
    if direction == "notes":
        return True
    if direction == "act":
        return True  # Any worker can act
    if direction == "remember":
        memory_write_tools = {"save_to_memory", "add_entity", "add_relation"}
        return bool(target_tools & memory_write_tools)
    return False


@dataclass
class DirectionResult:
    """Result of a directed delegation."""

    direction: Direction
    success: bool = True
    result: Any = None
    error: str | None = None
    fire_and_forget: bool = False

    @property
    def is_fire_and_forget(self) -> bool:
        return self.direction == "notes" or self.fire_and_forget


async def direct(
    source_role: str,
    target_agent: str,
    direction: Direction,
    payload: dict[str, Any],
    *,
    handler: Any = None,
) -> DirectionResult:
    """Send a directed message to another agent.

    Args:
        source_role: Role of the sending agent.
        target_agent: ID/name of the target agent.
        direction: One of "remember", "act", "notes".
        payload: Data to send.
        handler: Async callable to dispatch the message (injected by gateway).

    Returns:
        DirectionResult with outcome.
    """
    if not can_send_direction(source_role, direction):
        raise DirectionPermissionError(f"Role '{source_role}' cannot send direction '{direction}'")

    msg = DirectedMessage(
        direction=direction,
        target_agent=target_agent,
        payload=payload,
    )

    log.info(
        "direction_sent",
        direction=direction,
        target=target_agent,
        source_role=source_role,
    )

    if direction == "notes":
        # Fire-and-forget: don't wait for result
        if handler is not None:
            try:
                await handler(msg)
            except Exception:
                log.debug("notes_handler_failed", exc_info=True)
        return DirectionResult(direction="notes", fire_and_forget=True)

    if handler is not None:
        try:
            result = await handler(msg)
            return DirectionResult(direction=direction, result=result)
        except Exception as exc:
            return DirectionResult(direction=direction, success=False, error=str(exc))

    return DirectionResult(direction=direction, success=False, error="No handler provided")
