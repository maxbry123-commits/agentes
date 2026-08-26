# -*- coding: utf-8 -*-
"""CapabilityBrain — T45. discover→register→map→verify→select→prepare→load. 0% LLM."""
from __future__ import annotations

from typing import Any

from .capability_intent import resolve_intent
from .environment_scan import scan_environment
from .extension_registry import ExtensionRegistry
from .hf_index import HFResourceIndex
from .resource_broker import ResourceBroker
from .resource_catalog import ResourceCatalog


class CapabilityBrain:
    def __init__(
        self,
        *,
        registry: ExtensionRegistry | None = None,
        hf_index: HFResourceIndex | None = None,
        catalog: ResourceCatalog | None = None,
    ):
        self.registry = registry or ExtensionRegistry()
        self.hf_index = hf_index or HFResourceIndex()
        self.catalog = catalog or ResourceCatalog()
        self.broker = ResourceBroker(self.catalog)

    def run(self, text: str, *,
            task_class: str | None = None) -> dict[str, Any]:
        # 1 discover env
        env = scan_environment()
        # 2 intent → required caps
        intent = resolve_intent(text, task_class=task_class)
        required = list(intent["capabilities"])

        # 3 map available
        available: dict[str, list[str]] = {}
        for cap in required:
            pkgs = self.registry.find_by_capability(cap)
            available[cap] = pkgs

        # 4 verify gaps
        missing = [c for c, pkgs in available.items() if not pkgs and c not in env.get("capabilities", [])]

        # 5 select first package per cap when present
        selected: dict[str, str | None] = {}
        loaded: dict[str, Any] = {}
        for cap, pkgs in available.items():
            if pkgs:
                selected[cap] = pkgs[0]
                loaded[cap] = self.registry.load(pkgs[0])
            else:
                selected[cap] = None

        # 6 hf index hint for resource-like caps
        hf_hits = []
        if "hf_index" in required or "resource" in required:
            hf_hits = self.hf_index.find()

        return {
            "ok": len(missing) == 0 or any(selected.values()),
            "intent": intent,
            "env_capabilities": env.get("capabilities"),
            "required": required,
            "available": available,
            "missing": missing,
            "selected": selected,
            "loaded": {k: (v.get("ok") if isinstance(v, dict) else False) for k, v in loaded.items()},
            "hf_index_count": len(hf_hits),
            "stages": [
                "discover",
                "register",
                "map",
                "verify",
                "select",
                "prepare",
                "load",
            ],
        }
