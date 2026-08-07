"""Monta Evolution Engine como extensión del kernel (dual Wordflow).

Uso:
  from extension.evolution_mount import mount_evolution
  from extension.abi import WordflowExtension
  ext = WordflowExtension()
  ext.load({"mount_mode": "extension"})
  svc = mount_evolution(ext)
  ext.execute("evolution.evolve", {"path": "...", "identity": "x"})
"""
from __future__ import annotations

from typing import Any


def mount_evolution(ext: Any, sources_dir: str = "evolution/sources") -> Any:
    from evolution.bridge_abi import EvolutionExtensionService

    svc = EvolutionExtensionService(sources_dir=sources_dir)
    mounted = svc.attach_to_wordflow_extension(ext)
    return svc, mounted
