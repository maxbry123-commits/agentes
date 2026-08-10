# -*- coding: utf-8 -*-
"""
Resource Brain — registry mínimo de capacidades
Fuente: PIPELINE 12 FULL §10
Flujo: descubre → registra → mapea → verifica → selecciona → prepara → carga → ejecuta
Estados: DISCOVERED → REGISTERED → CONFIGURED → REACHABLE → HEALTHY → AUTHORIZED → AVAILABLE
A6 — Implementación ejecutable (no stub)
"""

from __future__ import annotations

import time
from dataclasses import dataclass, field, asdict
from enum import Enum
from typing import Any, Dict, List, Optional, Set


class ResourceState(str, Enum):
    DISCOVERED = "DISCOVERED"
    REGISTERED = "REGISTERED"
    CONFIGURED = "CONFIGURED"
    REACHABLE = "REACHABLE"
    HEALTHY = "HEALTHY"
    AUTHORIZED = "AUTHORIZED"
    AVAILABLE = "AVAILABLE"
    UNHEALTHY = "UNHEALTHY"
    REVOKED = "REVOKED"


_PROGRESSION = [
    ResourceState.DISCOVERED,
    ResourceState.REGISTERED,
    ResourceState.CONFIGURED,
    ResourceState.REACHABLE,
    ResourceState.HEALTHY,
    ResourceState.AUTHORIZED,
    ResourceState.AVAILABLE,
]


@dataclass
class ResourceRecord:
    resource_id: str
    kind: str
    state: ResourceState
    meta: Dict[str, Any] = field(default_factory=dict)
    discovered_at: float = field(default_factory=time.time)
    updated_at: float = field(default_factory=time.time)

    def to_dict(self) -> Dict:
        d = asdict(self)
        d["state"] = self.state.value
        return d


class ResourceBrain:
    def __init__(self):
        self._resources: Dict[str, ResourceRecord] = {}

    def discover(self, resource_id: str, kind: str = "capability", meta: Optional[Dict] = None) -> ResourceRecord:
        if resource_id in self._resources:
            return self._resources[resource_id]
        rec = ResourceRecord(
            resource_id=resource_id,
            kind=kind,
            state=ResourceState.DISCOVERED,
            meta=meta or {},
        )
        self._resources[resource_id] = rec
        return rec

    def register(self, resource_id: str) -> ResourceRecord:
        rec = self._require(resource_id)
        return self._advance(rec, ResourceState.REGISTERED)

    def configure(self, resource_id: str, config: Optional[Dict] = None) -> ResourceRecord:
        rec = self._require(resource_id)
        if config:
            rec.meta.update(config)
        return self._advance(rec, ResourceState.CONFIGURED)

    def mark_reachable(self, resource_id: str) -> ResourceRecord:
        rec = self._require(resource_id)
        return self._advance(rec, ResourceState.REACHABLE)

    def mark_healthy(self, resource_id: str) -> ResourceRecord:
        rec = self._require(resource_id)
        return self._advance(rec, ResourceState.HEALTHY)

    def mark_unhealthy(self, resource_id: str) -> ResourceRecord:
        rec = self._require(resource_id)
        rec.state = ResourceState.UNHEALTHY
        rec.updated_at = time.time()
        return rec

    def authorize(self, resource_id: str) -> ResourceRecord:
        rec = self._require(resource_id)
        return self._advance(rec, ResourceState.AUTHORIZED)

    def make_available(self, resource_id: str) -> ResourceRecord:
        rec = self._require(resource_id)
        return self._advance(rec, ResourceState.AVAILABLE)

    def revoke(self, resource_id: str) -> ResourceRecord:
        rec = self._require(resource_id)
        rec.state = ResourceState.REVOKED
        rec.updated_at = time.time()
        return rec

    def onboard(
        self,
        resource_id: str,
        kind: str = "capability",
        meta: Optional[Dict] = None,
        auto_authorize: bool = True,
    ) -> ResourceRecord:
        self.discover(resource_id, kind=kind, meta=meta)
        self.register(resource_id)
        self.configure(resource_id)
        self.mark_reachable(resource_id)
        self.mark_healthy(resource_id)
        if auto_authorize:
            self.authorize(resource_id)
            self.make_available(resource_id)
        return self._resources[resource_id]

    def is_available(self, resource_id: str) -> bool:
        rec = self._resources.get(resource_id)
        return rec is not None and rec.state == ResourceState.AVAILABLE

    def list_available(self) -> List[str]:
        return [rid for rid, r in self._resources.items() if r.state == ResourceState.AVAILABLE]

    def select(self, needed: List[str]) -> Dict[str, bool]:
        return {rid: self.is_available(rid) for rid in needed}

    def select_ready(self, needed: List[str]) -> List[str]:
        return [rid for rid in needed if self.is_available(rid)]

    def get(self, resource_id: str) -> Optional[ResourceRecord]:
        return self._resources.get(resource_id)

    def snapshot(self) -> Dict[str, Any]:
        return {
            "total": len(self._resources),
            "available": self.list_available(),
            "by_state": self._count_by_state(),
            "resources": {k: v.to_dict() for k, v in self._resources.items()},
        }

    def _count_by_state(self) -> Dict[str, int]:
        counts: Dict[str, int] = {}
        for r in self._resources.values():
            counts[r.state.value] = counts.get(r.state.value, 0) + 1
        return counts

    def _require(self, resource_id: str) -> ResourceRecord:
        if resource_id not in self._resources:
            raise KeyError(f"Resource not discovered: {resource_id}")
        return self._resources[resource_id]

    def _advance(self, rec: ResourceRecord, target: ResourceState) -> ResourceRecord:
        if rec.state in (ResourceState.REVOKED, ResourceState.UNHEALTHY):
            raise ValueError(f"Cannot advance from {rec.state.value}")
        try:
            current_idx = _PROGRESSION.index(rec.state)
            target_idx = _PROGRESSION.index(target)
        except ValueError:
            raise ValueError(f"Invalid state transition {rec.state} → {target}")
        if target_idx < current_idx:
            raise ValueError(f"Cannot go backwards: {rec.state.value} → {target.value}")
        if target_idx > current_idx + 1:
            for s in _PROGRESSION[current_idx + 1 : target_idx + 1]:
                rec.state = s
                rec.updated_at = time.time()
        else:
            rec.state = target
            rec.updated_at = time.time()
        return rec


if __name__ == "__main__":
    rb = ResourceBrain()
    rb.onboard("extract_goal", kind="microflujo")
    rb.onboard("decompose_tasks", kind="microflujo")
    rb.discover("llm_helper", kind="llm")
    rb.register("llm_helper")
    print("Available:", rb.list_available())
    print("Select:", rb.select(["extract_goal", "decompose_tasks", "llm_helper"]))
    print("Ready:", rb.select_ready(["extract_goal", "llm_helper", "decompose_tasks"]))
    print("Snapshot states:", rb.snapshot()["by_state"])
