"""Puente UniversalPlugin ↔ extension.abi.ExtensionABI / WordflowExtension.

REGLA: el kernel solo habla ABI (load/unload/health/capabilities/execute).
Todo plugin evolucionado se monta como handlers del ABI sin tocar el kernel.
"""
from __future__ import annotations

from typing import Any, Mapping

from .plugin.universal_plugin import UniversalPlugin
from .registry.capability_registry import CapabilityRegistry

try:
    from extension.abi import EvidenceOutput, WordflowExtension
except ImportError:  # pragma: no cover
    EvidenceOutput = None  # type: ignore
    WordflowExtension = None  # type: ignore


def mount_plugin_on_extension(ext: Any, plugin: UniversalPlugin) -> list[str]:
    """Registra cada capability del plugin como handler ABI execute()."""
    mounted: list[str] = []
    if not hasattr(ext, "register"):
        return mounted

    def _make_handler(cap_id: str, plug: UniversalPlugin):
        def _handler(params: dict[str, Any], nivel: str = "MID") -> Any:
            if not plug._loaded:
                plug.load({})
            out = plug.invoke(cap_id, params)
            if EvidenceOutput is None:
                return out
            return EvidenceOutput(
                ok=bool(out.get("ok", False)),
                capability=cap_id,
                evidence_hash=f"sha256:evo:{cap_id}",
                data=dict(out),
                error=out.get("error"),
            )

        return _handler

    for cap in plugin.capability_ids():
        ext.register(cap, _make_handler(cap, plugin))
        mounted.append(cap)
    return mounted


def mount_registry_on_extension(ext: Any, registry: CapabilityRegistry) -> list[str]:
    """Monta todas las capabilities del registry en el ABI."""
    all_mounted: list[str] = []
    for pid, plugin in list(registry._plugins.items()):
        all_mounted.extend(mount_plugin_on_extension(ext, plugin))
    return all_mounted


class EvolutionExtensionService:
    """Servicio montable: evolve_path + invoke via ABI."""

    def __init__(self, sources_dir: str = "evolution/sources") -> None:
        from .controller import EvolutionController

        self.controller = EvolutionController(sources_dir=sources_dir)
        self.registry = self.controller.registry

    def evolve(
        self,
        *,
        path: str,
        identity: str,
        source_type: str = "agent",
        repo_url: str = "",
        allow_director_license: bool = False,
    ) -> dict[str, Any]:
        r = self.controller.evolve_path(
            path,
            identity=identity,
            source_type=source_type,
            repo_url=repo_url,
            allow_director_license=allow_director_license,
            register=True,
        )
        return r.to_dict()

    def attach_to_wordflow_extension(self, ext: Any) -> list[str]:
        """Registra capability evolution.evolve + todas las absorbidas."""
        mounted = mount_registry_on_extension(ext, self.registry)

        def _evolve_handler(params: dict[str, Any], nivel: str = "MID") -> Any:
            result = self.evolve(
                path=str(params.get("path") or ""),
                identity=str(params.get("identity") or "unknown"),
                source_type=str(params.get("source_type") or "agent"),
                repo_url=str(params.get("repo_url") or ""),
                allow_director_license=bool(params.get("allow_director_license", False)),
            )
            # re-mount new capabilities
            mount_registry_on_extension(ext, self.registry)
            if EvidenceOutput is None:
                return result
            return EvidenceOutput(
                ok=bool(result.get("ok")),
                capability="evolution.evolve",
                evidence_hash=f"sha256:evolve:{result.get('plugin_id')}",
                data=result,
                error=result.get("error") or None,
            )

        if hasattr(ext, "register"):
            ext.register("evolution.evolve", _evolve_handler)
            mounted.append("evolution.evolve")
        return mounted
