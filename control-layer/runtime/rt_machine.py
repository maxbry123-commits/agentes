"""Máquina RT-00→RT-90 — transiciones fijas.
SOURCE: runtime/rt_states.yaml · UOOS Parte 2
"""
from __future__ import annotations
from dataclasses import dataclass, field

BOOT = ["RT-00", "RT-01", "RT-02", "RT-03", "RT-04"]
PER_NODE = [
    "RT-10", "RT-11", "RT-12", "RT-13", "RT-14",
    "RT-20", "RT-30", "RT-31", "RT-40", "RT-41",
    "RT-42", "RT-43", "RT-44", "RT-45",
]
RECOVERY = "RT-80"
CLOSE = "RT-90"


@dataclass
class RTMachine:
    state: str = "RT-00"
    history: list[str] = field(default_factory=list)

    def advance_boot(self) -> str:
        if self.state not in BOOT:
            self.state = BOOT[0]
        idx = BOOT.index(self.state)
        if idx + 1 < len(BOOT):
            self.state = BOOT[idx + 1]
        self.history.append(self.state)
        return self.state

    def start_node_cycle(self) -> str:
        self.state = PER_NODE[0]
        self.history.append(self.state)
        return self.state

    def advance_node(self) -> str:
        if self.state not in PER_NODE:
            return self.start_node_cycle()
        idx = PER_NODE.index(self.state)
        if idx + 1 < len(PER_NODE):
            self.state = PER_NODE[idx + 1]
        else:
            self.state = PER_NODE[0]  # siguiente nodo reinicia ciclo
        self.history.append(self.state)
        return self.state

    def fail(self) -> str:
        self.state = RECOVERY
        self.history.append(self.state)
        return self.state

    def close(self) -> str:
        self.state = CLOSE
        self.history.append(self.state)
        return self.state
