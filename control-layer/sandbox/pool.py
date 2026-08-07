"""Sandbox Pool + Broker (stub determinista).
SOURCE: SALIDA_7 · agentes nunca crean sandbox; solo solicitan.
"""
from __future__ import annotations
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
    queue: list[str] = field(default_factory=list)

    def __post_init__(self) -> None:
        if not self.light:
            self.light = [Sandbox(f"L{i}", "light") for i in range(1, 5)]
        if not self.heavy:
            self.heavy = [Sandbox(f"H{i}", "heavy") for i in range(1, 3)]

    def request(self, tipo: SandboxType, task_id: str) -> Sandbox | None:
        pool = self.light if tipo == "light" else self.heavy
        for sb in pool:
            if not sb.busy:
                sb.busy = True
                return sb
        self.queue.append(task_id)
        return None

    def release(self, sb: Sandbox) -> None:
        sb.busy = False
