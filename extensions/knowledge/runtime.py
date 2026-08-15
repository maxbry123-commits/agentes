# -*- coding: utf-8 -*-
"""C-27 Knowledge Runtime — thin facade over UnifiedRegistry. 0% LLM."""
from __future__ import annotations

from typing import Any

from .registry import UnifiedRegistry, make_package, RegistryError


class KnowledgeRuntime:
    def __init__(self, registry: UnifiedRegistry | None = None):
        self.registry = registry or UnifiedRegistry()

    def register_skill(self, package_id: str, **kwargs: Any) -> dict[str, Any]:
        pkg = make_package(kind="skill", package_id=package_id, **kwargs)
        return self.registry.register(pkg)

    def register_dataset(self, package_id: str, **kwargs: Any) -> dict[str, Any]:
        pkg = make_package(kind="dataset", package_id=package_id, **kwargs)
        return self.registry.register(pkg)

    def register_method(self, package_id: str, **kwargs: Any) -> dict[str, Any]:
        pkg = make_package(kind="method", package_id=package_id, **kwargs)
        return self.registry.register(pkg)

    def register_adapter(self, package_id: str, **kwargs: Any) -> dict[str, Any]:
        pkg = make_package(kind="adapter", package_id=package_id, **kwargs)
        return self.registry.register(pkg)

    def promote_method(self, package_id: str, version: str = "1.0.0") -> dict[str, Any]:
        """Verify deps then mark meta.promoted=true (deterministic)."""
        resolved = self.registry.resolve_deps(package_id, version)
        if not resolved["ok"]:
            return {"ok": False, "reason": "DEPS_MISSING", "detail": resolved}
        pkg = self.registry.get(package_id, version)
        if not pkg:
            return {"ok": False, "reason": "NOT_FOUND"}
        # re-register with promoted flag (new hash)
        meta = dict(pkg.get("meta") or {})
        meta["promoted"] = True
        new_pkg = make_package(
            kind=pkg["kind"],
            package_id=pkg["package_id"],
            version=pkg["version"],
            inputs=pkg.get("inputs"),
            outputs=pkg.get("outputs"),
            deps=pkg.get("deps"),
            license=pkg.get("license", "MIT"),
            tests=pkg.get("tests"),
            meta=meta,
        )
        self.registry.register(new_pkg)
        return {"ok": True, "package_id": package_id, "promoted": True, "llm_control": "DENY"}
