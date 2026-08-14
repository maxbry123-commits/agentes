# -*- coding: utf-8 -*-
"""ExtensionRegistry — T38. KER-style capability packages. 0% LLM.

Kernel stays thin: packages register by id + contract, no hard imports of
engines into core beyond registry lookup.
"""
from __future__ import annotations

from typing import Any, Callable


class ExtensionRegistry:
    def __init__(self):
        self._packages: dict[str, dict[str, Any]] = {}

    def register(
        self,
        package_id: str,
        *,
        kind: str,
        version: str = "1.0",
        capabilities: list[str] | None = None,
        factory: Callable[[], Any] | None = None,
        meta: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        if not package_id:
            raise ValueError("package_id required")
        if package_id in self._packages:
            raise ValueError(f"duplicate package: {package_id}")
        entry = {
            "package_id": package_id,
            "kind": kind,
            "version": version,
            "capabilities": list(capabilities or []),
            "factory": factory,
            "meta": dict(meta or {}),
            "loaded": False,
            "instance": None,
        }
        self._packages[package_id] = entry
        return {
            "ok": True,
            "package_id": package_id,
            "kind": kind,
            "version": version,
        }

    def load(self, package_id: str) -> dict[str, Any]:
        e = self._packages.get(package_id)
        if not e:
            return {"ok": False, "reason": "NOT_FOUND"}
        if e["loaded"] and e["instance"] is not None:
            return {"ok": True, "package_id": package_id, "instance": e["instance"], "cached": True}
        inst = None
        if e["factory"] is not None:
            inst = e["factory"]()
        e["instance"] = inst
        e["loaded"] = True
        return {"ok": True, "package_id": package_id, "instance": inst, "cached": False}

    def find_by_capability(self, cap: str) -> list[str]:
        return [
            pid
            for pid, e in self._packages.items()
            if cap in (e.get("capabilities") or [])
        ]

    def list_packages(self) -> list[dict[str, Any]]:
        out = []
        for e in self._packages.values():
            out.append(
                {
                    "package_id": e["package_id"],
                    "kind": e["kind"],
                    "version": e["version"],
                    "capabilities": list(e["capabilities"]),
                    "loaded": e["loaded"],
                }
            )
        return out
