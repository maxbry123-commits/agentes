"""Monta Evolution Engine como extensión del kernel."""
from __future__ import annotations
from typing import Any

def mount_evolution(ext: Any, sources_dir: str = "evolution/sources", extensions_dir: str = "extensions"):
    from evolution.bridge_abi import EvolutionExtensionService
    svc = EvolutionExtensionService(sources_dir=sources_dir, extensions_dir=extensions_dir)
    mounted = svc.attach_to_wordflow_extension(ext)
    return svc, mounted
