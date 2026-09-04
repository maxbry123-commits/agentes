# -*- coding: utf-8 -*-
"""C-27 Unified Registry — Skill/Dataset/Method/Adapter packages. 0% LLM."""
from __future__ import annotations

import hashlib
import json
from typing import Any

KINDS = frozenset({"skill", "dataset", "method", "adapter", "capability"})


class RegistryError(Exception):
    def __init__(self, reason_code: str, detail: str = ""):
        self.reason_code = reason_code
        self.detail = detail
        super().__init__(f"{reason_code}: {detail}" if detail else reason_code)


def _pkg_hash(body: dict[str, Any]) -> str:
    canonical = json.dumps(body, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def make_package(
    *,
    kind: str,
    package_id: str,
    version: str = "1.0.0",
    inputs: list[str] | None = None,
    outputs: list[str] | None = None,
    deps: list[str] | None = None,
    license: str = "MIT",
    tests: list[str] | None = None,
    meta: dict[str, Any] | None = None,
) -> dict[str, Any]:
    if kind not in KINDS:
        raise RegistryError("INVALID_KIND", kind)
    if not package_id:
        raise RegistryError("PACKAGE_ID_EMPTY")
    body = {
        "kind": kind,
        "package_id": package_id,
        "version": version,
        "inputs": list(inputs or []),
        "outputs": list(outputs or []),
        "deps": list(deps or []),
        "license": license,
        "tests": list(tests or []),
        "meta": dict(meta or {}),
        "llm_control": "DENY",
    }
    body["package_hash"] = _pkg_hash({k: v for k, v in body.items() if k != "package_hash"})
    return body


class UnifiedRegistry:
    def __init__(self) -> None:
        self._by_id: dict[str, dict[str, Any]] = {}

    def register(self, package: dict[str, Any]) -> dict[str, Any]:
        if not isinstance(package, dict):
            raise RegistryError("PACKAGE_NOT_OBJECT")
        for f in ("kind", "package_id", "version", "package_hash"):
            if f not in package:
                raise RegistryError("MISSING_FIELD", f)
        if package["kind"] not in KINDS:
            raise RegistryError("INVALID_KIND", package["kind"])
        expected = _pkg_hash({k: v for k, v in package.items() if k != "package_hash"})
        if package["package_hash"] != expected:
            raise RegistryError("HASH_MISMATCH", package["package_id"])
        key = f"{package['package_id']}@{package['version']}"
        self._by_id[key] = package
        return {"ok": True, "key": key}

    def get(self, package_id: str, version: str = "1.0.0") -> dict[str, Any] | None:
        return self._by_id.get(f"{package_id}@{version}")

    def list(self, kind: str | None = None) -> list[dict[str, Any]]:
        rows = list(self._by_id.values())
        if kind:
            rows = [p for p in rows if p.get("kind") == kind]
        return rows

    def resolve_deps(self, package_id: str, version: str = "1.0.0") -> dict[str, Any]:
        pkg = self.get(package_id, version)
        if not pkg:
            return {"ok": False, "reason": "NOT_FOUND"}
        missing = []
        for dep in pkg.get("deps") or []:
            # dep format: id or id@version
            if "@" in dep:
                pid, ver = dep.split("@", 1)
            else:
                pid, ver = dep, "1.0.0"
            if self.get(pid, ver) is None:
                missing.append(dep)
        return {
            "ok": len(missing) == 0,
            "package_id": package_id,
            "missing_deps": missing,
            "deps": list(pkg.get("deps") or []),
        }
