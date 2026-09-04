"""Method/Capability registry · mínimo · quarantine hasta tests_passed.

Kernel solo ve registry + execute por capability id.
No compila packages pesados aquí (eso es fase TEAM).
"""
from __future__ import annotations

import json
import time
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Mapping, Optional


@dataclass
class MethodManifest:
    id: str
    name: str
    version: str
    capabilities: list[str]
    inputs: list[str] = field(default_factory=list)
    outputs: list[str] = field(default_factory=list)
    contracts: list[str] = field(default_factory=list)
    quarantine: bool = True
    tests_passed: bool = False
    entry: str = ""
    meta: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    @staticmethod
    def from_dict(d: Mapping[str, Any]) -> "MethodManifest":
        return MethodManifest(
            id=str(d["id"]),
            name=str(d.get("name") or d["id"]),
            version=str(d.get("version") or "0.0.0"),
            capabilities=list(d.get("capabilities") or []),
            inputs=list(d.get("inputs") or []),
            outputs=list(d.get("outputs") or []),
            contracts=list(d.get("contracts") or []),
            quarantine=bool(d.get("quarantine", True)),
            tests_passed=bool(d.get("tests_passed", False)),
            entry=str(d.get("entry") or ""),
            meta=dict(d.get("meta") or {}),
        )

    @property
    def active(self) -> bool:
        return self.tests_passed and not self.quarantine


@dataclass
class MethodRecord:
    manifest: MethodManifest
    registered_at: float
    source: str = "local"

    def to_dict(self) -> dict[str, Any]:
        return {
            "manifest": self.manifest.to_dict(),
            "registered_at": self.registered_at,
            "source": self.source,
            "active": self.manifest.active,
        }


class MethodRegistry:
    def __init__(self, path: Path | None = None) -> None:
        self._by_id: Dict[str, MethodRecord] = {}
        self._path = path
        if path and path.is_file():
            self._load(path)

    def _load(self, path: Path) -> None:
        data = json.loads(path.read_text(encoding="utf-8"))
        for item in data.get("methods") or []:
            m = MethodManifest.from_dict(item["manifest"])
            self._by_id[m.id] = MethodRecord(
                manifest=m,
                registered_at=float(item.get("registered_at") or time.time()),
                source=str(item.get("source") or "local"),
            )

    def save(self) -> None:
        if not self._path:
            return
        self._path.parent.mkdir(parents=True, exist_ok=True)
        payload = {
            "methods": [r.to_dict() for r in self._by_id.values()],
        }
        self._path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")

    def register(self, manifest: MethodManifest | Mapping[str, Any], *, source: str = "local") -> MethodRecord:
        m = manifest if isinstance(manifest, MethodManifest) else MethodManifest.from_dict(manifest)
        if not m.id or not m.capabilities:
            raise ValueError("id_and_capabilities_required")
        # nuevo package entra en quarantine
        m.quarantine = True if not m.tests_passed else m.quarantine
        rec = MethodRecord(manifest=m, registered_at=time.time(), source=source)
        self._by_id[m.id] = rec
        self.save()
        return rec

    def mark_tests_passed(self, method_id: str, passed: bool = True) -> MethodRecord:
        rec = self._by_id.get(method_id)
        if rec is None:
            raise KeyError(method_id)
        rec.manifest.tests_passed = passed
        if passed:
            rec.manifest.quarantine = False
        self.save()
        return rec

    def get(self, method_id: str) -> MethodRecord | None:
        return self._by_id.get(method_id)

    def resolve_capability(self, capability: str, *, only_active: bool = True) -> list[MethodRecord]:
        out: list[MethodRecord] = []
        for rec in self._by_id.values():
            if capability in rec.manifest.capabilities:
                if only_active and not rec.manifest.active:
                    continue
                out.append(rec)
        return out

    def list_active(self) -> list[MethodRecord]:
        return [r for r in self._by_id.values() if r.manifest.active]

    def list_all(self) -> list[MethodRecord]:
        return list(self._by_id.values())
