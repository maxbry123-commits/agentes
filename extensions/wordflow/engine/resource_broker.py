# -*- coding: utf-8 -*-
"""ResourceBroker — T12. prepare + load local only. 0% LLM."""
from __future__ import annotations

from typing import Any

from .capability_passport import authorize, verify_passport
from .resource_catalog import ResourceCatalog
from .resource_gate import check_entry


class ResourceBroker:
    """Orchestrates catalog + gate + optional passport for resource access."""

    def __init__(
        self,
        catalog: ResourceCatalog,
        *,
        passport: dict[str, Any] | None = None,
    ):
        self.catalog = catalog
        self.passport = passport
        self._loaded: dict[str, dict[str, Any]] = {}

    def _passport_ok(self, capability: str) -> dict[str, Any]:
        if self.passport is None:
            return {"ok": True, "reason": "NO_PASSPORT_REQUIRED"}
        v = verify_passport(self.passport)
        if not v["ok"]:
            return v
        return authorize(self.passport, capability)

    def prepare(self, resource_id: str) -> dict[str, Any]:
        """Plan access: metadata only, no I/O fetch."""
        p = self._passport_ok("resource:read")
        if not p["ok"]:
            return {"ok": False, "stage": "passport", "detail": p}

        entry = self.catalog.get(resource_id)
        if entry is None:
            return {"ok": False, "stage": "catalog", "reason": "NOT_FOUND", "resource_id": resource_id}

        g = check_entry(entry, action="prepare")
        if not g["ok"]:
            return {"ok": False, "stage": "gate", "detail": g}

        return {
            "ok": True,
            "stage": "prepare",
            "resource_id": resource_id,
            "entry": entry,
            "fetchable": bool(entry.get("fetchable")),
            "source": entry.get("source"),
            "plan": {
                "next": "load" if entry.get("source") == "local" and entry.get("fetchable") else "deny_fetch",
            },
        }

    def load(self, resource_id: str) -> dict[str, Any]:
        """Load resource content path/ref if local fetchable; else DENY remote."""
        p = self._passport_ok("resource:read")
        if not p["ok"]:
            return {"ok": False, "stage": "passport", "detail": p}

        entry = self.catalog.get(resource_id)
        if entry is None:
            return {"ok": False, "stage": "catalog", "reason": "NOT_FOUND", "resource_id": resource_id}

        g = check_entry(entry, action="fetch")
        if not g["ok"]:
            return {
                "ok": False,
                "stage": "gate",
                "detail": g,
                "resource_id": resource_id,
            }

        # Local load: record ref only (no file IO required for stub)
        payload = {
            "resource_id": resource_id,
            "ref": entry.get("ref") or entry.get("name"),
            "kind": entry.get("kind"),
            "source": entry.get("source"),
            "content_sha256": entry.get("content_sha256"),
            "pin_id": entry.get("pin_id"),
        }
        self._loaded[resource_id] = payload
        return {"ok": True, "stage": "load", "payload": payload}

    def list_loaded(self) -> list[str]:
        return sorted(self._loaded.keys())

    def get_loaded(self, resource_id: str) -> dict[str, Any] | None:
        return self._loaded.get(resource_id)
