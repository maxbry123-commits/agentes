"""Capability Registry."""
from __future__ import annotations
from dataclasses import asdict, dataclass
from typing import Any
from ..plugin.universal_plugin import UniversalPlugin

@dataclass
class RegistryEntry:
    capability_id: str
    plugin_id: str
    contract: dict
    priority: int = 50
    domain: str = ""
    def to_dict(self): return asdict(self)

class CapabilityRegistry:
    def __init__(self):
        self._by_cap = {}
        self._plugins = {}
    def register_plugin(self, plugin: UniversalPlugin, domain=""):
        self._plugins[plugin.manifest.id] = plugin
        registered = []
        for c in plugin.manifest.capabilities:
            entry = RegistryEntry(c.id, plugin.manifest.id, c.to_dict(), c.priority, domain or plugin.manifest.placement_domain)
            self._by_cap.setdefault(c.id, []).append(entry)
            self._by_cap[c.id].sort(key=lambda e: -e.priority)
            registered.append(c.id)
        return registered
    def resolve(self, capability_id):
        entries = self._by_cap.get(capability_id) or []
        return entries[0] if entries else None
    def list_capabilities(self):
        return sorted(self._by_cap.keys())
    def invoke(self, capability_id, payload=None):
        entry = self.resolve(capability_id)
        if not entry: return {"ok": False, "error": f"capability_not_found:{capability_id}"}
        plugin = self._plugins.get(entry.plugin_id)
        if not plugin: return {"ok": False, "error": f"plugin_missing:{entry.plugin_id}"}
        if not plugin._loaded: plugin.load({})
        return plugin.invoke(capability_id, payload)
    def to_dict(self):
        return {"capabilities": {k: [e.to_dict() for e in v] for k, v in self._by_cap.items()}, "plugins": list(self._plugins.keys())}
