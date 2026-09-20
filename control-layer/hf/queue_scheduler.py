from collections import deque
from dataclasses import dataclass, field
from typing import Deque, Literal

Priority = Literal[0, 1, 2, 3, 4]  # P0 production → P4 background


@dataclass(order=True)
class QueuedTask:
    priority: Priority
    task_id: str = field(compare=False)
    payload: dict = field(compare=False, default_factory=dict)


class LocalQueue:
    """Cola local por dominio (SOURCE: arquitectura final de hf.md)."""

    def __init__(self) -> None:
        self._q: Deque[QueuedTask] = deque()

    def enqueue(self, task_id: str, priority: Priority = 1, payload: dict | None = None) -> None:
        self._q.append(QueuedTask(priority=priority, task_id=task_id, payload=payload or {}))
        # keep sorted by priority (0 highest)
        self._q = deque(sorted(self._q))

    def dequeue(self) -> QueuedTask | None:
        if not self._q:
            return None
        return self._q.popleft()

    def __len__(self) -> int:
        return len(self._q)


class Scheduler:
    """Scheduler simple que respeta prioridad y ResourceGovernor."""

    def __init__(self, queue: LocalQueue) -> None:
        self.queue = queue

    def next_task(self, max_concurrency: int, current_running: int) -> QueuedTask | None:
        if current_running >= max_concurrency:
            return None
        return self.queue.dequeue()
