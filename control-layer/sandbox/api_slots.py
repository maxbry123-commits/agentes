"""API Slot Pool — multi-API paralelo, orden de registro (determinista).
SOURCE: SALIDA_7 · APORTES_3 · nunca random.
Estados: FREE · BUSY · COOLDOWN · DEAD
"""
from __future__ import annotations
from dataclasses import dataclass, field
from enum import Enum
from time import time


class SlotState(str, Enum):
    FREE = "FREE"
    BUSY = "BUSY"
    COOLDOWN = "COOLDOWN"
    DEAD = "DEAD"


@dataclass
class Slot:
    id: str
    state: SlotState = SlotState.FREE
    fails: int = 0
    cooldown_until: float = 0.0


@dataclass
class ApiSlotPool:
    slots: list[Slot] = field(default_factory=list)
    max_fails: int = 3
    cooldown_s: float = 30.0

    def acquire(self) -> Slot | None:
        now = time()
        for s in self.slots:
            if s.state == SlotState.COOLDOWN and now >= s.cooldown_until:
                s.state = SlotState.FREE
            if s.state == SlotState.FREE:
                s.state = SlotState.BUSY
                return s
        return None

    def release(self, slot: Slot) -> None:
        if slot.state != SlotState.DEAD:
            slot.state = SlotState.FREE

    def mark_429(self, slot: Slot) -> None:
        slot.state = SlotState.COOLDOWN
        slot.cooldown_until = time() + self.cooldown_s

    def mark_fail(self, slot: Slot) -> None:
        slot.fails += 1
        if slot.fails >= self.max_fails:
            slot.state = SlotState.DEAD
        else:
            self.mark_429(slot)
