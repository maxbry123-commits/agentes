# -*- coding: utf-8 -*-
"""WordflowBootstrap — T41. Thin Kernel.start(). 0% LLM.

No god-controller: wires registry + optional defaults only.
"""
from __future__ import annotations

from typing import Any

from .environment_scan import scan_environment
from .extension_registry import ExtensionRegistry
from .github_publisher import DryRunExecutor, GitHubPublisher, MapCredentialStore
from .hf_index import HFResourceIndex
from .runtime_bus import RuntimeBus


class WordflowKernel:
    def __init__(self):
        self.registry = ExtensionRegistry()
        self.bus = RuntimeBus()
        self.hf_index = HFResourceIndex()
        self.env: dict[str, Any] = {}
        self.publisher: GitHubPublisher | None = None
        self.started = False

    def start(
        self,
        *,
        register_defaults: bool = True,
        credential_map: dict[str, str] | None = None,
        declared_services: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        self.env = scan_environment(declared_services=declared_services)
        if register_defaults:
            self._register_defaults(credential_map=credential_map)
        self.started = True
        return {
            "ok": True,
            "started": True,
            "packages": self.registry.list_packages(),
            "capabilities": list(self.env.get("capabilities") or []),
        }

    def _register_defaults(self, *,
                           credential_map: dict[str, str] | None = None) -> None:
        def pub_factory():
            return GitHubPublisher(
                credentials=MapCredentialStore(credential_map or {}),
                executor=DryRunExecutor(),
            )

        self.registry.register(
            "wordflow.github_publisher",
            kind="capability",
            version="1.0",
            capabilities=["github_publish"],
            factory=pub_factory,
        )
        self.registry.register(
            "wordflow.hf_index",
            kind="capability",
            version="1.0",
            capabilities=["hf_index", "resource"],
            factory=lambda: self.hf_index,
        )
        self.registry.register(
            "wordflow.runtime_bus",
            kind="runtime",
            version="1.0",
            capabilities=["engine_bus"],
            factory=lambda: self.bus,
        )

    def load(self, package_id: str) -> dict[str, Any]:
        if not self.started:
            return {"ok": False, "reason": "NOT_STARTED"}
        return self.registry.load(package_id)
