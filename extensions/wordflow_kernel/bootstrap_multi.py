"""Bootstrap multi-instance + hook programming pipeline (wire G-W1)."""
from __future__ import annotations
from typing import Optional, Dict, Any
from .spawn import spawn_wordflow, get_registry
from .instance import WordflowInstance

def bootstrap(instance_id: str = "v1", name: str = "default", config: Optional[Dict[str, Any]] = None) -> WordflowInstance:
    reg = get_registry()
    existing = reg.get(instance_id)
    if existing:
        return existing
    cfg = dict(config or {})
    cfg.setdefault("instance_id_preferred", instance_id)
    cfg.setdefault("programming_pipeline", "extensions.wordflow.engine.programming_pipeline.ProgrammingPipeline")
    cfg.setdefault("copy_first", True)
    cfg.setdefault("forensic_post_verify", True)
    inst = spawn_wordflow(name=name, config=cfg)
    return inst

def get_default() -> Optional[WordflowInstance]:
    reg = get_registry()
    for inst in reg.list():
        if inst.config.get("instance_id_preferred") == "v1" or inst.name == "default":
            return inst
    return None

def get_programming_pipeline():
    """Lazy import para no ciclar."""
    from extensions.wordflow.engine.programming_pipeline import default_pipeline
    return default_pipeline()
