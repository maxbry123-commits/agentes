"""Persistent gap lifecycle adapter.

Uses GapRegistry as the single storage/ownership authority; this module adds
explicit lifecycle validation without creating a second gap store.
"""
from __future__ import annotations

from .gap_registry import GapRegistry, Gap


class GapStateMachine:
    STATES = ("OPEN", "FIXED", "VERIFIED", "CLOSED")

    def __init__(self, registry: GapRegistry | None = None) -> None:
        self.registry = registry or GapRegistry()

    def create(self, gap: Gap) -> Gap:
        if gap.status != "OPEN":
            raise ValueError("new gaps must start OPEN")
        self.registry.add(gap)
        return gap

    def advance(self, gap_id: str, status: str, *, evidence: str, revision: str = "") -> Gap:
        if status not in self.STATES:
            raise ValueError(f"unknown gap state: {status}")
        return self.registry.transition(gap_id, status, evidence=evidence, revision=revision)

    def recover(self) -> list[dict]:
        return self.registry.to_list()

    def is_closed(self, gap_id: str) -> bool:
        return any(g["gap_id"] == gap_id and g["status"] == "CLOSED" for g in self.recover())
