"""Sandbox Pool + Broker (determinista).
SOURCE: SALIDA_7 · agentes nunca crean sandbox; solo solicitan.
max_mounted + liberación FIFO al saturar.
"""
from __future__ import annotations
from collections import deque
from dataclasses import dataclass, field
from typing import Literal

SandboxType = Literal["light", "heavy"]


@dataclass
class Sandbox:
    id: str
    tipo: SandboxType
    busy: bool = False


@dataclass
class SandboxPool:
    light: list[Sandbox] = field(default_factory=list)
    heavy: list[Sandbox] = field(default_factory=list)
    queue: deque[str] = field(default_factory=deque)
    max_mounted: int = 12

    def __post_init__(self) -> None:
        if not self.light:
            self.light = [Sandbox(f"L{i}", "light") for i in range(1, 5)]
        if not self.heavy:
            self.heavy = [Sandbox(f"H{i}", "heavy") for i in range(1, 3)]

    def _all(self) -> list[Sandbox]:
        return self.light + self.heavy

    def request(self, tipo: SandboxType, task_id: str) -> Sandbox | None:
        pool = self.light if tipo == "light" else self.heavy
        for sb in pool:
            if not sb.busy:
                sb.busy = True
                return sb
        # saturado: encolar (no crear más allá del pool fijo)
        if task_id not in self.queue:
            self.queue.append(task_id)
        return None

    def release(self, sb: Sandbox) -> str | None:
        sb.busy = False
        if self.queue:
            return self.queue.popleft()
        return None

    def busy_count(self) -> int:
        return sum(1 for s in self._all() if s.busy)
