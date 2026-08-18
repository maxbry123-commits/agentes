"""Instance state isolation — S08/T08
Cada instancia tiene su state.json bajo instances/<id>/state.json
"""
from __future__ import annotations
from pathlib import Path
import json
from typing import Dict, Any, Optional
from .instance import WordflowInstance, InstanceRegistry

DEFAULT_ROOT = Path(__file__).resolve().parents[2] / "instances"

class InstanceStore:
    def __init__(self, root: Optional[Path] = None):
        self.root = root or DEFAULT_ROOT
        self.root.mkdir(parents=True, exist_ok=True)

    def _path(self, instance_id: str) -> Path:
        d = self.root / instance_id
        d.mkdir(parents=True, exist_ok=True)
        return d / "state.json"

    def save(self, inst: WordflowInstance) -> Path:
        path = self._path(inst.instance_id)
        data = {
            "instance_id": inst.instance_id,
            "name": inst.name,
            "created_at": inst.created_at,
            "status": inst.status,
            "config": inst.config,
            "state": inst.state,
        }
        path.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")
        return path

    def load(self, instance_id: str) -> Optional[Dict[str, Any]]:
        path = self._path(instance_id)
        if not path.exists():
            return None
        return json.loads(path.read_text(encoding="utf-8"))

    def exists(self, instance_id: str) -> bool:
        return self._path(instance_id).exists()

class PersistentRegistry(InstanceRegistry):
    """Registry + store (create guarda state.json)."""
    def __init__(self, store: Optional[InstanceStore] = None):
        super().__init__()
        self.store = store or InstanceStore()

    def create(self, name: str, config=None) -> WordflowInstance:
        inst = super().create(name, config)
        self.store.save(inst)
        return inst
