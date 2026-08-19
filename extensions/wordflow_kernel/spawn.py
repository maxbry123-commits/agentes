"""spawn_wordflow — S09/T09

Crea una instancia nueva (copia) sin tocar las que ya existen.
Usa el registro (T07) y el guardado en disco (T08).
T11: optional instance_id so bootstrap can pin the key.
"""
from __future__ import annotations

from typing import Any, Dict, List, Optional

from .instance import WordflowInstance
from .instance_store import InstanceStore, PersistentRegistry

_default_registry = PersistentRegistry()


def get_registry() -> PersistentRegistry:
    return _default_registry


def spawn_wordflow(
    name: str,
    config: Optional[Dict[str, Any]] = None,
    dna: Optional[Dict[str, Any]] = None,
    *,
    registry: Optional[PersistentRegistry] = None,
    start_running: bool = True,
    instance_id: Optional[str] = None,
) -> WordflowInstance:
    """Crea una instancia nueva sin modificar las existentes."""
    reg = registry or _default_registry
    cfg: Dict[str, Any] = dict(config or {})
    if dna is not None:
        cfg["dna"] = dna
    inst = reg.create(name=name, config=cfg, instance_id=instance_id)
    if start_running:
        inst.set_status("running")
        reg.store.save(inst)
    return inst


def list_spawned(registry: Optional[PersistentRegistry] = None) -> List[WordflowInstance]:
    return (registry or _default_registry).list()


def spawn_count(registry: Optional[PersistentRegistry] = None) -> int:
    return (registry or _default_registry).count()


if __name__ == "__main__":
    import tempfile
    from pathlib import Path

    with tempfile.TemporaryDirectory() as tmp:
        store = InstanceStore(root=Path(tmp))
        reg = PersistentRegistry(store=store)
        a = spawn_wordflow("alpha", {"k": 1}, registry=reg)
        b = spawn_wordflow("beta", dna={"v": 2}, registry=reg)
        assert a.instance_id != b.instance_id
        assert a.status == "running"
        assert store.exists(a.instance_id) and store.exists(b.instance_id)
        assert spawn_count(reg) == 2
        print("ok", a.instance_id, b.instance_id, spawn_count(reg))
