# -*- coding: utf-8 -*-
"""C-08 Resource Runtime — 8-step lifecycle. No load unless AVAILABLE. 0% LLM."""
from __future__ import annotations

from typing import Any

from .resource_catalog import ResourceCatalog, make_entry, verify_entry
from .resource_gate import check_entry

STATES = (
    "DISCOVERED",
    "REGISTERED",
    "RESOLVED",
    "PINNED",
    "CACHED",
    "PREPARED",
    "AVAILABLE",
    "FAILED",
)

# Allowed transitions (strict)
TRANSITIONS: dict[str, set[str]] = {
    "DISCOVERED": {"REGISTERED", "FAILED"},
    "REGISTERED": {"RESOLVED", "FAILED"},
    "RESOLVED": {"PINNED", "FAILED"},
    "PINNED": {"CACHED", "PREPARED", "FAILED"},
    "CACHED": {"PREPARED", "FAILED"},
    "PREPARED": {"AVAILABLE", "FAILED"},
    "AVAILABLE": set(),
    "FAILED": set(),
}


class ResourceRuntimeError(Exception):
    def __init__(self, reason_code: str, detail: str = ""):
        self.reason_code = reason_code
        self.detail = detail
        super().__init__(f"{reason_code}: {detail}" if detail else reason_code)


class ResourceRuntime:
    """Tracks per-resource lifecycle. Load denied unless AVAILABLE."""

    def __init__(self, catalog: ResourceCatalog | None = None):
        self.catalog = catalog or ResourceCatalog()
        self._state: dict[str, str] = {}
        self._meta: dict[str, dict[str, Any]] = {}

    def state_of(self, resource_id: str) -> str | None:
        return self._state.get(resource_id)

    def _set(self, resource_id: str, new_state: str, **meta: Any) -> None:
        cur = self._state.get(resource_id)
        if cur is None:
            if new_state != "DISCOVERED":
                raise ResourceRuntimeError("MUST_START_DISCOVERED", resource_id)
        else:
            allowed = TRANSITIONS.get(cur, set())
            if new_state not in allowed:
                raise ResourceRuntimeError(
                    "INVALID_TRANSITION",
                    f"{cur}->{new_state}",
                )
        self._state[resource_id] = new_state
        row = self._meta.get(resource_id, {})
        row.update(meta)
        row["state"] = new_state
        self._meta[resource_id] = row

    def discover(self, *, name: str, kind: str, source: str = "local", **kwargs: Any) -> dict[str, Any]:
        entry = make_entry(name=name, kind=kind, source=source, **kwargs)
        rid = entry["resource_id"]
        self._set(rid, "DISCOVERED", entry=entry)
        return {"ok": True, "resource_id": rid, "state": "DISCOVERED", "entry": entry}

    def register(self, resource_id: str) -> dict[str, Any]:
        meta = self._meta.get(resource_id) or {}
        entry = meta.get("entry")
        if not entry:
            raise ResourceRuntimeError("NO_ENTRY", resource_id)
        self.catalog.add(entry)
        self._set(resource_id, "REGISTERED")
        return {"ok": True, "resource_id": resource_id, "state": "REGISTERED"}

    def resolve(self, resource_id: str) -> dict[str, Any]:
        entry = self.catalog.get(resource_id) or (self._meta.get(resource_id) or {}).get("entry")
        if not entry:
            raise ResourceRuntimeError("NOT_IN_CATALOG", resource_id)
        v = verify_entry(entry)
        if not v["ok"]:
            self._set(resource_id, "FAILED", reason=v["reason"])
            return {"ok": False, "state": "FAILED", "reason": v["reason"]}
        self._set(resource_id, "RESOLVED", entry=entry)
        return {"ok": True, "resource_id": resource_id, "state": "RESOLVED"}

    def pin(self, resource_id: str, pin_id: str) -> dict[str, Any]:
        if not pin_id:
            raise ResourceRuntimeError("PIN_EMPTY", resource_id)
        self._set(resource_id, "PINNED", pin_id=pin_id)
        return {"ok": True, "resource_id": resource_id, "state": "PINNED", "pin_id": pin_id}

    def cache(self, resource_id: str) -> dict[str, Any]:
        self._set(resource_id, "CACHED")
        return {"ok": True, "resource_id": resource_id, "state": "CACHED"}

    def prepare(self, resource_id: str) -> dict[str, Any]:
        entry = self.catalog.get(resource_id) or (self._meta.get(resource_id) or {}).get("entry")
        if entry:
            g = check_entry(entry, action="prepare")
            if not g.get("ok"):
                self._set(resource_id, "FAILED", reason=g.get("reason"))
                return {"ok": False, "state": "FAILED", "reason": g.get("reason")}
        self._set(resource_id, "PREPARED")
        return {"ok": True, "resource_id": resource_id, "state": "PREPARED"}

    def mark_available(self, resource_id: str) -> dict[str, Any]:
        self._set(resource_id, "AVAILABLE")
        return {"ok": True, "resource_id": resource_id, "state": "AVAILABLE"}

    def load(self, resource_id: str) -> dict[str, Any]:
        """Fail-closed: only AVAILABLE resources may load."""
        st = self._state.get(resource_id)
        if st != "AVAILABLE":
            return {
                "ok": False,
                "reason": "NOT_AVAILABLE",
                "state": st,
                "resource_id": resource_id,
            }
        entry = self.catalog.get(resource_id) or (self._meta.get(resource_id) or {}).get("entry")
        return {
            "ok": True,
            "resource_id": resource_id,
            "state": "AVAILABLE",
            "entry": entry,
            "llm_control": "DENY",
        }

    def run_pipeline(self, *, name: str, kind: str, source: str = "local", pin_id: str = "pin_local") -> dict[str, Any]:
        """DISCOVERED→…→AVAILABLE happy path for local resources."""
        d = self.discover(name=name, kind=kind, source=source, fetchable=(source == "local"))
        rid = d["resource_id"]
        self.register(rid)
        self.resolve(rid)
        self.pin(rid, pin_id)
        self.cache(rid)
        self.prepare(rid)
        self.mark_available(rid)
        return self.load(rid)
