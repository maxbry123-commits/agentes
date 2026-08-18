"""spawn_wordflow — S09/T09
Crea una nueva instancia a partir de config/DNA sin tocar otras.
"""
from __future__ import annotations
from typing import Dict, Any, Optional
from .instance import WordflowInstance
from .instance_store import PersistentRegistry, InstanceStore

_registry = PersistentRegistry()

def spawn_wordflow(
    name: str,
    config: Optional[Dict[str, Any]] = None,
    dna: Optional[Dict[str, Any]] = None,
) -> WordflowInstance:
    """
    DNA (opcional) se fusiona en config.
    No modifica instancias existentes.
    """
    cfg = dict(config or {})
    if dna:
        cfg["dna"] = dna
    inst = _registry.create(name=name, config=cfg)
    inst.status = "running"
    _registry.store.save(inst)
    return inst

def get_registry() -> PersistentRegistry:
    return _registry
