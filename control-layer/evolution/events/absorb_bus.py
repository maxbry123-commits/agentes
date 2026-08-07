"""Eventos absorb.*."""
from __future__ import annotations
from dataclasses import asdict, dataclass, field
from typing import Any, Callable

@dataclass
class AbsorbEvent:
    type: str
    payload: dict = field(default_factory=dict)
    def to_dict(self): return asdict(self)

class AbsorbBus:
    def __init__(self):
        self._subs = []
        self.history = []
    def subscribe(self, fn):
        self._subs.append(fn)
    def emit(self, type_, payload=None):
        ev = AbsorbEvent(type=type_, payload=dict(payload or {}))
        self.history.append(ev)
        for fn in self._subs:
            try: fn(ev)
            except Exception: pass
        return ev
