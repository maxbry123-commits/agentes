"""ATL ActionQueue — priority-based action queue with blocked types."""

from __future__ import annotations

import heapq
from dataclasses import dataclass, field
from typing import Any

__all__ = ["ATLAction", "ActionQueue"]


@dataclass
class ATLAction:
    """A single proposed action from the ATL thinking cycle."""

    type: str
    params: dict[str, Any] = field(default_factory=dict)
    priority: int = 3  # 1 = highest
    rationale: str = ""


class ActionQueue:
    """Priority queue for ATL actions with max limit and blocked types."""

    def __init__(self, max_actions: int = 3, blocked_types: set[str] | None = None) -> None:
        self._max = max_actions
        self._blocked = blocked_types or set()
        self._heap: list[tuple[int, int, ATLAction]] = []  # (priority, seq, action)
        self._seq = 0

    def enqueue(self, action: ATLAction) -> bool:
        """Add action to queue. Returns False if blocked or queue full."""
        if action.type in self._blocked:
            return False
        if len(self._heap) >= self._max:
            return False
        heapq.heappush(self._heap, (action.priority, self._seq, action))
        self._seq += 1
        return True

    def dequeue(self) -> ATLAction | None:
        """Remove and return highest-priority action, or None if empty."""
        if not self._heap:
            return None
        _, _, action = heapq.heappop(self._heap)
        return action

    def empty(self) -> bool:
        return len(self._heap) == 0

    def size(self) -> int:
        return len(self._heap)

    def clear(self) -> None:
        self._heap.clear()
        self._seq = 0
