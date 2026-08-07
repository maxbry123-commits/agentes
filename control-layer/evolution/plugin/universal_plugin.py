"""Universal Plugin + UCC."""
from __future__ import annotations
from dataclasses import asdict, dataclass, field
from typing import Any, Callable, Mapping

@dataclass
class CapabilityContract:
    id: str
    version: str = "1.0.0"
    input_schema: str = "object"
    output_schema: str = "object"
    requires: list = field(default_factory=list)
    provides: list = field(default_factory=list)
    permissions: dict = field(default_factory=dict)
    resources: dict = field(default_factory=dict)
    triggers: list = field(default_factory=list)
    entrypoint: str = ""
    isolation: str = "none"
    owner_plugin: str = ""
    priority: int = 50
    def to_dict(self): return asdict(self)

@dataclass
class PluginManifest:
    id: str
    version: str
    namespace: str
    origin_type: str
    source_repo: str = ""
    source_ref: str = ""
    source_sha256: str = ""
    license_spdx: str = ""
    capabilities: list = field(default_factory=list)
    placement_domain: str = "integrations"
    placement_path: str = ""
    authority_notes: dict = field(default_factory=dict)
    dependencies: list = field(default_factory=list)
    meta: dict = field(default_factory=dict)
    def to_dict(self):
        d = asdict(self)
        d["capabilities"] = [c if isinstance(c, dict) else c.to_dict() for c in self.capabilities]
        return d

@dataclass
class UniversalPlugin:
    manifest: PluginManifest
    handlers: dict = field(default_factory=dict)
    _loaded: bool = False
    def load(self, ctx=None):
        self._loaded = True; return True
    def unload(self):
        self._loaded = False
    def health(self):
        return {"status": "ok" if self._loaded else "down", "plugin_id": self.manifest.id, "capabilities": [c.id for c in self.manifest.capabilities]}
    def capability_ids(self):
        return [c.id for c in self.manifest.capabilities]
    def invoke(self, capability, payload=None):
        if not self._loaded: return {"ok": False, "error": "plugin_not_loaded"}
        h = self.handlers.get(capability)
        if h is None: return {"ok": False, "error": f"unknown_capability:{capability}"}
        return h(dict(payload or {}))
    def to_dict(self):
        return {"manifest": self.manifest.to_dict(), "loaded": self._loaded}
