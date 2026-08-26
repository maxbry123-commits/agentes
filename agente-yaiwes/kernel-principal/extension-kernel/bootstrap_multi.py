"""Bootstrap multi-instance aware — T11.

ADAPT: instance_id is the registry/store key (default v1).
If it already exists on disk → load_into_memory; else spawn/create.
"""
from __future__ import annotations

from typing import Any, Dict, Optional

from .instance import WordflowInstance
from .instance_store import PersistentRegistry
from .spawn import get_registry, spawn_wordflow


def bootstrap(
    instance_id: str = "v1",
    name: str = "default",
    config: Optional[Dict[str, Any]] = None,
    *,
    registry: Optional[PersistentRegistry] = None,
) -> WordflowInstance:
    """Create or reuse the instance for instance_id. Does not break multi-instance."""
    if not instance_id or not str(instance_id).strip():
        raise ValueError("instance_id is required")
    instance_id = str(instance_id)
    reg = registry or get_registry()

    existing = reg.get(instance_id)
    if existing is not None:
        return existing

    loaded = reg.load_into_memory(instance_id)
    if loaded is not None:
        return loaded

    cfg = dict(config or {})
    cfg.setdefault("instance_id_preferred", instance_id)
    cfg.setdefault("programming_pipeline", "extensions.wordflow.engine.programming_pipeline.ProgrammingPipeline")
    cfg.setdefault("copy_first", True)
    cfg.setdefault("forensic_post_verify", True)
    return spawn_wordflow(
        name=name,
        config=cfg,
        registry=reg,
        instance_id=instance_id,
    )


def get_default() -> Optional[WordflowInstance]:
    reg = get_registry()
    hit = reg.get("v1")
    if hit is not None:
        return hit
    for inst in reg.list():
        if inst.config.get("instance_id_preferred") == "v1" or inst.name == "default":
            return inst
    return None


def get_programming_pipeline():
    """Lazy import para no ciclar."""
    from extensions.wordflow.engine.programming_pipeline import default_pipeline

    return default_pipeline()


if __name__ == "__main__":
    import tempfile
    from pathlib import Path

    from .instance_store import InstanceStore

    with tempfile.TemporaryDirectory() as tmp:
        store = InstanceStore(root=Path(tmp))
        reg = PersistentRegistry(store=store)
        a = bootstrap("v1", name="default", registry=reg)
        b = bootstrap("v2", name="second", registry=reg)
        a2 = bootstrap("v1", name="default", registry=reg)
        assert a.instance_id == "v1", a.instance_id
        assert b.instance_id == "v2", b.instance_id
        assert a.instance_id != b.instance_id
        assert a2.instance_id == a.instance_id
        assert store.exists("v1") and store.exists("v2")
        print("ok", a.instance_id, b.instance_id)
