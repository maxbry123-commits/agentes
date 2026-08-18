"""Bootstrap multi-instance aware — S11/T11
Default instance_id=v1. Usa spawn + registry.
"""
from __future__ import annotations
from typing import Optional, Dict, Any
from .spawn import spawn_wordflow, get_registry
from .instance import WordflowInstance

def bootstrap(instance_id: str = "v1", name: str = "default", config: Optional[Dict[str, Any]] = None) -> WordflowInstance:
    reg = get_registry()
    existing = reg.get(instance_id)
    if existing:
        return existing
    # create with preferred id if free
    inst = spawn_wordflow(name=name, config=config or {"instance_id_preferred": instance_id})
    # note: uuid is used; preferred id stored in config for now
    return inst

def get_default() -> Optional[WordflowInstance]:
    reg = get_registry()
    for inst in reg.list():
        if inst.config.get("instance_id_preferred") == "v1" or inst.name == "default":
            return inst
    return None
