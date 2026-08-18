"""InstanceStore + PersistentRegistry — S08/T08

Cada instancia guarda su estado en:
  instances/<instance_id>/state.json

Así A y B no comparten el mismo archivo.
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, Optional

from .instance import InstanceRegistry, WordflowInstance

# Carpeta raíz de instancias (inyectable en tests)
DEFAULT_ROOT = Path(__file__).resolve().parents[2] / "instances"


class InstanceStore:
    """Guarda y lee el state.json de cada instancia."""

    def __init__(self, root: Optional[Path] = None) -> None:
        self.root = Path(root) if root is not None else DEFAULT_ROOT
        self.root.mkdir(parents=True, exist_ok=True)

    def dir_for(self, instance_id: str) -> Path:
        if not instance_id or "/" in instance_id or "\\" in instance_id or ".." in instance_id:
            raise ValueError(f"invalid instance_id: {instance_id!r}")
        d = self.root / instance_id
        d.mkdir(parents=True, exist_ok=True)
        return d

    def path_for(self, instance_id: str) -> Path:
        return self.dir_for(instance_id) / "state.json"

    def save(self, inst: WordflowInstance) -> Path:
        path = self.path_for(inst.instance_id)
        data = {
            "instance_id": inst.instance_id,
            "name": inst.name,
            "created_at": inst.created_at,
            "status": inst.status,
            "config": inst.config,
            "state": inst.state,
        }
        path.write_text(
            json.dumps(data, indent=2, ensure_ascii=False),
            encoding="utf-8",
        )
        return path

    def load(self, instance_id: str) -> Optional[Dict[str, Any]]:
        path = self.path_for(instance_id)
        if not path.is_file():
            return None
        return json.loads(path.read_text(encoding="utf-8"))

    def exists(self, instance_id: str) -> bool:
        return self.path_for(instance_id).is_file()

    def delete(self, instance_id: str) -> bool:
        """Borra state.json si existe. No toca el registry en memoria."""
        path = self.path_for(instance_id)
        if not path.is_file():
            return False
        path.unlink()
        return True


class PersistentRegistry(InstanceRegistry):
    """Registro en memoria + guarda en disco al crear."""

    def __init__(self, store: Optional[InstanceStore] = None) -> None:
        super().__init__()
        self.store = store or InstanceStore()

    def create(
        self,
        name: str,
        config: Optional[Dict[str, Any]] = None,
        *,
        instance_id: Optional[str] = None,
    ) -> WordflowInstance:
        inst = super().create(name, config, instance_id=instance_id)
        self.store.save(inst)
        return inst

    def terminate(self, instance_id: str) -> WordflowInstance:
        inst = super().terminate(instance_id)
        self.store.save(inst)
        return inst

    def load_into_memory(self, instance_id: str) -> Optional[WordflowInstance]:
        """Lee state.json y mete la instancia en el registry si no estaba."""
        data = self.store.load(instance_id)
        if not data:
            return None
        if self.has(instance_id):
            return self.get(instance_id)
        inst = WordflowInstance(
            instance_id=data["instance_id"],
            name=data["name"],
            created_at=data.get("created_at", ""),
            config=dict(data.get("config") or {}),
            state=dict(data.get("state") or {}),
            status=data.get("status") or "created",
        )
        self._instances[inst.instance_id] = inst
        return inst


if __name__ == "__main__":
    import tempfile

    with tempfile.TemporaryDirectory() as tmp:
        store = InstanceStore(root=Path(tmp))
        reg = PersistentRegistry(store=store)
        a = reg.create("inst_a", {"role": "test"})
        b = reg.create("inst_b")
        assert store.exists(a.instance_id)
        assert store.exists(b.instance_id)
        assert store.path_for(a.instance_id) != store.path_for(b.instance_id)
        loaded = store.load(a.instance_id)
        assert loaded is not None
        assert loaded["name"] == "inst_a"
        assert loaded["config"]["role"] == "test"
        reg.terminate(a.instance_id)
        again = store.load(a.instance_id)
        assert again is not None and again["status"] == "terminated"
        print("ok", a.instance_id, b.instance_id, store.root)
